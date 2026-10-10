"""Add an isolated, non-submitting artist intake preview to the test website."""
from pathlib import Path
import argparse
import re
import shutil

BASE = '/kingdom-circuit-test/'
ROUTE = 'test-artist-intake/'


def build(site: Path) -> None:
    source = (site / 'submit/artist/index.html').read_text()
    if 'name="environment" value="test"' not in source or 'noindex,nofollow' not in source:
        raise ValueError('The artist intake mockup may only be built on the test site.')
    assets = Path(__file__).resolve().parents[1] / 'test-overrides'
    main = (assets / 'artist-intake-mockup.html').read_text()
    page, count = re.subn(r'<main\b[^>]*>.*?</main>', lambda _: main, source, count=1, flags=re.S)
    assert count == 1
    page = re.sub(r'<script\b[^>]*>.*?</script>', '', page, flags=re.S)
    page = re.sub(r'<title>.*?</title>', '<title>Artist Submission Preview | Kingdom Circuit Test</title>', page, flags=re.S)
    page = page.replace(BASE + 'submit/artist/', BASE + ROUTE)
    page = re.sub(r'(<meta\s+name="description"\s+content=")[^"]*', r'\1Try the Kingdom Circuit artist submission form mockup. No submissions are sent or saved.', page)
    policy = "default-src 'self'; base-uri 'none'; object-src 'none'; frame-src 'none'; form-action 'none'; connect-src 'none'; img-src 'self' data:; font-src 'self' data:; style-src 'self' 'unsafe-inline'; script-src 'self';"
    page = re.sub(r'<meta\b[^>]*http-equiv="Content-Security-Policy"[^>]*>', '', page, flags=re.I)
    page = page.replace('<head>', '<head>\n<meta http-equiv="Content-Security-Policy" content="' + policy + '">', 1)
    page = page.replace('</head>', f'<link rel="stylesheet" href="{BASE}assets/artist-intake-mockup.css">\n<script defer src="{BASE}assets/artist-intake-mockup.js"></script>\n</head>', 1)
    target = site / ROUTE / 'index.html'
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(page)
    for suffix in ('css', 'js'):
        shutil.copyfile(assets / f'artist-intake-mockup.{suffix}', site / 'assets' / f'artist-intake-mockup.{suffix}')
    verify(site)


def verify(site: Path) -> None:
    from html.parser import HTMLParser
    class Elements(HTMLParser):
        def __init__(self):
            super().__init__(); self.tags = []
        def handle_starttag(self, tag, attrs):
            self.tags.append((tag, dict(attrs)))
    page = (site / ROUTE / 'index.html').read_text()
    parser = Elements(); parser.feed(page)
    forms = [attrs for tag, attrs in parser.tags if tag == 'form']
    assert len(forms) == 1 and not forms[0].get('action')
    assert "form-action 'none'" in page and "connect-src 'none'" in page
    assert 'noindex,nofollow' in page
    assert 'formspree.io' not in page and 'googletagmanager.com' not in page
    assert not (site / 'CNAME').exists()
    scripts = [a.get('src') for tag, a in parser.tags if tag == 'script']
    assert scripts == [BASE + 'assets/artist-intake-mockup.js']
    fields = {a.get('name'): a for tag, a in parser.tags if tag in ('input','textarea')}
    assert set(fields) == {'artistName','email','website','instagram','spotify','youtube','artistPhoto'}
    assert not any(tag == 'textarea' or attrs.get('type') == 'checkbox' for tag, attrs in parser.tags)
    assert fields['artistPhoto']['type'] == 'file' and '.heic' in fields['artistPhoto']['accept']
    ids = [a['id'] for _, a in parser.tags if 'id' in a]
    assert len(ids) == len(set(ids)), 'Duplicate field ids'
    for tag, attrs in parser.tags:
        if tag == 'button': assert attrs.get('type') == 'button'
        for key in ('src', 'href'):
            url = attrs.get(key, '')
            if url.startswith(BASE):
                target = site / url[len(BASE):].split('?')[0].split('#')[0]
                if url.split('?')[0].split('#')[0].endswith('/'): target = target / 'index.html'
                assert target.is_file(), f'Missing local asset or page: {url}'
    js = (site / 'assets/artist-intake-mockup.js').read_text()
    for forbidden in ('fetch(', 'XMLHttpRequest', 'sendBeacon', 'localStorage', 'sessionStorage', '.submit('):
        assert forbidden not in js, f'Mockup must not send or store data: {forbidden}'
    print('Artist intake mockup verified: separate test route, all fields, local photo preview, no submission or storage.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('site', type=Path)
    parser.add_argument('--verify-only', action='store_true')
    args = parser.parse_args()
    (verify if args.verify_only else build)(args.site)
