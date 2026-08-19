from __future__ import annotations

import datetime as dt
import html
import json
import pathlib
import re
from collections import Counter, defaultdict

BASE = "/kingdom-circuit-test/"
TEST_ORIGIN = "https://84lorinw-a11y.github.io/kingdom-circuit-test"
TODAY = dt.date.today()
STATE_NAMES = {
    "AL":"Alabama","AK":"Alaska","AZ":"Arizona","AR":"Arkansas","CA":"California","CO":"Colorado","CT":"Connecticut","DE":"Delaware","DC":"District of Columbia","FL":"Florida","GA":"Georgia","HI":"Hawaii","ID":"Idaho","IL":"Illinois","IN":"Indiana","IA":"Iowa","KS":"Kansas","KY":"Kentucky","LA":"Louisiana","ME":"Maine","MD":"Maryland","MA":"Massachusetts","MI":"Michigan","MN":"Minnesota","MS":"Mississippi","MO":"Missouri","MT":"Montana","NE":"Nebraska","NV":"Nevada","NH":"New Hampshire","NJ":"New Jersey","NM":"New Mexico","NY":"New York","NC":"North Carolina","ND":"North Dakota","OH":"Ohio","OK":"Oklahoma","OR":"Oregon","PA":"Pennsylvania","RI":"Rhode Island","SC":"South Carolina","SD":"South Dakota","TN":"Tennessee","TX":"Texas","UT":"Utah","VT":"Vermont","VA":"Virginia","WA":"Washington","WV":"West Virginia","WI":"Wisconsin","WY":"Wyoming"
}

CSS_MARKER = "/* KC SEO TEST OVERLAY V1 */"
JS_MARKER = "/* KC SEO TEST DIRECTORY GUARD */"
SCHEMA_MARKER = "<!-- KC SEO TEST SCHEMA -->"


def esc(v): return html.escape(str(v or ""), quote=True)
def norm(v): return str(v or "").strip().casefold()
def slug(v):
    value = norm(v).replace("&", " and ")
    return re.sub(r"[^a-z0-9]+", "-", value).strip("-") or "item"

def fnv(value):
    h = 0x811C9DC5
    for b in str(value).encode():
        h ^= b
        h = (h * 0x01000193) & 0xFFFFFFFF
    return f"{h:08x}"[:6]

def event_slug(event):
    payload = event.get("id") or json.dumps(event, sort_keys=True)
    return f"{slug(event.get('title') or 'event')}-{event.get('startDate','')}-{slug(event.get('city',''))}-{fnv(payload)}"

def event_href(event): return f"{BASE}event/{event_slug(event)}/"
def artist_href(name): return f"{BASE}artists/{slug(name)}/"
def state_href(code): return f"{BASE}shows/{slug(STATE_NAMES.get(code, code))}/"
def city_href(city, code): return f"{BASE}shows/{slug(city)}-{slug(STATE_NAMES.get(code, code))}/"
def artist_state_href(name, code): return f"{BASE}artists/{slug(name)}/{slug(STATE_NAMES.get(code, code))}/"
def canonical(path): return TEST_ORIGIN.rstrip("/") + "/" + path.lstrip("/")

def parse_date(raw):
    try: return dt.date.fromisoformat(str(raw or "")[:10])
    except Exception: return None

def format_date(event):
    d = parse_date(event.get("startDate"))
    if not d: return "Date to be announced"
    text = d.strftime("%a, %b %-d, %Y")
    raw = event.get("startTime")
    if raw:
        try:
            h, m = map(int, raw.split(":")[:2])
            text += f" - {h % 12 or 12}:{m:02d} {'AM' if h < 12 else 'PM'}"
        except Exception: pass
    return text

def future(event):
    d = parse_date(event.get("endDate") or event.get("startDate"))
    return d is None or d >= TODAY

def merge_events(primary, supplemental):
    out, keys = [], set()
    for event in [*primary, *supplemental]:
        artists = tuple(sorted(norm(x) for x in event.get("artists", [])))
        key = event.get("id") or (event.get("startDate"), norm(event.get("city")), norm(event.get("venue")), artists)
        if key in keys: continue
        keys.add(key); out.append(event)
    return sorted([e for e in out if future(e)], key=lambda e: (e.get("startDate", ""), e.get("startTime", ""), e.get("title", "")))

def extract_json_object(text, marker):
    start = text.find(marker)
    if start < 0: return {}
    brace = text.find("{", start + len(marker))
    if brace < 0: return {}
    depth = 0; in_string = False; escape = False
    for idx in range(brace, len(text)):
        ch = text[idx]
        if in_string:
            if escape: escape = False
            elif ch == "\\": escape = True
            elif ch == '"': in_string = False
            continue
        if ch == '"': in_string = True
        elif ch == "{": depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                try: return json.loads(text[brace:idx + 1])
                except Exception: return {}
    return {}

def spotify_image(meta):
    if not meta.get("sourceRegistryVerified"): return ""
    match = re.search(r"open\.spotify\.com/artist/([A-Za-z0-9]+)", meta.get("spotifyProfile", ""))
    return f"https://open.voidware.de/artist/{match.group(1)}" if match else ""

def asset_url(value):
    value = str(value or "")
    if not value: return f"{BASE}assets/event-fallback.webp"
    if value.startswith("http://"): return "https://" + value[7:]
    if value.startswith("https://"): return value
    return BASE + value.lstrip("/")

ICONS = {
    "Instagram": '<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="3" y="3" width="18" height="18" rx="5" fill="none" stroke="currentColor" stroke-width="2"/><circle cx="12" cy="12" r="4" fill="none" stroke="currentColor" stroke-width="2"/><circle cx="17.5" cy="6.5" r="1.2" fill="currentColor"/></svg>',
    "Spotify": '<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="9" fill="none" stroke="currentColor" stroke-width="2"/><path d="M7 9.3c3.8-1 7.5-.7 10.7.9M7.8 12.4c3.1-.8 6.4-.5 9.1.8M8.7 15.2c2.5-.6 5-.4 7.2.6" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></svg>',
    "YouTube": '<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="3" y="6" width="18" height="12" rx="4" fill="none" stroke="currentColor" stroke-width="2"/><path d="M10 9.2 15 12l-5 2.8z" fill="currentColor"/></svg>',
    "Website": '<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="9" fill="none" stroke="currentColor" stroke-width="2"/><path d="M3.5 12h17M12 3c2.3 2.4 3.5 5.4 3.5 9S14.3 18.6 12 21M12 3C9.7 5.4 8.5 8.4 8.5 12S9.7 18.6 12 21" fill="none" stroke="currentColor" stroke-width="1.5"/></svg>',
}

