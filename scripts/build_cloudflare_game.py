"""Package the manifest-approved Apollo draft for Cloudflare Pages Git builds.

GitHub remains the source of truth. This creates only static game files and
Cloudflare routing/header rules; it never changes DNS or deploys an account.
"""
import argparse
import hashlib
import json
import re
import tempfile
from pathlib import Path

import build_chh_game as game

MAX_FILE_BYTES = 25 * 1024 * 1024
MAX_FILES = 20000


def asset_version(files: dict[str, bytes]) -> str:
    digest = hashlib.sha256()
    for name, data in sorted(files.items()):
        if name.startswith('play/assets/'):
            digest.update(name.encode() + b'\0' + hashlib.sha256(data).digest())
    return digest.hexdigest()[:16]


def expected_files() -> dict[str, bytes]:
    approved = game.expected_files()
    # Retain every existing game safeguard, including the approved cast,
    # device-only scores, silent video and exact source inventory checks.
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        for name, data in approved.items():
            target = root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
        game.verify(root)

    version = asset_version(approved)
    prefix = f'/play/assets/{version}/'
    result = {}
    for name, data in approved.items():
        if name.startswith('play/assets/'):
            name = name.replace('play/assets/', prefix.lstrip('/'), 1)
        elif Path(name).suffix in game.TEXT_EXTENSIONS:
            # Lazy arcade loaders resolve ./assets/ against import.meta.url.
            # They need the same media namespace as the venue's absolute URLs,
            # including template strings such as ./assets/${file}.
            text = data.decode().replace(game.BASE, '/play/')
            data = text.replace('/play/assets/', prefix).replace('./assets/', prefix).encode()
        result[name] = data

    result['index.html'] = b'''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex,nofollow"><meta http-equiv="refresh" content="0;url=/play/"><title>Apollo draft</title><a href="/play/">Enter the Apollo draft</a></html>'''
    result['404.html'] = b'''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex,nofollow"><title>Not found</title><h1>This spot is not part of the show.</h1><a href="/play/">Back to the game</a></html>'''
    result['robots.txt'] = b'User-agent: *\nDisallow: /\n'
    result['_redirects'] = b'/ /play/ 302\n'
    headers = [
        '/*',
        '  X-Robots-Tag: noindex, nofollow',
        '  X-Content-Type-Options: nosniff',
        '  Referrer-Policy: strict-origin-when-cross-origin',
        '  X-Frame-Options: DENY',
        '  Permissions-Policy: camera=(), microphone=(), geolocation=()',
        '', prefix + '*',
        '  Cache-Control: public, max-age=31536000, immutable',
    ]
    # Cache media by a content-derived namespace. Revalidate the small runtime
    # so a returning player receives fixes without a stale HTML/JS mixture.
    paths = {'/', '/play/'} | {'/' + name for name in result if Path(name).suffix in game.TEXT_EXTENSIONS}
    for path in sorted(paths):
        headers.extend(['', path, '  Cache-Control: no-cache'])
    assert len(paths) + 2 <= 100, 'Cloudflare header-rule limit exceeded'
    result['_headers'] = ('\n'.join(headers) + '\n').encode()
    assert len(result) <= MAX_FILES, 'Cloudflare file limit exceeded'
    assert all(len(data) <= MAX_FILE_BYTES for data in result.values()), 'Cloudflare per-file size limit exceeded'
    return result


def verify(site: Path, expected=None) -> dict:
    expected = expected if expected is not None else expected_files()
    actual = {p.relative_to(site).as_posix() for p in site.rglob('*') if p.is_file()}
    assert actual == set(expected), 'Unexpected or missing Cloudflare artifact files'
    for name, data in expected.items():
        path = site / name
        assert not path.is_symlink(), 'Cloudflare artifact may not contain symlinks'
        assert path.read_bytes() == data, f'Cloudflare content mismatch: {name}'
        if path.suffix in game.TEXT_EXTENSIONS:
            text = data.decode()
            assert game.BASE not in text, f'GitHub-only base path remains: {name}'
            assert './assets/' not in text, f'Unversioned lazy artwork URL remains: {name}'
            for ref in re.findall(r'''(?:from\s+|(?:href|src)=)["'](\.[^"']+|/play/[^"']*)''', text):
                ref = ref.split('?')[0].split('#')[0]
                target = site / ref.lstrip('/') if ref.startswith('/') else path.parent / ref
                if target.is_dir():
                    target /= 'index.html'
                assert target.is_file(), f'Missing Cloudflare dependency: {ref}'
    assert not any(name.endswith(('.env', '.toml')) or name.startswith(('functions/', '_worker')) for name in actual)
    media = {name: data for name, data in expected.items() if name.startswith('play/assets/')}
    return {'route': '/play/', 'files': len(expected), 'bytes': sum(map(len, expected.values())),
            'mediaFiles': len(media), 'largestFileBytes': max(map(len, expected.values())),
            'assetVersion': next(iter(media)).split('/')[2], 'staticOnly': True,
            'scoreboard': 'device-only', 'deploymentPerformed': False}


def build(site: Path) -> dict:
    expected = expected_files()
    assert not site.is_symlink(), 'Output directory must not be a symlink'
    assert not site.exists() or not any(site.iterdir()), 'Use an empty output directory; no existing files will be overwritten'
    site.mkdir(parents=True, exist_ok=True)
    for name, data in expected.items():
        target = site / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    return verify(site, expected)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('site', type=Path)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    print(json.dumps(verify(args.site) if args.check else build(args.site), indent=2))
