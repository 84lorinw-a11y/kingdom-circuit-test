"""Publish the owner-approved, password-free game as an isolated test route."""
import argparse
import hashlib
import json
import re
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'test-overrides/chh-show-night'
MANIFEST = json.loads((ROOT / 'test-overrides/chh-show-night-manifest.json').read_text())
BASE = '/kingdom-circuit-test/play/'
GAME_FILES = frozenset('play/' + name for name in MANIFEST)
TEXT_EXTENSIONS = {'.html', '.css', '.mjs'}


def expected_files() -> dict[str, bytes]:
    actual = {p.relative_to(SOURCE).as_posix() for p in SOURCE.rglob('*') if p.is_file()}
    assert actual == set(MANIFEST), 'Game source inventory changed without a reviewed manifest'
    result = {}
    for name, digest in MANIFEST.items():
        relative = PurePosixPath(name)
        assert not relative.is_absolute() and '..' not in relative.parts
        assert relative.suffix in TEXT_EXTENSIONS | {'.png', '.jpg', '.webp', '.m4a', '.wav', '.mp4'}
        source = SOURCE / name
        assert not source.is_symlink(), 'Game sources may not be symlinks'
        data = source.read_bytes()
        assert hashlib.sha256(data).hexdigest() == digest, f'Game source changed: {name}'
        if relative.suffix in TEXT_EXTENSIONS:
            text = data.decode('utf-8')
            assert not any(s in text for s in ('PLAY_PASSWORD', '/api/login', '/api/logout', 'googletagmanager.com'))
            data = text.replace('/play/', BASE).encode('utf-8')
        result['play/' + name] = data
    return result


def verify(site: Path) -> dict:
    expected = expected_files()
    actual = {p.relative_to(site).as_posix() for p in (site / 'play').rglob('*') if p.is_file()}
    assert actual == set(expected), 'Unexpected or missing game deployment files'
    for name, data in expected.items():
        assert (site / name).read_bytes() == data, f'Game content mismatch: {name}'
    page = (site / 'play/index.html').read_text()
    assert '<meta name="robots" content="noindex,nofollow">' in page
    assert 'id="lock"' not in page and 'type="password"' not in page
    assert 'TEST PREVIEW' in page and 'Content-Security-Policy' in page
    assert 'id="scoreboard"' in page and 'id="menu"' in page
    assert 'aria-valuemax="125"' not in page
    scoring = (site / 'play/scoring.mjs').read_text()
    assert 'ROUND_MAX=1000' in scoring and 'OPPORTUNITIES=20' in scoring
    assert all(name in scoring for name in ('eli', 'marty', 'brenno', 'apollo'))
    assert '<meta name="score-service" content="">' in page, 'Apollo TEST must stay off the original competition'
    assert "connect-src 'self';" in page
    assert "script-src 'self';" in page
    assert "frame-src 'none';" in page
    assert 'youtube' not in page.lower()
    assert (site / 'play/assets/video/apollo-stage-draft-v2.mp4').is_file()
    assert "createOnlineScores(localStorage,{base:''})" in (site / 'play/game.mjs').read_text()
    crew = (site / 'play/apollo-crew.mjs').read_text()
    for artist in ('marty', 'brenno', 'ryan-ellis', 'gavin-the-hotrod', 'lj-the-messenger', 'dearis', 'tonyxtrotter', 'eli-williams', 'andrew-prim'):
        assert f"id:'{artist}'" in crew
        assert (site / f'play/assets/apollo-{artist}-v1.webp').is_file()
    for name in expected:
        assert not any(old in name for old in ('chambliss', 'artist-joz', 'artist-steven', 'music/joz', 'music/outside-steven')), 'Legacy artist media in Apollo build'
        assert PurePosixPath(name).name not in {
            'apollo-badge-v1.png', 'apollo-official-heart.png',
            'merch-apollo-v1.webp', 'jay-apollo-v1.webp',
        }, 'Retired cartoon Apollo badge in published inventory'
    for name in expected:
        path = site / name
        if path.suffix not in TEXT_EXTENSIONS:
            continue
        text = path.read_text()
        assert not re.search(r'''["'`]\/play\/''', text), f'Wrong game base path: {name}'
        for ref in re.findall(r'''(?:from\s+|(?:href|src)=)["'](\.[^"']+|/kingdom-circuit-test/[^"']+)''', text):
            ref = ref.split('?')[0].split('#')[0]
            target = site / ref.removeprefix('/kingdom-circuit-test/') if ref.startswith('/') else path.parent / ref
            assert target.is_file(), f'Missing game dependency: {ref}'
    # Keep this direct-link test out of site navigation and generated sitemaps.
    for other in site.rglob('*'):
        if other.is_file() and other.suffix in {'.html', '.xml'} and 'play' not in other.relative_to(site).parts:
            assert BASE not in other.read_text(), f'Game unexpectedly advertised: {other}'
    return {'route': BASE, 'fileCount': len(expected), 'passwordRequired': False, 'roundMaximum': 1000, 'sessionScoreCapped': False}


def build(site: Path) -> dict:
    assert not (site / 'CNAME').exists(), 'Never add the game through a production build'
    assert (site / 'robots.txt').read_text() == 'User-agent: *\nDisallow: /\n'
    assert 'noindex,nofollow' in (site / 'index.html').read_text()
    assert not (site / 'play').exists(), 'The isolated game must not overwrite a live route'
    for name, data in expected_files().items():
        target = site / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    return verify(site)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('site', type=Path)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    print(json.dumps(verify(args.site) if args.check else build(args.site), indent=2))