def social_links(meta, compact=False):
    pairs = [("Instagram", meta.get("instagramProfile")), ("Spotify", meta.get("spotifyProfile")), ("YouTube", meta.get("youtubeProfile")), ("Website", meta.get("website") or meta.get("officialWebsite") or meta.get("officialProfile"))]
    out = []
    for label, url in pairs:
        if not url: continue
        klass = "seo-social-link seo-social-link-compact" if compact else "seo-social-link"
        label_html = "" if compact else f"<span>{esc(label)}</span>"
        out.append(f'<a class="{klass}" href="{esc(url)}" target="_blank" rel="noopener" aria-label="{esc(label)}">{ICONS[label]}{label_html}</a>')
    return "".join(out)

def artist_meta(config, registry):
    merged = dict(config); verified = registry.get(norm(config.get("name")), {})
    for key, value in verified.items():
        if value not in (None, "", [], {}): merged[key] = value
    merged["imageUrl"] = merged.get("imageUrl") or spotify_image(merged)
    return merged

def event_card(event, meta_by_name):
    names = event.get("artists", []) or ([event.get("headliner")] if event.get("headliner") else [])
    first = meta_by_name.get(norm(names[0]), {}) if names else {}
    image = asset_url(event.get("image") or first.get("imageUrl"))
    image_type = "event-artwork" if event.get("imageType") == "event_artwork" else "artist-photo"
    position = event.get("imagePosition") or first.get("imagePosition") or "center"
    location = ", ".join(x for x in (event.get("city"), event.get("state")) if x) or "Location to be announced"
    artist_links = " - ".join(f'<a href="{artist_href(n)}">{esc(n)}</a>' for n in names)
    official = event.get("officialUrl") or event.get("ticketUrl") or event_href(event)
    source = event.get("sourceName") or ((event.get("sources") or [{}])[0].get("name")) or "Official source"
    return f'''<article class="event-card" data-event-card data-state="{esc(event.get('state'))}" data-type="{esc(event.get('eventType') or 'concert')}" data-date="{esc(event.get('startDate'))}" data-end-date="{esc(event.get('endDate') or event.get('startDate'))}"><a class="event-media" href="{event_href(event)}"><img class="{image_type}" src="{esc(image)}" alt="{esc(event.get('title') or 'Christian hip-hop event')}" loading="lazy" decoding="async" width="1200" height="675" style="object-position:{esc(position)}"></a><div class="event-content"><div class="event-main"><div class="event-badges"><span class="badge badge-gold">{esc('Festival' if event.get('eventType') == 'festival' else 'Concert')}</span></div><h3><a href="{event_href(event)}">{esc(event.get('title') or 'Christian hip-hop event')}</a></h3><p class="artist-line">{artist_links}</p><dl class="event-meta"><div><dt>Date</dt><dd>{esc(format_date(event))}</dd></div><div><dt>Venue</dt><dd>{esc(event.get('venue') or 'Venue to be announced')}</dd></div><div><dt>Location</dt><dd>{esc(location)}</dd></div></dl></div><div class="event-footer"><a class="official-button" href="{esc(official)}" target="_blank" rel="noopener">Official details</a><p class="source-line">Source: {esc(source)}</p></div></div></article>'''

def schema_script(obj): return f'<script type="application/ld+json">{json.dumps(obj, separators=(",", ":"), ensure_ascii=False).replace("</", "<\\/")}</script>'

def patch_head(text, title, description, canonical_path, schemas=None, enhancements=False):
    text = re.sub(r"<title>.*?</title>", f"<title>{esc(title)}</title>", text, flags=re.S)
    text = re.sub(r'<meta name="description" content="[^"]*">', f'<meta name="description" content="{esc(description)}">', text, count=1)
    text = re.sub(r'<link rel="canonical"[^>]*>\s*', '', text)
    text = re.sub(r'\s*<!-- KC SEO TEST SCHEMA -->.*?<!-- /KC SEO TEST SCHEMA -->\s*', '\n', text, flags=re.S)
    additions = [f'<link rel="canonical" href="{esc(canonical(canonical_path))}">']
    if schemas: additions.append(SCHEMA_MARKER + "".join(schema_script(x) for x in schemas) + "<!-- /KC SEO TEST SCHEMA -->")
    if enhancements and "seo-test-enhancements.js" not in text: additions.append(f'<script src="{BASE}seo-test-enhancements.js?v=1" defer></script>')
    return text.replace("</head>", "  " + "\n  ".join(additions) + "\n</head>", 1)

def replace_main(text, content): return re.sub(r"<main>.*?</main>", f"<main>{content}</main>", text, count=1, flags=re.S)

def write_page(root, rel, text):
    path = root / rel.strip("/") / "index.html"; path.parent.mkdir(parents=True, exist_ok=True); path.write_text(text, encoding="utf-8")

def breadcrumb(items):
    parts = [esc(label) if i == len(items) - 1 else f'<a class="text-link" href="{href}">{esc(label)}</a>' for i, (label, href) in enumerate(items)]
    return '<p class="eyebrow">' + ' / '.join(parts) + '</p>'

def breadcrumb_schema(items):
    return {"@context":"https://schema.org","@type":"BreadcrumbList","itemListElement":[{"@type":"ListItem","position":i+1,"name":name,"item":canonical(path)} for i,(name,path) in enumerate(items)]}

def artist_schema(name, meta, page_path):
    same_as = [x for x in [meta.get("instagramProfile"), meta.get("spotifyProfile"), meta.get("youtubeProfile"), meta.get("website") or meta.get("officialWebsite")] if x]
    obj = {"@context":"https://schema.org","@type":"MusicGroup","name":name,"url":canonical(page_path),"genre":["Christian hip hop","Christian rap"]}
    if meta.get("imageUrl"): obj["image"] = meta["imageUrl"]
    if same_as: obj["sameAs"] = same_as
    return obj

