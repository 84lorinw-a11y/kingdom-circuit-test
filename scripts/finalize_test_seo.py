from __future__ import annotations

import html
import json
import pathlib
import re
import sys

BAD = 'https://84lorinw-a11y.github.io/kingdom-circuit-test/kingdom-circuit-test/'
GOOD = 'https://84lorinw-a11y.github.io/kingdom-circuit-test/'
BASE = '/kingdom-circuit-test/'
MARKER = '<!-- KC SEO TEST SCHEMA -->'
FIDELITY_CSS_MARKER = '/* KC ARTIST LIVE-FIDELITY V1 */'
VERIFIED_ARTIST_IMAGE_ENDPOINT = 'https://open.voidware.de/artist/'


def first(pattern, text):
    m = re.search(pattern, text, re.S | re.I)
    return m.group(1).strip() if m else ''


def set_meta(text, prop, value):
    if not value:
        return text
    pattern = rf'<meta property="{re.escape(prop)}" content="[^"]*">'
    tag = f'<meta property="{prop}" content="{value}">'
    if re.search(pattern, text, re.I):
        return re.sub(pattern, tag, text, count=1, flags=re.I)
    return text.replace('</head>', tag + '\n</head>', 1)


def drop_inherited_breadcrumb(text):
    if MARKER not in text:
        return text
    before, after = text.split(MARKER, 1)
    pattern = r'<script type="application/ld\+json">.*?</script>'
    before = re.sub(pattern, lambda m: '' if 'BreadcrumbList' in m.group(0) else m.group(0), before, flags=re.S)
    return before + MARKER + after


def extract_js_value(text, marker, opener, closer):
    start = text.find(marker)
    if start < 0:
        return None
    pos = text.find(opener, start + len(marker))
    if pos < 0:
        return None
    depth = 0
    in_string = False
    quote = ''
    escape = False
    for idx in range(pos, len(text)):
        ch = text[idx]
        if in_string:
            if escape:
                escape = False
            elif ch == '\\':
                escape = True
            elif ch == quote:
                in_string = False
            continue
        if ch in ('"', "'"):
            in_string = True
            quote = ch
            continue
        if ch == opener:
            depth += 1
        elif ch == closer:
            depth -= 1
            if depth == 0:
                return text[pos:idx + 1]
    return None


def parse_json_js_value(text, marker, opener, closer):
    raw = extract_js_value(text, marker, opener, closer)
    if not raw:
        return [] if opener == '[' else {}
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return [] if opener == '[' else {}


def parse_simple_js_object(text, marker):
    raw = extract_js_value(text, marker, '{', '}')
    if not raw:
        return {}
    normalized = re.sub(r'([,{]\s*)([A-Za-z_$][A-Za-z0-9_$]*)(\s*:)', r'\1"\2"\3', raw)
    try:
        return json.loads(normalized)
    except json.JSONDecodeError:
        return {}


def norm(value):
    return str(value or '').strip().casefold()


def slug(value):
    value = norm(value).replace('&', ' and ')
    return re.sub(r'[^a-z0-9]+', '-', value).strip('-') or 'item'


def spotify_image(artist):
    if artist.get('sourceRegistryVerified') is not True:
        return ''
    profile = artist.get('spotifyProfile') or (
        f"https://open.spotify.com/artist/{artist['spotifyId']}" if artist.get('spotifyId') else ''
    )
    match = re.search(r'open\.spotify\.com/artist/([A-Za-z0-9]+)', str(profile))
    return VERIFIED_ARTIST_IMAGE_ENDPOINT + match.group(1) if match else ''


def local_asset_url(value):
    value = str(value or '').strip()
    if not value:
        return ''
    if value.startswith('http://'):
        return 'https://' + value[7:]
    if value.startswith('https://'):
        return value
    return BASE + value.lstrip('/')


