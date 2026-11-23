"""Mirror the exact live Pages package without crawling thousands of public URLs."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import tarfile
import tempfile
import urllib.error
import urllib.request
import zipfile

from capture_live_site import capture, fetch, output_path, SEPARATELY_MANAGED_PATH_PREFIXES

REPOSITORY = '84lorinw-a11y/kingdom-circuit'


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def github(path: str, token: str) -> bytes:
    request = urllib.request.Request('https://api.github.com/repos/' + REPOSITORY + path,
        headers={'User-Agent': 'KingdomCircuitTestMirror/3.0',
                 'Authorization': 'Bearer ' + token, 'Accept': 'application/vnd.github+json'})
    try:
        with urllib.request.build_opener(NoRedirect).open(request, timeout=60) as response:
            return response.read()
    except urllib.error.HTTPError as error:
        if error.code != 302:
            raise
        # Never forward GitHub credentials to the signed artifact storage URL.
        destination = error.headers['Location']
        if not destination.startswith('https://'):
            raise ValueError('Artifact redirect must use HTTPS')
        with urllib.request.urlopen(destination, timeout=180) as response:
            return response.read()


def identity(manifest: dict) -> tuple[str, str, str]:
    match = re.fullmatch(r'([a-f0-9]{40})-([0-9]+)-([0-9]+)', manifest.get('releaseId', ''))
    if not match or not manifest.get('files'):
        raise ValueError('Invalid live publication identity')
    return match.groups()


def select_artifact(artifacts: list[dict], run: str, attempt: str) -> dict:
    name = f'github-pages-{run}-{attempt}'
    matches = [item for item in artifacts if item.get('name') == name and not item.get('expired')]
    if len(matches) != 1:
        raise FileNotFoundError('Exact published Pages artifact is unavailable')
    return matches[0]


def unpack(package: bytes, output: Path) -> None:
    with tempfile.TemporaryDirectory() as temporary:
        archive = Path(temporary) / 'pages.zip'
        archive.write_bytes(package)
        with zipfile.ZipFile(archive) as bundle:
            if bundle.namelist() != ['artifact.tar']:
                raise ValueError('Unexpected Pages package contents')
            with bundle.open('artifact.tar') as source, (Path(temporary) / 'pages.tar').open('wb') as target:
                shutil.copyfileobj(source, target)
        with tarfile.open(Path(temporary) / 'pages.tar') as archive:
            members = archive.getmembers()
            for member in members:
                path = PurePosixPath(member.name)
                if path.is_absolute() or '..' in path.parts or not (member.isfile() or member.isdir()):
                    raise ValueError('Unsafe Pages package member')
            archive.extractall(output, members=members, filter='data')


def verify(output: Path, manifest: dict, min_html: int, min_files: int) -> None:
    saved = json.loads((output / 'publication-manifest.json').read_text())
    if saved != manifest:
        raise ValueError('Package does not match the currently published release')
    for path, entry in manifest['files'].items():
        if entry.get('kind') == 'not-found':
            continue
        relative = PurePosixPath(path)
        if not path.startswith('/') or '..' in relative.parts:
            raise ValueError('Invalid publication file path')
        target = output_path('https://kingdomcircuit.com' + path,
                             'text/html' if entry.get('kind') == 'html' else '', output)
        if not target.is_file() or hashlib.sha256(target.read_bytes()).hexdigest() != entry['sha256']:
            raise ValueError('Publication file mismatch: ' + path)
    files = [path for path in output.rglob('*') if path.is_file()]
    if len(files) < min_files or sum(path.suffix == '.html' for path in files) < min_html:
        raise ValueError('Incomplete published package')


def capture_release(origin: str, output: Path, *, token: str, min_html: int = 800,
                    min_files: int = 900) -> dict:
    _, _, payload = fetch(origin + '/publication-manifest.json')
    manifest = json.loads(payload)
    sha, run, attempt = identity(manifest)
    mode = 'published-pages-package'
    try:
        artifacts = json.loads(github(f'/actions/runs/{run}/artifacts?per_page=100', token))['artifacts']
        artifact = select_artifact(artifacts, run, attempt)
        package = github(f"/actions/artifacts/{artifact['id']}/zip", token)
    except (urllib.error.HTTPError, urllib.error.URLError, FileNotFoundError, TimeoutError) as error:
        # Cross-repository credentials or retention may prevent artifact access.
        # Retain the strict public capture with pacing and shared rate-limit waits.
        print('Published package unavailable; using paced public capture: ' + type(error).__name__)
        capture(origin, output, workers=4, min_html=min_html, min_files=min_files,
                publication_manifest=True)
        mode = 'paced-public-capture'
    else:
        digest = artifact.get('digest')
        if digest and digest != 'sha256:' + hashlib.sha256(package).hexdigest():
            raise ValueError('Pages package digest mismatch')
        if output.exists():
            shutil.rmtree(output)
        output.mkdir(parents=True)
        unpack(package, output)
        verify(output, manifest, min_html, min_files)
        for prefix in SEPARATELY_MANAGED_PATH_PREFIXES:
            shutil.rmtree(output / prefix.strip('/'), ignore_errors=True)
    _, _, current = fetch(origin + '/publication-manifest.json')
    if current != payload:
        raise ValueError('Production changed during test capture; retry with the new release')
    return {'sha': sha, 'run_id': run, 'attempt': attempt, 'mode': mode,
            'publicationReleaseId': manifest['releaseId']}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('origin')
    parser.add_argument('output', type=Path)
    parser.add_argument('--min-html', type=int, default=800)
    parser.add_argument('--min-files', type=int, default=900)
    parser.add_argument('--github-output', action='store_true')
    args = parser.parse_args()
    receipt = capture_release(args.origin.rstrip('/'), args.output, token=os.environ.get('GH_TOKEN', ''),
                              min_html=args.min_html, min_files=args.min_files)
    Path('test-capture-receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
    if args.github_output:
        with open(os.environ['GITHUB_OUTPUT'], 'a') as output:
            for key in ('sha', 'run_id'):
                output.write(f'{key}={receipt[key]}\n')
    print(json.dumps(receipt, indent=2))