def state_chips(name, shows):
    counts = Counter(e.get("state") for e in shows if e.get("state"))
    return "".join(f'<a class="seo-chip" href="{artist_state_href(name, code)}">{esc(STATE_NAMES.get(code, code))} <span>{count}</span></a>' for code, count in sorted(counts.items(), key=lambda x: (-x[1], STATE_NAMES.get(x[0], x[0]))))

def summary_for_artist(name, shows):
    if not shows: return f"Kingdom Circuit monitors {esc(name)} for newly announced Christian hip-hop concerts, festivals, and tour dates across the United States. No upcoming U.S. dates are currently confirmed in our verified listings."
    states = sorted({e.get("state") for e in shows if e.get("state")}); first = shows[0]
    location = ", ".join(x for x in (first.get("city"), first.get("state")) if x)
    return f"Kingdom Circuit currently lists {len(shows)} verified upcoming U.S. show{'s' if len(shows) != 1 else ''} for {esc(name)} across {len(states)} state{'s' if len(states) != 1 else ''}. The next confirmed appearance is {esc(format_date(first))}{(' in ' + esc(location)) if location else ''}."

def artist_page_main(name, meta, shows, meta_by_name):
    states = sorted({e.get("state") for e in shows if e.get("state")}); festivals = sum(1 for e in shows if e.get("eventType") == "festival"); next_show = shows[0] if shows else None; image = meta.get("imageUrl")
    visual = f'<div class="seo-profile-image"><img src="{esc(image)}" alt="{esc(name)}" width="900" height="900"></div>' if image else f'<div class="seo-profile-image seo-profile-placeholder" aria-hidden="true">{esc(name[:1])}</div>'
    next_copy = "No confirmed date" if not next_show else f"{esc(format_date(next_show))}<br><span>{esc(', '.join(x for x in (next_show.get('city'), next_show.get('state')) if x))}</span>"
    state_options = "".join(f'<option value="{esc(code)}">{esc(STATE_NAMES.get(code, code))}</option>' for code in states)
    event_html = "".join(event_card(e, meta_by_name) for e in shows) if shows else '<div class="empty-panel">No upcoming U.S. shows are currently confirmed. Kingdom Circuit continues monitoring official sources for new dates.</div>'
    label_line = f'<p class="seo-roster-note">Roster data: {esc(meta.get("label"))}</p>' if meta.get("label") else ""; chips = state_chips(name, shows)
    return f'''<section class="seo-artist-profile"><div class="seo-breadcrumb-wrap">{breadcrumb([('Artists', BASE+'artists/'), (name, artist_href(name))])}</div><section class="seo-artist-hero">{visual}<div class="seo-artist-copy"><p class="eyebrow">Christian hip-hop artist</p><h1>{esc(name)} Concerts &amp; Tour Dates</h1><p class="seo-artist-summary">{summary_for_artist(name, shows)}</p>{label_line}<div class="seo-social-links" aria-label="Official {esc(name)} links">{social_links(meta)}</div></div></section><section class="seo-stat-grid" aria-label="{esc(name)} show summary"><div><span>Upcoming shows</span><strong>{len(shows)}</strong></div><div><span>States</span><strong>{len(states)}</strong></div><div><span>Festivals</span><strong>{festivals}</strong></div><div class="seo-next-show"><span>Next show</span><strong>{next_copy}</strong></div></section>{f'<section class="seo-location-strip"><div><p class="eyebrow">Browse by location</p><h2>{esc(name)} Shows by State</h2></div><div class="seo-chip-row">{chips}</div></section>' if chips else ''}<section class="calendar seo-artist-calendar" id="shows" data-artist-show-calendar><div class="calendar-heading"><div><p class="eyebrow">Verified listings</p><h2>Upcoming {esc(name)} Shows</h2><p class="section-intro">Filter {esc(name)} concerts and festival appearances by state, date, or location. The complete verified listing remains available below.</p></div><p class="results-count" data-artist-results-count>{len(shows)} shows</p></div><div class="filter-dock" data-artist-page-filters><div class="quick-filters" role="group" aria-label="Quick {esc(name)} show filters"><button class="filter-chip active" type="button" data-artist-date-mode="all">All dates</button><button class="filter-chip" type="button" data-artist-date-mode="next30">Next 30 days</button><button class="filter-chip" type="button" data-artist-date-mode="month">This month</button><button class="filter-chip" type="button" data-artist-type-mode="festival">Festivals</button></div><form class="filters seo-artist-filters" role="search"><label class="field field-search"><span>Search</span><input data-artist-show-search type="search" placeholder="City, venue, or event" autocomplete="off"></label><label class="field"><span>State</span><select data-artist-state-filter><option value="">All states</option>{state_options}</select></label><label class="field"><span>Type</span><select data-artist-type-filter><option value="">All events</option><option value="concert">Concerts</option><option value="festival">Festivals</option></select></label><button class="reset-button" data-artist-reset type="button">Clear filters</button></form></div><div class="event-grid" data-artist-event-grid>{event_html}</div><div class="empty-panel" data-artist-filter-empty hidden>No {esc(name)} shows match those filters.</div></section></section>'''

def artist_state_main(name, code, shows, meta_by_name):
    state = STATE_NAMES.get(code, code); cities = Counter(e.get("city") for e in shows if e.get("city")); city_links = "".join(f'<a class="seo-chip" href="{city_href(city, code)}">{esc(city)} <span>{count}</span></a>' for city, count in sorted(cities.items(), key=lambda x: (-x[1], x[0])))
    return f'''<section class="page-hero hero-compact seo-location-hero">{breadcrumb([('Artists', BASE+'artists/'), (name, artist_href(name)), (state, artist_state_href(name, code))])}<p class="eyebrow">{esc(name)} in {esc(state)}</p><h1>{esc(name)} Concerts in {esc(state)}</h1><p class="hero-text">Find {len(shows)} verified upcoming {esc(name)} Christian hip-hop show{'s' if len(shows) != 1 else ''} in {esc(state)}, including official dates, venues, cities, and ticket sources.</p><div class="seo-context-links"><a class="secondary-button" href="{artist_href(name)}">All {esc(name)} shows</a><a class="secondary-button" href="{state_href(code)}">All CHH shows in {esc(state)}</a></div></section><section class="seo-location-strip"><div><p class="eyebrow">Cities</p><h2>{esc(name)} Shows Across {esc(state)}</h2></div><div class="seo-chip-row">{city_links}</div></section><section class="calendar"><div class="calendar-heading"><div><p class="eyebrow">Verified listings</p><h2>Upcoming {esc(name)} Shows in {esc(state)}</h2></div><p class="results-count">{len(shows)} shows</p></div><div class="event-grid">{''.join(event_card(e, meta_by_name) for e in shows)}</div></section>'''

