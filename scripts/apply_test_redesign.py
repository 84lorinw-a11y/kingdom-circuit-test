#!/usr/bin/env python3
"""Apply the mobile-first Kingdom Circuit redesign to a captured test artifact.

The test deployment is rebuilt from the published production site every day.  This
overlay intentionally changes presentation and test-only submission UX after the
live artifact has passed its exact-mirror checks.
"""

from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import pathlib
import re
import shutil
import sys
from typing import Iterable
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit
from zoneinfo import ZoneInfo


TEST_BASE = "/kingdom-circuit-test/"
INSTAGRAM_URL = "https://www.instagram.com/thekingdomcircuit/"
FORM_ENDPOINT = "https://formspree.io/f/mljreawj"
VERSION = "mobile-first-test-redesign-v1"
DEPLOYMENT_ENVIRONMENT = "test"
GENERATED_PAGE_TITLE_SUFFIX = "Kingdom Circuit Test"
UPCOMING_PAGE_ROBOTS = "noindex,nofollow"
PAST_PAGE_ROBOTS = "noindex,nofollow"
MANIFEST_FILENAME = "test-redesign-manifest.json"
FAVICON_ASSET_NAMES = (
    "favicon-kc-stacked-v1-48.png",
    "favicon-kc-stacked-v1-96.png",
    "favicon-kc-stacked-v1-180.png",
    "favicon-kc-stacked-v1-192.png",
    "favicon-kc-stacked-v1-512.png",
    "favicon-kc-stacked-v1-maskable-512.png",
)
SITE_TIMEZONE = ZoneInfo("America/Los_Angeles")
NEW_WINDOW_DAYS = 7
PAST_GRACE_DAYS = 0
INACTIVE_STATUSES = {"cancelled", "canceled", "postponed", "merged"}
TRUSTED_AUTHORITIES = {
    "artist_calendar",
    "artist_label",
    "festival",
    "official",
    "official_site",
    "primary",
    "promoter",
    "ticketing",
    "venue",
    "venue_ticket",
}
PLACEHOLDER_VENUES = {
    "",
    "tba",
    "venue tba",
    "venue not provided",
    "venue to be announced",
}
STATE_NAMES = {
    "CA": "California",
    "IL": "Illinois",
    "IN": "Indiana",
    "MO": "Missouri",
    "OH": "Ohio",
}
EVENT_CARD_PATTERN = re.compile(
    r'<article\b(?=[^>]*\bdata-event-card\b)[^>]*>.*?</article>',
    re.I | re.S,
)
ARTIST_CARD_PATTERN = re.compile(
    r'<article\b(?=[^>]*\bdata-artist-card\b)[^>]*>.*?</article>',
    re.I | re.S,
)
PAST_SHOW_ROW_PATTERN = re.compile(
    r'<article\b(?=[^>]*\bpast-show-row\b)[^>]*>.*?</article>',
    re.I | re.S,
)


def configure_environment(production: bool) -> None:
    global TEST_BASE
    global VERSION
    global DEPLOYMENT_ENVIRONMENT
    global GENERATED_PAGE_TITLE_SUFFIX
    global UPCOMING_PAGE_ROBOTS
    global PAST_PAGE_ROBOTS
    global MANIFEST_FILENAME
    if production:
        TEST_BASE = "/"
        VERSION = "mobile-first-live-redesign-v1"
        DEPLOYMENT_ENVIRONMENT = "production"
        GENERATED_PAGE_TITLE_SUFFIX = "Kingdom Circuit"
        UPCOMING_PAGE_ROBOTS = "index,follow"
        PAST_PAGE_ROBOTS = "noindex,follow"
        MANIFEST_FILENAME = "assets/live-redesign-manifest.json"
    else:
        TEST_BASE = "/kingdom-circuit-test/"
        VERSION = "mobile-first-test-redesign-v1"
        DEPLOYMENT_ENVIRONMENT = "test"
        GENERATED_PAGE_TITLE_SUFFIX = "Kingdom Circuit Test"
        UPCOMING_PAGE_ROBOTS = "noindex,nofollow"
        PAST_PAGE_ROBOTS = "noindex,nofollow"
        MANIFEST_FILENAME = "test-redesign-manifest.json"


def clean_text(value: str) -> str:
    value = re.sub(r"<[^>]+>", " ", value)
    return " ".join(html.unescape(value).split())


def normalized_key(value: object) -> str:
    return " ".join(str(value or "").casefold().split())


def semantic_key(value: object) -> str:
    return " ".join(re.sub(r"[^a-z0-9]+", " ", str(value or "").casefold()).split())


def slug(value: object) -> str:
    text = str(value or "").strip().casefold().replace("&", " and ")
    return re.sub(r"[^a-z0-9]+", "-", text).strip("-") or "item"


def fnv(value: object) -> str:
    result = 0x811C9DC5
    for byte in str(value or "").encode():
        result ^= byte
        result = (result * 0x01000193) & 0xFFFFFFFF
    return f"{result:08x}"[:6]


def parse_iso_date(value: object) -> dt.date | None:
    try:
        return dt.date.fromisoformat(str(value or "")[:10])
    except ValueError:
        return None


def site_today() -> dt.date:
    return dt.datetime.now(SITE_TIMEZONE).date()


def visibility_cutoff(today: dt.date) -> dt.date:
    """Keep shows active through their final date, then archive them next day."""
    return today - dt.timedelta(days=PAST_GRACE_DAYS)


def is_active_event(event: dict[str, object], cutoff: dt.date) -> bool:
    status = normalized_key(event.get("status"))
    if status in INACTIVE_STATUSES:
        return False
    last_date = parse_iso_date(event.get("endDate") or event.get("startDate"))
    return last_date is None or last_date >= cutoff


def event_source_key(event: dict[str, object]) -> tuple[str, str, str]:
    return (
        normalized_key(event.get("title")),
        str(event.get("startDate") or "")[:10],
        normalized_key(event.get("city")),
    )


def recent_event_keys(
    source_events: Iterable[dict[str, object]],
    today: dt.date,
    days: int = NEW_WINDOW_DAYS,
) -> set[tuple[str, str, str]]:
    keys: set[tuple[str, str, str]] = set()
    for event in source_events:
        if normalized_key(event.get("status")) in INACTIVE_STATUSES:
            continue
        raw_seen = str(event.get("firstSeen") or "").strip()
        if not raw_seen:
            continue
        try:
            seen = dt.datetime.fromisoformat(raw_seen.replace("Z", "+00:00"))
        except ValueError:
            continue
        if seen.tzinfo is None:
            seen = seen.replace(tzinfo=dt.timezone.utc)
        age = (today - seen.astimezone(SITE_TIMEZONE).date()).days
        if 0 <= age < days:
            keys.add(event_source_key(event))
    return keys


def attribute(fragment: str, name: str) -> str:
    match = re.search(rf"\b{re.escape(name)}=(?:\"([^\"]*)\"|'([^']*)')", fragment)
    if not match:
        return ""
    return html.unescape(match.group(1) if match.group(1) is not None else match.group(2))


def event_cards(document: str) -> list[str]:
    return EVENT_CARD_PATTERN.findall(document)


def card_source_key(card: str) -> tuple[str, str, str]:
    opening = card[: card.find(">") + 1]
    title_match = re.search(r'<h3>\s*<a\b[^>]*>(.*?)</a>', card, re.I | re.S)
    title = clean_text(title_match.group(1)) if title_match else ""
    location_match = re.search(
        r'<dt>\s*Location\s*</dt>\s*<dd>(.*?)</dd>',
        card,
        re.I | re.S,
    )
    location = clean_text(location_match.group(1)) if location_match else ""
    city = location.rsplit(",", 1)[0].strip() if "," in location else location
    return (
        normalized_key(title),
        attribute(opening, "data-date")[:10],
        normalized_key(city),
    )


def prune_expired_event_cards(document: str, cutoff: dt.date) -> str:
    def keep_or_remove(match: re.Match[str]) -> str:
        card = match.group(0)
        opening = card[: card.find(">") + 1]
        last_date = parse_iso_date(
            attribute(opening, "data-end-date") or attribute(opening, "data-date")
        )
        return "" if last_date is not None and last_date < cutoff else card

    return EVENT_CARD_PATTERN.sub(keep_or_remove, document)


def card_last_date(card: str) -> dt.date | None:
    opening = card[: card.find(">") + 1]
    return parse_iso_date(
        attribute(opening, "data-end-date") or attribute(opening, "data-date")
    )


def expired_event_cards(document: str, cutoff: dt.date) -> list[str]:
    return [
        card
        for card in event_cards(document)
        if (last_date := card_last_date(card)) is not None and last_date < cutoff
    ]


def update_results_count(document: str) -> str:
    count = len(event_cards(document))
    return re.sub(
        r'(<[^>]+\bdata-results-count\b[^>]*>).*?(</[^>]+>)',
        rf"\g<1>{count} show{'s' if count != 1 else ''}\g<2>",
        document,
        flags=re.I | re.S,
    )


def transform_new_shows(
    document: str,
    recent_keys: set[tuple[str, str, str]],
) -> str:
    document = EVENT_CARD_PATTERN.sub(
        lambda match: match.group(0) if card_source_key(match.group(0)) in recent_keys else "",
        document,
    )
    document = re.sub(r"\b14 days\b", "7 days", document, flags=re.I)
    return update_results_count(document)