def resolve_live_artists(root):
    artists = json.loads((root / 'config/artists.json').read_text(encoding='utf-8'))
    app = (root / 'app.js').read_text(encoding='utf-8', errors='ignore')
    roster = parse_json_js_value(app, 'const ARTIST_ROSTER_ORDER =', '[', ']')
    registry = parse_json_js_value(app, 'const VERIFIED_ARTIST_REGISTRY =', '{', '}')
    overrides = parse_simple_js_object(app, 'const ARTIST_OVERRIDES =')
    order_by_name = {norm(name): idx + 1 for idx, name in enumerate(roster)}

    resolved = []
    for artist in artists:
        key = norm(artist.get('name'))
        legacy = overrides.get(key, {})
        verified = registry.get(key, {})
        aliases = []
        for alias in [*(artist.get('aliases') or []), *(legacy.get('aliases') or []), *(verified.get('aliases') or [])]:
            if alias not in aliases:
                aliases.append(alias)

        merged = dict(artist)
        merged.update(legacy)
        merged.update(verified)
        if aliases:
            merged['aliases'] = aliases
        if key in order_by_name:
            merged['rosterOrder'] = order_by_name[key]

        if merged.get('sourceRegistryVerified') is True:
            primary = merged.get('imageUrl') or spotify_image(merged)
            fallback = spotify_image(merged)
            merged['_resolvedImage'] = local_asset_url(primary)
            merged['_resolvedFallback'] = (
                local_asset_url(fallback)
                if primary and fallback and local_asset_url(primary) != local_asset_url(fallback)
                else ''
            )
        else:
            merged['_resolvedImage'] = ''
            merged['_resolvedFallback'] = ''
        merged['_resolvedPosition'] = merged.get('imagePosition') or 'center'
        resolved.append(merged)

    enabled = [a for a in resolved if a.get('enabled') is not False]
    enabled.sort(key=lambda a: (a.get('rosterOrder') or 9999, str(a.get('name') or '').casefold()))
    return enabled


def brand_svg(label, sequence=0):
    if label == 'Instagram':
        gid = f'kc-seo-instagram-{sequence}'
        return (
            f'<svg class="seo-brand-icon" viewBox="0 0 24 24" aria-hidden="true" focusable="false">'
            f'<defs><radialGradient id="{gid}-glow" cx="30%" cy="100%" r="105%">'
            '<stop offset="0" stop-color="#feda75"/><stop offset=".3" stop-color="#fa7e1e"/>'
            '<stop offset=".61" stop-color="#e1306c"/><stop offset=".82" stop-color="#c13584"/>'
            '<stop offset="1" stop-color="#833ab4"/></radialGradient>'
            f'<linearGradient id="{gid}-sky" x1="0" y1="0" x2="1" y2="1">'
            '<stop offset="0" stop-color="#405de6"/><stop offset=".42" stop-color="#5851db" stop-opacity=".8"/>'
            '<stop offset="1" stop-color="#833ab4" stop-opacity="0"/></linearGradient></defs>'
            f'<rect x="1" y="1" width="22" height="22" rx="6.4" fill="url(#{gid}-glow)"/>'
            f'<rect x="1" y="1" width="22" height="22" rx="6.4" fill="url(#{gid}-sky)"/>'
            '<rect x="6.1" y="6.1" width="11.8" height="11.8" rx="3.7" fill="none" stroke="#fff" stroke-width="1.85"/>'
            '<circle cx="12" cy="12" r="3" fill="none" stroke="#fff" stroke-width="1.85"/>'
            '<circle cx="17.25" cy="6.85" r="1.15" fill="#fff"/></svg>'
        )
    if label == 'Spotify':
        return (
            '<svg class="seo-brand-icon" viewBox="0 0 24 24" aria-hidden="true" focusable="false">'
            '<circle cx="12" cy="12" r="11" fill="#1ed760"/>'
            '<path d="M6.35 9.05c3.92-1.12 8.32-.77 11.83 1.08M7.2 12.15c3.22-.88 6.87-.59 9.74.81M8.05 15.1c2.5-.63 5.29-.41 7.52.62" fill="none" stroke="#090909" stroke-width="1.75" stroke-linecap="round"/></svg>'
        )
    if label == 'YouTube':
        return (
            '<svg class="seo-brand-icon" viewBox="0 0 24 24" aria-hidden="true" focusable="false">'
            '<rect x="1" y="4.25" width="22" height="15.5" rx="4.4" fill="#ff0033"/>'
            '<path d="m10 8.45 6 3.55-6 3.55v-7.1Z" fill="#fff"/></svg>'
        )
    if label == 'Website':
        return (
            '<svg class="seo-brand-icon" viewBox="0 0 24 24" aria-hidden="true" focusable="false">'
            '<circle cx="12" cy="12" r="9.5" fill="none" stroke="#e3b75d" stroke-width="1.9"/>'
            '<path d="M2.75 12h18.5M12 2.5c2.45 2.55 3.72 5.7 3.72 9.5S14.45 18.95 12 21.5M12 2.5C9.55 5.05 8.28 8.2 8.28 12S9.55 18.95 12 21.5" fill="none" stroke="#e3b75d" stroke-width="1.65" stroke-linecap="round"/></svg>'
        )
    return ''