def directory_card(meta, shows):
    name = meta.get("name") or "Artist"; image = meta.get("imageUrl"); states = Counter(e.get("state") for e in shows if e.get("state")); state_text = ", ".join(code for code, _ in states.most_common(3)); next_show = shows[0] if shows else None
    visual = f'<img src="{esc(image)}" alt="{esc(name)}" loading="lazy" decoding="async" width="600" height="600">' if image else f'<span class="seo-artist-initial">{esc(name[:1])}</span>'
    next_line = f'<p class="seo-card-next"><strong>Next:</strong> {esc(format_date(next_show))} · {esc(", ".join(x for x in (next_show.get("city"), next_show.get("state")) if x))}</p>' if next_show else '<p class="seo-card-next">Monitoring for new dates</p>'; state_line = f'<p class="seo-card-states"><strong>Upcoming:</strong> {esc(state_text)}</p>' if state_text else ""
    return f'''<article class="artist-card seo-artist-card" data-artist-card data-has-shows="{str(bool(shows)).lower()}" data-search="{esc(name)} {esc(state_text)}"><a class="artist-visual" href="{artist_href(name)}" aria-label="View {esc(name)}">{visual}</a><div class="artist-card-body"><h2><a href="{artist_href(name)}">{esc(name)}</a></h2><p>{len(shows)} upcoming show{'s' if len(shows) != 1 else ''}</p>{next_line}{state_line}<div class="seo-card-socials">{social_links(meta, compact=True)}</div><div class="artist-card-footer"><a class="text-link" href="{artist_href(name)}">View concerts &amp; tour dates</a></div></div></article>'''

def build_directory(root, artists, shows_by_artist, meta_by_name):
    path = root / "artists/index.html"
    if not path.exists(): return
    text = path.read_text(encoding="utf-8"); cards = []; item_list = []
    ordered = sorted((a for a in artists if a.get("enabled") is not False), key=lambda a: (a.get("rosterOrder", 9999), norm(a.get("name"))))
    for idx, cfg in enumerate(ordered):
        name = cfg.get("name") or "Artist"; meta = meta_by_name[norm(name)]; shows = shows_by_artist.get(norm(name), []); cards.append(directory_card(meta, shows)); item_list.append({"@type":"ListItem","position":idx+1,"url":canonical(artist_href(name)),"name":name})
    main = f'''<section class="page-hero hero-compact seo-directory-hero"><p class="eyebrow">Christian hip-hop artists</p><h1>Christian Hip-Hop Artists, Rappers &amp; Upcoming Shows</h1><p class="hero-text">Browse the Kingdom Circuit directory of Christian hip-hop and Christian rap artists. Open verified official social and streaming profiles, see the next confirmed concert, and explore every upcoming show by artist.</p></section><section class="directory-section" data-artist-directory data-seo-enhanced-directory><div class="directory-toolbar"><label class="field field-search"><span>Search artists</span><input data-artist-search type="search" placeholder="Search artist or state"></label><label class="check-field"><input data-has-shows-filter type="checkbox"> Only artists with upcoming shows</label><p class="results-count" data-artist-count>{len(cards)} artists</p></div><div class="artist-grid seo-artist-grid" data-artist-grid>{''.join(cards)}</div><div class="empty-panel" data-artist-empty hidden>No artists match that search.</div></section><section class="seo-topic-section"><p class="eyebrow">Explore Christian rap live</p><h2>Find Christian Hip-Hop Concerts by Artist</h2><p>Kingdom Circuit connects artist profiles directly to verified concert, festival, city, state, and event pages. That makes it easier to find searches such as KB concerts, Lecrae tour dates, Christian rap shows in Texas, and upcoming CHH festivals without digging through unrelated listings.</p></section>'''
    schema = {"@context":"https://schema.org","@type":"ItemList","name":"Christian Hip-Hop Artists","itemListElement":item_list}
    text = patch_head(text, "Christian Hip-Hop Artists, Rappers & Concerts | Kingdom Circuit", "Browse Christian hip-hop and Christian rap artists, verified social profiles, upcoming concerts, tour dates, festivals, and official show links.", BASE + "artists/", [schema], enhancements=True); text = replace_main(text, main); path.write_text(text, encoding="utf-8")

def build_artist_pages(root, artists, shows_by_artist, meta_by_name):
    generated_state_pages = []
    for cfg in (a for a in artists if a.get("enabled") is not False):
        name = cfg.get("name") or "Artist"; meta = meta_by_name[norm(name)]; shows = shows_by_artist.get(norm(name), []); path = root / f"artists/{slug(name)}/index.html"
        if not path.exists(): continue
        text = path.read_text(encoding="utf-8"); page_path = BASE + f"artists/{slug(name)}/"; schemas = [artist_schema(name, meta, page_path), breadcrumb_schema([("Artists", BASE + "artists/"), (name, page_path)])]
        text = patch_head(text, f"{name} Concerts & Tour Dates {TODAY.year} | Kingdom Circuit", f"Find upcoming {name} concerts, tour dates, festivals, locations, and verified official show links. Filter {name} shows by state and date.", page_path, schemas, enhancements=True); text = replace_main(text, artist_page_main(name, meta, shows, meta_by_name)); path.write_text(text, encoding="utf-8")
        by_state = defaultdict(list)
        for event in shows:
            if event.get("state"): by_state[event["state"]].append(event)
        for code, state_shows in by_state.items():
            state = STATE_NAMES.get(code, code); state_path = BASE + f"artists/{slug(name)}/{slug(state)}/"; state_text = patch_head(text, f"{name} Concerts in {state} | Upcoming Shows", f"Find verified upcoming {name} concerts and Christian hip-hop shows in {state}, with dates, cities, venues, and official links.", state_path, [artist_schema(name, meta, artist_href(name)), breadcrumb_schema([("Artists", BASE + "artists/"), (name, artist_href(name)), (state, state_path)])]); state_text = replace_main(state_text, artist_state_main(name, code, state_shows, meta_by_name)); write_page(root, f"artists/{slug(name)}/{slug(state)}/", state_text); generated_state_pages.append(state_path)
    return generated_state_pages

