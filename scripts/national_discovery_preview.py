"""Approved TEST-only national discovery layer; live content is the sole input.

The homepage becomes a selection, never the authority for the full catalog.
Existing event/artist/location pages, data, assets and SEO identities are retained.
The new destinations are an evergreen weekend calendar and the owner's About Us page.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import date, datetime, timedelta
from html import escape
import json
from pathlib import Path
import re
from urllib.parse import unquote, urlsplit
from zoneinfo import ZoneInfo

import mobile_seo_preview as mobile
from mobile_seo_preview import Document, replace_spans, test_source
from live_mirror_v2 import TEST_BASE, TEST_SITE

ROOT = Path(__file__).resolve().parents[1]
VERSION = '20261013-5'
ASSETS = ('national-discovery.css', 'national-discovery.js')
WEEKEND_PATH = 'shows/this-weekend/index.html'
WEEKEND_HREF = TEST_BASE + 'shows/this-weekend/'
ABOUT_PATH = 'about-us/index.html'
ABOUT_HREF = TEST_BASE + 'about-us/'
HOME_HEADING = 'Find CHH Shows Near You!'
HOME_SUBTITLE = 'CHH concerts, christian rap shows and festivals!'


def today():
    # Match the published catalog's existing expiration boundary.
    return datetime.now(ZoneInfo('America/Los_Angeles')).date()


def weekend_window(day):
    offset = 4 - day.weekday() if day.weekday() >= 4 else (4 - day.weekday()) % 7
    friday = day + timedelta(days=offset)
    return friday, friday + timedelta(days=2)


def date_label(first, last):
    if first.year != last.year:
        return f'{first:%b} {first.day}, {first.year} – {last:%b} {last.day}, {last.year}'
    if first.month != last.month:
        return f'{first:%b} {first.day} – {last:%b} {last.day}, {last.year}'
    return f'{first:%B} {first.day}–{last.day}, {last.year}'


def weekend_matches(start, end, day):
    first, last = weekend_window(day)
    start, end = date.fromisoformat(start), date.fromisoformat(end or start)
    return start <= last and end >= max(first, day)


def card_records(text):
    doc = Document(text)
    records = []
    for node in doc.nodes:
        if 'data-event-card' not in node.attrs:
            continue
        fragment = Document(doc.raw(node))
        title = fragment.one(lambda n: n.tag == 'h3')
        link = next(n for n in title.children if n.tag == 'a')
        image = fragment.one(lambda n: n.tag == 'img')
        artists = fragment.one(lambda n: n.has('artist-line'))
        badges = fragment.one(lambda n: n.has('event-badges'))
        meta = {}
        for dt in (n for n in fragment.nodes if n.tag == 'dt'):
            dd = next(n for n in fragment.nodes if n.tag == 'dd' and n.start >= dt.end)
            meta[fragment.text(dt)] = fragment.text(dd)
        records.append({'html': doc.raw(node), 'attrs': node.attrs, 'href': link.attrs['href'],
                        'name': fragment.text(title), 'image': fragment.raw(image),
                        'artists': fragment.raw(artists), 'badges': fragment.raw(badges), 'meta': meta})
    hrefs = [r['href'] for r in records]
    assert len(set(hrefs)) == len(hrefs), 'Duplicate event destinations in catalog'
    return records


def feature_eligible(record):
    # Respect existing owner guidance: keep school/private/TBA/cancelled listings
    # available, but do not automatically promote them as public shows on home.
    text = (record['name'] + ' ' + ' '.join(record['meta'].values()) + ' ' + record['badges']).lower()
    return not any(x in text for x in ('cancelled', 'canceled', 'sold out', 'details pending',
                                     'invite only', 'school', 'venue to be announced', 'venue not provided'))


def load_context(live, as_of):
    states = mobile.catalog(live)
    records = card_records(test_source(live, 'shows/index.html'))
    active = [r for r in records if (r['attrs'].get('data-end-date') or r['attrs']['data-date']) >= as_of.isoformat()]
    weekend = [r for r in active if weekend_matches(r['attrs']['data-date'], r['attrs'].get('data-end-date'), as_of)]
    directory = Document(test_source(live, 'artists/index.html'))
    portraits = {}
    for node in directory.nodes:
        if 'data-artist-card' not in node.attrs:
            continue
        part = Document(directory.raw(node))
        heading = part.one(lambda n: n.tag == 'h2')
        link = next(n for n in heading.children if n.tag == 'a')
        portraits[link.attrs['href']] = {'name': part.text(heading),
                                        'image': part.raw(part.one(lambda n: n.tag == 'img'))}
    counts = Counter()
    upcoming = []
    for record in active:
        fragment = Document(record['artists'])
        for link in (n for n in fragment.nodes if n.tag == 'a'):
            href = link.attrs['href']
            counts[href] += 1
            if feature_eligible(record) and href in portraits and href not in upcoming:
                upcoming.append(href)
    # Counts are computed over every show, while selection follows the next dates.
    artists = [{**portraits[href], 'href': href, 'count': counts[href]} for href in upcoming[:6]]
    active_by_href = {r['href']: r for r in active}
    recent = [active_by_href[r['href']] for r in card_records(test_source(live, 'new-shows/index.html'))
              if r['href'] in active_by_href]
    return {'states': states, 'records': records, 'active': active, 'weekend': weekend,
            'artists': artists, 'artist_total': len(portraits), 'recent': recent, 'as_of': as_of}


def section_heading(eyebrow, title, href, action, ident):
    return (f'<header class="kc-discovery-heading"><div><p class="eyebrow">{escape(eyebrow)}</p>'
            f'<h2 id="{ident}">{escape(title)}</h2></div><a href="{href}">{escape(action)} <span aria-hidden="true">↗</span></a></header>')


def teaser(record, image=True):
    attrs = record['attrs']
    picture = ''
    if image:
        # Preserve the exact real image, responsive variants, fit class and focal point.
        responsive_image = re.sub(r'sizes="[^"]*"', 'sizes="(min-width: 1000px) 115px, (max-width: 360px) 66px, 88px"', record['image'])
        picture = f'<div class="kc-teaser-image" aria-hidden="true">{responsive_image}</div>'
    return (f'<article class="kc-discovery-show" data-discovery-show data-date="{attrs["data-date"]}" '
            f'data-end-date="{attrs.get("data-end-date") or attrs["data-date"]}">'
            f'{picture}<div class="kc-teaser-copy">{record["badges"]}'
            f'<p class="kc-teaser-date">{escape(record["meta"].get("Date", ""))}</p>'
            f'<h3><a href="{record["href"]}">{escape(record["name"])}</a></h3>'
            f'{record["artists"]}<p class="kc-teaser-location">{escape(record["meta"].get("Location", ""))}</p>'
            f'<p class="kc-teaser-venue">{escape(record["meta"].get("Venue", ""))}</p></div></article>')


def artist_tile(artist):
    # The adjacent visible name labels this single link; avoid reading it twice.
    image = re.sub(r'alt="[^"]*"', 'alt=""', artist['image'])
    image = re.sub(r'sizes="[^"]*"',
                   'sizes="(min-width: 1000px) 170px, (min-width: 700px) 30vw, 45vw"', image)
    count = artist['count']
    return (f'<a class="kc-discovery-artist" href="{artist["href"]}"><div>{image}</div>'
            f'<strong>{escape(artist["name"])}</strong><span>{count} upcoming show{"s" if count != 1 else ""}</span></a>')


def home_content(text, context):
    doc = Document(text)
    title = f'<h1 class="kc-rd-home-title">{HOME_HEADING}</h1>'
    states = context['states']
    first, last = weekend_window(context['as_of'])
    label = date_label(first, last)
    state_finder = Document(mobile.finder(states))
    picker = state_finder.raw(state_finder.one(lambda n: 'data-state-picker' in n.attrs))
    disclosure = state_finder.raw(state_finder.one(lambda n: n.tag == 'details'))
    primary = [r for r in context['weekend'] if feature_eligible(r)][:6]
    primary_title = 'CHH shows this weekend'
    primary_kicker = label
    primary_href, primary_action = WEEKEND_HREF, 'All weekend shows'
    if not primary:
        primary = [r for r in context['active'] if feature_eligible(r)][:6]
        primary_title, primary_kicker = 'Coming up across the circuit', 'Plan your next show'
        primary_href, primary_action = TEST_BASE + 'shows/', 'All upcoming shows'
    used = {r['href'] for r in primary}
    festivals = [r for r in context['active'] if r['attrs'].get('data-type') == 'festival'
                 and feature_eligible(r) and r['href'] not in used][:3]
    used.update(r['href'] for r in festivals)
    recent = [r for r in context['recent'] if feature_eligible(r) and r['href'] not in used][:4]
    tiles = ''.join(artist_tile(a) for a in context['artists'])
    out = f'''<div class="kc-discovery-home" data-national-home>
<section class="kc-discovery-hero" aria-label="Find your next show">
<div class="kc-discovery-intro">{title}
<p class="kc-discovery-deck">{HOME_SUBTITLE}</p>
<div class="kc-discovery-counts">
<a class="kc-discovery-primary" href="{TEST_BASE}shows/">Browse all {len(context['active'])} shows <span aria-hidden="true">↗</span></a>
<a class="kc-discovery-artist-count" href="{TEST_BASE}artists/"><strong>{context['artist_total']}</strong> artists <span aria-hidden="true">↗</span></a></div>
<form class="kc-discovery-search" action="{TEST_BASE}shows/" method="get" role="search">
<label class="kc-discovery-sr-only" for="kc-home-search">Search shows by artist, city, venue or show name</label><div><input id="kc-home-search" name="q" type="search" placeholder="Artist, city or show" maxlength="160"><button type="submit">Search</button></div></form></div>
<section class="kc-discovery-finder" id="browse-states" aria-label="Browse shows by state">
{picker}{disclosure}</section></section>
<section class="kc-discovery-section" id="calendar" aria-labelledby="kc-weekend-heading">
{section_heading(primary_kicker, primary_title, primary_href, primary_action, 'kc-weekend-heading')}
<div class="kc-teaser-grid">{''.join(teaser(r) for r in primary)}</div>
<p class="kc-discovery-empty" data-discovery-empty{' hidden' if primary else ''}>More shows are on the way. <a href="{TEST_BASE}shows/">Explore the complete calendar.</a></p></section>'''
    if tiles:
        out += (f'<section class="kc-discovery-section" aria-labelledby="kc-artists-heading">'
                + section_heading('Follow the music', 'Artists with upcoming shows', TEST_BASE + 'artists/', 'All artists', 'kc-artists-heading')
                + f'<div class="kc-discovery-artists">{tiles}</div></section>')
    if festivals:
        out += (f'<section class="kc-discovery-section" aria-labelledby="kc-festivals-heading">'
                + section_heading('Make a day of it', 'Upcoming festivals', TEST_BASE + 'festivals/', 'All festivals', 'kc-festivals-heading')
                + '<div class="kc-teaser-grid kc-festival-teasers">' + ''.join(teaser(r) for r in festivals) + '</div></section>')
    if recent:
        out += (f'<section class="kc-discovery-section" aria-labelledby="kc-new-heading">'
                + section_heading('Added to our calendar in the last 7 days', 'Recently added shows', TEST_BASE + 'new-shows/', 'All new listings', 'kc-new-heading')
                + '<div class="kc-teaser-grid kc-recent-teasers">' + ''.join(teaser(r, image=False) for r in recent) + '</div></section>')
    out += (f'<section class="kc-discovery-submit"><div><h2>Know a show we should list?</h2>'
            f'<p>Help more people find live Christian hip-hop.</p></div><a href="{TEST_BASE}submit/">Submit a show <span aria-hidden="true">↗</span></a></section></div>')
    main = doc.one(lambda n: n.tag == 'main')
    result = replace_spans(text, [(main.opening_end, main.closing_start, out)])
    # Home is now delivered content, not a duplicate app-rendered full calendar.
    return re.sub(r'<script\b[^>]*src="' + re.escape(TEST_BASE) + r'app\.js[^\"]*"[^>]*>\s*</script>',
                  f'<script src="{TEST_BASE}seo-static.js?v=1" defer></script>', result)


def add_shared_navigation(text, relative):
    doc = Document(text)
    footers = [n for n in doc.nodes if n.has('footer-links')]
    changes = []
    for nav in (n for n in doc.nodes if n.has('kc-rd-nav')):
        links = [n for n in nav.children if n.tag == 'a']
        assert len(links) == 6, 'Primary navigation changed upstream; review the eight-link contract'
        content = ''
        for link in links:
            raw = doc.raw(link)
            if relative in {WEEKEND_PATH, ABOUT_PATH}:
                raw = raw.replace(' aria-current="page"', '')
            content += raw
            if link.attrs.get('href') == TEST_BASE + 'shows/':
                active = ' aria-current="page"' if relative == WEEKEND_PATH else ''
                content += f'<a href="{WEEKEND_HREF}"{active}>This Weekend</a>'
        active = ' aria-current="page"' if relative == ABOUT_PATH else ''
        content += f'<a href="{ABOUT_HREF}"{active}>About Us</a>'
        changes.append((nav.start, nav.end,
                        f'<nav class="kc-rd-nav" aria-label="Primary navigation" data-compact-navigation>{content}</nav>'))
    if footers:
        node = footers[0]
        changes.append((node.opening_end, node.opening_end,
                        f'<a href="{WEEKEND_HREF}">This Weekend</a><a href="{ABOUT_HREF}">About Us</a>'))
    # Existing artist identity, schedules, social links and archives are untouched.
    if relative.startswith('artists/') and relative != 'artists/index.html':
        shells = [n for n in doc.nodes if 'data-kc-rd-artist-profile' in n.attrs]
        if shells:
            title = doc.one(lambda n: n.tag == 'h1')
            crumb = (f'<nav class="kc-discovery-breadcrumb" aria-label="Breadcrumb">'
                     f'<a href="{TEST_BASE}">Home</a><span aria-hidden="true">/</span>'
                     f'<a href="{TEST_BASE}artists/">Artists</a><span aria-hidden="true">/</span>'
                     f'<span aria-current="page">{escape(doc.text(title))}</span></nav>')
            changes.append((shells[0].start, shells[0].start, crumb))
    if relative == 'artists/index.html':
        heading = doc.one(lambda n: n.tag == 'h1')
        changes.append((heading.end, heading.end,
                        '<p class="kc-directory-guide">Find artist profiles, official socials, and upcoming and past shows.</p>'))
    # Contextual destination for the existing in-place weekend filter, not a new
    # replacement filter or a page for every combination of controls.
    if relative in {'shows/index.html', 'shows/this-month/index.html', 'new-shows/index.html', 'festivals/index.html'}:
        heading = doc.one(lambda n: n.has('calendar-heading'))
        changes.append((heading.end, heading.end,
                        f'<p class="kc-weekend-route"><a href="{WEEKEND_HREF}">Explore this weekend’s CHH shows <span aria-hidden="true">↗</span></a></p>'))
    return replace_spans(text, changes)


def transform(relative, source, context):
    name = relative.as_posix()
    if name == 'sitemap.xml':
        text = source.decode()
        additions = ''
        for path in ('/shows/this-weekend/', '/about-us/'):
            url = TEST_SITE + path
            assert url not in text, f'{path} already exists in baseline; review the overlay'
            additions += f'<url><loc>{url}</loc></url>\n'
        return text.replace('</urlset>', additions + '</urlset>').encode()
    if relative.suffix != '.html' or name.startswith('test-'):
        return source
    text = source.decode()
    if '<main' not in text or 'class="site-footer"' not in text or not re.search(r'<h1\b', text):
        return source  # Redirect documents and error shells keep their exact behavior.
    if 'data-national-discovery' in text:
        raise ValueError('National discovery overlay must run once')
    if name == 'index.html':
        text = home_content(text, context)
    text = add_shared_navigation(text, name)
    assets = (f'<link rel="stylesheet" href="{TEST_BASE}assets/{ASSETS[0]}?v={VERSION}" data-national-discovery>'
              f'<script src="{TEST_BASE}assets/{ASSETS[1]}?v={VERSION}" defer></script>')
    return text.replace('</head>', assets + '</head>', 1).encode()


def weekend_page(live, context):
    text = test_source(live, 'shows/index.html')
    text = mobile.transform(Path('shows/index.html'), text.encode(), context['states']).decode()
    doc = Document(text)
    first, last = weekend_window(context['as_of'])
    label = date_label(first, last)
    title = 'CHH Concerts & Shows This Weekend | Kingdom Circuit'
    description = f'Find Christian hip-hop concerts, Christian rap shows and festivals for {label} across the U.S. Browse artists, venues and official event details.'
    canonical = TEST_SITE + '/shows/this-weekend/'
    changes = []
    hero = doc.one(lambda n: n.tag == 'section' and n.has('page-hero'))
    changes.append((hero.start, hero.end,
                    f'<section class="page-hero hero-compact kc-weekend-hero" data-weekend-page data-weekend-end="{last}">'
                    f'<p class="eyebrow">Friday through Sunday · {escape(label)}</p>'
                    f'<h1>Christian Hip-Hop Shows This Weekend</h1><p class="hero-text">'
                    f'Explore {len(context["weekend"])} upcoming CHH concerts, festivals and live events across the U.S. '
                    'Dates and times follow each event’s local listing.</p>'
                    f'<p class="kc-weekend-expired" hidden>These dates have passed. <a href="{TEST_BASE}shows/">Browse all upcoming shows.</a></p></section>'))
    grid = doc.one(lambda n: n.has('event-grid'))
    changes.append((grid.opening_end, grid.closing_start, ''.join(r['html'] for r in context['weekend'])))
    filters = doc.one(lambda n: 'data-event-filters' in n.attrs)
    form = doc.raw(filters)
    for attr in ('data-artist-filter', 'data-state-filter'):
        fd = Document(form)
        select = fd.one(lambda n: n.tag == 'select' and attr in n.attrs)
        first_option = select.children[0]
        form = replace_spans(form, [(first_option.end, select.closing_start, '')])
    changes.append((filters.start, filters.end, form))
    for n in doc.nodes:
        if n.has('quick-filters'):
            changes.append((n.start, n.end, ''))
        if n.tag == 'title':
            changes.append((n.start, n.end, f'<title>{escape(title)}</title>'))
        if n.tag == 'meta':
            key = n.attrs.get('name') or n.attrs.get('property')
            value = {'description': description, 'og:description': description, 'twitter:description': description,
                     'og:title': title, 'twitter:title': title, 'og:url': canonical}.get(key)
            if value:
                raw = re.sub(r'content="[^"]*"', f'content="{escape(value, quote=True)}"', doc.raw(n))
                changes.append((n.start, n.end, raw))
        if n.tag == 'link' and n.attrs.get('rel') == 'canonical':
            changes.append((n.start, n.end, f'<link rel="canonical" href="{canonical}">'))
        if n.tag == 'script' and n.attrs.get('type') == 'application/ld+json':
            schema = {'@context': 'https://schema.org', '@type': 'CollectionPage',
                      'name': 'Christian Hip-Hop Shows This Weekend', 'description': description,
                      'url': canonical, 'isPartOf': {'@type': 'WebSite', 'name': 'The Kingdom Circuit', 'url': TEST_SITE + '/'}}
            changes.append((n.start, n.end, '<script type="application/ld+json">' + json.dumps(schema).replace('<', '\\u003c') + '</script>'))
        if n.tag == 'script' and n.attrs.get('src', '').startswith(TEST_BASE + 'app.js'):
            changes.append((n.start, n.end, f'<script src="{TEST_BASE}seo-static.js?v=1" defer></script>'))
        if n.has('calendar-heading'):
            changes.append((n.start, n.end,
                            f'<div class="calendar-heading"><div><h2 id="calendar-title">Weekend shows</h2><p>Filter this weekend’s listings by artist or location.</p></div>'
                            f'<p class="results-count" data-results-count role="status" aria-live="polite">{len(context["weekend"])} shows</p></div>'))
    text = replace_spans(text, changes).replace(' aria-current="page"', '')
    text = text.replace('No shows currently match those filters.',
                        f'No upcoming shows match this weekend’s selection. <a href="{TEST_BASE}shows/">Explore all upcoming shows.</a>')
    # Empty weekend still has a truthful usable fallback without executing the old
    # full-calendar bootstrap (which would otherwise repopulate all dates).
    if not context['weekend']:
        text = text.replace('data-filtered-empty hidden', 'data-filtered-empty')
    return transform(Path(WEEKEND_PATH), text.encode(), context)


def about_content(text):
    """Move the exact existing mission into a small, honest standalone page."""
    doc = Document(text)
    mission_node = doc.one(lambda n: n.has('mission-statement'))
    mission = doc.raw(mission_node)
    description = doc.text(mission_node)
    title = 'About Us | Kingdom Circuit'
    canonical = TEST_SITE + '/about-us/'
    main = doc.one(lambda n: n.tag == 'main')
    content = (f'<section class="kc-about-page" data-about-page aria-labelledby="kc-about-title">'
               '<p class="eyebrow">The Kingdom Circuit</p><h1 id="kc-about-title">About Us</h1>'
               f'<div class="kc-about-mission"><h2>Why we exist</h2>{mission}</div>'
               f'<div class="kc-about-links"><a class="kc-discovery-primary" href="{TEST_BASE}shows/">Find a show <span aria-hidden="true">↗</span></a>'
               f'<a href="{TEST_BASE}artists/">Explore artists</a>'
               f'<a href="{TEST_BASE}submit/">Submit a show</a></div></section>')
    changes = [(main.opening_end, main.closing_start, content)]
    for n in doc.nodes:
        if n.tag == 'title':
            changes.append((n.start, n.end, f'<title>{title}</title>'))
        if n.tag == 'meta':
            key = n.attrs.get('name') or n.attrs.get('property')
            value = {'description': description, 'og:description': description, 'twitter:description': description,
                     'og:title': title, 'twitter:title': title, 'og:url': canonical}.get(key)
            if value:
                raw = re.sub(r'content="[^"]*"', f'content="{escape(value, quote=True)}"', doc.raw(n))
                changes.append((n.start, n.end, raw))
        if n.tag == 'link' and n.attrs.get('rel') == 'canonical':
            changes.append((n.start, n.end, f'<link rel="canonical" href="{canonical}">'))
        if n.tag == 'script' and n.attrs.get('type') == 'application/ld+json':
            schema = {'@context': 'https://schema.org', '@type': 'AboutPage', 'name': 'About Us',
                      'description': description, 'url': canonical,
                      'isPartOf': {'@type': 'WebSite', 'name': 'The Kingdom Circuit', 'url': TEST_SITE + '/'}}
            changes.append((n.start, n.end, '<script type="application/ld+json">' + json.dumps(schema).replace('<', '\\u003c') + '</script>'))
        if n.tag == 'script' and n.attrs.get('src', '').startswith(TEST_BASE + 'app.js'):
            changes.append((n.start, n.end, f'<script src="{TEST_BASE}seo-static.js?v=1" defer></script>'))
    return replace_spans(text, changes)


def about_page(live, context):
    source = test_source(live, 'index.html')
    source = mobile.transform(Path('index.html'), source.encode(), context['states']).decode()
    return transform(Path(ABOUT_PATH), about_content(source).encode(), context)


def combined_transform(relative, source, context):
    return transform(relative, mobile.transform(relative, source, context['states']), context)


def apply(site, live):
    as_of = today()
    context = load_context(live, as_of)
    for path in sorted(site.rglob('*')):
        if path.is_file() and (path.suffix == '.html' or path.name == 'sitemap.xml'):
            before = path.read_bytes()
            after = transform(path.relative_to(site), before, context)
            if before != after:
                path.write_bytes(after)
    for relative, generate in ((WEEKEND_PATH, weekend_page), (ABOUT_PATH, about_page)):
        target = site / relative
        assert not target.exists(), f'New destination unexpectedly exists: {relative}'
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(generate(live, context))
    for asset in ASSETS:
        (site / 'assets' / asset).write_bytes((ROOT / 'test-overrides' / asset).read_bytes())
    manifest_path = site / 'test-live-mirror-manifest.json'
    manifest = json.loads(manifest_path.read_text())
    manifest['nationalDiscovery'] = {'version': VERSION, 'asOfDate': as_of.isoformat(), 'timezone': 'America/Los_Angeles'}
    manifest_path.write_text(json.dumps(manifest, indent=2) + '\n')
    print(json.dumps({'nationalDiscovery': VERSION, 'asOfDate': str(as_of), 'weekendShows': len(context['weekend'])}))


def verify(live, site, context):
    """Independent page/content invariants supplement exact recomputed byte parity."""
    home = Document((site / 'index.html').read_text())
    old_home = Document(test_source(live, 'index.html'))
    about = Document((site / ABOUT_PATH).read_text())
    assert (site / ABOUT_PATH).read_bytes() == about_page(live, context)
    assert about.raw(about.one(lambda n: n.has('mission-statement'))) == old_home.raw(old_home.one(lambda n: n.has('mission-statement')))
    assert not any(n.has('mission-statement') for n in home.nodes), 'Mission should live on About Us, not Home'
    assert home.text(home.one(lambda n: n.tag == 'h1')) == HOME_HEADING
    assert home.text(home.one(lambda n: n.has('kc-discovery-deck'))) == HOME_SUBTITLE
    intro = home.one(lambda n: n.has('kc-discovery-intro'))
    assert not any(n.has('eyebrow') for n in intro.children), 'Owner removed the homepage tagline'
    counts = home.one(lambda n: n.has('kc-discovery-counts'))
    assert f'Browse all {len(context["active"])} shows' in home.text(counts)
    assert f'{context["artist_total"]} artists' in home.text(counts)
    assert {n.attrs.get('href') for n in counts.children if n.tag == 'a'} == {TEST_BASE + 'shows/', TEST_BASE + 'artists/'}
    search = home.one(lambda n: n.has('kc-discovery-search'))
    assert search.attrs['action'] == TEST_BASE + 'shows/' and search.attrs['method'] == 'get'
    assert home.one(lambda n: n.tag == 'input' and n.attrs.get('id') == 'kc-home-search').attrs['name'] == 'q'
    assert home.text(home.one(lambda n: n.tag == 'label' and n.attrs.get('for') == 'kc-home-search'))
    assert not any(n.has('kc-discovery-when') for n in home.nodes), 'Date navigation is already available in the header'
    assert about.text(about.one(lambda n: n.tag == 'h1')) == 'About Us'
    assert about.one(lambda n: n.tag == 'link' and n.attrs.get('rel') == 'canonical').attrs['href'] == TEST_SITE + '/about-us/'
    assert about.one(lambda n: n.tag == 'meta' and n.attrs.get('name') == 'robots').attrs['content'] == 'noindex,nofollow'
    all_cards = card_records((site / 'shows/index.html').read_text())
    assert [r['html'] for r in all_cards] == [r['html'] for r in context['records']], 'Full national calendar changed'
    all_urls = {r['href'] for r in all_cards}
    assert {r['href'] for r in card_records(test_source(live, 'index.html'))} <= all_urls, 'A former home listing is missing from All Shows'
    teasers = [n for n in home.nodes if 'data-discovery-show' in n.attrs]
    assert len(teasers) <= 13, 'Homepage selection grew into another full calendar'
    for node in teasers:
        item = Document(home.raw(node))
        h3 = item.one(lambda n: n.tag == 'h3')
        link = next(n for n in h3.children if n.tag == 'a')
        source = next(r for r in all_cards if r['href'] == link.attrs['href'])
        assert item.text(h3) == source['name']
        assert source['artists'] in item.source and source['badges'] in item.source
        for field in ('Date', 'Venue', 'Location'):
            assert escape(source['meta'].get(field, '')) in item.source
    assert not any(n.attrs.get('src', '').startswith(TEST_BASE + 'app.js') for n in home.nodes)
    for state in context['states']:
        assert state['href'] in home.source
    assert (site / WEEKEND_PATH).read_bytes() == weekend_page(live, context)
    weekend = Document((site / WEEKEND_PATH).read_text())
    assert [r['html'] for r in card_records(weekend.source)] == [r['html'] for r in context['weekend']]
    checked = 0
    checked_links = set()
    def check_new_links(before, after):
        def references(doc):
            return {n.attrs[attr] for n in doc.nodes for attr in ('href', 'src', 'action') if attr in n.attrs}
        for link in references(after) - references(before):
            parts = urlsplit(link)
            if parts.netloc and parts.netloc != urlsplit(TEST_SITE).netloc:
                continue
            if not parts.path.startswith(TEST_BASE):
                continue
            relative = unquote(parts.path[len(TEST_BASE):])
            target = site / relative
            assert target.is_file() or (target / 'index.html').is_file(), f'New broken local link: {link}'
            checked_links.add(parts.path)
    check_new_links(Document(''), weekend)
    check_new_links(Document(''), about)
    def check_navigation(doc):
        for nav in (n for n in doc.nodes if n.has('kc-rd-nav')):
            links = [n for n in nav.children if n.tag == 'a']
            assert [doc.text(n) for n in links] == ['Home', 'All Shows', 'This Weekend', 'This Month', 'Festivals', 'New Shows', 'Artists', 'About Us']
            assert links[2].attrs['href'] == WEEKEND_HREF and links[-1].attrs['href'] == ABOUT_HREF
    check_navigation(weekend)
    check_navigation(about)
    for doc, active_href in ((weekend, WEEKEND_HREF), (about, ABOUT_HREF)):
        nav = doc.one(lambda n: n.has('kc-rd-nav'))
        assert [n.attrs['href'] for n in nav.children if n.attrs.get('aria-current') == 'page'] == [active_href]
    for path in live.rglob('*.html'):
        rel = path.relative_to(live)
        before, after = Document(test_source(live, rel)), Document((site / rel).read_text())
        if not any('data-national-discovery' in n.attrs for n in after.nodes):
            continue
        check_new_links(before, after)
        check_navigation(after)
        assert len([n for n in after.nodes if n.tag == 'h1']) == 1, rel
        # No original metadata, canonical or structured-data changes on existing URLs.
        for predicate in (lambda n: n.tag in {'meta', 'title'} or (n.tag == 'link' and n.attrs.get('rel') == 'canonical'),
                          lambda n: n.tag == 'script' and n.attrs.get('type') == 'application/ld+json'):
            assert Counter(before.raw(n) for n in before.nodes if predicate(n)) == Counter(after.raw(n) for n in after.nodes if predicate(n)), rel
        if rel.as_posix() != 'index.html':
            for predicate in (lambda n: 'data-event-card' in n.attrs or 'data-artist-card' in n.attrs or n.has('past-show-row'),
                              lambda n: 'data-event-filters' in n.attrs or 'data-artist-directory' in n.attrs,
                              lambda n: 'data-kc-rd-artist-profile' in n.attrs or n.has('event-detail-section')):
                assert Counter(before.raw(n) for n in before.nodes if predicate(n)) == Counter(after.raw(n) for n in after.nodes if predicate(n)), rel
        checked += 1
    for asset in ASSETS:
        assert (site / 'assets' / asset).read_bytes() == (ROOT / 'test-overrides' / asset).read_bytes()
    assert checked > 0
    return {'verifiedPages': checked, 'weekendShows': len(context['weekend']),
            'homepageShowPreviews': len(teasers), 'completeCalendarShows': len(all_cards),
            'verifiedNewLocalDestinations': len(checked_links),
            'allOriginalSeoIdentitiesPreserved': True, 'missionPreserved': True, 'missionLocation': ABOUT_HREF}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('site', type=Path)
    parser.add_argument('live', type=Path)
    args = parser.parse_args()
    apply(args.site, args.live)
