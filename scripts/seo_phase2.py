from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import pathlib
import re
import shutil
from collections import defaultdict

REPO = pathlib.Path.cwd()
OUT = REPO / "_site"
BASE_PATH = "/kingdom-circuit-test/"
SITE_ORIGIN = "https://84lorinw-a11y.github.io"
LIVE_SITE = "https://kingdomcircuit.com"
TODAY = dt.date.today()
YEAR = TODAY.year

STATE_NAMES = {
    "AL":"Alabama","AK":"Alaska","AZ":"Arizona","AR":"Arkansas","CA":"California","CO":"Colorado",
    "CT":"Connecticut","DE":"Delaware","DC":"District of Columbia","FL":"Florida","GA":"Georgia",
    "HI":"Hawaii","ID":"Idaho","IL":"Illinois","IN":"Indiana","IA":"Iowa","KS":"Kansas","KY":"Kentucky",
    "LA":"Louisiana","ME":"Maine","MD":"Maryland","MA":"Massachusetts","MI":"Michigan","MN":"Minnesota",
    "MS":"Mississippi","MO":"Missouri","MT":"Montana","NE":"Nebraska","NV":"Nevada","NH":"New Hampshire",
    "NJ":"New Jersey","NM":"New Mexico","NY":"New York","NC":"North Carolina","ND":"North Dakota",
    "OH":"Ohio","OK":"Oklahoma","OR":"Oregon","PA":"Pennsylvania","RI":"Rhode Island","SC":"South Carolina",
    "SD":"South Dakota","TN":"Tennessee","TX":"Texas","UT":"Utah","VT":"Vermont","VA":"Virginia",
    "WA":"Washington","WV":"West Virginia","WI":"Wisconsin","WY":"Wyoming"
}


def esc(v) -> str:
    return html.escape(str(v or ""), quote=True)


def norm(v) -> str:
    return str(v or "").strip().casefold()


def slug(v: str) -> str:
    value = norm(v).replace("&", " and ")
    return re.sub(r"[^a-z0-9]+", "-", value).strip("-") or "item"


def fnv(v) -> str:
    h = 0x811C9DC5
    for b in str(v).encode("utf-8"):
        h ^= b
        h = (h * 0x01000193) & 0xFFFFFFFF
    return f"{h:08x}"[:6]


def old_event_slug(e: dict) -> str:
    core = "-".join(filter(None, [slug(e.get("title") or "event"), e.get("startDate", ""), slug(e.get("city", ""))]))
    return f"{core}-{fnv(e.get('id') or json.dumps(e, sort_keys=True))}"


def clean_title_for_slug(title: str, year: int | None) -> str:
    text = str(title or "event").strip()
    if year:
        text = re.sub(rf"\b{year}\b", "", text)
        text = re.sub(r"\s{2,}", " ", text).strip(" -–—:")
    return text or "event"


def clean_event_slug(e: dict) -> str:
    year = None
    try:
        year = dt.date.fromisoformat(str(e.get("startDate"))[:10]).year
    except Exception:
        pass
    core = "-".join(filter(None, [slug(clean_title_for_slug(e.get("title") or "event", year)), e.get("startDate", ""), slug(e.get("city", ""))]))
    return f"{core}-{fnv(e.get('id') or json.dumps(e, sort_keys=True))}"


def absolute(path: str) -> str:
    if path.startswith("http://") or path.startswith("https://"):
        return path.replace("http://", "https://", 1)
    return SITE_ORIGIN.rstrip("/") + "/" + path.lstrip("/")


def local_path(path: str) -> str:
    return BASE_PATH + path.lstrip("/")


def parse_date(raw) -> dt.date | None:
    try:
        return dt.date.fromisoformat(str(raw)[:10])
    except Exception:
        return None


def is_upcoming(e: dict) -> bool:
    d = parse_date(e.get("endDate") or e.get("startDate"))
    return d is None or d >= TODAY


def clean_city(raw: str) -> tuple[str, str]:
    text = re.sub(r"\s+", " ", str(raw or "").strip())
    text = re.sub(r"^sponsor\s+", "", text, flags=re.I)
    metro = ""
    match = re.match(r"^(.*?)\s*\(([^)]+)\)\s*$", text)
    if match:
        text = match.group(1).strip()
        metro = match.group(2).strip()
    return text, metro


def clean_event(e: dict) -> dict:
    out = dict(e)
    city, metro = clean_city(out.get("city", ""))
    if city:
        out["city"] = city
    if metro and not out.get("metro"):
        out["metro"] = metro
    title = str(out.get("title") or "")
    out["title"] = re.sub(r"([—–-]\s*)Sponsor\s+", r"\1", title, flags=re.I)
    return out


def event_artist_set(e: dict) -> set[str]:
    return {norm(x) for x in e.get("artists", []) if x}


def source_priority(e: dict) -> int:
    priorities = [s.get("priority", 0) or 0 for s in e.get("sources", []) if isinstance(s, dict)]
    return max(priorities or [0])


def same_event(a: dict, b: dict) -> bool:
    if a.get("startDate") != b.get("startDate"):
        return False
    shared = bool(event_artist_set(a) & event_artist_set(b))
    if not shared:
        return False
    acity, _ = clean_city(a.get("city", ""))
    bcity, _ = clean_city(b.get("city", ""))
    same_city = norm(acity) == norm(bcity) and bool(norm(acity))
    same_venue = norm(a.get("venue")) == norm(b.get("venue")) and bool(norm(a.get("venue")))
    same_address = norm(a.get("address")) == norm(b.get("address")) and bool(norm(a.get("address")))
    return same_city or same_venue or same_address


def richer_value(old, new) -> bool:
    oldn = norm(old)
    return (not oldn or "to be announced" in oldn or oldn in {"tba", "unknown"}) and bool(norm(new))


def merge_events(*lists: list[dict]) -> list[dict]:
    merged: list[dict] = []
    for source_list in lists:
        for raw in source_list:
            if not isinstance(raw, dict):
                continue
            incoming = clean_event(raw)
            found = next((x for x in merged if same_event(x, incoming)), None)
            if not found:
                merged.append(dict(incoming, artists=list(incoming.get("artists", []))))
                continue
            found["artists"] = list(dict.fromkeys([*found.get("artists", []), *incoming.get("artists", [])]))
            for key in ("venue", "address", "city", "timezone", "image", "imageType", "imagePosition", "price", "ticketUrl", "officialUrl", "firstSeen", "lastVerified"):
                if richer_value(found.get(key), incoming.get(key)):
                    found[key] = incoming[key]
            if source_priority(incoming) > source_priority(found):
                for key in ("sourceName", "sources", "officialUrl", "ticketUrl"):
                    if incoming.get(key):
                        found[key] = incoming[key]
    return merged


def load_json(path: pathlib.Path, fallback):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return fallback


def find_supplemental() -> list[dict]:
    for path in [OUT / "supplemental-events-v6.json", OUT / "supplemental-events.json", REPO / "supplemental-events-v6.json", REPO / "supplemental-events.json"]:
        if path.exists():
            data = load_json(path, [])
            if isinstance(data, list):
                return data
    return []


PRIMARY_EVENTS = load_json(OUT / "events.json", load_json(REPO / "events.json", []))
ARTISTS = load_json(OUT / "artists.json", load_json(REPO / "artists.json", []))
SUPPLEMENTAL = find_supplemental()
ARCHIVE = load_json(REPO / "event-archive.json", [])
if not isinstance(ARCHIVE, list):
    ARCHIVE = []