def location_stats(shows):
    artists = Counter(); cities = Counter()
    for e in shows:
        for n in e.get("artists", []): artists[n] += 1
        if e.get("city"): cities[e["city"]] += 1
    return artists, cities

def patch_location_pages(root, events, meta_by_name):
    by_state = defaultdict(list); by_city = defaultdict(list)
    for e in events:
        if e.get("state"): by_state[e["state"]].append(e)
        if e.get("state") and e.get("city"): by_city[(e["city"], e["state"])].append(e)
    for code, shows in by_state.items():
        state = STATE_NAMES.get(code, code); path = root / f"shows/{slug(state)}/index.html"
        if not path.exists(): continue
        text = path.read_text(encoding="utf-8"); artist_counts, city_counts = location_stats(shows); artist_links = "".join(f'<a class="seo-chip" href="{artist_href(name)}">{esc(name)} <span>{count}</span></a>' for name, count in artist_counts.most_common(14)); city_links = "".join(f'<a class="seo-chip" href="{city_href(city, code)}">{esc(city)} <span>{count}</span></a>' for city, count in city_counts.most_common()); next_show = shows[0]
        main = f'''<section class="page-hero hero-compact seo-location-hero">{breadcrumb([('Shows', BASE+'shows/'), (state, state_href(code))])}<p class="eyebrow">Christian hip-hop in {esc(state)}</p><h1>Christian Hip-Hop &amp; Rap Concerts in {esc(state)}</h1><p class="hero-text">Browse {len(shows)} verified upcoming Christian hip-hop concerts, Christian rap shows, and festivals across {len(city_counts)} {esc(state)} cit{'ies' if len(city_counts) != 1 else 'y'}. The next confirmed listing is {esc(format_date(next_show))} in {esc(next_show.get('city') or state)}.</p></section><section class="seo-location-strip"><div><p class="eyebrow">Featured artists</p><h2>Artists With Upcoming {esc(state)} Shows</h2></div><div class="seo-chip-row">{artist_links}</div></section><section class="seo-location-strip"><div><p class="eyebrow">Browse cities</p><h2>Christian Hip-Hop Shows by City</h2></div><div class="seo-chip-row">{city_links}</div></section><section class="calendar"><div class="calendar-heading"><div><p class="eyebrow">Verified listings</p><h2>Upcoming CHH Shows in {esc(state)}</h2></div><p class="results-count">{len(shows)} shows</p></div><div class="event-grid">{''.join(event_card(e, meta_by_name) for e in shows)}</div></section>'''
        state_path = BASE + f"shows/{slug(state)}/"; text = patch_head(text, f"Christian Hip-Hop & Rap Concerts in {state} | Kingdom Circuit", f"Find upcoming Christian hip-hop concerts, Christian rap shows, festivals, artists, cities, and verified event details in {state}.", state_path, [breadcrumb_schema([("Shows", BASE + "shows/"), (state, state_path)])]); text = replace_main(text, main); path.write_text(text, encoding="utf-8")
    for (city, code), shows in by_city.items():
        state = STATE_NAMES.get(code, code); path = root / f"shows/{slug(city)}-{slug(state)}/index.html"
        if not path.exists(): continue
        text = path.read_text(encoding="utf-8"); artist_counts, _ = location_stats(shows); artist_links = "".join(f'<a class="seo-chip" href="{artist_href(name)}">{esc(name)} <span>{count}</span></a>' for name, count in artist_counts.most_common(14)); next_show = shows[0]; city_path = BASE + f"shows/{slug(city)}-{slug(state)}/"
        main = f'''<section class="page-hero hero-compact seo-location-hero">{breadcrumb([('Shows', BASE+'shows/'), (state, state_href(code)), (city, city_path)])}<p class="eyebrow">{esc(city)}, {esc(code)}</p><h1>Christian Hip-Hop &amp; Rap Concerts in {esc(city)}</h1><p class="hero-text">Find {len(shows)} verified upcoming Christian hip-hop concert{'s' if len(shows) != 1 else ''} and festival{'s' if len(shows) != 1 else ''} in {esc(city)}, {esc(state)}. The next confirmed listing is {esc(format_date(next_show))} at {esc(next_show.get('venue') or 'a local venue')}.</p><div class="seo-context-links"><a class="secondary-button" href="{state_href(code)}">All {esc(state)} CHH shows</a></div></section><section class="seo-location-strip"><div><p class="eyebrow">Artists coming to {esc(city)}</p><h2>Upcoming Christian Rap Artists</h2></div><div class="seo-chip-row">{artist_links}</div></section><section class="calendar"><div class="calendar-heading"><div><p class="eyebrow">Verified listings</p><h2>Upcoming CHH Shows in {esc(city)}</h2></div><p class="results-count">{len(shows)} shows</p></div><div class="event-grid">{''.join(event_card(e, meta_by_name) for e in shows)}</div></section>'''
        text = patch_head(text, f"Christian Hip-Hop & Rap Concerts in {city}, {code} | Kingdom Circuit", f"Find upcoming Christian hip-hop concerts, Christian rap shows, festivals, artists, venues, and verified event details in {city}, {state}.", city_path, [breadcrumb_schema([("Shows", BASE + "shows/"), (state, state_href(code)), (city, city_path)])]); text = replace_main(text, main); path.write_text(text, encoding="utf-8")