def transform_this_month(document: str) -> str:
    cards = event_cards(document)
    states: set[str] = set()
    artists: set[str] = set()
    for card in cards:
        opening = card[: card.find(">") + 1]
        state = attribute(opening, "data-state").strip().upper()
        if state:
            states.add(state)
        for artist in attribute(opening, "data-artists").split("|"):
            artist_key = normalized_key(artist)
            if artist_key:
                artists.add(artist_key)

    def replace_stat(name: str, value: int, source: str) -> str:
        return re.sub(
            rf'(<strong\b[^>]*\bdata-month-{name}-count\b[^>]*>).*?(</strong>)',
            rf"\g<1>{value}\g<2>",
            source,
            count=1,
            flags=re.I | re.S,
        )

    document = replace_stat("show", len(cards), document)
    document = replace_stat("state", len(states), document)
    document = re.sub(
        r'<div>\s*<strong\b[^>]*\bdata-month-festival-count\b[^>]*>.*?</strong>\s*<span>\s*Festivals\s*</span>\s*</div>',
        f'<div><strong data-month-artist-count>{len(artists)}</strong><span>Artists</span></div>',
        document,
        count=1,
        flags=re.I | re.S,
    )
    document = re.sub(
        r'\s*<p class="section-intro">\s*Browse (?:the|the complete) month chronologically, or filter by artist, state, or event type\.\s*</p>',
        "",
        document,
        count=1,
        flags=re.I | re.S,
    )
    return update_results_count(document)