MERGED_CURRENT = merge_events(PRIMARY_EVENTS, SUPPLEMENTAL)
ALL_EVENTS = merge_events(ARCHIVE, MERGED_CURRENT)
UPCOMING = sorted((e for e in ALL_EVENTS if is_upcoming(e)), key=lambda e: (e.get("startDate", ""), e.get("startTime", ""), e.get("title", "")))
PAST = sorted((e for e in ALL_EVENTS if not is_upcoming(e)), key=lambda e: (e.get("startDate", ""), e.get("startTime", "")), reverse=True)

ARTIST_BY_NAME = {}
for artist in ARTISTS:
    if artist.get("enabled") is False:
        continue
    ARTIST_BY_NAME[norm(artist.get("name"))] = artist
    for alias in artist.get("aliases", []):
        ARTIST_BY_NAME.setdefault(norm(alias), artist)

EXISTING_EVENT_DIRS = {p.name for p in (OUT / "event").iterdir() if p.is_dir()} if (OUT / "event").exists() else set()


def event_slug(e: dict) -> str:
    old = old_event_slug(e)
    return old if old in EXISTING_EVENT_DIRS else clean_event_slug(e)


def event_path(e: dict) -> str:
    return local_path(f"event/{event_slug(e)}/")


def artist_path(name: str) -> str:
    return local_path(f"artists/{slug(name)}/")


def state_path(code: str) -> str:
    return local_path(f"shows/{slug(STATE_NAMES.get(code, code))}/")


def city_path(city: str, code: str) -> str:
    cleaned, _ = clean_city(city)
    return local_path(f"shows/{slug(cleaned)}-{slug(STATE_NAMES.get(code, code))}/")


def month_path(d: dt.date) -> str:
    return local_path(f"shows/{d.strftime('%B').lower()}-{d.year}/")


def asset_url(value: str | None) -> str:
    if not value:
        return local_path("assets/event-fallback.webp")
    text = str(value)
    if text.startswith("http://") or text.startswith("https://"):
        return text.replace("http://", "https://", 1)
    return local_path(text)


def artist_cfg(name: str) -> dict:
    return ARTIST_BY_NAME.get(norm(name), {})


def artist_image(artist: dict) -> str:
    return asset_url(artist.get("imageUrl")) if artist.get("imageUrl") else ""


def spotify(artist: dict) -> str:
    return artist.get("spotifyProfile") or (f"https://open.spotify.com/artist/{artist['spotifyId']}" if artist.get("spotifyId") else "")


def instagram(artist: dict) -> str:
    return artist.get("instagramProfile", "")


def youtube(artist: dict) -> str:
    if artist.get("youtubeProfile"):
        return artist["youtubeProfile"]
    value = artist.get("officialProfile", "")
    return value if re.search(r"youtu\.be|youtube\.com", value, re.I) else ""


def website(artist: dict) -> str:
    value = artist.get("website") or artist.get("officialWebsite") or artist.get("officialProfile") or ""
    if re.search(r"instagram\.com|open\.spotify\.com|youtu\.be|youtube\.com|music\.apple\.com|bandsintown\.com", value, re.I):
        return ""
    return value


def verified_socials(artist: dict) -> list[tuple[str, str]]:
    pairs = [("Instagram", instagram(artist)), ("Spotify", spotify(artist)), ("YouTube", youtube(artist)), ("Website", website(artist))]
    return [(label, url) for label, url in pairs if url]


def format_date(e: dict, include_year=True) -> str:
    date = parse_date(e.get("startDate"))
    if not date:
        return "Date to be announced"
    fmt = "%a, %b %-d, %Y" if include_year else "%a, %b %-d"
    text = date.strftime(fmt)
    if e.get("startTime"):
        try:
            hour, minute = [int(x) for x in str(e["startTime"]).split(":")[:2]]
            text += f" · {hour % 12 or 12}:{minute:02d} {'AM' if hour < 12 else 'PM'}"
        except Exception:
            pass
    return text


def source_text(e: dict) -> str:
    return e.get("sourceName") or ((e.get("sources") or [{}])[0].get("name")) or "Official source"


def location_html(e: dict) -> str:
    city = e.get("city") or ""
    state = e.get("state") or ""
    if city and state:
        return f'<a href="{city_path(city, state)}">{esc(city)}</a>, <a href="{state_path(state)}">{esc(state)}</a>'
    if city:
        return esc(city)
    if state:
        return f'<a href="{state_path(state)}">{esc(STATE_NAMES.get(state, state))}</a>'
    return "Location to be announced"


def event_card(e: dict) -> str:
    cfg = artist_cfg(e.get("headliner") or ((e.get("artists") or [""])[0]))
    image = asset_url(e.get("image") or cfg.get("imageUrl"))
    image_class = "event-artwork" if e.get("imageType") == "event_artwork" else "artist-photo"
    position = e.get("imagePosition") or cfg.get("imagePosition") or "center"
    search = " ".join(str(x or "") for x in [e.get("title"), e.get("venue"), e.get("city"), e.get("state"), source_text(e), *e.get("artists", [])])
    artists_data = "|".join(norm(x) for x in e.get("artists", []))
    artists_html = " · ".join(f'<a href="{artist_path(name)}">{esc(name)}</a>' for name in e.get("artists", []))
    official = e.get("ticketUrl") or e.get("officialUrl") or "#"
    label = "Tickets / official details" if e.get("ticketUrl") else "Official details"
    price = f'<p class="price-line">Listed price: {esc(e.get("price"))}</p>' if e.get("price") else ""
    alt_suffix = "event artwork" if image_class == "event-artwork" else "artist photo"
    return f'''<article class="event-card" data-event-card data-search="{esc(norm(search))}" data-artists="{esc(artists_data)}" data-state="{esc(e.get('state'))}" data-type="{esc(e.get('eventType') or 'concert')}" data-date="{esc(e.get('startDate'))}" data-end-date="{esc(e.get('endDate') or e.get('startDate'))}">
<a class="event-media" href="{event_path(e)}" aria-label="View {esc(e.get('title'))}"><img class="{image_class}" src="{esc(image)}" alt="{esc(e.get('title'))} {alt_suffix}" loading="lazy" decoding="async" width="1200" height="675" style="object-position:{esc(position)}"></a>
<div class="event-content"><div class="event-main"><div class="event-badges"><span class="badge badge-gold">{esc('Festival' if e.get('eventType') == 'festival' else 'Concert')}</span></div><h3><a href="{event_path(e)}">{esc(e.get('title'))}</a></h3><p class="artist-line">{artists_html}</p><dl class="event-meta"><div><dt>Date</dt><dd>{esc(format_date(e))}</dd></div><div><dt>Venue</dt><dd>{esc(e.get('venue') or 'Venue to be announced')}</dd></div><div><dt>Location</dt><dd>{location_html(e)}</dd></div></dl>{price}</div><div class="event-footer"><a class="official-button" href="{esc(official)}" target="_blank" rel="noopener">{esc(label)}</a><p class="source-line">Source: {esc(source_text(e))}</p></div></div></article>'''


def filter_dock(include_artist=False) -> str:
    artist_field = '<label class="field"><span>Artist</span><select data-artist-filter><option value="">All artists</option></select></label>' if include_artist else ""
    return f'''<div class="filter-dock" data-filter-dock>
<div class="quick-filters" role="group" aria-label="Quick event filters"><button class="filter-chip active" type="button" data-date-mode="all">All dates</button><button class="filter-chip" type="button" data-date-mode="weekend">This weekend</button><button class="filter-chip" type="button" data-date-mode="next30">Next 30 days</button><button class="filter-chip" type="button" data-date-mode="month">This month</button><button class="filter-chip" type="button" data-type-mode="festival">Festivals</button></div>
<form class="filters" role="search" data-event-filters><label class="field field-search"><span>Search</span><input data-search-filter type="search" placeholder="City, venue, or event" autocomplete="off"></label>{artist_field}<label class="field"><span>State</span><select data-state-filter><option value="">All states</option></select></label><label class="field"><span>Type</span><select data-type-filter><option value="">All events</option><option value="concert">Concerts</option><option value="festival">Festivals</option></select></label><button class="reset-button" data-reset-filters type="button">Clear filters</button></form></div>'''