def patch_home(root, events, shows_by_artist):
    path = root / "index.html"
    if not path.exists(): return
    text = path.read_text(encoding="utf-8"); states = Counter(e.get("state") for e in events if e.get("state")); active_artists = Counter({name:len(shows) for name, shows in shows_by_artist.items() if shows}); meta = json.loads((root / "config/artists.json").read_text(encoding="utf-8")); proper = {norm(a.get("name")):a.get("name") for a in meta}
    state_links = "".join(f'<a class="seo-chip" href="{state_href(code)}">{esc(STATE_NAMES.get(code, code))} <span>{count}</span></a>' for code, count in states.most_common(12)); artist_links = "".join(f'<a class="seo-chip" href="{artist_href(proper.get(name, name))}">{esc(proper.get(name, name))} <span>{count}</span></a>' for name, count in active_artists.most_common(16)); section = f'''<section class="seo-discovery-section"><div><p class="eyebrow">Explore the Christian rap circuit</p><h2>Christian Hip-Hop Concerts by Artist &amp; State</h2><p>Use Kingdom Circuit to find verified Christian hip-hop and Christian rap concerts across the U.S. Browse active artists, tour dates, state calendars, festivals, and individual event pages.</p></div><div class="seo-discovery-grid"><div><h3>Popular active artists</h3><div class="seo-chip-row">{artist_links}</div></div><div><h3>States with upcoming shows</h3><div class="seo-chip-row">{state_links}</div></div></div></section>'''
    if "seo-discovery-section" not in text: text = text.replace("</main>", section + "</main>", 1)
    org = {"@context":"https://schema.org","@type":"Organization","name":"The Kingdom Circuit","url":TEST_ORIGIN+"/","logo":TEST_ORIGIN+"/assets/logo.png","description":"Christian hip-hop concert, festival, artist, and live-event discovery."}; site = {"@context":"https://schema.org","@type":"WebSite","name":"The Kingdom Circuit","url":TEST_ORIGIN+"/","about":["Christian hip hop","Christian rap","Christian hip-hop concerts"]}
    text = patch_head(text, "Christian Hip-Hop Shows, Concerts & Festivals | Kingdom Circuit", "Find verified Christian hip-hop concerts, Christian rap shows, tour dates, festivals, artists, and live events across the United States.", BASE, [org, site]); path.write_text(text, encoding="utf-8")

def patch_event_pages(root, events):
    by_artist = defaultdict(list); by_state = defaultdict(list)
    for e in events:
        for n in e.get("artists", []): by_artist[norm(n)].append(e)
        if e.get("state"): by_state[e["state"]].append(e)
    for event in events:
        path = root / f"event/{event_slug(event)}/index.html"
        if not path.exists(): continue
        text = path.read_text(encoding="utf-8"); names = event.get("artists", []); related = []; seen = {event_slug(event)}
        for n in names:
            for other in by_artist[norm(n)]:
                key = event_slug(other)
                if key not in seen: seen.add(key); related.append(other)
        for other in by_state.get(event.get("state"), []):
            key = event_slug(other)
            if key not in seen: seen.add(key); related.append(other)
        links = "".join(f'<a class="seo-chip" href="{artist_href(n)}">More {esc(n)} concerts</a>' for n in names[:4])
        if event.get("state"): links += f'<a class="seo-chip" href="{state_href(event["state"])}">More CHH shows in {esc(STATE_NAMES.get(event["state"], event["state"]))}</a>'
        if event.get("city") and event.get("state"): links += f'<a class="seo-chip" href="{city_href(event["city"], event["state"])}">More shows in {esc(event["city"])}</a>'
        cards = "".join(f'<article class="seo-related-card"><p>{esc(format_date(x))}</p><h3><a href="{event_href(x)}">{esc(x.get("title") or "Christian hip-hop event")}</a></h3><span>{esc(", ".join(y for y in (x.get("city"), x.get("state")) if y))}</span></article>' for x in related[:3]); block = f'''<section class="seo-related-section"><p class="eyebrow">Keep exploring</p><h2>More Christian Hip-Hop Shows</h2><div class="seo-chip-row">{links}</div>{f'<div class="seo-related-grid">{cards}</div>' if cards else ''}</section>'''
        if "seo-related-section" not in text: text = text.replace("</main>", block + "</main>", 1)
        path.write_text(text, encoding="utf-8")

def patch_app(root):
    path = root / "app.js"
    if not path.exists(): return
    text = path.read_text(encoding="utf-8")
    if JS_MARKER not in text:
        pattern = r"(^\s*)renderArtistDirectory\(\);"; replacement = r"\1" + JS_MARKER + "\n" + r"\1if (!document.querySelector('[data-seo-enhanced-directory]')) renderArtistDirectory();"; text, count = re.subn(pattern, replacement, text, count=1, flags=re.M)
        if count != 1: raise RuntimeError("Could not guard renderArtistDirectory in app.js")
    path.write_text(text, encoding="utf-8")

def write_enhancement_js(root):
    code = r'''"use strict";(function(){function isoDate(v){const d=new Date(String(v||"")+"T12:00:00");return Number.isNaN(d.getTime())?null:d}function today(){const d=new Date();d.setHours(0,0,0,0);return d}function bindDirectory(){const r=document.querySelector('[data-seo-enhanced-directory]');if(!r)return;const i=r.querySelector('[data-artist-search]'),o=r.querySelector('[data-has-shows-filter]'),c=r.querySelector('[data-artist-count]'),e=r.querySelector('[data-artist-empty]'),cards=[...r.querySelectorAll('[data-artist-card]')];function apply(){const q=String(i?.value||'').trim().toLowerCase();let n=0;for(const card of cards){const ok=(!q||String(card.dataset.search||card.textContent||'').toLowerCase().includes(q))&&(!o?.checked||card.dataset.hasShows==='true');card.hidden=!ok;if(ok)n++}if(c)c.textContent=`${n} artist${n===1?'':'s'}`;if(e)e.hidden=n!==0}i?.addEventListener('input',apply);o?.addEventListener('change',apply);apply()}function bindArtist(){const cal=document.querySelector('[data-artist-show-calendar]');if(!cal)return;const d=cal.querySelector('[data-artist-page-filters]'),cards=[...cal.querySelectorAll('[data-event-card]')],q=d?.querySelector('[data-artist-show-search]'),s=d?.querySelector('[data-artist-state-filter]'),t=d?.querySelector('[data-artist-type-filter]'),reset=d?.querySelector('[data-artist-reset]'),count=cal.querySelector('[data-artist-results-count]'),empty=cal.querySelector('[data-artist-filter-empty]');let dm='all',tm='';function passDate(card){if(dm==='all')return true;const x=isoDate(card.dataset.date);if(!x)return true;const now=today();if(dm==='next30'){const end=new Date(now);end.setDate(end.getDate()+30);return x>=now&&x<=end}if(dm==='month')return x.getFullYear()===now.getFullYear()&&x.getMonth()===now.getMonth();return true}function apply(){const needle=String(q?.value||'').trim().toLowerCase(),st=String(s?.value||''),ty=tm||String(t?.value||'');let n=0;for(const card of cards){const ok=passDate(card)&&(!needle||String(card.textContent||'').toLowerCase().includes(needle))&&(!st||card.dataset.state===st)&&(!ty||card.dataset.type===ty);card.hidden=!ok;if(ok)n++}if(count)count.textContent=`${n} show${n===1?'':'s'}`;if(empty)empty.hidden=n!==0}d?.querySelectorAll('[data-artist-date-mode]').forEach(btn=>btn.addEventListener('click',()=>{dm=btn.dataset.artistDateMode||'all';d.querySelectorAll('[data-artist-date-mode]').forEach(x=>x.classList.toggle('active',x===btn));apply()}));d?.querySelectorAll('[data-artist-type-mode]').forEach(btn=>btn.addEventListener('click',()=>{tm=tm==='festival'?'':(btn.dataset.artistTypeMode||'');btn.classList.toggle('active',tm==='festival');if(t)t.value='';apply()}));q?.addEventListener('input',apply);s?.addEventListener('change',apply);t?.addEventListener('change',()=>{tm='';d?.querySelectorAll('[data-artist-type-mode]').forEach(x=>x.classList.remove('active'));apply()});reset?.addEventListener('click',()=>{if(q)q.value='';if(s)s.value='';if(t)t.value='';dm='all';tm='';d?.querySelectorAll('[data-artist-date-mode]').forEach(x=>x.classList.toggle('active',x.dataset.artistDateMode==='all'));d?.querySelectorAll('[data-artist-type-mode]').forEach(x=>x.classList.remove('active'));history.replaceState(null,'',location.pathname);apply()});const requested=new URLSearchParams(location.search).get('state');if(requested&&s&&[...s.options].some(o=>o.value===requested))s.value=requested;apply()}document.addEventListener('DOMContentLoaded',()=>{bindDirectory();bindArtist()})})();'''
    (root / "seo-test-enhancements.js").write_text(code, encoding="utf-8")