def replace_social_icons(text):
    sequence = 0
    for label in ('Instagram', 'Spotify', 'YouTube', 'Website'):
        pattern = re.compile(rf'(<a class="seo-social-link[^"]*"[^>]*aria-label="{label}"[^>]*>)(.*?)(</a>)', re.S)

        def repl(match, label=label):
            nonlocal sequence
            sequence += 1
            inner = re.sub(r'<svg\b.*?</svg>', brand_svg(label, sequence), match.group(2), count=1, flags=re.S)
            return match.group(1) + inner + match.group(3)

        text = pattern.sub(repl, text)
    return text


def artist_visual_content(artist):
    image = artist.get('_resolvedImage') or ''
    if not image:
        return ''
    fallback = artist.get('_resolvedFallback') or ''
    fallback_attr = f' data-fallback-src="{html.escape(fallback, quote=True)}"' if fallback else ''
    return (
        f'<img src="{html.escape(image, quote=True)}"{fallback_attr} '
        f'alt="{html.escape(str(artist.get("name") or ""), quote=True)}" '
        'loading="lazy" decoding="async" width="600" height="600" referrerpolicy="no-referrer" '
        f'style="object-position:{html.escape(str(artist.get("_resolvedPosition") or "center"), quote=True)}">'
    )


def patch_directory(root, artists):
    path = root / 'artists/index.html'
    if not path.exists():
        return
    text = path.read_text(encoding='utf-8')
    blocks = re.findall(r'<article class="artist-card seo-artist-card".*?</article>', text, flags=re.S)
    if not blocks:
        return

    by_name = {}
    for block in blocks:
        match = re.search(r'<h2><a [^>]*>(.*?)</a></h2>', block, flags=re.S)
        if match:
            by_name[norm(html.unescape(re.sub(r'<[^>]+>', '', match.group(1))))] = block

    rebuilt = []
    for artist in artists:
        key = norm(artist.get('name'))
        block = by_name.pop(key, None)
        if not block:
            continue
        visual = artist_visual_content(artist)
        if visual:
            block = re.sub(
                r'(<a class="artist-visual(?: artist-visual-empty)?"[^>]*>).*?(</a>)',
                lambda m: m.group(1).replace(' artist-visual-empty', '') + visual + m.group(2),
                block,
                count=1,
                flags=re.S,
            )
        else:
            block = re.sub(
                r'(<a class="artist-visual)(?: artist-visual-empty)?("[^>]*>).*?(</a>)',
                r'\1 artist-visual-empty\2\3',
                block,
                count=1,
                flags=re.S,
            )
        rebuilt.append(block)

    rebuilt.extend(by_name.values())
    new_cards = ''.join(rebuilt)
    text = re.sub(
        r'(<div class="artist-grid seo-artist-grid" data-artist-grid>).*?(</div><div class="empty-panel" data-artist-empty)',
        lambda m: m.group(1) + new_cards + m.group(2),
        text,
        count=1,
        flags=re.S,
    )
    path.write_text(replace_social_icons(text), encoding='utf-8')


def patch_artist_profiles(root, artists):
    for artist in artists:
        name = str(artist.get('name') or '')
        path = root / f'artists/{slug(name)}/index.html'
        if not path.exists():
            continue
        text = path.read_text(encoding='utf-8')
        image = artist.get('_resolvedImage') or ''
        if image:
            fallback = artist.get('_resolvedFallback') or ''
            fallback_attr = f' data-fallback-src="{html.escape(fallback, quote=True)}"' if fallback else ''
            visual = (
                f'<div class="seo-profile-image"><img src="{html.escape(image, quote=True)}"{fallback_attr} '
                f'alt="{html.escape(name, quote=True)}" width="900" height="900" referrerpolicy="no-referrer" '
                f'style="object-position:{html.escape(str(artist.get("_resolvedPosition") or "center"), quote=True)}"></div>'
            )
        else:
            visual = '<div class="seo-profile-image seo-profile-placeholder" aria-hidden="true"></div>'
        text = re.sub(r'<div class="seo-profile-image(?: [^"]*)?"(?: [^>]*)?>.*?</div>', visual, text, count=1, flags=re.S)
        path.write_text(replace_social_icons(text), encoding='utf-8')