def test_header(current="") -> str:
    items = [("Home", BASE_PATH, "home"), ("All Shows", local_path("shows/"), "shows"), ("This Month", local_path("shows/this-month/"), "month"), ("Festivals", local_path("festivals/"), "festivals"), ("New Shows", local_path("new-shows/"), "new"), ("Artists", local_path("artists/"), "artists"), ("Submit a Show", local_path("submit/"), "submit")]
    links = []
    for label, href, key in items:
        current_attr = ' aria-current="page"' if key == current else ""
        links.append(f'<a href="{href}"{current_attr}>{label}</a>')
    return f'''<div class="test-site-banner">TEST SITE — SEO Phase 2 preview. <a href="{LIVE_SITE}">Open the live site</a></div><header class="site-header"><div class="header-inner"><a class="brand" href="{BASE_PATH}" aria-label="The Kingdom Circuit home"><img src="{local_path('assets/logo.png')}" alt="The Kingdom Circuit — Christian hip-hop, live and connected"></a><button class="menu-toggle" type="button" aria-expanded="false" aria-controls="site-menu" aria-label="Open navigation"><span></span><span></span><span></span></button></div></header><div class="menu-backdrop" hidden></div><nav class="menu-drawer" id="site-menu" aria-label="Primary navigation" aria-hidden="true"><div class="menu-drawer-head"><span>Explore Kingdom Circuit</span><button class="menu-close" type="button" aria-label="Close navigation">×</button></div><div class="menu-links">{''.join(links)}</div><p class="menu-mission">Christian hip-hop, live and connected.</p></nav>'''


def test_footer() -> str:
    return f'''<footer class="site-footer"><div><strong>The Kingdom Circuit</strong><p>Christian hip-hop, live and connected.</p></div><div class="footer-links"><a href="{local_path('shows/')}">All Shows</a><a href="{local_path('artists/')}">Artists</a><a href="{local_path('festivals/')}">Festivals</a><a href="{local_path('about/')}">How we verify shows</a><a href="{local_path('submit/')}">Submit a Show</a></div><p class="footer-note">Test site data is loaded from Kingdom Circuit sources. Event details may change; confirm with the official source before traveling.</p></footer>'''