def append_styles(root):
    path = root / "styles.css"; text = path.read_text(encoding="utf-8")
    if CSS_MARKER in text: return
    css = r'''/* KC SEO TEST OVERLAY V1 */
.seo-breadcrumb-wrap{max-width:var(--max);margin:auto;padding:44px 24px 0}.seo-artist-hero{max-width:var(--max);margin:auto;padding:34px 24px 54px;display:grid;grid-template-columns:minmax(260px,360px) 1fr;gap:48px;align-items:center}.seo-profile-image{aspect-ratio:1/1;border-radius:24px;overflow:hidden;border:1px solid var(--line);background:linear-gradient(145deg,#17120a,#080808)}.seo-profile-image img{width:100%;height:100%;object-fit:cover;display:block}.seo-profile-placeholder{display:grid;place-items:center;color:var(--gold-light);font-size:8rem;font-weight:900}.seo-artist-copy h1{font-size:clamp(3rem,7vw,6rem);line-height:.92;letter-spacing:-.05em;text-transform:uppercase;margin:0 0 24px}.seo-artist-summary{font-size:1.16rem;color:var(--muted);max-width:780px}.seo-roster-note{color:#777;font-size:.86rem}.seo-social-links,.seo-card-socials{display:flex;gap:10px;flex-wrap:wrap;margin-top:22px}.seo-social-link{display:inline-flex;align-items:center;gap:9px;border:1px solid #4d4d4d;border-radius:999px;padding:10px 14px;text-decoration:none;font-weight:800}.seo-social-link:hover{border-color:var(--gold);color:var(--gold-light)}.seo-social-link svg{width:20px;height:20px;display:block}.seo-social-link-compact{width:36px;height:36px;padding:7px;justify-content:center}.seo-social-link-compact svg{width:18px;height:18px}.seo-stat-grid{max-width:var(--max);margin:0 auto 56px;padding:0 24px;display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:14px}.seo-stat-grid>div{border:1px solid var(--line);border-radius:16px;padding:20px;background:var(--panel)}.seo-stat-grid span{display:block;color:var(--muted);font-size:.72rem;text-transform:uppercase;letter-spacing:.1em;font-weight:900}.seo-stat-grid strong{display:block;margin-top:8px;font-size:2rem;color:var(--gold-light);line-height:1.05}.seo-stat-grid .seo-next-show strong{font-size:1rem;color:var(--cream);line-height:1.4}.seo-stat-grid .seo-next-show strong span{margin-top:4px;text-transform:none;letter-spacing:0;font-size:.9rem}.seo-location-strip,.seo-topic-section,.seo-discovery-section,.seo-related-section{max-width:var(--max);margin:auto;padding:54px 24px;border-top:1px solid var(--line)}.seo-location-strip{display:grid;grid-template-columns:minmax(240px,340px) 1fr;gap:30px;align-items:start}.seo-location-strip h2,.seo-topic-section h2,.seo-discovery-section h2,.seo-related-section h2{font-size:clamp(2rem,4vw,3.5rem);line-height:1;margin:0}.seo-chip-row{display:flex;flex-wrap:wrap;gap:9px}.seo-chip{display:inline-flex;gap:8px;align-items:center;border:1px solid #444;border-radius:999px;padding:9px 13px;text-decoration:none;font-weight:800}.seo-chip:hover{border-color:var(--gold);color:var(--gold-light)}.seo-chip span{color:var(--muted);font-size:.8em}.seo-context-links{display:flex;gap:10px;flex-wrap:wrap;margin-top:24px}.seo-artist-calendar{border-top:1px solid var(--line)}.seo-artist-filters{grid-template-columns:2fr 1fr 1fr auto}.seo-artist-grid .seo-artist-card{display:flex;flex-direction:column}.seo-artist-grid .artist-visual{aspect-ratio:1/1}.seo-artist-grid .artist-card-body{display:flex;flex-direction:column;flex:1}.seo-artist-grid .artist-card-footer{margin-top:auto;padding-top:14px}.seo-artist-initial{font-size:4rem;font-weight:900;color:var(--gold-light)}.seo-card-next,.seo-card-states{font-size:.86rem;line-height:1.4}.seo-card-next strong,.seo-card-states strong{color:var(--cream)}.seo-card-socials{margin:8px 0 4px}.seo-topic-section p,.seo-discovery-section p{color:var(--muted);max-width:900px;font-size:1.05rem}.seo-discovery-grid{display:grid;grid-template-columns:1fr 1fr;gap:28px;margin-top:32px}.seo-discovery-grid h3{margin:0 0 14px;font-size:1.25rem}.seo-related-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:14px;margin-top:24px}.seo-related-card{border:1px solid var(--line);border-radius:15px;background:var(--panel);padding:18px}.seo-related-card p,.seo-related-card span{color:var(--muted);font-size:.84rem}.seo-related-card h3{margin:8px 0;font-size:1.15rem}.seo-related-card h3 a{text-decoration:none}.seo-directory-hero,.seo-location-hero{background:radial-gradient(circle at 75% 10%,rgba(198,148,60,.08),transparent 34%)}
@media(max-width:900px){.seo-artist-hero{grid-template-columns:1fr}.seo-profile-image{max-width:500px}.seo-stat-grid{grid-template-columns:1fr 1fr}.seo-location-strip{grid-template-columns:1fr}.seo-discovery-grid{grid-template-columns:1fr}.seo-related-grid{grid-template-columns:1fr}.seo-artist-filters{grid-template-columns:1fr 1fr}.seo-artist-filters .reset-button{grid-column:1/-1}}
@media(max-width:600px){.seo-breadcrumb-wrap{padding:34px 16px 0}.seo-artist-hero{padding:28px 16px 42px;gap:28px}.seo-stat-grid{padding:0 16px;grid-template-columns:1fr 1fr}.seo-stat-grid strong{font-size:1.6rem}.seo-location-strip,.seo-topic-section,.seo-discovery-section,.seo-related-section{padding:42px 16px}.seo-artist-filters{grid-template-columns:1fr}.seo-artist-filters .reset-button{grid-column:auto}}'''
    path.write_text(text.rstrip() + "\n\n" + css + "\n", encoding="utf-8")