def append_fidelity_css(root):
    path = root / 'styles.css'
    if not path.exists():
        return
    text = path.read_text(encoding='utf-8')
    if FIDELITY_CSS_MARKER in text:
        return
    text += '''

/* KC ARTIST LIVE-FIDELITY V1 */
.seo-social-link .seo-brand-icon{display:block;width:25px;height:25px;flex:0 0 25px;filter:drop-shadow(0 2px 7px rgba(0,0,0,.28))}
.seo-social-link-compact .seo-brand-icon{width:28px;height:28px;flex-basis:28px}
.seo-social-link:hover .seo-brand-icon{transform:scale(1.05)}
.seo-artist-card .artist-visual img,.seo-profile-image img{object-fit:cover}
'''
    path.write_text(text, encoding='utf-8')


def verify_artist_fidelity(root, artists):
    failures = []
    directory = root / 'artists/index.html'
    if not directory.exists():
        return ['missing:artists/index.html']
    text = directory.read_text(encoding='utf-8')
    names = [
        html.unescape(re.sub(r'<[^>]+>', '', value)).strip()
        for value in re.findall(r'<article class="artist-card seo-artist-card".*?<h2><a [^>]*>(.*?)</a></h2>', text, flags=re.S)
    ]
    expected = [str(a.get('name') or '') for a in artists]
    if names != expected[:len(names)]:
        failures.append(f'artist-order:first-10={names[:10]} expected={expected[:10]}')

    one_k = next((a for a in artists if norm(a.get('name')) == '1k phew'), None)
    if one_k:
        expected_src = one_k.get('_resolvedImage') or ''
        block_text = ''
        for block in re.findall(r'<article class="artist-card seo-artist-card".*?</article>', text, flags=re.S):
            if '>1K Phew</a></h2>' in block:
                block_text = block
                break
        if expected_src and f'src="{html.escape(expected_src, quote=True)}"' not in block_text:
            failures.append(f'1k-phew-image:{expected_src}')

    for token in ('#1ed760', '#ff0033', '#e1306c'):
        if token not in text:
            failures.append(f'brand-icon:{token}')
    if FIDELITY_CSS_MARKER not in (root / 'styles.css').read_text(encoding='utf-8'):
        failures.append('artist-fidelity-css')
    return failures


def main(root):
    root = pathlib.Path(root)
    failures = []
    changed = 0

    for p in root.rglob('*.html'):
        text = p.read_text(encoding='utf-8', errors='ignore')
        original = text
        text = text.replace(BAD, GOOD)
        text = drop_inherited_breadcrumb(text)
        text = text.replace('>1 shows<', '>1 show<')
        title = first(r'<title>(.*?)</title>', text)
        desc = first(r'<meta name="description" content="([^"]*)">', text)
        canon = first(r'<link rel="canonical" href="([^"]+)">', text)
        text = set_meta(text, 'og:title', title)
        text = set_meta(text, 'og:description', desc)
        text = set_meta(text, 'og:url', canon)
        if BAD in text:
            failures.append(f'duplicate-canonical:{p}')
        if 'name="robots" content="noindex,nofollow"' not in text:
            failures.append(f'noindex:{p}')
        if MARKER in text:
            marker_at = text.index(MARKER)
            if 'BreadcrumbList' in text[:marker_at]:
                failures.append(f'inherited-breadcrumb:{p}')
        if text != original:
            p.write_text(text, encoding='utf-8')
            changed += 1

    sitemap = root / 'sitemap.xml'
    if sitemap.exists():
        text = sitemap.read_text(encoding='utf-8').replace(BAD, GOOD)
        sitemap.write_text(text, encoding='utf-8')

    artists = resolve_live_artists(root)
    patch_directory(root, artists)
    patch_artist_profiles(root, artists)
    for p in root.rglob('*.html'):
        text = p.read_text(encoding='utf-8', errors='ignore')
        branded = replace_social_icons(text)
        if branded != text:
            p.write_text(branded, encoding='utf-8')

    append_fidelity_css(root)
    failures.extend(verify_artist_fidelity(root, artists))

    for rel in ['artists/index.html', 'artists/kb/index.html']:
        p = root / rel
        if not p.exists():
            failures.append(f'missing:{rel}')
            continue
        t = p.read_text(encoding='utf-8')
        if BAD in t:
            failures.append(f'bad-prefix:{rel}')
        if GOOD not in t:
            failures.append(f'missing-test-origin:{rel}')

    if failures:
        raise SystemExit('\n'.join(failures[:80]))
    print(f'Finalized SEO test output: {changed} HTML files normalized; artist directory matched to live order/images/icons')


if __name__ == '__main__':
    if len(sys.argv) != 2:
        raise SystemExit('Usage: finalize_test_seo.py SITE_ROOT')
    main(sys.argv[1])