def filter_public_event_data(site: pathlib.Path, cutoff: dt.date) -> int:
    removed = 0
    for filename in ("events.json", "supplemental-events.json"):
        path = site / filename
        if not path.is_file():
            continue
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, list):
            continue
        kept = [event for event in payload if not isinstance(event, dict) or is_active_event(event, cutoff)]
        removed += len(payload) - len(kept)
        path.write_text(json.dumps(kept, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return removed


def patch_runtime(site: pathlib.Path) -> None:
    path = site / "app.js"
    if not path.is_file():
        return
    source = path.read_text(encoding="utf-8")
    source = source.replace(
        "cutoff.setDate(cutoff.getDate() - 14);",
        f"cutoff.setDate(cutoff.getDate() - {NEW_WINDOW_DAYS});",
    )
    source = source.replace(
        'document.querySelector("[data-month-festival-count]")?.replaceChildren(String(list.filter(event => event.eventType === "festival").length));',
        'document.querySelector("[data-month-artist-count]")?.replaceChildren(String(new Set(list.flatMap(event => event.artists || []).map(normalize).filter(Boolean)).size));',
    )
    source = source.replace(
        'async function boot() {\n  const staticCards = [...document.querySelectorAll("[data-event-card]")];',
        ('''function kcStaticVisibilityCutoff() {
  const parts = Object.fromEntries(new Intl.DateTimeFormat("en-US", { timeZone: "America/Los_Angeles", year: "numeric", month: "2-digit", day: "2-digit" }).formatToParts(new Date()).filter(part => part.type !== "literal").map(part => [part.type, Number(part.value)]));
  const cutoff = new Date(Date.UTC(parts.year, parts.month - 1, parts.day));
  cutoff.setUTCDate(cutoff.getUTCDate() - __KC_PAST_GRACE_DAYS__);
  return cutoff;
}
function kcStaticCardIsActive(card) {
  const value = card?.dataset?.endDate || card?.dataset?.date || "";
  const match = /^(\\d{4})-(\\d{2})-(\\d{2})$/.exec(value);
  if (!match) return true;
  return new Date(Date.UTC(Number(match[1]), Number(match[2]) - 1, Number(match[3]))) >= kcStaticVisibilityCutoff();
}
async function boot() {
  const allStaticCards = [...document.querySelectorAll("[data-event-card]")];
  const staticCards = allStaticCards.filter(kcStaticCardIsActive);
  allStaticCards.filter(card => !kcStaticCardIsActive(card)).forEach(card => card.remove());'''
        ).replace("__KC_PAST_GRACE_DAYS__", str(PAST_GRACE_DAYS)),
    )
    path.write_text(source, encoding="utf-8")


def instagram_icon(icon_class: str = "kc-rd-instagram-icon", token: str = "icon") -> str:
    return f'''<svg class="{icon_class}" viewBox="0 0 24 24" aria-hidden="true" focusable="false">
  <defs>
    <radialGradient id="kc-rd-instagram-{token}-glow" cx="30%" cy="100%" r="105%">
      <stop offset="0" stop-color="#feda75"/><stop offset=".3" stop-color="#fa7e1e"/>
      <stop offset=".61" stop-color="#e1306c"/><stop offset=".82" stop-color="#c13584"/>
      <stop offset="1" stop-color="#833ab4"/>
    </radialGradient>
    <linearGradient id="kc-rd-instagram-{token}-sky" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#405de6"/><stop offset=".42" stop-color="#5851db" stop-opacity=".8"/>
      <stop offset="1" stop-color="#833ab4" stop-opacity="0"/>
    </linearGradient>
  </defs>
  <rect x="1" y="1" width="22" height="22" rx="6.4" fill="url(#kc-rd-instagram-{token}-glow)"/>
  <rect x="1" y="1" width="22" height="22" rx="6.4" fill="url(#kc-rd-instagram-{token}-sky)"/>
  <rect x="6.1" y="6.1" width="11.8" height="11.8" rx="3.7" fill="none" stroke="#fff" stroke-width="1.85"/>
  <circle cx="12" cy="12" r="3" fill="none" stroke="#fff" stroke-width="1.85"/>
  <circle cx="17.25" cy="6.85" r="1.15" fill="#fff"/>
</svg>'''


def active_section(relative: pathlib.PurePath) -> str:
    parts = relative.parts
    if relative.as_posix() == "index.html":
        return "home"
    if parts and parts[0] == "artists":
        return "artists"
    if parts and parts[0] == "festivals":
        return "festivals"
    if parts and parts[0] == "new-shows":
        return "new"
    if parts[:2] == ("shows", "this-month"):
        return "month"
    if parts and parts[0] in {"shows", "event", "state", "city"}:
        return "shows"
    return ""


def navigation(relative: pathlib.PurePath) -> str:
    active = active_section(relative)
    items = (
        ("home", "Home", TEST_BASE),
        ("shows", "All Shows", f"{TEST_BASE}shows/"),
        ("month", "This Month", f"{TEST_BASE}shows/this-month/"),
        ("festivals", "Festivals", f"{TEST_BASE}festivals/"),
        ("new", "New Shows", f"{TEST_BASE}new-shows/"),
        ("artists", "Artists", f"{TEST_BASE}artists/"),
    )
    links = []
    for key, label, href in items:
        current = ' aria-current="page"' if key == active else ""
        links.append(f'<a href="{href}"{current}>{label}</a>')
    return "".join(links)


def follow_bar(token: str) -> str:
    return f'''<div class="kc-rd-followbar">
    <a class="kc-rd-follow-link" href="{INSTAGRAM_URL}" target="_blank" rel="noopener" aria-label="Follow The Kingdom Circuit on Instagram (opens in new tab)">
      {instagram_icon(token=token)}<span>Follow @thekingdomcircuit</span>
    </a>
    <span class="kc-rd-follow-tagline">Christian hip-hop, live and connected</span>
  </div>'''


def full_header(relative: pathlib.PurePath) -> str:
    button_icon = instagram_icon(token="button")
    return f'''<header class="kc-rd-header">
  {follow_bar("follow")}
  <div class="kc-rd-primary">
    <a class="kc-rd-brand" href="{TEST_BASE}" aria-label="Kingdom Circuit home">
      <img src="{TEST_BASE}assets/logo-wordmark.svg?v=1" alt="Kingdom Circuit">
    </a>
    <div class="kc-rd-actions">
      <a class="kc-rd-submit" href="{TEST_BASE}submit/">Submit a Show</a>
      <a class="kc-rd-instagram-button" href="{INSTAGRAM_URL}" target="_blank" rel="noopener" aria-label="Instagram (opens in new tab)">{button_icon}</a>
    </div>
  </div>
  <nav class="kc-rd-nav" aria-label="Primary navigation">{navigation(relative)}</nav>
</header>'''


def profile_header() -> str:
    return f'''<header class="kc-rd-header kc-rd-header--profile">
  {follow_bar("profile-follow")}
  <div class="kc-rd-primary">
    <a class="kc-rd-brand" href="{TEST_BASE}" aria-label="Kingdom Circuit home">
      <img src="{TEST_BASE}assets/logo-wordmark.svg?v=1" alt="Kingdom Circuit">
    </a>
  </div>
</header>'''


def replace_legacy_header(document: str, header: str) -> str:
    if "kc-rd-header" in document:
        return document
    pattern = re.compile(r'<header\b[^>]*class="[^"]*\bsite-header\b[^"]*"[^>]*>.*?</header>', re.S)
    document, count = pattern.subn(header, document, count=1)
    if count != 1:
        raise ValueError("legacy site header was not found")
    document = re.sub(
        r'<div\b[^>]*class="[^"]*\bmenu-backdrop\b[^"]*"[^>]*>.*?</div>\s*',
        "",
        document,
        count=1,
        flags=re.S,
    )
    document = re.sub(
        r'<nav\b[^>]*class="[^"]*\bmenu-drawer\b[^"]*"[^>]*>.*?</nav>\s*',
        "",
        document,
        count=1,
        flags=re.S,
    )
    return document


def inject_assets(document: str) -> str:
    css = f'{TEST_BASE}assets/kc-redesign-v1.css?v=6'
    js = f'{TEST_BASE}assets/kc-redesign-v1.js?v=2'
    if DEPLOYMENT_ENVIRONMENT == "test":
        document = re.sub(
            r'''\s*<link\b[^>]*\brel=["'](?:shortcut icon|icon|apple-touch-icon|manifest)["'][^>]*>''',
            "",
            document,
            flags=re.I,
        )
        document = re.sub(
            r'''\s*<meta\b[^>]*\bname=["']apple-mobile-web-app-title["'][^>]*>''',
            "",
            document,
            flags=re.I,
        )
        favicon_markup = f'''  <link rel="icon" type="image/png" sizes="48x48" href="{TEST_BASE}assets/favicon-kc-stacked-v1-48.png">
  <link rel="icon" type="image/png" sizes="96x96" href="{TEST_BASE}assets/favicon-kc-stacked-v1-96.png">
  <link rel="apple-touch-icon" sizes="180x180" href="{TEST_BASE}assets/favicon-kc-stacked-v1-180.png">
  <link rel="manifest" href="{TEST_BASE}manifest.webmanifest">
  <meta name="apple-mobile-web-app-title" content="Kingdom Circuit">'''
        document = document.replace("</head>", f"{favicon_markup}\n</head>", 1)
    if css not in document:
        document = document.replace(
            "</head>",
            f'  <link rel="stylesheet" href="{css}">\n</head>',
            1,
        )
    if js not in document:
        document = document.replace(
            "</body>",
            f'  <script src="{js}" defer></script>\n</body>',
            1,
        )
    return document


def transform_home(document: str, show_count: int, artist_count: int) -> str:
    if (
        "kc-rd-home-title" in document
        and 'data-kc-rd-stat="shows"' in document
        and 'data-kc-rd-stat="artists"' in document
    ):
        return document
    match = re.search(r'<section class="page-hero home-hero">.*?</section>', document, re.S)
    if not match:
        raise ValueError("home hero was not found")
    hero = match.group(0)
    hero = hero.replace(
        'class="page-hero home-hero"',
        'class="page-hero home-hero kc-rd-home kc-rd-home-hero"',
        1,
    )
    hero, heading_count = re.subn(
        r"<h1>.*?</h1>",
        '<h1 class="kc-rd-home-title"><span>Find Christian</span><span>Hip Hop Shows</span><span>Near You!</span></h1>',
        hero,
        count=1,
        flags=re.S,
    )
    if heading_count != 1:
        raise ValueError("home heading was not found")
    stats = f'''<div class="kc-rd-home-stats" aria-label="Kingdom Circuit coverage">
    <a class="kc-rd-stat" href="#calendar" data-kc-rd-stat="shows"><strong class="kc-rd-stat-number">{show_count}</strong><span class="kc-rd-stat-label">Shows Listed</span></a>
    <a class="kc-rd-stat" href="{TEST_BASE}artists/" data-kc-rd-stat="artists"><strong class="kc-rd-stat-number">{artist_count}</strong><span class="kc-rd-stat-label">Artists Tracked</span></a>
  </div>'''
    hero, mission_count = re.subn(
        r'(<p class="mission-statement">.*?</p>)',
        rf"\1\n  {stats}",
        hero,
        count=1,
        flags=re.S,
    )
    if mission_count != 1:
        raise ValueError("home mission statement was not found")
    hero = re.sub(r'\s*<p class="trust-line">.*?</p>', "", hero, count=1, flags=re.S)
    hero = re.sub(r'\s*<div class="home-paths".*?</div>', "", hero, count=1, flags=re.S)
    hero = re.sub(r'\s*<p class="hero-text">.*?</p>', "", hero, count=1, flags=re.S)
    document = document[: match.start()] + hero + document[match.end() :]
    document = re.sub(
        r'<p class="eyebrow">\s*Verified listings\s*</p>\s*',
        "",
        document,
        count=1,
        flags=re.I | re.S,
    )
    return document


def transform_directory(
    document: str,
    artist_count: int,
    profile_events: dict[str, list[dict[str, str]]],
) -> str:
    if "kc-rd-directory-intro" in document and "kc-rd-directory" in document:
        return document
    document, removed = re.subn(
        r'\s*<section class="page-hero hero-compact seo-directory-hero">.*?</section>',
        "",
        document,
        count=1,
        flags=re.S,
    )
    if removed != 1:
        raise ValueError("artist directory hero was not found")
    intro = f'''<section class="kc-rd-directory-intro" aria-labelledby="kc-rd-directory-title">
  <div class="kc-rd-directory-summary">
    <h1 id="kc-rd-directory-title" class="sr-only">Christian Hip-Hop Artists</h1>
    <span class="kc-rd-directory-eyebrow">Artist Directory</span>
    <p class="kc-rd-directory-count"><strong>{artist_count}</strong><span><b>CHH Artists</b><small>Tracked &amp; growing</small></span></p>
  </div>
  <div class="kc-rd-directory-actions">
    <a class="kc-rd-button" href="{TEST_BASE}submit/">Submit a Show</a>
    <a class="kc-rd-button kc-rd-button--secondary" href="{TEST_BASE}submit/artist/">Submit a CHH Artist to Be Listed</a>
  </div>
</section>'''
    marker = '<section class="directory-section" data-artist-directory'
    if marker not in document:
        raise ValueError("artist directory section was not found")
    document = document.replace(marker, intro + '\n<section class="directory-section kc-rd-directory" data-artist-directory', 1)

    def remove_card_time(match: re.Match[str]) -> str:
        return re.sub(
            r'\s+-\s+\d{1,2}:\d{2}\s*(?:AM|PM)(?=\s*(?:·|&middot;|&#183;))',
            "",
            match.group(0),
            flags=re.I,
        )

    document = re.sub(
        r'<p\b[^>]*class="[^"]*\bseo-card-next\b[^"]*"[^>]*>.*?</p>',
        remove_card_time,
        document,
        flags=re.S,
    )

    def refresh_artist_card(match: re.Match[str]) -> str:
        card = match.group(0)
        href_match = re.search(r'href="[^"]*/artists/([^/]+)/"', card, re.I)
        if not href_match:
            return card
        events = profile_events.get(href_match.group(1), [])
        opening_end = card.find(">") + 1
        opening = card[:opening_end]
        opening = re.sub(
            r'\bdata-has-shows="[^"]*"',
            f'data-has-shows="{str(bool(events)).lower()}"',
            opening,
            count=1,
        )
        card = opening + card[opening_end:]
        card = re.sub(
            r'<p>\s*\d+\s+upcoming\s+shows?\s*</p>',
            f'<p>{len(events)} upcoming show{"s" if len(events) != 1 else ""}</p>',
            card,
            count=1,
            flags=re.I | re.S,
        )
        card = re.sub(
            r'\s*<p\b[^>]*class="[^"]*\bseo-card-next\b[^"]*"[^>]*>.*?</p>',
            "",
            card,
            count=1,
            flags=re.I | re.S,
        )
        card = re.sub(
            r'\s*<p\b[^>]*class="[^"]*\bseo-card-states\b[^"]*"[^>]*>.*?</p>',
            "",
            card,
            count=1,
            flags=re.I | re.S,
        )
        if not events:
            return card
        first = events[0]
        date_only = first["date"].split(" - ", 1)[0]
        states = list(dict.fromkeys(event["state"] for event in events if event["state"]))
        details = (
            f'<p class="seo-card-next"><strong>Next:</strong> {html.escape(date_only)} · '
            f'{html.escape(first["location"])}</p>'
        )
        if states:
            details += (
                f'<p class="seo-card-states"><strong>Upcoming:</strong> '
                f'{html.escape(", ".join(states))}</p>'
            )
        marker = re.search(r'(<div\b[^>]*class="[^"]*\bseo-card-socials\b)', card, re.I)
        if marker:
            card = card[: marker.start()] + details + card[marker.start() :]
        return card

    document = ARTIST_CARD_PATTERN.sub(refresh_artist_card, document)
    return document


def event_metadata(card: str) -> dict[str, str]:
    opening = card[: card.find(">") + 1]
    date_iso = attribute(opening, "data-date")
    title_match = re.search(
        r'<h3>\s*<a\b[^>]*href="([^"]+)"[^>]*>(.*?)</a>\s*</h3>',
        card,
        re.I | re.S,
    )
    href_match = title_match
    if not href_match:
        href_match = re.search(r'<a\b[^>]*href="([^"]+)"', card, re.S)
    artist_match = re.search(
        r'<p\b[^>]*class="[^"]*\bartist-line\b[^"]*"[^>]*>(.*?)</p>',
        card,
        re.I | re.S,
    )
    values: dict[str, str] = {}
    for label, value in re.findall(r'<div>\s*<dt>(.*?)</dt>\s*<dd>(.*?)</dd>\s*</div>', card, re.S):
        values[clean_text(label).lower()] = clean_text(value)
    date_text = values.get("date", "")
    time = date_text.split(" - ", 1)[1] if " - " in date_text else ""
    if date_iso:
        try:
            parsed = dt.date.fromisoformat(date_iso)
            month = parsed.strftime("%b").upper()
            day = str(parsed.day)
        except ValueError:
            month, day = "", ""
    else:
        month, day = "", ""
    return {
        "href": html.unescape(href_match.group(1)) if href_match else TEST_BASE,
        "title": clean_text(title_match.group(2)) if title_match else "Past show",
        "date": date_text,
        "start_date": date_iso[:10],
        "month": month,
        "day": day,
        "venue": values.get("venue", "Venue to be announced"),
        "location": values.get("location", "Location to be announced"),
        "time": time,
        "state": attribute(opening, "data-state").strip().upper(),
        "end_date": attribute(opening, "data-end-date") or date_iso,
        "artist_markup": artist_match.group(1).strip() if artist_match else "",
    }


def past_date_label(value: str) -> str:
    parsed = parse_iso_date(value)
    if parsed is None:
        return value or "Past date"
    return f"{parsed.strftime('%b')} {parsed.day}, {parsed.year}"


def past_show_row(card: str) -> str:
    event = event_metadata(card)
    href = html.escape(event["href"], quote=True)
    title = html.escape(event["title"])
    artist_markup = re.sub(
        r"</a>\s*(?:-|&middot;|&#183;|·)\s*<a",
        "</a> · <a",
        event["artist_markup"],
        flags=re.I,
    )
    details = [
        artist_markup,
        html.escape(event["venue"]),
        html.escape(event["location"]),
    ]
    details_html = " · ".join(part for part in details if part)
    return (
        '<article class="past-show-row">'
        f'<div class="past-show-date">{html.escape(past_date_label(event["start_date"]))}</div>'
        '<div class="past-show-copy">'
        f'<h3><a href="{href}">{title}</a></h3>'
        f"<p>{details_html}</p>"
        "</div></article>"
    )


def past_row_href(row: str) -> str:
    match = re.search(
        r'<h3>\s*<a\b[^>]*href="([^"]+)"',
        row,
        re.I | re.S,
    )
    return html.unescape(match.group(1)).strip() if match else ""


def past_archive_section(rows: list[str]) -> str:
    count = len(rows)
    noun = "show" if count == 1 else "shows"
    return (
        '<section class="past-shows-archive" data-past-shows-archive>'
        '<details><summary><span>Past shows</span>'
        f'<span class="past-count">{count} archived {noun}</span></summary>'
        f'<div class="past-show-list">{"".join(rows)}</div>'
        '<p class="past-archive-note">Past listings are preserved for concert history. '
        "Upcoming shows remain at the top of this page.</p></details></section>"
    )


def archive_expired_profile_cards(
    document: str,
    cutoff: dt.date,
) -> tuple[str, int]:
    """Move newly expired profile cards into the existing Past Shows archive."""
    expired = sorted(
        expired_event_cards(document, cutoff),
        key=lambda card: event_metadata(card)["start_date"],
        reverse=True,
    )
    if not expired:
        return document, 0

    section_match = re.search(
        r'<section\b(?=[^>]*\bdata-past-shows-archive\b)[^>]*>.*?</section>',
        document,
        re.I | re.S,
    )
    existing_rows = (
        PAST_SHOW_ROW_PATTERN.findall(section_match.group(0)) if section_match else []
    )
    existing_hrefs = {past_row_href(row) for row in existing_rows if past_row_href(row)}
    added_rows: list[str] = []
    for card in expired:
        row = past_show_row(card)
        href = past_row_href(row)
        if href and href in existing_hrefs:
            continue
        if href:
            existing_hrefs.add(href)
        added_rows.append(row)

    if not added_rows:
        return document, 0

    rows = added_rows + existing_rows
    section = past_archive_section(rows)
    if section_match:
        if "kc-rd-past-shows" in section_match.group(0):
            section = section.replace(
                'class="past-shows-archive"',
                'class="past-shows-archive kc-rd-past kc-rd-past-shows"',
                1,
            )
        document = document[: section_match.start()] + section + document[section_match.end() :]
    elif "</main>" in document:
        document = document.replace("</main>", section + "\n</main>", 1)
    else:
        raise ValueError("artist profile main element was not found for Past Shows archive")
    return document, len(added_rows)


def show_row(event: dict[str, str]) -> str:
    href = html.escape(event["href"], quote=True)
    location = html.escape(event["location"])
    venue = html.escape(event["venue"])
    date_label = html.escape(event["date"])
    return f'''<a class="kc-rd-show-row" href="{href}" aria-label="{date_label}, {location}, {venue}">
  <span class="kc-rd-show-date"><span>{event['month']}</span><strong>{event['day']}</strong></span>
  <span class="kc-rd-show-place"><strong>{location}</strong><span class="kc-rd-show-venue">{venue}</span></span>
  <span class="kc-rd-chevron" aria-hidden="true">›</span>
</a>'''


def extract_socials(profile: str) -> tuple[str, str]:
    match = re.search(r'<div class="seo-social-links"[^>]*>(.*?)</div>', profile, re.S)
    if not match:
        return "", ""
    social_anchors: list[str] = []
    website = ""
    for anchor in re.findall(r'<a\b.*?</a>', match.group(1), re.S):
        label = attribute(anchor[: anchor.find(">") + 1], "aria-label")
        href = attribute(anchor[: anchor.find(">") + 1], "href")
        if label.lower().startswith("website for"):
            website = href
            continue
        anchor = re.sub(r'<span>.*?</span>', "", anchor, flags=re.S)
        anchor = anchor.replace('class="seo-social-link"', 'class="seo-social-link kc-rd-social-link"', 1)
        social_anchors.append(anchor)
    return "".join(social_anchors), website


def profile_visual_shape(image_html: str) -> str:
    if "<img" not in image_html:
        return "placeholder"
    opening = image_html[: image_html.find(">") + 1]
    try:
        width = float(attribute(opening, "width"))
        height = float(attribute(opening, "height"))
        ratio = width / height
    except (TypeError, ValueError, ZeroDivisionError):
        return "portrait"
    if ratio < 0.95:
        return "portrait"
    if ratio < 1.25:
        return "square"
    if ratio < 1.65:
        return "landscape"
    return "wide"


def transform_artist_profile(document: str) -> tuple[str, int, bool]:
    main_match = re.search(r'<main\b[^>]*>.*?</main>', document, re.S)
    if not main_match:
        raise ValueError("artist profile main element was not found")
    old_main = main_match.group(0)
    name_match = re.search(r'<h1>(.*?)\s+Concerts(?:\s*&amp;|\s+&)\s*Tour Dates</h1>', old_main, re.S)
    if not name_match:
        raise ValueError("artist profile name was not found")
    artist_name = clean_text(name_match.group(1))

    image_match = re.search(r'<div class="seo-profile-image">\s*(.*?)\s*</div>', old_main, re.S)
    image_html = image_match.group(1) if image_match else ""
    visual_shape = profile_visual_shape(image_html)
    if "<img" in image_html:
        image_html = re.sub(
            r'class="([^"]*)"',
            lambda m: f'class="{m.group(1)} kc-rd-profile-img"',
            image_html,
            count=1,
        )
        if "kc-rd-profile-img" not in image_html:
            image_html = image_html.replace("<img ", '<img class="kc-rd-profile-img" ', 1)
        image_html = re.sub(
            r'sizes="[^"]*"',
            'sizes="(max-width: 720px) 100vw, (max-width: 1200px) calc(100vw - 48px), 1120px"',
            image_html,
            count=1,
        )
    else:
        initials = "".join(part[0] for part in artist_name.split()[:2]).upper()
        image_html = f'<div class="kc-rd-profile-placeholder" aria-hidden="true">{html.escape(initials)}</div>'

    socials, website = extract_socials(old_main)
    cards = re.findall(r'<article class="event-card"[^>]*>.*?</article>', old_main, re.S)
    events = [event_metadata(card) for card in cards]
    past_match = re.search(r'<section class="past-shows-archive"[^>]*>.*?</section>', old_main, re.S)
    past_html = past_match.group(0) if past_match else ""
    if past_html:
        past_html = past_html.replace(
            'class="past-shows-archive"',
            'class="past-shows-archive kc-rd-past kc-rd-past-shows"',
            1,
        )

    artist_escaped = html.escape(artist_name)
    website_html = ""
    if website:
        website_html = (
            f'<a class="kc-rd-profile-website" href="{html.escape(website, quote=True)}" '
            f'target="_blank" rel="noopener">Official website <span aria-hidden="true">↗</span></a>'
        )
    elif socials:
        website_html = '<span class="kc-rd-profile-website kc-rd-profile-website--empty">Official profiles</span>'
    if socials or website_html:
        actions_html = f'''<div class="kc-rd-profile-actions">
      <div class="kc-rd-profile-socials" aria-label="Official {artist_escaped} profiles">{socials}</div>
      {website_html}
    </div>'''
    else:
        actions_html = '<div class="kc-rd-profile-actions kc-rd-profile-actions--empty"><span>Official links coming soon</span></div>'

    next_html = ""
    if events:
        first = events[0]
        secondary = " · ".join(part for part in (first["venue"], first["time"]) if part)
        next_html = f'''<a class="kc-rd-next kc-rd-next-show" href="{html.escape(first['href'], quote=True)}">
  <span><span class="kc-rd-next-kicker">Next show · {html.escape(first['month'])} {html.escape(first['day'])}</span>
  <strong class="kc-rd-next-place">{html.escape(first['location'])}</strong>
  <span class="kc-rd-next-venue">{html.escape(secondary)}</span></span>
  <span class="kc-rd-chevron" aria-hidden="true">›</span>
</a>'''
    else:
        next_html = '<div class="kc-rd-next kc-rd-next-show kc-rd-next--empty"><strong>No upcoming shows confirmed yet.</strong><span>Follow the official profiles for updates.</span></div>'

    rows = "".join(show_row(event) for event in events)
    if not rows:
        rows = '<p class="kc-rd-profile-empty">No upcoming shows are currently listed.</p>'
    main = f'''<main id="kc-main-content" class="kc-rd-profile-page kc-rd-artist-profile">
  <article class="kc-rd-profile-shell" data-kc-rd-artist-profile>
    <section class="kc-rd-profile-hero" aria-labelledby="kc-rd-artist-name">
      <div class="kc-rd-profile-visual kc-rd-profile-visual--{visual_shape}">{image_html}</div>
      <h1 class="kc-rd-profile-name" id="kc-rd-artist-name">{artist_escaped}</h1>
    </section>
    {actions_html}
    {next_html}
    <section class="kc-rd-profile-shows" aria-labelledby="kc-rd-shows-title">
      <div class="kc-rd-profile-section-title"><h2 id="kc-rd-shows-title">All {artist_escaped} Shows</h2><span class="kc-rd-upcoming-total">{len(events)} upcoming</span></div>
      <div class="kc-rd-show-list">{rows}</div>
    </section>
    {past_html}
  </article>
</main>'''
    document = document[: main_match.start()] + main + document[main_match.end() :]
    document = re.sub(
        r'<body([^>]*)>',
        lambda m: '<body' + (m.group(1).replace('class="', 'class="kc-rd-profile-body ', 1) if 'class="' in m.group(1) else m.group(1) + ' class="kc-rd-profile-body"') + '>',
        document,
        count=1,
    )
    return document, len(events), bool(past_html)


def artist_submit_main() -> str:
    return f'''<main id="kc-main-content" class="kc-rd-form-page">
  <section class="kc-rd-form-card" aria-labelledby="kc-rd-artist-submit-title">
    <p class="eyebrow">Help grow the directory</p>
    <h1 id="kc-rd-artist-submit-title">Submit a CHH Artist</h1>
    <p>Share an official artist profile so the Kingdom Circuit team can verify the artist before listing them.</p>
    <form class="kc-rd-artist-submit kc-rd-form-grid" data-kc-artist-submit-form action="{FORM_ENDPOINT}" method="post">
      <input type="hidden" name="submission_type" value="CHH artist submission">
      <input type="hidden" name="_subject" value="Kingdom Circuit CHH artist submission">
      <input type="hidden" name="environment" value="{DEPLOYMENT_ENVIRONMENT}">
      <input type="hidden" name="page_url" value="">
      <input class="kc-rd-honeypot" type="text" name="_gotcha" tabindex="-1" autocomplete="off" aria-hidden="true">
      <label class="kc-rd-field"><span>Artist or group name <b aria-hidden="true">*</b></span><input name="artistName" type="text" autocomplete="organization" required></label>
      <label class="kc-rd-field"><span>Official artist link <b aria-hidden="true">*</b></span><input name="officialUrl" type="url" inputmode="url" placeholder="https://" required><small>Instagram, official website, Spotify, or YouTube.</small></label>
      <label class="kc-rd-field"><span>Your name <em>optional</em></span><input name="submitterName" type="text" autocomplete="name"></label>
      <label class="kc-rd-field"><span>Your email <em>optional</em></span><input name="email" type="email" inputmode="email" autocomplete="email"></label>
      <label class="kc-rd-field kc-rd-field--wide"><span>Anything else we should know? <em>optional</em></span><textarea name="notes" rows="4"></textarea></label>
      <button class="kc-rd-button kc-rd-form-submit" type="submit">Submit Artist</button>
      <p class="kc-rd-form-status" data-kc-artist-form-status role="status" aria-live="polite"></p>
    </form>
  </section>
</main>'''


def create_artist_submit_page(site: pathlib.Path) -> None:
    source = site / "submit" / "index.html"
    if not source.is_file():
        raise ValueError("submit page was not found")
    document = source.read_text(encoding="utf-8")
    main_match = re.search(r'<main\b[^>]*>.*?</main>', document, re.S)
    if not main_match:
        raise ValueError("submit page main element was not found")
    document = document[: main_match.start()] + artist_submit_main() + document[main_match.end() :]
    head_end = document.find("</head>")
    if head_end != -1:
        head = document[:head_end]
        tail = document[head_end:]
        head = re.sub(r'<title>.*?</title>', '<title>Submit a CHH Artist | Kingdom Circuit</title>', head, count=1, flags=re.S)
        head = re.sub(
            r'(<meta\s+name="description"\s+content=")[^"]*(")',
            r'\1Submit a Christian hip-hop artist for review and inclusion in the Kingdom Circuit artist directory.\2',
            head,
            count=1,
        )
        head = head.replace(f"{TEST_BASE}submit/", f"{TEST_BASE}submit/artist/")
        document = head + tail
    destination = site / "submit" / "artist" / "index.html"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(document, encoding="utf-8")


def is_profile_page(relative: pathlib.PurePath, document: str) -> bool:
    return (
        len(relative.parts) == 3
        and relative.parts[0] == "artists"
        and relative.parts[2] == "index.html"
        and relative.parts[1] != "profile"
        and ("seo-artist-profile" in document or "kc-rd-artist-profile" in document)
    )


def copy_assets(site: pathlib.Path, repo: pathlib.Path) -> None:
    asset_dir = site / "assets"
    asset_dir.mkdir(parents=True, exist_ok=True)
    for filename in ("kc-redesign-v1.css", "kc-redesign-v1.js"):
        source = repo / "test-overrides" / filename
        if not source.is_file():
            raise ValueError(f"missing redesign asset: {source}")
        shutil.copy2(source, asset_dir / filename)
    if DEPLOYMENT_ENVIRONMENT == "test":
        source_dir = repo / "test-overrides" / "assets"
        for filename in FAVICON_ASSET_NAMES:
            source = source_dir / filename
            if not source.is_file():
                raise ValueError(f"missing favicon asset: {source}")
            shutil.copy2(source, asset_dir / filename)
        web_manifest = {
            "name": "Kingdom Circuit",
            "short_name": "Kingdom Circuit",
            "id": TEST_BASE,
            "start_url": TEST_BASE,
            "scope": TEST_BASE,
            "display": "standalone",
            "background_color": "#080808",
            "theme_color": "#080808",
            "icons": [
                {
                    "src": f"{TEST_BASE}assets/favicon-kc-stacked-v1-192.png",
                    "sizes": "192x192",
                    "type": "image/png",
                    "purpose": "any",
                },
                {
                    "src": f"{TEST_BASE}assets/favicon-kc-stacked-v1-512.png",
                    "sizes": "512x512",
                    "type": "image/png",
                    "purpose": "any",
                },
                {
                    "src": f"{TEST_BASE}assets/favicon-kc-stacked-v1-maskable-512.png",
                    "sizes": "512x512",
                    "type": "image/png",
                    "purpose": "maskable",
                },
            ],
        }
        (site / "manifest.webmanifest").write_text(
            json.dumps(web_manifest, indent=2) + "\n",
            encoding="utf-8",
        )


def iter_html(site: pathlib.Path) -> Iterable[pathlib.Path]:
    return sorted(path for path in site.rglob("*.html") if path.is_file())


def load_source_events(paths: Iterable[pathlib.Path]) -> list[dict[str, object]]:
    events: list[dict[str, object]] = []
    for path in paths:
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, list):
            raise ValueError(f"source events must be a JSON array: {path}")
        events.extend(event for event in payload if isinstance(event, dict))
    return events


def merge_events_by_id(
    primary: Iterable[dict[str, object]],
    overrides: Iterable[dict[str, object]],
) -> list[dict[str, object]]:
    merged: dict[str, dict[str, object]] = {}
    order: list[str] = []
    for event in [*primary, *overrides]:
        event_id = str(event.get("id") or "").strip()
        if not event_id:
            raise ValueError("event override is missing an id")
        if event_id not in merged:
            order.append(event_id)
            merged[event_id] = dict(event)
        else:
            merged[event_id].update(event)
    return [merged[event_id] for event_id in order]


def event_internal_href(event: dict[str, object]) -> str:
    event_slug = "-".join(
        (
            slug(event.get("title") or "event"),
            str(event.get("startDate") or "")[:10],
            slug(event.get("city") or "location"),
            fnv(event.get("id") or json.dumps(event, sort_keys=True)),
        )
    )
    return f"{TEST_BASE}event/{event_slug}/"


def event_date_label(event: dict[str, object]) -> str:
    parsed = parse_iso_date(event.get("startDate"))
    if parsed is None:
        label = str(event.get("startDate") or "Date to be announced")
    else:
        label = f"{parsed.strftime('%a, %b')} {parsed.day}, {parsed.year}"
    raw_time = str(event.get("startTime") or "").strip()
    match = re.fullmatch(r"(\d{1,2}):(\d{2})", raw_time)
    if match:
        hour, minute = map(int, match.groups())
        label += f" - {hour % 12 or 12}:{minute:02d} {'AM' if hour < 12 else 'PM'}"
    return label


def event_card_sort_key(card: str) -> tuple[str, str, str]:
    opening = card[: card.find(">") + 1]
    date = attribute(opening, "data-date")
    start_time = attribute(opening, "data-start-time")
    if not start_time:
        date_match = re.search(
            r"<dt>\s*Date\s*</dt>\s*<dd>.*?-\s*(\d{1,2}):(\d{2})\s*(AM|PM)</dd>",
            card,
            re.I | re.S,
        )
        if date_match:
            hour = int(date_match.group(1)) % 12
            if date_match.group(3).upper() == "PM":
                hour += 12
            start_time = f"{hour:02d}:{int(date_match.group(2)):02d}"
    title = clean_text(
        (re.search(r"<h3>\s*<a\b[^>]*>(.*?)</a>", card, re.I | re.S) or ["", ""])[1]
    )
    return date, start_time, title.casefold()


def replace_event_card_sequence(document: str, cards: Iterable[str]) -> str:
    replacement = "".join(sorted(cards, key=event_card_sort_key))
    matches = list(EVENT_CARD_PATTERN.finditer(document))
    if matches:
        return document[: matches[0].start()] + replacement + document[matches[-1].end() :]
    grid = re.search(r'<div\b[^>]*class="[^"]*\bevent-grid\b[^"]*"[^>]*>', document, re.I)
    if not grid:
        raise ValueError("event grid was not found")
    return document[: grid.end()] + replacement + document[grid.end() :]


def is_808_beezy_card(card: str) -> bool:
    return bool(
        re.search(r'/artists/808-beezy/', card, re.I)
        or re.search(r'class="[^"]*artist-line[^"]*"[^>]*>[^<]*808\s+BEEZY', card, re.I)
    )


def event_card_image(template: str, title: str) -> str:
    match = re.search(r"<img\b[^>]*>", template, re.I | re.S)
    if match:
        image = match.group(0)
        escaped_title = html.escape(title, quote=True)
        if re.search(r"\balt=(?:\"[^\"]*\"|'[^']*')", image, re.I):
            image = re.sub(
                r"\balt=(?:\"[^\"]*\"|'[^']*')",
                f'alt="{escaped_title}"',
                image,
                count=1,
                flags=re.I,
            )
        else:
            image = image[:-1] + f' alt="{escaped_title}">'
        return image
    return (
        f'<img class="artist-photo" src="{TEST_BASE}assets/event-fallback.webp" '
        f'alt="{html.escape(title, quote=True)}" loading="lazy" decoding="async" '
        'width="1200" height="675">'
    )


def render_official_event_card(event: dict[str, object], template: str) -> str:
    title = str(event.get("title") or "808 BEEZY live")
    venue = str(event.get("venue") or "Venue to be announced")
    city = str(event.get("city") or "")
    state = str(event.get("state") or "")
    location = ", ".join(part for part in (city, state) if part)
    href = event_internal_href(event)
    official = str(event.get("officialUrl") or event.get("ticketUrl") or "#")
    search = normalized_key(" ".join((title, venue, city, state, "808 BEEZY")))
    image = event_card_image(template, title)
    return f'''<article class="event-card" data-event-card data-search="{html.escape(search, quote=True)}" data-artists="808 beezy" data-state="{html.escape(state, quote=True)}" data-type="concert" data-date="{html.escape(str(event.get('startDate') or ''), quote=True)}" data-end-date="{html.escape(str(event.get('endDate') or event.get('startDate') or ''), quote=True)}" data-start-time="{html.escape(str(event.get('startTime') or ''), quote=True)}"><a class="event-media" href="{html.escape(href, quote=True)}" tabindex="-1" aria-hidden="true" data-kc-duplicate-link="true">{image}</a><div class="event-content"><div class="event-main"><div class="event-badges"><span class="badge badge-gold">Concert</span></div><h3><a href="{html.escape(href, quote=True)}">{html.escape(title)}</a></h3><p class="artist-line"><a href="{TEST_BASE}artists/808-beezy/">808 BEEZY</a></p><dl class="event-meta"><div><dt>Date</dt><dd>{html.escape(event_date_label(event))}</dd></div><div><dt>Venue</dt><dd>{html.escape(venue)}</dd></div><div><dt>Location</dt><dd>{html.escape(location)}</dd></div></dl></div><div class="event-footer"><a class="official-button" href="{html.escape(official, quote=True)}" target="_blank" rel="noopener" aria-label="Official details for {html.escape(title, quote=True)} (opens in new tab)">Official details</a></div></div></article>'''


def create_official_event_page(
    site: pathlib.Path,
    event: dict[str, object],
    template: str,
) -> bool:
    relative = event_internal_href(event).removeprefix(TEST_BASE).strip("/")
    target = site / relative / "index.html"
    if target.is_file():
        return False
    target.parent.mkdir(parents=True, exist_ok=True)
    title = str(event.get("title") or "808 BEEZY live")
    venue = str(event.get("venue") or "Venue to be announced")
    city = str(event.get("city") or "")
    state = str(event.get("state") or "")
    location = ", ".join(part for part in (city, state) if part)
    official = str(event.get("officialUrl") or event.get("ticketUrl") or "#")
    image = event_card_image(template, title).replace('loading="lazy"', 'loading="eager"', 1)
    canonical = f"https://kingdomcircuit.com{event_internal_href(event)}" if DEPLOYMENT_ENVIRONMENT == "production" else ""
    production_head = (
        f'<link rel="canonical" href="{html.escape(canonical, quote=True)}">'
        '<script async src="https://www.googletagmanager.com/gtag/js?id=G-N2KK9XF4TJ"></script>'
        '<script>window.dataLayer=window.dataLayer||[];function gtag(){dataLayer.push(arguments);}'
        "gtag('js',new Date());gtag('config','G-N2KK9XF4TJ');</script>"
        if canonical else ""
    )
    target.write_text(
        f'''<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="robots" content="{UPCOMING_PAGE_ROBOTS}"><title>{html.escape(title)} | {GENERATED_PAGE_TITLE_SUFFIX}</title>
{production_head}<link rel="stylesheet" href="{TEST_BASE}styles.css"></head><body>
<header class="site-header"><div class="header-inner"><a class="brand" href="{TEST_BASE}">Kingdom Circuit</a></div></header>
<main id="kc-main-content"><section class="event-detail-section">
<p class="eyebrow"><a class="text-link" href="{TEST_BASE}shows/">Shows</a> / {html.escape(title)}</p>
<article class="event-detail"><div class="event-detail-media">{image}</div><div class="event-detail-copy">
<p class="eyebrow">Concert</p><h1>{html.escape(title)}</h1>
<p class="artist-line"><a href="{TEST_BASE}artists/808-beezy/">808 BEEZY</a></p>
<dl class="detail-list"><div><dt>Date</dt><dd>{html.escape(event_date_label(event))}</dd></div>
<div><dt>Venue</dt><dd>{html.escape(venue)}</dd></div><div><dt>Location</dt><dd>{html.escape(location)}</dd></div></dl>
<a class="primary-button" href="{html.escape(official, quote=True)}" target="_blank" rel="noopener">Official details</a>
<p class="disclaimer">Event details may change. Confirm final information with the official organizer before traveling.</p>
</div></article></section></main><footer class="site-footer"><strong>Kingdom Circuit</strong></footer></body></html>''',
        encoding="utf-8",
    )
    return True


def restore_official_808_beezy_schedule(
    site: pathlib.Path,
    overrides: Iterable[dict[str, object]],
    today: dt.date,
) -> dict[str, int]:
    cutoff = visibility_cutoff(today)
    official = sorted(
        (dict(event) for event in overrides if is_active_event(event, cutoff)),
        key=lambda event: (
            str(event.get("startDate") or ""),
            str(event.get("startTime") or ""),
            str(event.get("id") or ""),
        ),
    )
    if not official:
        return {"official808Events": 0, "official808PagesCreated": 0, "official808ListingsUpdated": 0}

    profile_path = site / "artists" / "808-beezy" / "index.html"
    if not profile_path.is_file():
        raise ValueError("808 BEEZY profile is missing from the captured site")
    profile = profile_path.read_text(encoding="utf-8")
    current_cards = event_cards(profile)
    if not current_cards:
        # Once production already contains the restored schedule, its redesigned
        # artist profile uses show rows instead of the legacy event-card markup.
        # In that case the test overlay should preserve the verified live output
        # rather than trying to render the same schedule a second time.
        missing_hrefs = [
            event_internal_href(event)
            for event in official
            if event_internal_href(event) not in profile
        ]
        events_path = site / "events.json"
        deployed = json.loads(events_path.read_text(encoding="utf-8"))
        deployed_ids = {
            str(event.get("id") or "")
            for event in deployed
            if isinstance(event, dict)
        }
        missing_ids = [
            str(event.get("id") or "")
            for event in official
            if str(event.get("id") or "") not in deployed_ids
        ]
        if "kc-rd-show-row" not in profile or missing_hrefs or missing_ids:
            raise ValueError(
                "808 BEEZY profile has no event-card template and the deployed "
                "schedule does not fully contain the verified override"
            )
        return {
            "official808Events": len(official),
            "official808PagesCreated": 0,
            "official808ListingsUpdated": 0,
        }
    template = current_cards[0]
    rendered = {str(event.get("id")): render_official_event_card(event, template) for event in official}

    profile_path.write_text(
        replace_event_card_sequence(profile, rendered.values()),
        encoding="utf-8",
    )

    page_specs: dict[pathlib.Path, list[dict[str, object]]] = {
        site / "index.html": official,
        site / "shows" / "index.html": official,
        site / "new-shows" / "index.html": official,
        site / "shows" / "this-month" / "index.html": [
            event
            for event in official
            if parse_iso_date(event.get("startDate"))
            and parse_iso_date(event.get("startDate")).year == today.year
            and parse_iso_date(event.get("startDate")).month == today.month
        ],
    }
    for state in sorted({str(event.get("state") or "") for event in official}):
        state_name = STATE_NAMES.get(state)
        if not state_name:
            continue
        selected = [event for event in official if event.get("state") == state]
        page_specs[site / "shows" / slug(state_name) / "index.html"] = selected
        page_specs[site / "artists" / "808-beezy" / slug(state_name) / "index.html"] = selected
    for year, month in sorted(
        {
            (parsed.year, parsed.month)
            for event in official
            if (parsed := parse_iso_date(event.get("startDate"))) is not None
        }
    ):
        label = dt.date(year, month, 1).strftime("%B").casefold()
        page_specs[site / "shows" / f"{label}-{year}" / "index.html"] = [
            event
            for event in official
            if (parsed := parse_iso_date(event.get("startDate"))) is not None
            and parsed.year == year
            and parsed.month == month
        ]

    listings_updated = 1
    for path, selected in page_specs.items():
        if not path.is_file():
            continue
        document = path.read_text(encoding="utf-8")
        existing = [card for card in event_cards(document) if not is_808_beezy_card(card)]
        cards = [*existing, *(rendered[str(event.get("id"))] for event in selected)]
        path.write_text(replace_event_card_sequence(document, cards), encoding="utf-8")
        listings_updated += 1

    events_path = site / "events.json"
    deployed = json.loads(events_path.read_text(encoding="utf-8"))
    if not isinstance(deployed, list):
        raise ValueError("captured events.json must be an array")
    image_match = re.search(r'<img\b[^>]*\bsrc="([^"]+)"', template, re.I)
    image = image_match.group(1) if image_match else ""
    if image.startswith(TEST_BASE):
        image = image.removeprefix(TEST_BASE)
    enriched: list[dict[str, object]] = []
    for event in official:
        current = dict(event)
        if image:
            current.setdefault("image", image)
            current.setdefault("imageType", "artist")
            current.setdefault("imagePosition", "center")
        enriched.append(current)
    deployed = merge_events_by_id(deployed, enriched)
    deployed.sort(
        key=lambda event: (
            str(event.get("startDate") or ""),
            str(event.get("startTime") or ""),
            str(event.get("title") or ""),
        )
    )
    events_path.write_text(json.dumps(deployed, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    pages_created = sum(create_official_event_page(site, event, template) for event in official)
    return {
        "official808Events": len(official),
        "official808PagesCreated": pages_created,
        "official808ListingsUpdated": listings_updated,
    }


def artist_alias_index(site: pathlib.Path) -> tuple[dict[str, str], dict[str, str]]:
    """Return normalized artist/alias -> profile slug and profile slug -> display name."""
    path = site / "config" / "artists.json"
    if not path.is_file():
        return {}, {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError("config/artists.json must be a JSON array")
    aliases: dict[str, str] = {}
    display_names: dict[str, str] = {}
    for item in payload:
        if not isinstance(item, dict) or item.get("enabled") is False:
            continue
        name = str(item.get("name") or "").strip()
        if not name:
            continue
        profile_slug = slug(name)
        display_names[profile_slug] = name
        aliases[normalized_key(name)] = profile_slug
        for alias in item.get("aliases", []) if isinstance(item.get("aliases"), list) else []:
            alias_key = normalized_key(alias)
            if alias_key:
                aliases[alias_key] = profile_slug
    return aliases, display_names


def history_event_slug(event: dict[str, object]) -> str:
    signature = event.get("id") or json.dumps(event, sort_keys=True)
    return (
        f"{slug(event.get('title') or 'event')}-"
        f"{str(event.get('startDate') or '')[:10]}-"
        f"{slug(event.get('city'))}-{fnv(signature)}"
    )


def history_event_href(event: dict[str, object]) -> str:
    return f"{TEST_BASE}event/{history_event_slug(event)}/"


def history_event_page(site: pathlib.Path, event: dict[str, object]) -> pathlib.Path:
    return site / "event" / history_event_slug(event) / "index.html"


def event_is_test_data(event: dict[str, object]) -> bool:
    artists = event.get("artists", [])
    names = artists if isinstance(artists, list) else []
    text = " ".join(
        [
            str(event.get("title") or ""),
            str(event.get("venue") or ""),
            str(event.get("city") or ""),
            str(event.get("headliner") or ""),
            " ".join(str(name) for name in names if name),
        ]
    ).casefold()
    urls = " ".join(
        str(event.get(key) or "") for key in ("ticketUrl", "officialUrl")
    ).casefold()
    return any(domain in urls for domain in ("example.com", "example.org", "example.net")) or bool(
        re.search(r"\btest\s+(artist|city|venue|event|show|concert)\b", text)
    )


def history_event_is_trusted(event: dict[str, object]) -> bool:
    if event.get("verifiedVersion") or normalized_key(event.get("confidence")) in {
        "high",
        "verified",
    }:
        return True
    sources = event.get("sources", [])
    for source in sources if isinstance(sources, list) else []:
        if isinstance(source, dict) and normalized_key(source.get("authority")) in TRUSTED_AUTHORITIES:
            return True
    url = str(event.get("officialUrl") or event.get("ticketUrl") or "").casefold()
    return bool(url and "bandsintown.com" not in url)


def normalized_history_url(value: object) -> str:
    raw = str(value or "").strip()
    if not raw:
        return ""
    try:
        parts = urlsplit(raw)
    except ValueError:
        return raw.casefold()
    kept_query = [
        (key, value)
        for key, value in parse_qsl(parts.query, keep_blank_values=True)
        if not key.casefold().startswith("utm_")
        and key.casefold() not in {"fbclid", "gclid", "mc_cid", "mc_eid"}
    ]
    return urlunsplit(
        (
            parts.scheme.casefold(),
            parts.netloc.casefold(),
            parts.path.rstrip("/"),
            urlencode(kept_query),
            "",
        )
    )


def history_event_artists(event: dict[str, object]) -> list[str]:
    raw = event.get("artists", [])
    names = [str(name).strip() for name in raw if str(name).strip()] if isinstance(raw, list) else []
    headliner = str(event.get("headliner") or "").strip()
    if not names and headliner:
        names = [headliner]
    return list(dict.fromkeys(names))


def history_event_duplicate(left: dict[str, object], right: dict[str, object]) -> bool:
    left_date = str(left.get("startDate") or "")[:10]
    right_date = str(right.get("startDate") or "")[:10]
    left_city = semantic_key(str(left.get("city") or "").split("(", 1)[0])
    right_city = semantic_key(str(right.get("city") or "").split("(", 1)[0])
    if (
        left_date != right_date
        or left_city != right_city
        or semantic_key(left.get("state")) != semantic_key(right.get("state"))
    ):
        return False
    left_time = str(left.get("startTime") or "").strip()
    right_time = str(right.get("startTime") or "").strip()
    if left_time and right_time and left_time != right_time:
        return False

    left_urls = {
        normalized_history_url(left.get(key))
        for key in ("officialUrl", "ticketUrl")
        if normalized_history_url(left.get(key))
    }
    right_urls = {
        normalized_history_url(right.get(key))
        for key in ("officialUrl", "ticketUrl")
        if normalized_history_url(right.get(key))
    }
    if left_urls & right_urls:
        return True
    if semantic_key(left.get("title")) != semantic_key(right.get("title")):
        return False
    left_venue = semantic_key(left.get("venue"))
    right_venue = semantic_key(right.get("venue"))
    return (
        left_venue == right_venue
        or left_venue in PLACEHOLDER_VENUES
        or right_venue in PLACEHOLDER_VENUES
    )


def history_event_score(site: pathlib.Path, event: dict[str, object]) -> tuple[int, ...]:
    sources = event.get("sources", [])
    source_authorities = {
        normalized_key(source.get("authority"))
        for source in sources if isinstance(sources, list) and isinstance(source, dict)
    }
    venue = semantic_key(event.get("venue"))
    completeness = sum(
        bool(str(event.get(key) or "").strip())
        for key in ("startTime", "venue", "address", "officialUrl", "ticketUrl", "image")
    )
    return (
        int(history_event_page(site, event).is_file()),
        int(bool(event.get("verifiedVersion"))),
        int(bool(source_authorities & TRUSTED_AUTHORITIES)),
        len(history_event_artists(event)),
        int(venue not in PLACEHOLDER_VENUES),
        completeness,
        int(normalized_key(event.get("confidence")) in {"high", "verified"}),
    )


def dedupe_history_events(
    site: pathlib.Path,
    events: Iterable[dict[str, object]],
) -> list[dict[str, object]]:
    selected: list[dict[str, object]] = []
    for event in sorted(events, key=lambda item: history_event_score(site, item), reverse=True):
        duplicate = next(
            (existing for existing in selected if history_event_duplicate(event, existing)),
            None,
        )
        if duplicate is not None:
            duplicate["_profileSlugs"] = sorted(
                {
                    str(profile_slug)
                    for profile_slug in (
                        list(duplicate.get("_profileSlugs", []))
                        + list(event.get("_profileSlugs", []))
                    )
                }
            )
            duplicate["artists"] = list(
                dict.fromkeys(history_event_artists(duplicate) + history_event_artists(event))
            )
            continue
        selected.append(event)
    return sorted(
        selected,
        key=lambda event: (
            str(event.get("startDate") or ""),
            str(event.get("startTime") or ""),
            str(event.get("title") or ""),
        ),
        reverse=True,
    )


def load_source_history(
    paths: Iterable[pathlib.Path],
    site: pathlib.Path,
    cutoff: dt.date,
) -> tuple[list[dict[str, object]], dict[str, list[dict[str, object]]], dict[str, str]]:
    aliases, _display_names = artist_alias_index(site)
    candidates: list[dict[str, object]] = []
    for path in paths:
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict) or not isinstance(payload.get("events"), list):
            raise ValueError(f"source history must contain an events array: {path}")
        for record in payload["events"]:
            if not isinstance(record, dict):
                continue
            event = record.get("event")
            if not isinstance(event, dict):
                continue
            occurrence_confirmed = bool(record.get("observedOnOrAfterEventDate")) or normalized_key(
                record.get("calendarPresence")
            ) == "present"
            last_date = parse_iso_date(event.get("endDate") or event.get("startDate"))
            status = normalized_key(event.get("status"))
            country = str(event.get("country") or "US").strip().upper()
            required = all(str(event.get(key) or "").strip() for key in ("title", "city", "state", "startDate"))
            known_profiles = {
                aliases[normalized_key(name)]
                for name in history_event_artists(event)
                if normalized_key(name) in aliases
            }
            if not (
                occurrence_confirmed
                and last_date is not None
                and last_date < cutoff
                and status not in INACTIVE_STATUSES
                and country in {"", "US", "USA"}
                and required
                and known_profiles
                and not event_is_test_data(event)
                and history_event_is_trusted(event)
            ):
                continue
            normalized_event = dict(event)
            normalized_event["_profileSlugs"] = sorted(known_profiles)
            candidates.append(normalized_event)

    events = dedupe_history_events(site, candidates)
    by_profile: dict[str, list[dict[str, object]]] = {}
    for event in events:
        for profile_slug in event.get("_profileSlugs", []):
            by_profile.setdefault(str(profile_slug), []).append(event)
    return events, by_profile, aliases


def history_archive_row(
    event: dict[str, object],
    aliases: dict[str, str],
) -> str:
    artist_parts: list[str] = []
    names = history_event_artists(event)
    for name in names[:5]:
        profile_slug = aliases.get(normalized_key(name))
        if profile_slug:
            artist_parts.append(
                f'<a href="{TEST_BASE}artists/{profile_slug}/">{html.escape(name)}</a>'
            )
        else:
            artist_parts.append(html.escape(name))
    if len(names) > 5:
        artist_parts.append(f"+{len(names) - 5} more")
    location = ", ".join(
        value
        for value in (
            str(event.get("city") or "").strip(),
            str(event.get("state") or "").strip(),
        )
        if value
    )
    details = " · ".join(
        part
        for part in (
            " · ".join(artist_parts),
            html.escape(str(event.get("venue") or "Venue to be announced")),
            html.escape(location),
        )
        if part
    )
    return (
        '<article class="past-show-row">'
        f'<div class="past-show-date">{html.escape(past_date_label(str(event.get("startDate") or "")))}</div>'
        '<div class="past-show-copy">'
        f'<h3><a href="{html.escape(history_event_href(event), quote=True)}">'
        f'{html.escape(str(event.get("title") or "Past show"))}</a></h3>'
        f"<p>{details}</p></div></article>"
    )


def replace_profile_archive(document: str, rows: list[str]) -> str:
    if not rows:
        return document
    section_match = re.search(
        r'<section\b(?=[^>]*\bdata-past-shows-archive\b)[^>]*>.*?</section>',
        document,
        re.I | re.S,
    )
    section = past_archive_section(rows)
    if section_match:
        if "kc-rd-past-shows" in section_match.group(0):
            section = section.replace(
                'class="past-shows-archive"',
                'class="past-shows-archive kc-rd-past kc-rd-past-shows"',
                1,
            )
        return document[: section_match.start()] + section + document[section_match.end() :]
    if "</main>" not in document:
        raise ValueError("artist profile main element was not found for Past Shows archive")
    return document.replace("</main>", section + "\n</main>", 1)


def create_history_event_page(site: pathlib.Path, event: dict[str, object]) -> bool:
    target = history_event_page(site, event)
    if target.is_file():
        return False
    target.parent.mkdir(parents=True, exist_ok=True)
    title = html.escape(str(event.get("title") or "Past Christian hip-hop show"))
    venue = html.escape(str(event.get("venue") or "Venue to be announced"))
    city = html.escape(str(event.get("city") or ""))
    state = html.escape(str(event.get("state") or ""))
    artists = " · ".join(html.escape(name) for name in history_event_artists(event))
    date = html.escape(past_date_label(str(event.get("startDate") or "")))
    canonical = f"https://kingdomcircuit.com{history_event_href(event)}" if DEPLOYMENT_ENVIRONMENT == "production" else ""
    production_head = (
        f'<link rel="canonical" href="{html.escape(canonical, quote=True)}">'
        '<script async src="https://www.googletagmanager.com/gtag/js?id=G-N2KK9XF4TJ"></script>'
        '<script>window.dataLayer=window.dataLayer||[];function gtag(){dataLayer.push(arguments);}'
        "gtag('js',new Date());gtag('config','G-N2KK9XF4TJ');</script>"
        if canonical else ""
    )
    target.write_text(
        f'''<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="robots" content="{PAST_PAGE_ROBOTS}"><title>{title} - Past Show | {GENERATED_PAGE_TITLE_SUFFIX}</title>
{production_head}<link rel="stylesheet" href="{TEST_BASE}styles.css"></head><body>
<header class="site-header"><div class="header-inner"><a class="brand" href="{TEST_BASE}">Kingdom Circuit</a></div></header>
<main id="kc-main-content"><section class="event-detail-section">
<p class="eyebrow"><a class="text-link" href="{TEST_BASE}shows/">Shows</a> / Past show</p>
<article class="event-detail"><div class="event-detail-copy"><p class="eyebrow">Past show</p><h1>{title}</h1>
<p class="artist-line">{artists}</p><div class="past-event-notice"><strong>This event has passed.</strong></div>
<dl class="detail-list"><div><dt>Date</dt><dd>{date}</dd></div><div><dt>Venue</dt><dd>{venue}</dd></div>
<div><dt>Location</dt><dd>{city}, {state}</dd></div></dl></div></article></section></main>
<footer class="site-footer"><strong>Kingdom Circuit</strong></footer></body></html>''',
        encoding="utf-8",
    )
    return True


def profile_event_index(
    documents: dict[pathlib.PurePath, str],
) -> dict[str, list[dict[str, str]]]:
    profiles: dict[str, list[dict[str, str]]] = {}
    for relative, document in documents.items():
        if is_profile_page(relative, document):
            profiles[relative.parts[1]] = [event_metadata(card) for card in event_cards(document)]
    return profiles


def month_counts(document: str) -> tuple[int, int, int]:
    cards = event_cards(document)
    states: set[str] = set()
    artists: set[str] = set()
    for card in cards:
        opening = card[: card.find(">") + 1]
        state = attribute(opening, "data-state").strip().upper()
        if state:
            states.add(state)
        artists.update(
            normalized_key(name)
            for name in attribute(opening, "data-artists").split("|")
            if normalized_key(name)
        )
    return len(cards), len(states), len(artists)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("site_root", type=pathlib.Path)
    parser.add_argument(
        "--source-events",
        type=pathlib.Path,
        action="append",
        default=[],
        help="Unsanitized event JSON used only at build time for the seven-day New Shows window.",
    )
    parser.add_argument(
        "--source-history",
        type=pathlib.Path,
        action="append",
        default=[],
        help="Full live event history used only at build time to restore complete artist archives.",
    )
    parser.add_argument(
        "--event-overrides",
        type=pathlib.Path,
        action="append",
        default=[],
        help="Test-only verified event records restored after the live artifact is captured.",
    )
    parser.add_argument(
        "--production",
        action="store_true",
        help="Apply the approved redesign with production paths, form identity, and indexing rules.",
    )
    parser.add_argument("--today", type=dt.date.fromisoformat, help=argparse.SUPPRESS)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    configure_environment(args.production)
    site = args.site_root.resolve()
    repo = pathlib.Path(__file__).resolve().parent.parent
    home_path = site / "index.html"
    directory_path = site / "artists" / "index.html"
    if not home_path.is_file() or not directory_path.is_file():
        raise SystemExit("captured home page or artists directory is missing")

    copy_assets(site, repo)
    create_artist_submit_page(site)
    today = args.today or site_today()
    cutoff = visibility_cutoff(today)
    source_events = load_source_events(args.source_events)
    event_overrides = load_source_events(args.event_overrides)
    official_event_stats = restore_official_808_beezy_schedule(site, event_overrides, today)
    if event_overrides:
        source_events = merge_events_by_id(source_events, event_overrides)
    recent_keys = recent_event_keys(source_events, today)
    history_events, history_by_profile, history_aliases = load_source_history(
        args.source_history,
        site,
        cutoff,
    )
    generated_history_pages = sum(
        int(create_history_event_page(site, event)) for event in history_events
    )
    filter_public_event_data(site, cutoff)
    patch_runtime(site)

    documents: dict[pathlib.PurePath, str] = {}
    expired_card_count = 0
    expired_profile_cards_archived = 0
    history_profile_rows_loaded = 0
    for page in iter_html(site):
        relative = page.relative_to(site)
        document = page.read_text(encoding="utf-8")
        if is_profile_page(relative, document):
            profile_history = history_by_profile.get(relative.parts[1], [])
            if profile_history:
                rows = [
                    history_archive_row(event, history_aliases)
                    for event in profile_history
                ]
                document = replace_profile_archive(document, rows)
                history_profile_rows_loaded += len(rows)
            document, archived = archive_expired_profile_cards(document, cutoff)
            expired_profile_cards_archived += archived
        before = len(event_cards(document))
        document = prune_expired_event_cards(document, cutoff)
        expired_card_count += before - len(event_cards(document))
        if relative.as_posix() == "new-shows/index.html":
            if not args.source_events:
                recent_keys = {card_source_key(card) for card in event_cards(document)}
            document = transform_new_shows(document, recent_keys)
        elif relative.as_posix() == "shows/this-month/index.html":
            document = transform_this_month(document)
        else:
            document = update_results_count(document)
        documents[relative] = document

    home_source = documents[pathlib.PurePath("index.html")]
    directory_source = documents[pathlib.PurePath("artists/index.html")]
    show_count = len(event_cards(home_source))
    artist_count = len(ARTIST_CARD_PATTERN.findall(directory_source))
    if show_count < 1 or artist_count < 1:
        raise SystemExit(f"invalid published counts: shows={show_count}, artists={artist_count}")
    profile_events = profile_event_index(documents)
    new_show_count = len(event_cards(documents.get(pathlib.PurePath("new-shows/index.html"), "")))
    month_show_count, month_state_count, month_artist_count = month_counts(
        documents.get(pathlib.PurePath("shows/this-month/index.html"), "")
    )

    profile_pages = 0
    profile_show_rows = 0
    profile_past_show_rows = 0
    profile_pages_with_past = 0
    header_pages = 0
    for relative, document in documents.items():
        page = site / relative
        profile = is_profile_page(relative, document)
        if relative.as_posix() == "index.html":
            document = transform_home(document, show_count, artist_count)
        elif relative.as_posix() == "artists/index.html":
            document = transform_directory(document, artist_count, profile_events)
        if profile:
            if "kc-rd-artist-profile" in document:
                event_rows = len(re.findall(r'\bclass="[^"]*\bkc-rd-show-row\b', document))
                has_past = "kc-rd-past-shows" in document
            else:
                document, event_rows, has_past = transform_artist_profile(document)
            profile_pages += 1
            profile_show_rows += event_rows
            profile_past_show_rows += len(PAST_SHOW_ROW_PATTERN.findall(document))
            profile_pages_with_past += int(has_past)
        document = replace_legacy_header(document, profile_header() if profile else full_header(relative))
        document = inject_assets(document)
        page.write_text(document, encoding="utf-8")
        header_pages += 1

    production = DEPLOYMENT_ENVIRONMENT == "production"
    mirror_path = site / "test-live-mirror-manifest.json"
    if not production:
        mirror = json.loads(mirror_path.read_text(encoding="utf-8"))
        mirror["mode"] = "live-baseline-with-test-redesign"
        mirror["contentAndLayoutParity"] = False
        mirror["testRedesignApplied"] = True
        mirror.setdefault("testOnlyDifferences", []).append(
            "mobile-first navigation, homepage, artist directory, submission, and artist profile redesign"
        )
        mirror_path.write_text(json.dumps(mirror, indent=2) + "\n", encoding="utf-8")

    manifest = {
        "mode": VERSION,
        "source": (
            "verified production deployment artifact"
            if production
            else "published live-site capture after exact baseline verification"
        ),
        "siteBase": TEST_BASE,
        "testBase": TEST_BASE if not production else None,
        "showCount": show_count,
        "artistCount": artist_count,
        "profilePageCount": profile_pages,
        "profileShowRowCount": profile_show_rows,
        "profilePastShowRowCount": profile_past_show_rows,
        "profilePagesWithPastShows": profile_pages_with_past,
        "headerPageCount": header_pages,
        "artistSubmissionPath": f"{TEST_BASE}submit/artist/",
        "visibilityCutoff": cutoff.isoformat(),
        "pastGraceDays": PAST_GRACE_DAYS,
        "newWindowDays": NEW_WINDOW_DAYS,
        "newShowCount": new_show_count,
        "monthShowCount": month_show_count,
        "monthStateCount": month_state_count,
        "monthArtistCount": month_artist_count,
        "expiredEventCardsRemoved": expired_card_count,
        "expiredProfileCardsArchived": expired_profile_cards_archived,
        "sourceMetadataUsed": bool(args.source_events),
        "sourceHistoryUsed": bool(args.source_history),
        "historicalEventCount": len(history_events),
        "historicalProfileRowCount": history_profile_rows_loaded,
        "generatedHistoricalEventPages": generated_history_pages,
        **official_event_stats,
        "deploymentEnvironment": DEPLOYMENT_ENVIRONMENT,
        "productionChanged": production,
    }
    manifest_path = site / MANIFEST_FILENAME
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(
        json.dumps(manifest, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
