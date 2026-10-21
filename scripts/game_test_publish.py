"""Reuse a verified TEST website for game releases, without contacting the live site.

Only full-refresh runs create snapshots. Each archive stores the live baseline and
the verified test pages, excluding /play/. Identical files share one SHA-256 object
so website images are stored only once. The archive never enters the Pages output.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parents[1]
CACHE_PREFIX = 'verified-test-website-v1-'
REFERENCE = Path('_website_reference/reference.json')
WORKFLOW = '.github/workflows/mirror-live.yml'
MIRROR_MANIFEST = 'test-live-mirror-manifest.json'
RECOVERY = 'Run Mirror Live Site to Test manually with mode=full-refresh, then retry the game update.'
GAME_PREFIXES = ('test-overrides/chh-show-night/', 'game-backend/', 'tests/chh-game/')
GAME_FILES = frozenset({
    'test-overrides/chh-show-night-manifest.json', 'scripts/build_chh_game.py',
    'scripts/build_cloudflare_game.py', 'tests/test_chh_game.py',
    'tests/test_cloudflare_game.py', 'tests/test_game_test_publish.py',
    '.github/workflows/cloudflare-game-check.yml',
})


def is_game_path(path: str) -> bool:
    return path in GAME_FILES or path.startswith(GAME_PREFIXES)


def publish_mode(event_name: str, event: dict, changed: list[str]) -> str:
    if event_name == 'workflow_dispatch':
        mode = event.get('inputs', {}).get('mode', 'full-refresh')
        if mode not in {'game-only', 'full-refresh'}:
            raise ValueError('Unknown publishing mode')
        return mode
    if event_name != 'push' or not changed:
        return 'full-refresh'
    # Release notes often accompany a game update. They are not deployed.
    relevant = [path for path in changed if not path.endswith('.md')]
    return 'game-only' if relevant and all(map(is_game_path, relevant)) else 'full-refresh'


def changed_paths(event: dict) -> list[str]:
    before, after = event.get('before', ''), event.get('after', '')
    if not re.fullmatch(r'[0-9a-f]{40}', before) or before == '0' * 40:
        return []
    if not re.fullmatch(r'[0-9a-f]{40}', after):
        raise ValueError('Invalid push revision')
    if subprocess.run(['git', 'cat-file', '-e', before + '^{commit}'],
                      cwd=ROOT, capture_output=True).returncode:
        subprocess.run(['git', 'fetch', '--no-tags', '--depth=1', 'origin', before], cwd=ROOT, check=True)
    # Include every commit and both sides of renames; never rely on truncated event file lists.
    result = subprocess.check_output(['git', 'diff', '--no-renames', '--name-only', '-z', before, after], cwd=ROOT)
    return [name for name in result.decode().split('\0') if name]


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def files(root: Path, *, omit_game: bool = False) -> dict[str, bytes]:
    result = {}
    for path in sorted(root.rglob('*')):
        if path.is_symlink():
            raise ValueError(f'Symlink not allowed: {path}')
        if path.is_file():
            relative = path.relative_to(root).as_posix()
            if not (omit_game and relative.startswith('play/')):
                result[relative] = path.read_bytes()
    if not result:
        raise ValueError(f'Empty website: {root}')
    return result


def recipe(root: Path = ROOT) -> str:
    # A manually requested game-only run must not silently skip changed website code.
    sources = {}
    for directory in ('scripts', 'test-overrides'):
        for path in sorted((root / directory).rglob('*')):
            relative = path.relative_to(root).as_posix()
            if path.is_file() and '__pycache__' not in path.parts and not is_game_path(relative):
                sources[relative] = sha(path.read_bytes())
    sources[WORKFLOW] = sha((root / WORKFLOW).read_bytes())
    return sha(json.dumps(sources, sort_keys=True).encode())


def seal(live: Path, site: Path, archive: Path, *, source_run: str, source_commit: str) -> dict:
    from verify_live_baseline import verify
    verify(live, site)  # The saved website must pass the same complete release gate.
    inventories = {'live': files(live), 'site': files(site, omit_game=True)}
    metadata = {
        'version': 1, 'recipe': recipe(), 'sourceRun': source_run,
        'sourceCommit': source_commit, 'sourceAttempt': os.environ.get('GITHUB_RUN_ATTEMPT', '1'),
        'trees': {name: {path: sha(data) for path, data in tree.items()}
                  for name, tree in inventories.items()},
    }
    archive.parent.mkdir(parents=True, exist_ok=True)
    objects = {sha(data): data for tree in inventories.values() for data in tree.values()}
    with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED) as output:
        output.writestr('snapshot.json', json.dumps(metadata, sort_keys=True))
        for digest, data in sorted(objects.items()):
            output.writestr('objects/' + digest, data)
    return metadata


def read_snapshot(archive: Path) -> tuple[dict, dict[str, bytes]]:
    if not archive.is_file():
        raise ValueError('Verified website snapshot is missing. ' + RECOVERY)
    with zipfile.ZipFile(archive) as source:
        metadata = json.loads(source.read('snapshot.json'))
        if metadata.get('version') != 1 or metadata.get('recipe') != recipe():
            raise ValueError('Website publishing recipe changed. ' + RECOVERY)
        trees = metadata['trees']
        if set(trees) != {'live', 'site'} or not all(trees.values()):
            raise ValueError('Incomplete snapshot')
        digests = set()
        for name, tree in trees.items():
            for path, digest in tree.items():
                parts = PurePosixPath(path)
                if (parts.is_absolute() or '..' in parts.parts or '\\' in path
                        or path != parts.as_posix() or path in {'', '.'}
                        or (name == 'site' and (parts.parts[0] == 'play' or path == 'CNAME'))):
                    raise ValueError(f'Unsafe snapshot path: {path}')
                if not re.fullmatch(r'[0-9a-f]{64}', digest):
                    raise ValueError('Invalid snapshot digest')
                digests.add(digest)
        expected = {'snapshot.json'} | {'objects/' + digest for digest in digests}
        if set(source.namelist()) != expected or len(source.namelist()) != len(expected):
            raise ValueError('Unexpected or duplicate snapshot objects')
        objects = {digest: source.read('objects/' + digest) for digest in digests}
        if any(sha(data) != digest for digest, data in objects.items()):
            raise ValueError('Snapshot checksum mismatch. ' + RECOVERY)
    return metadata, objects


def restore(archive: Path, live: Path, site: Path, *, source_run: str, source_commit: str,
            source_key: str = '') -> dict:
    metadata, objects = read_snapshot(archive)
    if metadata['sourceRun'] != source_run or metadata['sourceCommit'] != source_commit:
        raise ValueError('Snapshot provenance does not match its successful workflow run')
    if source_key and source_key != CACHE_PREFIX + source_run + '-' + metadata['sourceAttempt']:
        raise ValueError('Cache returned a different workflow attempt; refusing a partial match')
    if live.exists() or site.exists():
        raise ValueError('Restore requires new, empty output paths')
    for name, root in (('live', live), ('site', site)):
        root.mkdir(parents=True)
        for relative, digest in metadata['trees'][name].items():
            path = root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(objects[digest])
    return metadata


def check_unchanged(archive: Path, site: Path) -> int:
    metadata, objects = read_snapshot(archive)
    expected = dict(metadata['trees']['site'])
    actual = {path: sha(data) for path, data in files(site, omit_game=True).items()}
    # The release gate updates only these game-derived counts in its audit manifest.
    old = json.loads(objects[expected.pop(MIRROR_MANIFEST)])
    new = json.loads((site / MIRROR_MANIFEST).read_text())
    actual.pop(MIRROR_MANIFEST)
    for key in ('chhShowNight', 'isolatedExperimentFileCount', 'htmlPageCount'):
        old.pop(key, None)
        new.pop(key, None)
    if actual != expected or new != old:
        raise ValueError('Game-only update changed the verified website; refusing to publish')
    print(f'Confirmed {len(actual)} non-game website files are byte-identical; no live-site capture.')
    return len(actual)


def api(path: str) -> dict:
    request = urllib.request.Request('https://api.github.com/' + path, headers={
        'Accept': 'application/vnd.github+json',
        'Authorization': 'Bearer ' + os.environ['GH_TOKEN'],
        'User-Agent': 'KingdomCircuitTestPublisher',
    })
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.load(response)


def find_snapshot(repository: str, request=api) -> dict:
    if repository != '84lorinw-a11y/kingdom-circuit-test':
        raise ValueError('This publisher is restricted to the test repository')
    prefix = f'repos/{repository}/actions'
    for page in range(1, 11):
        runs = request(f'{prefix}/workflows/mirror-live.yml/runs?branch=main&status=success&per_page=100&page={page}')['workflow_runs']
        for run in runs:
            if (run['status'] == 'completed' and run['conclusion'] == 'success'
                    and run['path'] == WORKFLOW and run['head_branch'] == 'main'
                    and run['head_repository']['full_name'] == repository):
                # Follow the LAST successful publication's small reference. Never
                # fall back to an older cache: doing so could roll back new listings.
                return {'published_run': str(run['id'])}
        if len(runs) < 100:
            break
    raise ValueError('No successful test publication is available. ' + RECOVERY)


def reference(archive: Path | None = None) -> dict:
    if archive:
        metadata, _ = read_snapshot(archive)
        values = {'cache_key': CACHE_PREFIX + metadata['sourceRun'] + '-' + metadata['sourceAttempt'],
                  'run_id': metadata['sourceRun'], 'sha': metadata['sourceCommit']}
        REFERENCE.parent.mkdir(parents=True, exist_ok=True)
        REFERENCE.write_text(json.dumps(values) + '\n')
    else:
        if not REFERENCE.is_file():
            raise ValueError('Last publication has no verified website reference. ' + RECOVERY)
        values = json.loads(REFERENCE.read_text())
        if (not re.fullmatch(re.escape(CACHE_PREFIX) + re.escape(values['run_id']) + r'-\d+', values['cache_key'])
                or not re.fullmatch(r'\d+', values['run_id'])
                or not re.fullmatch(r'[0-9a-f]{40}', values['sha'])):
            raise ValueError('Invalid website reference')
    return values


def output(values: dict) -> None:
    for key, value in values.items():
        print(f'{key}={value}')
    if os.environ.get('GITHUB_OUTPUT'):
        with open(os.environ['GITHUB_OUTPUT'], 'a') as target:
            for key, value in values.items():
                target.write(f'{key}={value}\n')


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('route', 'find', 'seal', 'restore', 'check', 'read-reference', 'write-reference'))
    parser.add_argument('--archive', type=Path, default=Path('_website_snapshot/website.zip'))
    parser.add_argument('--live', type=Path, default=Path('_live_site'))
    parser.add_argument('--site', type=Path, default=Path('_site'))
    parser.add_argument('--source-run', default=os.environ.get('GITHUB_RUN_ID', ''))
    parser.add_argument('--source-commit', default=os.environ.get('GITHUB_SHA', ''))
    parser.add_argument('--source-key', default='')
    args = parser.parse_args()
    if args.command == 'route':
        event_name = os.environ['GITHUB_EVENT_NAME']
        event = json.loads(Path(os.environ['GITHUB_EVENT_PATH']).read_text())
        changed = changed_paths(event) if event_name == 'push' else []
        output({'mode': publish_mode(event_name, event, changed)})
    elif args.command == 'find':
        output(find_snapshot(os.environ['GITHUB_REPOSITORY']))
    elif args.command == 'seal':
        seal(args.live, args.site, args.archive, source_run=args.source_run, source_commit=args.source_commit)
    elif args.command == 'restore':
        restore(args.archive, args.live, args.site, source_run=args.source_run,
                source_commit=args.source_commit, source_key=args.source_key)
    elif args.command == 'read-reference':
        output(reference())
    elif args.command == 'write-reference':
        reference(args.archive)
    else:
        check_unchanged(args.archive, args.site)


if __name__ == '__main__':
    main()
