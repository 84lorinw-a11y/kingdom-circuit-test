"""Add a fail-closed, server-side review gate to an exact Cloudflare game build.

No credentials or private music belong in this repository or build output.
--game-revision keeps the already-live game unchanged during a security release.
"""
import argparse
import io
import json
import re
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))
import build_cloudflare_game as public

WORKER = Path(__file__).with_name('worker.mjs')
PINNED_PATHS = ['scripts/build_chh_game.py', 'scripts/build_cloudflare_game.py',
                'test-overrides/chh-show-night', 'test-overrides/chh-show-night-manifest.json']


def base_files(revision=None):
    if revision is None:
        return public.expected_files()
    assert re.fullmatch(r'[0-9a-f]{40}', revision), 'Use an exact reviewed game commit'
    exists = subprocess.run(['git', 'cat-file', '-e', revision + '^{commit}'], cwd=ROOT,
                            capture_output=True).returncode == 0
    if not exists:
        # Cloudflare may make a shallow clone. Fetch only the explicitly pinned
        # TEST commit, never another repository, branch or mutable release tag.
        subprocess.run(['git', 'fetch', '--no-tags', '--depth=1',
                        'https://github.com/84lorinw-a11y/kingdom-circuit-test.git', revision],
                       cwd=ROOT, check=True)
    archive = subprocess.check_output(['git', 'archive', revision, '--', *PINNED_PATHS], cwd=ROOT)
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
            for member in tar.getmembers():
                path = Path(member.name)
                assert not path.is_absolute() and '..' not in path.parts
                assert member.isfile() or member.isdir(), 'Unexpected archive link'
                target = root / path
                if member.isdir():
                    target.mkdir(parents=True, exist_ok=True)
                else:
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_bytes(tar.extractfile(member).read())
        out = root / 'output'
        subprocess.run([sys.executable, str(root / 'scripts/build_cloudflare_game.py'), str(out)],
                       check=True, capture_output=True)
        return {p.relative_to(out).as_posix(): p.read_bytes() for p in out.rglob('*') if p.is_file()}


def expected_files(revision=None):
    result = base_files(revision)
    result['_worker.js'] = WORKER.read_bytes()
    result['_routes.json'] = b'{"version":1,"include":["/*"],"exclude":[]}\n'
    # Worker responses also override the old public asset cache headers.
    result['_headers'] = b'/*\n  Cache-Control: private, no-store\n  X-Robots-Tag: noindex, nofollow, noarchive\n  X-Content-Type-Options: nosniff\n'
    return result


def verify(site, revision=None, expected=None):
    expected = expected if expected is not None else expected_files(revision)
    actual = {p.relative_to(site).as_posix() for p in site.rglob('*') if p.is_file()}
    assert actual == set(expected), 'Unexpected or missing private-review artifact file'
    for name, data in expected.items():
        file = site / name
        assert not file.is_symlink() and file.read_bytes() == data, f'Review file mismatch: {name}'
    assert json.loads((site / '_routes.json').read_text()) == {'version': 1, 'include': ['/*'], 'exclude': []}
    assert not any(name.endswith(('.env', '.toml', '.sql')) for name in actual)
    assert all(len(data) <= public.MAX_FILE_BYTES for data in expected.values())
    return {'privateReview': True, 'files': len(expected), 'bytes': sum(map(len, expected.values())),
            'gameRevision': revision or 'current', 'credentialsIncluded': False,
            'requiredBindings': ['APOLLO_REVIEW_PASSWORD', 'REVIEW_AUTH_DB'],
            'requiresCloudflareFailClosed': True, 'deploymentPerformed': False}


def build(site, revision=None):
    expected = expected_files(revision)
    assert not site.is_symlink()
    assert not site.exists() or not any(site.iterdir()), 'Use an empty output directory'
    site.mkdir(parents=True, exist_ok=True)
    for name, data in expected.items():
        target = site / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    return verify(site, revision, expected)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('site', type=Path)
    parser.add_argument('--game-revision')
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    print(json.dumps(verify(args.site, args.game_revision) if args.check else build(args.site, args.game_revision), indent=2))