def schemas_html(schemas: list[dict]) -> str:
    return "\n".join('<script type="application/ld+json">' + json.dumps(schema, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/") + "</script>" for schema in schemas)


def head(title: str, desc: str, canonical_path: str, schemas=None, production_index=True, og_image="") -> str:
    canonical = absolute(canonical_path)
    og_image = og_image or absolute(local_path("assets/logo.png"))
    policy = "index,follow" if production_index else "noindex,follow"
    return f'''<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><meta name="robots" content="noindex,nofollow"><meta name="kc-production-index-policy" content="{policy}"><meta name="description" content="{esc(desc)}"><meta name="theme-color" content="#080808"><link rel="canonical" href="{esc(canonical)}"><link rel="icon" href="{local_path('assets/favicon.svg')}" type="image/svg+xml"><link rel="stylesheet" href="{local_path('styles.css')}"><link rel="stylesheet" href="{local_path('patch-v6.css')}"><link rel="stylesheet" href="{local_path('seo-phase2.css')}"><meta property="og:type" content="website"><meta property="og:title" content="{esc(title)}"><meta property="og:description" content="{esc(desc)}"><meta property="og:url" content="{esc(canonical)}"><meta property="og:image" content="{esc(og_image)}"><meta name="twitter:card" content="summary_large_image"><script src="{local_path('seo-static.js')}" defer></script><script src="{local_path('seo-phase2.js')}" defer></script><title>{esc(title)}</title>{schemas_html(schemas or [])}</head>'''


def breadcrumb_schema(items: list[tuple[str, str]]) -> dict:
    return {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [{"@type": "ListItem", "position": i + 1, "name": name, "item": absolute(path)} for i, (name, path) in enumerate(items)]}


def breadcrumb_html(items: list[tuple[str, str]]) -> str:
    parts = []
    for i, (name, path) in enumerate(items):
        parts.append(esc(name) if i == len(items) - 1 else f'<a class="text-link" href="{path}">{esc(name)}</a>')
    return '<p class="eyebrow">' + " / ".join(parts) + "</p>"


def page(title, desc, canonical, body, current="", schemas=None, production_index=True, og_image="") -> str:
    return f'<!DOCTYPE html><html lang="en">{head(title, desc, canonical, schemas, production_index, og_image)}<body>{test_header(current)}<main>{body}</main>{test_footer()}</body></html>'


def write_page(path: str, content: str):
    relative = path[len(BASE_PATH):] if path.startswith(BASE_PATH) else path
    relative = relative.strip("/")
    target = OUT / relative / "index.html" if relative else OUT / "index.html"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")


def artist_events(name: str, pool: list[dict]) -> list[dict]:
    target = norm(name)
    return [e for e in pool if target in event_artist_set(e)]


def production_artist_indexable(artist: dict, shows: list[dict]) -> bool:
    return bool(shows) or (bool(artist_image(artist)) and len(verified_socials(artist)) >= 2)


def artist_profile_schema(artist: dict, name: str) -> dict:
    same_as = [url for _, url in verified_socials(artist)]
    entity = {"@type": "Thing", "name": name, "url": absolute(artist_path(name))}
    if same_as:
        entity["sameAs"] = same_as
    image = artist_image(artist)
    if image:
        entity["image"] = absolute(image) if image.startswith(BASE_PATH) else image
    return {"@context": "https://schema.org", "@type": "ProfilePage", "url": absolute(artist_path(name)), "mainEntity": entity}


TOUR_GROUPS: dict[str, list[dict]] = defaultdict(list)
TOUR_DISPLAY: dict[str, str] = {}
for event in UPCOMING:
    title = str(event.get("title") or "")
    if re.search(r"\btour\b", title, re.I):
        key = norm(re.sub(r"\s+", " ", title))
        TOUR_GROUPS[key].append(event)
        TOUR_DISPLAY[key] = title
TOUR_GROUPS = {key: shows for key, shows in TOUR_GROUPS.items() if len(shows) >= 2}


def tour_path_from_key(key: str) -> str:
    return local_path(f"tours/{slug(TOUR_DISPLAY[key])}/")


EVENT_TO_TOUR = {}
for key, shows in TOUR_GROUPS.items():
    for event in shows:
        EVENT_TO_TOUR[event.get("id")] = key


def generate_artist_pages() -> tuple[list[str], dict]:
    urls = []
    metrics = {"artistProductionIndexable": 0, "artistProductionNoindex": 0, "artistPagesWithPrimaryImage": 0, "artistPagesWithVerifiedSocials": 0}
    enabled = sorted((x for x in ARTISTS if x.get("enabled") is not False), key=lambda x: (x.get("rosterOrder", 9999), str(x.get("name", "")).casefold()))
    for artist in enabled:
        name = artist.get("name") or "Artist"
        path = artist_path(name)
        urls.append(path)
        shows = sorted(artist_events(name, UPCOMING), key=lambda e: (e.get("startDate", ""), e.get("startTime", "")))
        history = sorted(artist_events(name, PAST), key=lambda e: (e.get("startDate", ""), e.get("startTime", "")), reverse=True)[:6]
        socials = verified_socials(artist)
        image = artist_image(artist)
        if image:
            metrics["artistPagesWithPrimaryImage"] += 1
        if socials:
            metrics["artistPagesWithVerifiedSocials"] += 1
        production_index = production_artist_indexable(artist, shows)
        metrics["artistProductionIndexable" if production_index else "artistProductionNoindex"] += 1
        has_ticket = any(event.get("ticketUrl") for event in shows)
        if has_ticket:
            title = f"{name} Tickets, Concerts & Tour Dates {YEAR} | The Kingdom Circuit"
        elif shows:
            title = f"{name} Concerts & Tour Dates {YEAR} | The Kingdom Circuit"
        else:
            title = f"{name} — Christian Hip-Hop Artist | The Kingdom Circuit"
        description = f"Find {len(shows)} verified upcoming {name} Christian hip-hop show{'s' if len(shows) != 1 else ''}, tour dates, locations, official links, and ticket details." if shows else f"Explore {name} on The Kingdom Circuit with verified official links and future Christian hip-hop concert listings."
        crumbs = [("Artists", local_path("artists/")), (name, path)]
        social_html = "".join(f'<a class="kc-social-pill" href="{esc(url)}" target="_blank" rel="noopener">{esc(label)}</a>' for label, url in socials) or '<span class="kc-social-empty">Verified social links are still being added.</span>'
        if image:
            visual = f'<div class="kc-artist-image"><img src="{esc(image)}" alt="{esc(name)} artist photo" decoding="async" style="object-position:{esc(artist.get("imagePosition") or "center")}"></div>'
        else:
            visual = f'<div class="kc-artist-image kc-artist-image-empty"><span>{esc(name)}</span><small>Artist image pending verification</small></div>'
        states = sorted({event.get("state") for event in shows if event.get("state")})
        stat_html = f'<div><strong>{len(shows)}</strong><span>upcoming show{"s" if len(shows) != 1 else ""}</span></div><div><strong>{len(states)}</strong><span>state{"s" if len(states) != 1 else ""}</span></div>'
        if shows:
            next_date = parse_date(shows[0].get("startDate"))
            stat_html += f'<div><strong>{esc(next_date.strftime("%b %-d") if next_date else "TBA")}</strong><span>next show</span></div>'
        tours = [(TOUR_DISPLAY[key], tour_path_from_key(key)) for key, events in TOUR_GROUPS.items() if any(norm(name) in event_artist_set(event) for event in events)]
        tours_html = '<div class="kc-artist-tours"><span>Current tour:</span> ' + " · ".join(f'<a class="text-link" href="{path}">{esc(tour)}</a>' for tour, path in tours[:3]) + "</div>" if tours else ""
        latest_verified = max((str(event.get("lastVerified") or "") for event in shows), default="")
        verification = f'<p class="kc-verification">Listings sourced from official artist, promoter, venue, or ticketing pages when available.{f" Latest verification: {esc(latest_verified[:10])}." if latest_verified else ""}</p>'
        summary = f'''<section class="kc-artist-overview">{visual}<div class="kc-artist-copy">{breadcrumb_html(crumbs)}<p class="eyebrow">Artist profile</p><h1>{esc(name)}</h1><p class="kc-artist-intro">{esc(name)} Christian hip-hop concerts, tour dates, festival appearances, and verified official links tracked by The Kingdom Circuit.</p><div class="kc-social-links" aria-label="{esc(name)} official links">{social_html}</div><div class="kc-artist-stats">{stat_html}</div>{tours_html}{verification}</div></section>'''
        next_cards = "".join(f'<a class="kc-next-show" href="{event_path(event)}"><span class="kc-next-date">{esc(format_date(event, include_year=False))}</span><strong>{esc(event.get("title"))}</strong><span>{esc(event.get("city") or "Location TBA")}{", " + esc(event.get("state")) if event.get("state") else ""}</span></a>' for event in shows[:3])
        next_section = f'<section class="kc-artist-next"><div class="calendar-heading"><div><p class="eyebrow">At a glance</p><h2>Next {esc(name)} Shows</h2><p class="section-intro">Quick links to the next verified appearances.</p></div></div><div class="kc-next-grid">{next_cards}</div></section>' if next_cards else ""
        if shows:
            full = f'<section class="calendar kc-artist-calendar" data-kc-filter-scope><div class="calendar-heading"><div><p class="eyebrow">Verified listings</p><h2>All Upcoming {esc(name)} Shows</h2><p class="section-intro">Search and filter {esc(name)} concerts, festivals, cities, and venues.</p></div><p class="results-count" data-results-count>{len(shows)} shows</p></div>{filter_dock(False)}<div class="event-grid" data-event-grid>{"".join(event_card(event) for event in shows)}</div><div class="empty-panel" data-filtered-empty hidden>No shows currently match those filters.</div></section>'
        else:
            full = f'<section class="calendar kc-artist-calendar"><div class="calendar-heading"><div><p class="eyebrow">Verified listings</p><h2>Upcoming {esc(name)} Shows</h2></div></div><div class="empty-panel">No upcoming U.S. shows are currently confirmed. Kingdom Circuit will add verified dates as they are announced.</div></section>'
        history_html = ""
        if history:
            history_html = '<section class="kc-history"><div class="calendar-heading"><div><p class="eyebrow">Archive</p><h2>Past Kingdom Circuit Listings</h2></div></div><div class="kc-history-list">' + "".join(f'<a href="{event_path(event)}"><strong>{esc(event.get("title"))}</strong><span>{esc(format_date(event))} · {esc(event.get("city"))}, {esc(event.get("state"))}</span></a>' for event in history) + "</div></section>"
        schemas = [breadcrumb_schema(crumbs), artist_profile_schema(artist, name)]
        write_page(path, page(title, description, path, summary + next_section + full + history_html, current="artists", schemas=schemas, production_index=production_index, og_image=image))
    return urls, metrics


def event_status_schema(event: dict) -> str:
    status = norm(event.get("status"))
    if "cancel" in status:
        return "https://schema.org/EventCancelled"
    if "postpon" in status:
        return "https://schema.org/EventPostponed"
    if "resched" in status:
        return "https://schema.org/EventRescheduled"
    return "https://schema.org/EventScheduled"


def event_schema(event: dict) -> dict:
    start = str(event.get("startDate") or "")
    if event.get("startTime"):
        start += "T" + str(event["startTime"])
    data = {"@context": "https://schema.org", "@type": "MusicEvent", "name": event.get("title") or "Christian hip-hop event", "startDate": start, "eventAttendanceMode": "https://schema.org/OfflineEventAttendanceMode", "eventStatus": event_status_schema(event), "url": absolute(event_path(event)), "image": [asset_url(event.get("image"))], "description": f"{event.get('title') or 'Christian hip-hop event'} in {event.get('city') or ''}, {event.get('state') or ''}. Verified listing from The Kingdom Circuit.", "performer": [{"@type": "MusicGroup", "name": name} for name in event.get("artists", [])]}
    place = {"@type": "Place"}
    venue = str(event.get("venue") or "").strip()
    if venue and "to be announced" not in norm(venue) and norm(venue) not in {"tba", "unknown"}:
        place["name"] = venue
    address = {"@type": "PostalAddress", "addressLocality": event.get("city") or "", "addressRegion": event.get("state") or "", "addressCountry": "US"}
    if event.get("address"):
        address["streetAddress"] = event["address"]
    if any(value for key, value in address.items() if key != "@type"):
        place["address"] = address
    if len(place) > 1:
        data["location"] = place
    if event.get("endDate"):
        data["endDate"] = event["endDate"]
    if event.get("ticketUrl"):
        offer = {"@type": "Offer", "url": event["ticketUrl"]}
        price = str(event.get("price") or "").strip()
        if price.casefold() == "free":
            offer.update({"price": 0, "priceCurrency": "USD"})
        elif re.fullmatch(r"\$?\d+(?:\.\d{1,2})?", price):
            offer.update({"price": price.lstrip("$"), "priceCurrency": "USD"})
        status = norm(event.get("status"))
        if "sold" in status and "out" in status:
            offer["availability"] = "https://schema.org/SoldOut"
        elif "onsale" in status or "on sale" in status:
            offer["availability"] = "https://schema.org/InStock"
        data["offers"] = offer
    if event.get("organizerName"):
        data["organizer"] = {"@type": "Organization", "name": event["organizerName"]}
        if event.get("organizerUrl"):
            data["organizer"]["url"] = event["organizerUrl"]
    return data


def generate_event_pages() -> list[str]:
    urls = []
    by_state = defaultdict(list)
    for event in UPCOMING:
        if event.get("state"):
            by_state[event["state"]].append(event)
    for event in ALL_EVENTS:
        path = event_path(event)
        urls.append(path)
        past = not is_upcoming(event)
        state_name = STATE_NAMES.get(event.get("state", ""), event.get("state", ""))
        location = ", ".join(x for x in (event.get("city"), event.get("state")) if x)
        title = f"{event.get('title')} — {location} | The Kingdom Circuit"
        artist_names = ", ".join(event.get("artists", [])) or event.get("headliner") or "CHH artists"
        description = f"{artist_names} live in {location} on {format_date(event)}. Verified venue, event, and official link information."
        crumbs = [("Shows", local_path("shows/"))]
        if event.get("state"):
            crumbs.append((state_name, state_path(event["state"])))
        crumbs.append((event.get("title") or "Event", path))
        image = asset_url(event.get("image"))
        image_class = "event-artwork" if event.get("imageType") == "event_artwork" else "artist-photo"
        artist_links = " · ".join(f'<a href="{artist_path(name)}">{esc(name)}</a>' for name in event.get("artists", []))
        ticket = event.get("ticketUrl")
        official = event.get("officialUrl") or ticket or "#"
        primary_label = "Tickets / registration" if ticket else "Official event details"
        status_notice = '<div class="kc-past-notice"><strong>This event has passed.</strong> Browse upcoming artist and nearby CHH listings below.</div>' if past else ""
        tour_html = ""
        if event.get("id") in EVENT_TO_TOUR:
            key = EVENT_TO_TOUR[event.get("id")]
            tour_html = f'<div><dt>Tour</dt><dd><a class="text-link" href="{tour_path_from_key(key)}">{esc(TOUR_DISPLAY[key])}</a></dd></div>'
        verified = f'<div><dt>Last verified</dt><dd>{esc(str(event.get("lastVerified") or "Recently verified")[:10])}</dd></div>'
        price_html = f'<div><dt>Price</dt><dd>{esc(event.get("price"))}</dd></div>' if event.get("price") else ""
        secondary = f'<a class="text-link kc-secondary-official" href="{esc(official)}" target="_blank" rel="noopener">Official organizer page</a>' if ticket and official != ticket else ""
        details = f'''<section class="event-detail-section">{breadcrumb_html(crumbs)}{status_notice}<article class="event-detail"><div class="event-detail-media"><img class="{image_class}" src="{esc(image)}" alt="{esc(event.get('title'))} event image" decoding="async" width="1200" height="675" style="object-position:{esc(event.get('imagePosition') or 'center')}"></div><div class="event-detail-copy"><p class="eyebrow">{esc('Festival' if event.get('eventType') == 'festival' else 'Concert')}</p><h1>{esc(event.get('title'))}</h1><p class="artist-line">{artist_links}</p><dl class="detail-list"><div><dt>Date</dt><dd>{esc(format_date(event))}</dd></div><div><dt>Venue</dt><dd>{esc(event.get('venue') or 'Venue to be announced')}</dd></div><div><dt>Location</dt><dd>{location_html(event)}</dd></div>{tour_html}{price_html}<div><dt>Source</dt><dd>{esc(source_text(event))}</dd></div>{verified}</dl><a class="primary-button" href="{esc(ticket or official)}" target="_blank" rel="noopener">{esc(primary_label)}</a>{secondary}<p class="disclaimer">Event details, availability, pricing, and lineups may change. Confirm final information with the official organizer or ticket provider before purchasing or traveling.</p></div></article></section>'''
        names = {norm(name) for name in event.get("artists", [])}
        related_artist = [other for other in UPCOMING if other.get("id") != event.get("id") and names & event_artist_set(other)]
        nearby = [other for other in by_state.get(event.get("state", ""), []) if other.get("id") != event.get("id")]
        related = related_artist[:3] or nearby[:3]
        related_html = f'<section class="calendar"><div class="calendar-heading"><div><p class="eyebrow">Keep exploring</p><h2>{"More shows from these artists" if related_artist else "Other nearby CHH shows"}</h2></div></div><div class="event-grid">{"".join(event_card(other) for other in related)}</div></section>' if related else ""
        schemas = [breadcrumb_schema(crumbs)]
        if not past:
            schemas.insert(0, event_schema(event))
        write_page(path, page(title, description, path, details + related_html, current="shows", schemas=schemas, production_index=True, og_image=image))
    return urls


def calendar_page(path: str, label: str, h1: str, intro: str, shows: list[dict], title: str, desc: str, current="shows"):
    crumbs = [("Shows", local_path("shows/")), (label, path)]
    body = f'<section class="page-hero hero-compact">{breadcrumb_html(crumbs)}<p class="eyebrow">{esc(label)}</p><h1>{esc(h1)}</h1><p class="hero-text">{esc(intro)}</p></section><section class="calendar" data-kc-filter-scope><div class="calendar-heading"><div><p class="eyebrow">Verified listings</p><h2>Upcoming Shows</h2></div><p class="results-count" data-results-count>{len(shows)} shows</p></div>{filter_dock(True)}<div class="event-grid" data-event-grid>{"".join(event_card(event) for event in shows)}</div><div class="empty-panel" data-filtered-empty hidden>No shows currently match those filters.</div></section>'
    write_page(path, page(title, desc, path, body, current=current, schemas=[breadcrumb_schema(crumbs)], production_index=bool(shows)))


def remove_old_location_dirs(valid_slugs: set[str]):
    root = OUT / "shows"
    if not root.exists():
        return
    for path in list(root.iterdir()):
        if path.is_dir() and path.name != "this-month" and path.name not in valid_slugs:
            shutil.rmtree(path)


def generate_location_and_time_pages() -> list[str]:
    urls = []
    states = defaultdict(list)
    cities = defaultdict(list)
    months = defaultdict(list)
    for event in UPCOMING:
        if event.get("state"):
            states[event["state"]].append(event)
        if event.get("city") and event.get("state"):
            cities[(event["city"], event["state"])].append(event)
        date = parse_date(event.get("startDate"))
        if date:
            months[(date.year, date.month)].append(event)
    valid_slugs = {slug(STATE_NAMES.get(code, code)) for code in states}
    valid_slugs |= {f"{slug(city)}-{slug(STATE_NAMES.get(code, code))}" for city, code in cities}
    valid_slugs |= {dt.date(year, month, 1).strftime("%B").lower() + f"-{year}" for year, month in months}
    valid_slugs |= {str(YEAR), "this-week", "this-weekend"}
    remove_old_location_dirs(valid_slugs)
    for code, shows in sorted(states.items()):
        name = STATE_NAMES.get(code, code)
        path = state_path(code)
        urls.append(path)
        calendar_page(path, name, f"Christian Hip-Hop Shows in {name}", f"Find upcoming Christian hip-hop and Christian rap concerts, festivals, artists, venues, and official event links in {name}.", shows, f"Christian Hip-Hop Concerts & Shows in {name} {YEAR} | The Kingdom Circuit", f"Find upcoming Christian hip-hop and Christian rap concerts, festivals, and live events in {name} in {YEAR}.")
    for (city, code), shows in sorted(cities.items(), key=lambda item: (item[0][1], item[0][0].casefold())):
        state_name = STATE_NAMES.get(code, code)
        path = city_path(city, code)
        urls.append(path)
        calendar_page(path, f"{city}, {code}", f"Christian Hip-Hop Shows in {city}", f"Find verified upcoming Christian hip-hop and Christian rap concerts in {city}, {state_name}, including artists, venues, dates, and official links.", shows, f"Christian Hip-Hop Concerts in {city}, {code} {YEAR} | The Kingdom Circuit", f"Find upcoming Christian hip-hop and Christian rap concerts, festivals, and live events in {city}, {state_name} in {YEAR}.")
    for (year, month), shows in sorted(months.items()):
        date = dt.date(year, month, 1)
        label = date.strftime("%B %Y")
        path = month_path(date)
        urls.append(path)
        calendar_page(path, label, f"Christian Hip-Hop Shows in {label}", f"Browse verified Christian hip-hop concerts, Christian rap shows, and festivals scheduled for {label}.", shows, f"Christian Hip-Hop Shows in {label} | The Kingdom Circuit", f"Find Christian hip-hop and Christian rap concerts, festivals, and live events in {label}.")
    year_shows = [event for event in UPCOMING if parse_date(event.get("startDate")) and parse_date(event.get("startDate")).year == YEAR]
    year_path = local_path(f"shows/{YEAR}/")
    urls.append(year_path)
    calendar_page(year_path, str(YEAR), f"Christian Hip-Hop Concerts & Shows {YEAR}", f"Browse the verified {YEAR} U.S. Christian hip-hop concert calendar, including CHH tours, festivals, cities, artists, and official event links.", year_shows, f"Christian Hip-Hop Concerts & Shows {YEAR} | The Kingdom Circuit", f"Find verified Christian hip-hop and Christian rap concerts, festivals, tours, and live events across the United States in {YEAR}.")
    monday = TODAY - dt.timedelta(days=TODAY.weekday())
    sunday = monday + dt.timedelta(days=6)
    week = [event for event in UPCOMING if parse_date(event.get("startDate")) and monday <= parse_date(event.get("startDate")) <= sunday]
    week_path = local_path("shows/this-week/")
    urls.append(week_path)
    calendar_page(week_path, "This week", "Christian Hip-Hop Shows This Week", f"Verified CHH concerts and festivals happening {monday.strftime('%b %-d')}–{sunday.strftime('%b %-d, %Y')}.", week, "Christian Hip-Hop Shows This Week | The Kingdom Circuit", "Find Christian hip-hop and Christian rap concerts happening this week across the United States.")
    friday = TODAY + dt.timedelta(days=(4 - TODAY.weekday()) % 7)
    weekend_end = friday + dt.timedelta(days=2)
    weekend = [event for event in UPCOMING if parse_date(event.get("startDate")) and friday <= parse_date(event.get("startDate")) <= weekend_end]
    weekend_path = local_path("shows/this-weekend/")
    urls.append(weekend_path)
    calendar_page(weekend_path, "This weekend", "Christian Hip-Hop Shows This Weekend", f"Verified CHH concerts and festivals happening {friday.strftime('%b %-d')}–{weekend_end.strftime('%b %-d, %Y')}.", weekend, "Christian Hip-Hop Shows This Weekend | The Kingdom Circuit", "Find Christian hip-hop and Christian rap concerts happening this weekend across the United States.")
    return urls


def generate_tour_pages() -> list[str]:
    urls = []
    for key, shows in sorted(TOUR_GROUPS.items()):
        title = TOUR_DISPLAY[key]
        path = tour_path_from_key(key)
        urls.append(path)
        artists = sorted({name for event in shows for name in event.get("artists", [])}, key=str.casefold)
        artist_links = " · ".join(f'<a href="{artist_path(name)}">{esc(name)}</a>' for name in artists)
        crumbs = [("Shows", local_path("shows/")), ("Tours", local_path("shows/")), (title, path)]
        body = f'<section class="page-hero hero-compact">{breadcrumb_html(crumbs)}<p class="eyebrow">Tour dates</p><h1>{esc(title)}</h1><p class="hero-text">{artist_links}</p><p class="hero-text">Verified {YEAR} dates, cities, venues, and official ticket or event links.</p></section><section class="calendar" data-kc-filter-scope><div class="calendar-heading"><div><p class="eyebrow">Verified tour listings</p><h2>{esc(title)} Dates</h2></div><p class="results-count" data-results-count>{len(shows)} shows</p></div>{filter_dock(False)}<div class="event-grid">{"".join(event_card(event) for event in shows)}</div><div class="empty-panel" data-filtered-empty hidden>No tour dates match those filters.</div></section>'
        write_page(path, page(f"{title} {YEAR}: Tour Dates & Tickets | The Kingdom Circuit", f"Find verified {title} {YEAR} tour dates, cities, venues, artists, and official ticket or event links.", path, body, current="shows", schemas=[breadcrumb_schema(crumbs)], production_index=True))
    return urls


def generate_about_page() -> str:
    path = local_path("about/")
    crumbs = [("Home", BASE_PATH), ("How we verify shows", path)]
    body = f'''<section class="page-hero hero-compact">{breadcrumb_html(crumbs)}<p class="eyebrow">About Kingdom Circuit</p><h1>How Kingdom Circuit Verifies CHH Shows</h1><p class="hero-text">The Kingdom Circuit exists to connect people with CHH music, concerts, festivals, and community so the music reaches farther and more people have the opportunity to hear the gospel.</p></section><section class="kc-about-grid"><article><h2>What we list</h2><p>We focus on Christian hip-hop concerts, tours, festivals, and live appearances in the United States when a monitored CHH artist is explicitly billed.</p></article><article><h2>Where details come from</h2><p>Listings are built from official artist, promoter, venue, festival, and ticketing sources when available. Each event keeps its source and verification information so visitors can confirm final details.</p></article><article><h2>What “verified” means</h2><p>Kingdom Circuit checks the artist, date, location, and official event or ticket source before presenting a listing as verified. Event details can still change, so the official source remains the final authority.</p></article><article><h2>Corrections and submissions</h2><p>Artists, promoters, venues, and fans can submit a show or correction through the Kingdom Circuit submission page.</p><p><a class="primary-button" href="{local_path('submit/')}">Submit a show or correction</a></p></article></section>'''
    write_page(path, page("How Kingdom Circuit Verifies CHH Shows | The Kingdom Circuit", "Learn how The Kingdom Circuit verifies Christian hip-hop concerts, festivals, artists, sources, and event details.", path, body, schemas=[breadcrumb_schema(crumbs)], production_index=True))
    return path


def patch_core_page(path: pathlib.Path, title: str, desc: str, h1_from=None, h1_to=None):
    if not path.exists():
        return
    text = path.read_text(encoding="utf-8")
    text = re.sub(r"<title>.*?</title>", f"<title>{esc(title)}</title>", text, flags=re.S)
    if re.search(r'<meta name="description" content="[^"]*">', text):
        text = re.sub(r'<meta name="description" content="[^"]*">', f'<meta name="description" content="{esc(desc)}">', text)
    if h1_from and h1_to:
        text = text.replace(h1_from, h1_to)
    path.write_text(text, encoding="utf-8")


def patch_core_pages():
    patch_core_page(OUT / "artists/index.html", "Christian Hip-Hop Artists & Christian Rappers | The Kingdom Circuit", "Browse Christian hip-hop artists and Christian rappers tracked by The Kingdom Circuit, with verified upcoming concerts and official links.", "Christian Hip-Hop Artist Directory", "Christian Hip-Hop Artists & Christian Rappers")
    patch_core_page(OUT / "festivals/index.html", f"Christian Hip-Hop Festivals {YEAR} | The Kingdom Circuit", f"Discover verified U.S. Christian hip-hop and Christian rap festivals in {YEAR}, with artists, dates, locations, and official links.")
    patch_core_page(OUT / "shows/index.html", f"Christian Hip-Hop Shows & Concerts {YEAR} | The Kingdom Circuit", f"Browse verified Christian hip-hop concerts, Christian rap shows, tours, and festivals across the United States in {YEAR}.")
    shows = OUT / "shows/index.html"
    if shows.exists():
        text = shows.read_text(encoding="utf-8")
        if "kc-browse-links" not in text:
            year_link = local_path(f"shows/{YEAR}/")
            insert = f'<p class="kc-browse-links">Browse <a href="{year_link}">{YEAR}</a> · <a href="{local_path("shows/this-week/")}">this week</a> · <a href="{local_path("shows/this-weekend/")}">this weekend</a> · <a href="{local_path("shows/this-month/")}">this month</a></p>'
            marker = re.search(r'(</section>\s*<section class="calendar")', text)
            if marker:
                text = text[:marker.start()] + insert + text[marker.start():]
            shows.write_text(text, encoding="utf-8")
    for html_file in OUT.rglob("*.html"):
        text = html_file.read_text(encoding="utf-8", errors="ignore")
        if "seo-phase2.css" not in text:
            text = text.replace("</head>", f'<link rel="stylesheet" href="{local_path("seo-phase2.css")}"><script src="{local_path("seo-phase2.js")}" defer></script></head>')
        html_file.write_text(text, encoding="utf-8")


def patch_location_links_everywhere():
    pattern = re.compile(r'<div><dt>Location</dt><dd>([^<]+?),\s*([A-Z]{2})</dd></div>')
    for html_file in OUT.rglob("*.html"):
        text = html_file.read_text(encoding="utf-8", errors="ignore")
        def replace(match):
            raw_city = match.group(1).strip()
            code = match.group(2)
            city, _ = clean_city(raw_city)
            if not city or code not in STATE_NAMES:
                return match.group(0)
            return f'<div><dt>Location</dt><dd><a href="{city_path(city, code)}">{esc(city)}</a>, <a href="{state_path(code)}">{esc(code)}</a></dd></div>'
        updated = pattern.sub(replace, text)
        if updated != text:
            html_file.write_text(updated, encoding="utf-8")


def write_assets():
    css = r'''/* Kingdom Circuit SEO Phase 2: restrained additions. */
.kc-artist-overview{display:grid;grid-template-columns:minmax(220px,360px) 1fr;gap:32px;align-items:stretch;margin:0 auto 34px;max-width:1180px;padding:34px 24px 0}.kc-artist-image{min-height:340px;border:1px solid rgba(255,255,255,.12);border-radius:18px;overflow:hidden;background:#111;display:flex;align-items:center;justify-content:center;position:relative}.kc-artist-image img{width:100%;height:100%;object-fit:cover;min-height:340px}.kc-artist-image-empty{flex-direction:column;gap:8px;text-align:center;padding:24px}.kc-artist-image-empty span{font-size:2rem;font-weight:800}.kc-artist-image-empty small{opacity:.62}.kc-artist-copy{padding:10px 0}.kc-artist-copy h1{margin:.15em 0}.kc-artist-intro{max-width:760px;font-size:1.05rem;line-height:1.65}.kc-social-links{display:flex;flex-wrap:wrap;gap:10px;margin:20px 0}.kc-social-pill{border:1px solid rgba(208,179,120,.55);border-radius:999px;padding:9px 14px;text-decoration:none}.kc-social-pill:hover{border-color:currentColor}.kc-social-empty{opacity:.65;font-size:.92rem}.kc-artist-stats{display:flex;flex-wrap:wrap;gap:12px;margin:18px 0}.kc-artist-stats>div{border:1px solid rgba(255,255,255,.1);border-radius:12px;padding:12px 16px;min-width:120px}.kc-artist-stats strong,.kc-artist-stats span{display:block}.kc-artist-stats strong{font-size:1.1rem}.kc-artist-stats span{font-size:.78rem;opacity:.68;margin-top:4px}.kc-verification{font-size:.84rem;opacity:.68;max-width:720px}.kc-artist-tours{margin:14px 0;font-size:.93rem}.kc-artist-tours span{opacity:.7}.kc-artist-next,.kc-history{max-width:1180px;margin:0 auto 34px;padding:0 24px}.kc-next-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:14px}.kc-next-show{display:flex;flex-direction:column;gap:6px;border:1px solid rgba(255,255,255,.11);border-radius:14px;padding:16px;text-decoration:none;background:rgba(255,255,255,.025)}.kc-next-show:hover{border-color:rgba(208,179,120,.7)}.kc-next-date{font-size:.78rem;text-transform:uppercase;letter-spacing:.07em;opacity:.68}.kc-artist-calendar{max-width:1180px;margin-left:auto;margin-right:auto}.kc-history-list{display:grid;gap:10px}.kc-history-list>a{display:flex;justify-content:space-between;gap:18px;border-bottom:1px solid rgba(255,255,255,.08);padding:12px 0;text-decoration:none}.kc-history-list span{opacity:.68}.kc-past-notice{max-width:1180px;margin:16px auto;padding:14px 18px;border:1px solid rgba(208,179,120,.35);border-radius:12px;background:rgba(208,179,120,.07)}.kc-secondary-official{display:inline-block;margin:14px 0 0 14px}.kc-about-grid{max-width:1000px;margin:0 auto 60px;padding:0 24px;display:grid;grid-template-columns:1fr 1fr;gap:18px}.kc-about-grid article{border:1px solid rgba(255,255,255,.1);border-radius:16px;padding:22px}.kc-about-grid h2{margin-top:0}.kc-browse-links{max-width:1180px;margin:0 auto 24px;padding:0 24px;font-size:.92rem;opacity:.84}.kc-browse-links a{text-decoration:underline;text-underline-offset:3px}@media(max-width:760px){.kc-artist-overview{grid-template-columns:1fr;padding-top:22px;gap:20px}.kc-artist-image,.kc-artist-image img{min-height:300px}.kc-next-grid{grid-template-columns:1fr}.kc-about-grid{grid-template-columns:1fr}.kc-history-list>a{flex-direction:column;gap:4px}.kc-secondary-official{display:block;margin:12px 0 0}}'''
    js = r'''"use strict";(function(){const n=v=>String(v||"").trim().toLowerCase(),pd=v=>{if(!v)return null;const p=v.split("-").map(Number);return p.length>=3?new Date(p[0],p[1]-1,p[2],12):null},sod=v=>new Date(v.getFullYear(),v.getMonth(),v.getDate());function dm(a,b,m){if(!m||m==="all")return true;const t=sod(new Date()),s=pd(a),e=pd(b)||s;if(!s||!e)return false;if(m==="next30"){const l=new Date(t);l.setDate(l.getDate()+30);return e>=t&&s<=l}if(m==="month")return s.getFullYear()===t.getFullYear()&&s.getMonth()===t.getMonth();if(m==="weekend"){const f=new Date(t);f.setDate(f.getDate()+((5-t.getDay()+7)%7));const u=new Date(f);u.setDate(u.getDate()+2);return e>=f&&s<=u}return true}function fill(sel,vals,label=v=>v){if(!sel)return;const f=sel.querySelector("option");sel.innerHTML=f?f.outerHTML:"";vals.forEach(v=>sel.insertAdjacentHTML("beforeend",`<option value="${v}">${label(v)}</option>`))}document.querySelectorAll("[data-kc-filter-scope]").forEach(scope=>{const cards=[...scope.querySelectorAll("[data-event-card]")],form=scope.querySelector("[data-event-filters]");if(!form||!cards.length)return;const search=form.querySelector("[data-search-filter]"),artist=form.querySelector("[data-artist-filter]"),state=form.querySelector("[data-state-filter]"),type=form.querySelector("[data-type-filter]"),reset=form.querySelector("[data-reset-filters]"),count=scope.querySelector("[data-results-count]"),empty=scope.querySelector("[data-filtered-empty]"),chips=[...scope.querySelectorAll(".filter-chip")],SN={AL:"Alabama",AK:"Alaska",AZ:"Arizona",AR:"Arkansas",CA:"California",CO:"Colorado",CT:"Connecticut",DE:"Delaware",DC:"District of Columbia",FL:"Florida",GA:"Georgia",HI:"Hawaii",ID:"Idaho",IL:"Illinois",IN:"Indiana",IA:"Iowa",KS:"Kansas",KY:"Kentucky",LA:"Louisiana",ME:"Maine",MD:"Maryland",MA:"Massachusetts",MI:"Michigan",MN:"Minnesota",MS:"Mississippi",MO:"Missouri",MT:"Montana",NE:"Nebraska",NV:"Nevada",NH:"New Hampshire",NJ:"New Jersey",NM:"New Mexico",NY:"New York",NC:"North Carolina",ND:"North Dakota",OH:"Ohio",OK:"Oklahoma",OR:"Oregon",PA:"Pennsylvania",RI:"Rhode Island",SC:"South Carolina",SD:"South Dakota",TN:"Tennessee",TX:"Texas",UT:"Utah",VT:"Vermont",VA:"Virginia",WA:"Washington",WV:"West Virginia",WI:"Wisconsin",WY:"Wyoming"};fill(state,[...new Set(cards.map(c=>c.dataset.state).filter(Boolean))].sort(),v=>SN[v]||v);if(artist){const vals=new Set;cards.forEach(c=>(c.dataset.artists||"").split("|").filter(Boolean).forEach(v=>vals.add(v)));fill(artist,[...vals].sort())}let mode="all";function apply(){const needle=n(search?.value),av=n(artist?.value),sv=state?.value||"",tv=type?.value||"";let visible=0;cards.forEach(c=>{const names=(c.dataset.artists||"").split("|"),ok=(!needle||(c.dataset.search||"").includes(needle))&&(!av||names.includes(av))&&(!sv||c.dataset.state===sv)&&(!tv||c.dataset.type===tv)&&dm(c.dataset.date,c.dataset.endDate,mode);c.hidden=!ok;if(ok)visible++});if(count)count.textContent=`${visible} show${visible===1?"":"s"}`;if(empty)empty.hidden=visible!==0}[search,artist,state,type].forEach(x=>x?.addEventListener(x===search?"input":"change",apply));chips.forEach(ch=>ch.addEventListener("click",()=>{if(ch.dataset.typeMode){if(type)type.value=ch.dataset.typeMode;mode="all"}else{mode=ch.dataset.dateMode||"all";if(type)type.value=""}chips.forEach(x=>x.classList.remove("active"));ch.classList.add("active");apply()}));reset?.addEventListener("click",()=>{form.reset();mode="all";chips.forEach(x=>x.classList.toggle("active",x.dataset.dateMode==="all"));apply()});apply()})})();'''
    (OUT / "seo-phase2.css").write_text(css + "\n", encoding="utf-8")
    (OUT / "seo-phase2.js").write_text(js + "\n", encoding="utf-8")


def write_sitemap(urls: list[str], artist_urls: list[str]) -> int:
    artist_indexable = {artist_path(artist.get("name") or "") for artist in ARTISTS if artist.get("enabled") is not False and production_artist_indexable(artist, artist_events(artist.get("name") or "", UPCOMING))}
    filtered = []
    seen = set()
    for path in urls:
        if path in artist_urls and path not in artist_indexable:
            continue
        url = absolute(path)
        if url not in seen:
            seen.add(url)
            filtered.append(url)
    xml = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    xml += [f'  <url><loc>{esc(url)}</loc></url>' for url in filtered]
    xml.append('</urlset>')
    (OUT / "sitemap.xml").write_text("\n".join(xml) + "\n", encoding="utf-8")
    return len(filtered)


def validation(urls: list[str], metrics: dict):
    problems = []
    for event in ALL_EVENTS:
        city = str(event.get("city") or "")
        if re.match(r"^Sponsor\b", city, re.I) or "(" in city or ")" in city:
            problems.append(f"dirty city remained: {city}")
    sponsor_pages = list((OUT / "shows").glob("sponsor-*/index.html")) if (OUT / "shows").exists() else []
    if sponsor_pages:
        problems.append(f"sponsor city pages remained: {len(sponsor_pages)}")
    kb = OUT / "artists/kb/index.html"
    if kb.exists():
        text = kb.read_text(encoding="utf-8")
        for token in ("kc-artist-overview", "kc-social-links", "Next KB Shows", "data-kc-filter-scope", "data-state-filter"):
            if token not in text:
                problems.append(f"KB page missing {token}")
    else:
        problems.append("KB page missing")
    for rel in [f"shows/{YEAR}/index.html", "shows/this-week/index.html", "shows/this-weekend/index.html", "about/index.html"]:
        if not (OUT / rel).exists():
            problems.append(f"missing {rel}")
    for html_file in OUT.rglob("index.html"):
        text = html_file.read_text(encoding="utf-8", errors="ignore")
        if 'content="noindex,nofollow"' not in text:
            problems.append(f"test page missing noindex: {html_file.relative_to(OUT)}")
            if len(problems) > 20:
                break
    if len(set(urls)) != len(urls):
        problems.append("duplicate generated URL paths")
    report = {"generatedAt": dt.datetime.now(dt.timezone.utc).isoformat(), "phase": "seo-phase2-test", "currentEvents": len(UPCOMING), "archivedPastEvents": len(PAST), "artists": len([artist for artist in ARTISTS if artist.get("enabled") is not False]), "states": len({event.get("state") for event in UPCOMING if event.get("state")}), "cities": len({(event.get("city"), event.get("state")) for event in UPCOMING if event.get("city") and event.get("state")}), "tourPages": len(TOUR_GROUPS), **metrics, "problems": problems, "status": "pass" if not problems else "fail"}
    (OUT / "seo-phase2-manifest.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    if problems:
        raise SystemExit("SEO Phase 2 validation failed:\n- " + "\n- ".join(problems[:30]))
    return report


def main(write_archive=False):
    if not OUT.exists():
        raise SystemExit("_site does not exist; run the baseline SEO builder first.")
    write_assets()
    patch_core_pages()
    event_urls = generate_event_pages()
    artist_urls, metrics = generate_artist_pages()
    location_urls = generate_location_and_time_pages()
    tour_urls = generate_tour_pages()
    about_url = generate_about_page()
    patch_location_links_everywhere()
    core = [BASE_PATH, local_path("shows/"), local_path("shows/this-month/"), local_path("festivals/"), local_path("new-shows/"), local_path("artists/"), local_path("submit/"), about_url]
    urls = core + event_urls + artist_urls + location_urls + tour_urls
    metrics["productionSitemapUrls"] = write_sitemap(urls, artist_urls)
    report = validation(urls, metrics)
    if write_archive:
        (REPO / "event-archive.json").write_text(json.dumps(ALL_EVENTS, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--write-archive", action="store_true")
    args = parser.parse_args()
    main(write_archive=args.write_archive)
