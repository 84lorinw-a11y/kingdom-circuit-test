"""Add an isolated artist intake form using the owner's approved Formspree endpoint."""
from pathlib import Path
import argparse
import hashlib
import re
import shutil

BASE = '/kingdom-circuit-test/'
ROUTE = 'test-artist-intake/'
ENDPOINT = 'https://formspree.io/f/mljreawj'


def build(site: Path) -> None:
    source = (site / 'submit/artist/index.html').read_text()
    if 'name="environment" value="test"' not in source or 'noindex,nofollow' not in source:
        raise ValueError('The artist intake mockup may only be built on the test site.')
    assets = Path(__file__).resolve().parents[1] / 'test-overrides'
    main = (assets / 'artist-intake-mockup.html').read_text()
    page, count = re.subn(r'<main\b[^>]*>.*?</main>', lambda _: main, source, count=1, flags=re.S)
    assert count == 1
    page = re.sub(r'<script\b[^>]*>.*?</script>', '', page, flags=re.S)
    page = re.sub(r'<title>.*?</title>', '<title>Submit Your Artist Profile | Kingdom Circuit Test</title>', page, flags=re.S)
    page = page.replace(BASE + 'submit/artist/', BASE + ROUTE)
    page = re.sub(r'(<meta\s+name="description"\s+content=")[^"]*', r'\1Submit your artist profile to Kingdom Circuit for review.', page)
    policy = f"default-src 'self'; base-uri 'none'; object-src 'none'; frame-src 'none'; form-action {ENDPOINT}; connect-src {ENDPOINT}; img-src 'self' data:; font-src 'self' data:; style-src 'self' 'unsafe-inline'; script-src 'self';"
    page = re.sub(r'<meta\b[^>]*http-equiv="Content-Security-Policy"[^>]*>', '', page, flags=re.I)
    page = page.replace('<head>', '<head>\n<meta http-equiv="Content-Security-Policy" content="' + policy + '">', 1)
    script_version = hashlib.sha256((assets / 'artist-intake-mockup.js').read_bytes()).hexdigest()[:12]
    style_version = hashlib.sha256((assets / 'artist-intake-mockup.css').read_bytes()).hexdigest()[:12]
    page = page.replace('</head>', f'<link rel="stylesheet" href="{BASE}assets/artist-intake-mockup.css?v={style_version}">\n<script defer src="{BASE}assets/artist-intake-mockup.js?v={script_version}"></script>\n</head>', 1)
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
    assert len(forms) == 1 and forms[0].get('action') == ENDPOINT
    assert forms[0].get('method') == 'post' and 'novalidate' not in forms[0]
    assert f"form-action {ENDPOINT};" in page and f"connect-src {ENDPOINT};" in page
    assert 'noindex,nofollow' in page
    assert 'googletagmanager.com' not in page
    assert not (site / 'CNAME').exists()
    scripts = [a.get('src') for tag, a in parser.tags if tag == 'script']
    script_version = hashlib.sha256((site / 'assets/artist-intake-mockup.js').read_bytes()).hexdigest()[:12]
    assert scripts == [BASE + 'assets/artist-intake-mockup.js?v=' + script_version]
    style_version = hashlib.sha256((site / 'assets/artist-intake-mockup.css').read_bytes()).hexdigest()[:12]
    assert f'artist-intake-mockup.css?v={style_version}' in page
    fields = {a.get('name'): a for tag, a in parser.tags if tag in ('input','textarea')}
    public_fields = {'artistName','submitter_name','email','website','instagram','spotify','youtube','photoUrl'}
    metadata = {'submission_type','subject','environment','page_url'}
    assert set(fields) == public_fields | metadata
    for name, attrs in fields.items():
        assert not {'pattern', 'maxlength'} & attrs.keys()
        assert ('required' in attrs) == (name in {'submitter_name', 'email'})
        assert attrs.get('type', 'text') == ('email' if name == 'email' else 'text' if name in public_fields else 'hidden')
    assert not any(tag == 'textarea' or attrs.get('type') == 'checkbox' for tag, attrs in parser.tags)
    assert fields['environment']['value'] == 'test'
    assert fields['submission_type']['value'] == 'CHH artist submission'
    assert fields['page_url']['value'] == 'https://84lorinw-a11y.github.io' + BASE + ROUTE
    assert not any(attrs.get('type') == 'file' for _, attrs in parser.tags), 'Free plan uses a photo link'
    assert 'ai-review' not in page and 'Preview artist submission' not in page
    ids = [a['id'] for _, a in parser.tags if 'id' in a]
    assert len(ids) == len(set(ids)), 'Duplicate field ids'
    for tag, attrs in parser.tags:
        if tag == 'button': assert attrs.get('type') == 'submit' and attrs.get('id') == 'ai-submit'
        for key in ('src', 'href'):
            url = attrs.get(key, '')
            if url.startswith(BASE):
                target = site / url[len(BASE):].split('?')[0].split('#')[0]
                if url.split('?')[0].split('#')[0].endswith('/'): target = target / 'index.html'
                assert target.is_file(), f'Missing local asset or page: {url}'
    js = (site / 'assets/artist-intake-mockup.js').read_text()
    for forbidden in ('XMLHttpRequest', 'sendBeacon', 'localStorage', 'sessionStorage', '.submit(', 'checkValidity('):
        assert forbidden not in js, f'Unexpected validation, storage or transport: {forbidden}'
    assert js.count('fetch(') == 1 and 'fetch(form.action,' in js
    assert 'if (!form.reportValidity()) return;' in js
    assert 'result.ok !== true' in js and 'if (sending) return' in js
    assert 'new FormData(form)' in js and 'method: "POST"' in js
    print('Artist intake verified: approved endpoint, one-step submit, optional photo link, flexible fields and honest result handling.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('site', type=Path)
    parser.add_argument('--verify-only', action='store_true')
    args = parser.parse_args()
    (verify if args.verify_only else build)(args.site)