def update_sitemap(root, extra_paths):
    path = root / "sitemap.xml"
    if not path.exists(): return
    text = path.read_text(encoding="utf-8"); existing = set(re.findall(r"<loc>(.*?)</loc>", text)); rows = []
    for p in extra_paths:
        url = canonical(p)
        if url in existing: continue
        existing.add(url); rows.append(f"<url><loc>{esc(url)}</loc><lastmod>{TODAY.isoformat()}</lastmod></url>")
    if rows: path.write_text(text.replace("</urlset>", "\n" + "\n".join(rows) + "\n</urlset>"), encoding="utf-8")

def verify(root, generated_state_pages):
    failures = []; kb = root / "artists/kb/index.html"
    if kb.exists():
        text = kb.read_text(encoding="utf-8")
        for required in ["KB Concerts &amp; Tour Dates", "data-artist-state-filter", "seo-social-link", "Upcoming KB Shows"]:
            if required not in text: failures.append(f"kb-missing:{required}")
    directory = (root / "artists/index.html").read_text(encoding="utf-8")
    for required in ["data-seo-enhanced-directory", "seo-card-socials", "Christian Hip-Hop Artists, Rappers"]:
        if required not in directory: failures.append(f"directory-missing:{required}")
    if JS_MARKER not in (root / "app.js").read_text(encoding="utf-8"): failures.append("app-directory-guard")
    if CSS_MARKER not in (root / "styles.css").read_text(encoding="utf-8"): failures.append("css-overlay")
    if not (root / "seo-test-enhancements.js").exists(): failures.append("enhancement-js")
    for p in root.rglob("*.html"):
        text = p.read_text(encoding="utf-8", errors="ignore")
        if 'name="robots" content="noindex,nofollow"' not in text:
            failures.append(f"noindex:{p}")
            if len(failures) > 40: break
    if generated_state_pages and not any((root / p.replace(BASE, "").strip("/") / "index.html").exists() for p in generated_state_pages): failures.append("artist-state-pages")
    if failures: raise SystemExit("SEO overlay verification failed:\n" + "\n".join(failures[:60]))

def main():
    import sys
    if len(sys.argv) != 2: raise SystemExit("Usage: apply_test_overlay.py SITE_ROOT")
    root = pathlib.Path(sys.argv[1]).resolve(); events = json.loads((root / "events.json").read_text(encoding="utf-8")); supplemental = json.loads((root / "supplemental-events.json").read_text(encoding="utf-8")) if (root / "supplemental-events.json").exists() else []; artists = json.loads((root / "config/artists.json").read_text(encoding="utf-8")); events = merge_events(events, supplemental); app_text = (root / "app.js").read_text(encoding="utf-8"); registry = extract_json_object(app_text, "const VERIFIED_ARTIST_REGISTRY =")
    meta_by_name = {}; aliases = {}
    for cfg in artists:
        meta = artist_meta(cfg, registry); name = cfg.get("name") or ""; meta_by_name[norm(name)] = meta
        for alias in [name, *cfg.get("aliases", [])]: aliases[norm(alias)] = norm(name)
    shows_by_artist = defaultdict(list)
    for event in events:
        attached = set()
        for raw_name in event.get("artists", []):
            key = aliases.get(norm(raw_name), norm(raw_name))
            if key in meta_by_name and key not in attached: attached.add(key); shows_by_artist[key].append(event)
    for key in shows_by_artist: shows_by_artist[key].sort(key=lambda e: (e.get("startDate", ""), e.get("startTime", "")))
    patch_app(root); write_enhancement_js(root); append_styles(root); build_directory(root, artists, shows_by_artist, meta_by_name); generated_state_pages = build_artist_pages(root, artists, shows_by_artist, meta_by_name); patch_location_pages(root, events, meta_by_name); patch_home(root, events, shows_by_artist); patch_event_pages(root, events); update_sitemap(root, generated_state_pages)
    manifest = {"generatedAt":dt.datetime.now(dt.timezone.utc).isoformat(),"mode":"seo-test-overlay-v1","artistsEnhanced":sum(1 for a in artists if a.get("enabled") is not False),"eventsEnhanced":len(events),"artistStatePages":len(generated_state_pages),"verifiedRegistryEntries":len(registry),"features":["artist-directory","artist-profiles","verified-social-icons","artist-show-filters","artist-state-pages","location-pages","event-internal-links","organization-schema","sitemap-expansion"]}
    (root / "seo-test-overlay-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8"); verify(root, generated_state_pages); print(json.dumps(manifest, indent=2))

if __name__ == "__main__": main()
