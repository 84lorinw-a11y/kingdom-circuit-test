#!/usr/bin/env python3
"""Build crawlable Kingdom Circuit pages into a GitHub Pages artifact.

The source repository remains the data authority. This builder reads the current
runtime JSON and current app.js, then enriches only the deployment artifact with
static HTML, permanent URLs, structured data, sitemap entries, and crawlable
internal links. It makes no network requests.
"""
from __future__ import annotations

import argparse
import calendar
import copy
import datetime as dt
import hashlib
import html
import json
import re
import shutil
import unicodedata
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

SITE_NAME = "The Kingdom Circuit"
MISSION = (
    "The Kingdom Circuit exists to connect people with CHH music, concerts, "
    "festivals, and community so the music reaches farther and more people have "
    "the opportunity to hear the gospel."
)
GA_ID = "G-N2KK9XF4TJ"
FALLBACK_IMAGE = "assets/event-fallback.webp"
SPOTIFY_IMAGE_ENDPOINT = "https://open.voidware.de/artist/"
STATE_NAMES = {
    "AL":"Alabama","AK":"Alaska","AZ":"Arizona","AR":"Arkansas","CA":"California",
    "CO":"Colorado","CT":"Connecticut","DE":"Delaware","DC":"District of Columbia",
    "FL":"Florida","GA":"Georgia","HI":"Hawaii","ID":"Idaho","IL":"Illinois",
    "IN":"Indiana","IA":"Iowa","KS":"Kansas","KY":"Kentucky","LA":"Louisiana",
    "ME":"Maine","MD":"Maryland","MA":"Massachusetts","MI":"Michigan","MN":"Minnesota",
    "MS":"Mississippi","MO":"Missouri","MT":"Montana","NE":"Nebraska","NV":"Nevada",
    "NH":"New Hampshire","NJ":"New Jersey","NM":"New Mexico","NY":"New York",
    "NC":"North Carolina","ND":"North Dakota","OH":"Ohio","OK":"Oklahoma","OR":"Oregon",
    "PA":"Pennsylvania","RI":"Rhode Island","SC":"South Carolina","SD":"South Dakota",
    "TN":"Tennessee","TX":"Texas","UT":"Utah","VT":"Vermont","VA":"Virginia",
    "WA":"Washington","WV":"West Virginia","WI":"Wisconsin","WY":"Wyoming",
}
GENERIC_VENUES = {
    "", "tbd", "location tbd", "venue tbd", "venue not provided",
    "venue to be announced", "location to be announced",
}
TITLE_STOP_WORDS = {"a", "an", "and", "at", "in", "of", "on", "the", "with"}
PLATFORM_DOMAINS = ("instagram.com", "open.spotify.com", "youtu.be", "youtube.com", "music.apple.com", "bandsintown.com")


def esc(value: Any) -> str:
    return html.escape(str(value or ""), quote=True)


def normalize(value: Any) -> str:
    return str(value or "").strip().casefold()


def normalize_event_text(value: Any) -> str:
    text = unicodedata.normalize("NFKD", str(value or ""))
    text = "".join(ch for ch in text if not unicodedata.combining(ch)).casefold()
    text = text.replace("&", " and ").replace("’", "").replace("'", "")
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", text)).strip()


def slugify(value: Any) -> str:
    text = unicodedata.normalize("NFKD", str(value or ""))
    text = "".join(ch for ch in text if not unicodedata.combining(ch)).casefold()
    text = text.replace("&", " and ").replace("’", "").replace("'", "")
    text = re.sub(r"[^a-z0-9]+", "-", text).strip("-")
    return re.sub(r"-{2,}", "-", text) or "item"


def fnv1a_hex(value: Any) -> str:
    # Matches the small JavaScript helper injected into app.js for ASCII IDs.
    number = 0x811C9DC5
    for ch in str(value or ""):
        number ^= ord(ch)
        number = (number * 0x01000193) & 0xFFFFFFFF
    return f"{number:08x}"


def artist_slug(name: str) -> str:
    return slugify(name)


def event_slug(event: dict[str, Any]) -> str:
    stem = slugify("-".join(str(event.get(key) or "") for key in ("title", "city", "state", "startDate")))
    identity = event.get("id") or "|".join(str(event.get(key) or "") for key in ("title", "city", "state", "startDate", "venue"))
    return f"{stem[:92].rstrip('-')}-{fnv1a_hex(identity)[:6]}"


def event_path(event: dict[str, Any]) -> str:
    prefix = "festivals" if normalize(event.get("eventType")) == "festival" else "events"
    return f"/{prefix}/{event_slug(event)}/"


def normalize_base_path(value: str) -> str:
    path = "/" + str(value or "/").strip("/")
    return "/" if path == "/" else path + "/"


def join_base_path(base_path: str, relative: str) -> str:
    clean = str(relative or "").lstrip("/")
    return f"{base_path}{clean}" if base_path != "/" else f"/{clean}"


def absolute_url(base_url: str, path: str) -> str:
    base = urlparse(base_url.rstrip("/"))
    origin = f"{base.scheme}://{base.netloc}"
    base_prefix = base.path.rstrip("/")
    clean_path = "/" + str(path or "").lstrip("/")
    if base_prefix and (clean_path == base_prefix or clean_path.startswith(base_prefix + "/")):
        return origin + clean_path
    return base_url.rstrip("/") + clean_path


def local_or_remote_url(value: Any, base_path: str) -> str:
    raw = str(value or "").strip()
    if not raw:
        return ""
    if re.match(r"^https?://", raw, flags=re.I):
        return re.sub(r"^http://", "https://", raw, flags=re.I)
    return join_base_path(base_path, raw)


def json_load(path: Path, fallback: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return copy.deepcopy(fallback)


def parse_js_json_constant(source: str, name: str, fallback: Any) -> Any:
    match = re.search(rf"const\s+{re.escape(name)}\s*=\s*(\[.*?\]|\{{.*?\}})\s*;", source, flags=re.S)
    if not match:
        return copy.deepcopy(fallback)
    try:
        return json.loads(match.group(1))
    except json.JSONDecodeError:
        return copy.deepcopy(fallback)


def spotify_id(artist: dict[str, Any]) -> str:
    value = artist.get("spotifyProfile") or (f"https://open.spotify.com/artist/{artist.get('spotifyId')}" if artist.get("spotifyId") else "")
    match = re.search(r"open\.spotify\.com/artist/([A-Za-z0-9]+)", str(value), flags=re.I)
    return match.group(1) if match else ""


def artist_image(artist: dict[str, Any]) -> str:
    if artist.get("imageUrl"):
        return str(artist["imageUrl"])
    if artist.get("sourceRegistryVerified") is True:
        sid = spotify_id(artist)
        if sid:
            return f"{SPOTIFY_IMAGE_ENDPOINT}{sid}"
    return ""


def merge_artists(base_artists: list[dict[str, Any]], app_source: str) -> list[dict[str, Any]]:
    roster = parse_js_json_constant(app_source, "ARTIST_ROSTER_ORDER", [])
    verified = parse_js_json_constant(app_source, "VERIFIED_ARTIST_REGISTRY", {})
    base_by_name = {normalize(item.get("name")): copy.deepcopy(item) for item in base_artists if item.get("name")}
    ordered_names = list(roster) if roster else [item.get("name") for item in base_artists if item.get("name")]
    seen: set[str] = set()
    result: list[dict[str, Any]] = []

    for index, name in enumerate(ordered_names, start=1):
        key = normalize(name)
        if not key or key in seen:
            continue
        seen.add(key)
        artist = base_by_name.get(key, {"name": name, "enabled": True})
        update = verified.get(key, {}) if isinstance(verified, dict) else {}
        aliases = []
        for alias in [*(artist.get("aliases") or []), *(update.get("aliases") or [])]:
            if alias and normalize(alias) not in {normalize(item) for item in aliases}:
                aliases.append(alias)
        artist.update(copy.deepcopy(update))
        artist["name"] = artist.get("name") or name
        artist["rosterOrder"] = index
        if aliases:
            artist["aliases"] = aliases
        if artist.get("sourceRegistryVerified") is True and not artist.get("imageUrl"):
            image = artist_image(artist)
            if image:
                artist["imageUrl"] = image
                artist["imageSource"] = "Verified Spotify artist profile"
        result.append(artist)

    for artist in base_artists:
        key = normalize(artist.get("name"))
        if not key or key in seen:
            continue
        seen.add(key)
        merged = copy.deepcopy(artist)
        update = verified.get(key, {}) if isinstance(verified, dict) else {}
        merged.update(copy.deepcopy(update))
        merged["rosterOrder"] = len(result) + 1
        result.append(merged)
    return result


def normalize_city(value: Any) -> str:
    text = re.sub(r"\s*\([^)]*\)\s*", " ", str(value or ""))
    normalized = normalize_event_text(text)
    normalized = re.sub(r"\bst\b", "saint", normalized)
    normalized = re.sub(r"\bft\b", "fort", normalized)
    normalized = re.sub(r"\bmt\b", "mount", normalized)
    return re.sub(r"\s+(metro|area)$", "", normalized).strip()


def normalize_venue(value: Any) -> str:
    normalized = normalize_event_text(value)
    return "" if normalized in GENERIC_VENUES else normalized


def title_tokens(event: dict[str, Any]) -> set[str]:
    return {token for token in normalize_event_text(event.get("title")).split() if len(token) > 1 and token not in TITLE_STOP_WORDS}


def token_containment(left: set[str], right: set[str]) -> float:
    if not left or not right:
        return 0.0
    return len(left & right) / min(len(left), len(right))


def configured_artist_name(name: Any, artists: list[dict[str, Any]]) -> str:
    target = normalize(name)
    for artist in artists:
        if normalize(artist.get("name")) == target or target in {normalize(alias) for alias in artist.get("aliases") or []}:
            return normalize(artist.get("name"))
    return target


def event_artist_set(event: dict[str, Any], artists: list[dict[str, Any]]) -> set[str]:
    return {configured_artist_name(name, artists) for name in event.get("artists") or [] if configured_artist_name(name, artists)}


def event_minutes(value: Any) -> int | None:
    match = re.match(r"^(\d{1,2}):(\d{2})", str(value or ""))
    return int(match.group(1)) * 60 + int(match.group(2)) if match else None


def times_compatible(left: dict[str, Any], right: dict[str, Any]) -> bool:
    a, b = event_minutes(left.get("startTime")), event_minutes(right.get("startTime"))
    return a is None or b is None or abs(a - b) <= 90


def normalized_url(value: Any) -> str:
    raw = str(value or "").strip()
    if not raw:
        return ""
    try:
        parsed = urlparse(raw if "://" in raw else f"https://kingdomcircuit.com/{raw.lstrip('/')}")
    except ValueError:
        return ""
    if parsed.scheme not in {"http", "https"}:
        return ""
    query = [(k, v) for k, v in parse_qsl(parsed.query, keep_blank_values=True) if k not in {"utm_source", "utm_medium", "utm_campaign", "utm_content", "utm_term", "fbclid", "gclid"}]
    path = parsed.path.rstrip("/").casefold()
    return urlunparse(("", parsed.netloc.casefold(), path, "", urlencode(query), "")).lstrip("//")


def specific_event_url(value: Any) -> bool:
    normalized = normalized_url(value)
    if not normalized:
        return False
    return not re.search(r"/collections?(?:/|$)", normalized) and not re.search(r"/(?:events?|shows?|tours?|calendar)/?(?:\?|$)", normalized)


def event_urls(event: dict[str, Any]) -> set[str]:
    values = [event.get("ticketUrl"), event.get("officialUrl")]
    values.extend(source.get("url") for source in event.get("sources") or [] if isinstance(source, dict))
    return {normalized_url(value) for value in values if specific_event_url(value) and normalized_url(value)}


def same_event(left: dict[str, Any], right: dict[str, Any], artists: list[dict[str, Any]]) -> bool:
    if str(left.get("startDate") or "") != str(right.get("startDate") or ""):
        return False
    left_state, right_state = normalize(left.get("state")), normalize(right.get("state"))
    if left_state and right_state and left_state != right_state:
        return False
    left_address, right_address = normalize_event_text(left.get("address")), normalize_event_text(right.get("address"))
    same_address = bool(left_address and right_address and left_address == right_address)
    left_city, right_city = normalize_city(left.get("city")), normalize_city(right.get("city"))
    if not same_address and (not left_city or not right_city or left_city != right_city):
        return False
    if not times_compatible(left, right):
        return False

    left_artists = event_artist_set(left, artists)
    shared_artist = bool(left_artists & event_artist_set(right, artists))
    left_title, right_title = normalize_event_text(left.get("title")), normalize_event_text(right.get("title"))
    title_score = token_containment(title_tokens(left), title_tokens(right))
    title_related = bool(left_title and right_title and (left_title == right_title or left_title in right_title or right_title in left_title))
    related = shared_artist or title_related or title_score >= 0.66
    left_venue, right_venue = normalize_venue(left.get("venue")), normalize_venue(right.get("venue"))
    venue_score = token_containment(set(left_venue.split()), set(right_venue.split()))
    same_venue = bool(left_venue and right_venue and (left_venue == right_venue or venue_score >= 0.80))
    one_unknown = not left_venue or not right_venue
    shared_url = bool(event_urls(left) & event_urls(right))

    if same_address and (related or shared_url):
        return True
    if left_venue and right_venue and not same_venue:
        return False
    if shared_url and related:
        return True
    if same_venue and related:
        return True
    return bool(one_unknown and shared_artist and (title_related or title_score >= 0.55))


def source_priority(event: dict[str, Any]) -> int:
    priorities = [int(event.get("sourcePriority") or 0)]
    priorities.extend(int(source.get("priority") or 0) for source in event.get("sources") or [] if isinstance(source, dict))
    return max(priorities or [0])


def record_score(event: dict[str, Any]) -> int:
    score = source_priority(event)
    score += 12 if normalize_venue(event.get("venue")) else 0
    score += 6 if normalize_event_text(event.get("address")) else 0
    score += 2 if event.get("startTime") else 0
    score += 6 if specific_event_url(event.get("officialUrl")) else 0
    score += 4 if specific_event_url(event.get("ticketUrl")) else 0
    image = str(event.get("image") or "")
    score += 5 if re.match(r"^/?assets/", image, flags=re.I) else (1 if image else 0)
    return score


def unique_sources(*groups: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    seen: set[str] = set()
    for group in groups:
        for source in group or []:
            if not isinstance(source, dict):
                continue
            key = normalized_url(source.get("url")) or normalize_event_text(source.get("name"))
            if not key or key in seen:
                continue
            seen.add(key)
            result.append(copy.deepcopy(source))
    return sorted(result, key=lambda item: int(item.get("priority") or 0), reverse=True)


def should_use_incoming_image(existing: dict[str, Any], incoming: dict[str, Any]) -> bool:
    if not incoming.get("image"):
        return False
    if incoming.get("imageOverride"):
        return True
    if not existing.get("image"):
        return True
    current = normalize(existing.get("image"))
    return current == "assets/event-fallback.webp" or current.endswith("/assets/event-fallback.webp") or normalize(existing.get("imageType")) == "fallback"


def merge_event_records(left: dict[str, Any], right: dict[str, Any]) -> dict[str, Any]:
    primary, secondary = (right, left) if record_score(right) > record_score(left) else (left, right)
    merged = copy.deepcopy(secondary)
    merged.update(copy.deepcopy(primary))
    for key, value in secondary.items():
        current = merged.get(key)
        if current is None or current == "" or current == []:
            merged[key] = copy.deepcopy(value)
    merged["artists"] = list(dict.fromkeys([*(primary.get("artists") or []), *(secondary.get("artists") or [])]))
    merged["mergedIds"] = list(dict.fromkeys([*(primary.get("mergedIds") or []), primary.get("id"), *(secondary.get("mergedIds") or []), secondary.get("id")]))
    merged["mergedIds"] = [item for item in merged["mergedIds"] if item]
    merged["sources"] = unique_sources(primary.get("sources") or [], secondary.get("sources") or [])
    if merged["sources"]:
        merged["sourceName"] = merged["sources"][0].get("name") or merged.get("sourceName")
    merged["officialUrl"] = next((value for value in (primary.get("officialUrl"), secondary.get("officialUrl")) if specific_event_url(value)), primary.get("officialUrl") or secondary.get("officialUrl") or "")
    merged["ticketUrl"] = next((value for value in (primary.get("ticketUrl"), secondary.get("ticketUrl")) if specific_event_url(value)), primary.get("ticketUrl") or secondary.get("ticketUrl") or merged.get("officialUrl") or "")
    if should_use_incoming_image(primary, secondary):
        merged["image"] = secondary.get("image")
        merged["imageType"] = secondary.get("imageType") or merged.get("imageType")
        merged["imagePosition"] = secondary.get("imagePosition") or merged.get("imagePosition")
    if left.get("firstSeen") or right.get("firstSeen"):
        merged["firstSeen"] = min(value for value in (left.get("firstSeen"), right.get("firstSeen")) if value)
    if left.get("lastVerified") or right.get("lastVerified"):
        merged["lastVerified"] = max(value for value in (left.get("lastVerified"), right.get("lastVerified")) if value)
    return merged


def merge_events(primary: list[dict[str, Any]], supplemental: list[dict[str, Any]], artists: list[dict[str, Any]]) -> list[dict[str, Any]]:
    merged: list[dict[str, Any]] = []
    for raw in [*primary, *supplemental]:
        if not isinstance(raw, dict):
            continue
        incoming = copy.deepcopy(raw)
        incoming["artists"] = list(raw.get("artists") or [])
        incoming["sources"] = list(raw.get("sources") or [])
        match_index = next((index for index, existing in enumerate(merged) if same_event(existing, incoming, artists)), None)
        if match_index is None:
            merged.append(incoming)
        else:
            merged[match_index] = merge_event_records(merged[match_index], incoming)
    return sorted(merged, key=lambda event: (str(event.get("startDate") or "9999-99-99"), str(event.get("startTime") or "99:99"), str(event.get("title") or "")))


def format_date(event: dict[str, Any]) -> str:
    raw = str(event.get("startDate") or "")
    try:
        date = dt.date.fromisoformat(raw)
        text = f"{calendar.day_abbr[date.weekday()]}, {calendar.month_abbr[date.month]} {date.day}, {date.year}"
    except ValueError:
        return "Date to be announced"
    time_value = str(event.get("startTime") or "")
    match = re.match(r"^(\d{1,2}):(\d{2})", time_value)
    if match:
        hour, minute = int(match.group(1)), int(match.group(2))
        suffix = "AM" if hour < 12 else "PM"
        display_hour = hour % 12 or 12
        text += f" - {display_hour}:{minute:02d} {suffix}"
    return text


def is_new_event(event: dict[str, Any], today: dt.date | None = None) -> bool:
    raw = str(event.get("firstSeen") or "").strip()
    if not raw:
        return False
    try:
        seen = dt.datetime.fromisoformat(raw.replace("Z", "+00:00")).date()
    except ValueError:
        try:
            seen = dt.date.fromisoformat(raw[:10])
        except ValueError:
            return False
    current = today or dt.datetime.now(dt.timezone.utc).date()
    return current - dt.timedelta(days=14) <= seen <= current + dt.timedelta(days=1)


def source_text(event: dict[str, Any]) -> str:
    sources = event.get("sources") or []
    return str(event.get("sourceName") or (sources[0].get("name") if sources and isinstance(sources[0], dict) else "") or "Official source")


def artist_lookup(artists: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    lookup: dict[str, dict[str, Any]] = {}
    for artist in artists:
        lookup[normalize(artist.get("name"))] = artist
        for alias in artist.get("aliases") or []:
            lookup.setdefault(normalize(alias), artist)
    return lookup


def event_image(event: dict[str, Any], lookup: dict[str, dict[str, Any]], base_path: str) -> str:
    artist = lookup.get(normalize(event.get("headliner") or ((event.get("artists") or [""])[0])))
    value = event.get("image") or (artist.get("imageUrl") if artist else "") or FALLBACK_IMAGE
    return local_or_remote_url(value, base_path)


def artist_page_url(name: str, base_path: str) -> str:
    return join_base_path(base_path, f"artists/{artist_slug(name)}/")


def event_page_url(event: dict[str, Any], base_path: str) -> str:
    return join_base_path(base_path, event_path(event))


def html_document(*, title: str, description: str, canonical: str, body: str, base_path: str, page: str, structured_data: list[dict[str, Any]] | None = None, preview: bool = False, image: str = "") -> str:
    robots = "noindex,nofollow" if preview else "index,follow"
    parsed_canonical = urlparse(canonical)
    origin = f"{parsed_canonical.scheme}://{parsed_canonical.netloc}"
    image_absolute = image if re.match(r"^https?://", str(image or ""), flags=re.I) else origin + (str(image) if str(image or "").startswith("/") else join_base_path(base_path, str(image or "assets/logo.png")))
    json_ld = "\n".join(
        f'<script type="application/ld+json">{json.dumps(item, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")}</script>'
        for item in (structured_data or [])
    )
    home = join_base_path(base_path, "")
    nav = (
        f'<a href="{home}">Home</a><a href="{join_base_path(base_path, "shows/")}">All Shows</a>'
        f'<a href="{join_base_path(base_path, "shows/this-month/")}">This Month</a>'
        f'<a href="{join_base_path(base_path, "festivals/")}">Festivals</a>'
        f'<a href="{join_base_path(base_path, "new-shows/")}">New Shows</a>'
        f'<a href="{join_base_path(base_path, "artists/")}">Artists</a>'
        f'<a href="{join_base_path(base_path, "submit/")}">Submit a Show</a>'
    )
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta name="robots" content="{robots}">
  <meta name="description" content="{esc(description)}">
  <meta name="theme-color" content="#080808">
  <meta property="og:type" content="website">
  <meta property="og:site_name" content="{SITE_NAME}">
  <meta property="og:title" content="{esc(title)}">
  <meta property="og:description" content="{esc(description)}">
  <meta property="og:url" content="{esc(canonical)}">
  <meta property="og:image" content="{esc(image_absolute)}">
  <meta name="twitter:card" content="summary_large_image">
  <link rel="icon" href="{join_base_path(base_path, 'assets/favicon.svg')}" type="image/svg+xml">
  <link rel="stylesheet" href="{join_base_path(base_path, 'styles.css')}?v=10.3">
  <link rel="stylesheet" href="{join_base_path(base_path, 'seo.css')}?v=1.0">
  <script src="{join_base_path(base_path, 'app.js')}?v=13.0" defer></script>
  <title>{esc(title)}</title>
  <script async src="https://www.googletagmanager.com/gtag/js?id={GA_ID}"></script>
  <script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments);}}gtag('js',new Date());gtag('config','{GA_ID}');</script>
  <link rel="canonical" href="{esc(canonical)}">
  {json_ld}
</head>
<body data-page="{esc(page)}">
<header class="site-header"><div class="header-inner"><a class="brand" href="{home}" aria-label="The Kingdom Circuit home"><img src="{join_base_path(base_path, 'assets/logo.png')}" alt="The Kingdom Circuit - Christian hip-hop, live and connected"></a><button class="menu-toggle" type="button" aria-expanded="false" aria-controls="site-menu" aria-label="Open navigation"><span></span><span></span><span></span></button></div></header>
<div class="menu-backdrop" hidden></div>
<nav class="menu-drawer" id="site-menu" aria-label="Primary navigation" aria-hidden="true"><div class="menu-drawer-head"><span>Explore Kingdom Circuit</span><button class="menu-close" type="button" aria-label="Close navigation">x</button></div><div class="menu-links">{nav}</div><p class="menu-mission">Christian hip-hop, live and connected.</p></nav>
<main>{body}</main>
<footer class="site-footer"><div><strong>The Kingdom Circuit</strong><p>Christian hip-hop, live and connected.</p></div><div class="footer-links"><a href="{join_base_path(base_path, 'shows/')}">All Shows</a><a href="{join_base_path(base_path, 'artists/')}">Artists</a><a href="{join_base_path(base_path, 'festivals/')}">Festivals</a><a href="{join_base_path(base_path, 'about/listings/')}">How We Verify</a><a href="{join_base_path(base_path, 'submit/')}">Submit a Show</a></div><p class="footer-note">Event details may change. Confirm final information with the official organizer or ticket seller before purchasing or traveling.</p><div id="notice" class="footer-status" data-calendar-status hidden></div></footer>
</body>
</html>'''


def breadcrumb(items: list[tuple[str, str]]) -> str:
    links = []
    for index, (label, url) in enumerate(items):
        if index == len(items) - 1:
            links.append(f'<span aria-current="page">{esc(label)}</span>')
        else:
            links.append(f'<a href="{esc(url)}">{esc(label)}</a>')
    return f'<nav class="seo-breadcrumbs" aria-label="Breadcrumb">{"<span aria-hidden=\"true\">/</span>".join(links)}</nav>'


def event_card(event: dict[str, Any], artists_by_name: dict[str, dict[str, Any]], base_path: str, eager: bool = False) -> str:
    image = event_image(event, artists_by_name, base_path)
    title = str(event.get("title") or "Christian hip-hop event")
    location = ", ".join(item for item in (str(event.get("city") or ""), str(event.get("state") or "")) if item) or "Location to be announced"
    artist_links = " - ".join(f'<a href="{artist_page_url(name, base_path)}">{esc(name)}</a>' for name in event.get("artists") or [])
    details = str(event.get("officialUrl") or event.get("ticketUrl") or "#")
    recent = '<span class="badge">New to Kingdom Circuit</span>' if is_new_event(event) else ""
    loading = "eager" if eager else "lazy"
    image_class = "event-artwork" if event.get("imageType") == "event_artwork" else "artist-photo"
    return f'''<article class="event-card seo-static-card">
<a class="event-media" href="{event_page_url(event, base_path)}" aria-label="View {esc(title)}"><img class="{image_class}" src="{esc(image)}" alt="{esc(title)}" loading="{loading}" decoding="async" width="900" height="900" style="object-position:{esc(event.get('imagePosition') or 'center')}" onerror="this.onerror=null;this.className='event-artwork';this.src='{join_base_path(base_path, FALLBACK_IMAGE)}';"></a>
<div class="event-content"><div class="event-main"><div class="event-badges"><span class="badge badge-gold">{'Festival' if normalize(event.get('eventType')) == 'festival' else 'Concert'}</span>{recent}</div><h3><a href="{event_page_url(event, base_path)}">{esc(title)}</a></h3><p class="artist-line">{artist_links}</p><dl class="event-meta"><div><dt>Date</dt><dd>{esc(format_date(event))}</dd></div><div><dt>Venue</dt><dd>{esc(event.get('venue') or 'Venue to be announced')}</dd></div><div><dt>Location</dt><dd>{esc(location)}</dd></div></dl></div><div class="event-footer"><a class="official-button" href="{esc(details)}" target="_blank" rel="noopener" data-official-details>Official details</a><p class="source-line">Source: {esc(source_text(event))}</p></div></div>
</article>'''


def artist_events_map(events: list[dict[str, Any]], lookup: dict[str, dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    result: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for event in events:
        for name in event.get("artists") or []:
            artist = lookup.get(normalize(name))
            key = normalize(artist.get("name") if artist else name)
            result[key].append(event)
    return result


def platform_links(artist: dict[str, Any]) -> list[tuple[str, str]]:
    links: list[tuple[str, str]] = []
    candidates = [
        ("Instagram", artist.get("instagramProfile")),
        ("Spotify", artist.get("spotifyProfile") or (f"https://open.spotify.com/artist/{artist.get('spotifyId')}" if artist.get("spotifyId") else "")),
        ("YouTube", artist.get("youtubeProfile")),
    ]
    website = artist.get("website") or artist.get("officialWebsite") or artist.get("officialProfile") or ""
    if website and not any(domain in str(website).casefold() for domain in PLATFORM_DOMAINS):
        candidates.append(("Website", website))
    for label, url in candidates:
        if url:
            links.append((label, str(url)))
    return links


def artist_card(artist: dict[str, Any], event_count: int, base_path: str) -> str:
    name = str(artist.get("name") or "Artist")
    image = artist_image(artist)
    visual = (
        f'<a class="artist-visual" href="{artist_page_url(name, base_path)}" aria-label="Open {esc(name)} profile"><img src="{esc(local_or_remote_url(image, base_path))}" alt="{esc(name)}" loading="lazy" decoding="async" width="800" height="800" referrerpolicy="no-referrer" style="object-position:{esc(artist.get("imagePosition") or "center")}"></a>'
        if image else f'<a class="artist-visual artist-visual-empty" href="{artist_page_url(name, base_path)}" aria-label="Open {esc(name)} profile"><span class="seo-artist-initial" aria-hidden="true">{esc(name[:1].upper())}</span></a>'
    )
    return f'''<article class="artist-card artist-card-text seo-static-card" data-artist-card data-search="{esc(normalize(' '.join([name, *(artist.get('aliases') or [])])))}" data-has-shows="{'true' if event_count else 'false'}">{visual}<div class="artist-card-body"><h2><a href="{artist_page_url(name, base_path)}">{esc(name)}</a></h2><p>{event_count} upcoming show{"" if event_count == 1 else "s"}</p><div class="artist-card-footer"><a class="text-link" href="{artist_page_url(name, base_path)}">Tap In</a></div></div></article>'''


def event_json_ld(event: dict[str, Any], lookup: dict[str, dict[str, Any]], base_url: str, base_path: str) -> dict[str, Any]:
    location = {
        "@type": "Place",
        "name": event.get("venue") or "Venue to be announced",
        "address": {
            "@type": "PostalAddress",
            "streetAddress": event.get("address") or "",
            "addressLocality": event.get("city") or "",
            "addressRegion": event.get("state") or "",
            "addressCountry": "US",
        },
    }
    status_map = {
        "cancelled": "https://schema.org/EventCancelled",
        "canceled": "https://schema.org/EventCancelled",
        "postponed": "https://schema.org/EventPostponed",
        "rescheduled": "https://schema.org/EventRescheduled",
    }
    status = status_map.get(normalize(event.get("status")), "https://schema.org/EventScheduled")
    artists = []
    for name in event.get("artists") or []:
        configured = lookup.get(normalize(name))
        display = configured.get("name") if configured else name
        artists.append({"@type": "MusicGroup" if normalize(configured.get("category") if configured else "") == "group" else "Person", "name": display, "url": absolute_url(base_url, artist_page_url(display, base_path))})
    official = event.get("officialUrl") or event.get("ticketUrl") or absolute_url(base_url, event_page_url(event, base_path))
    data: dict[str, Any] = {
        "@context": "https://schema.org",
        "@type": "MusicEvent",
        "name": event.get("title") or "Christian hip-hop event",
        "startDate": event.get("startDate"),
        "eventStatus": status,
        "eventAttendanceMode": "https://schema.org/OfflineEventAttendanceMode",
        "url": absolute_url(base_url, event_page_url(event, base_path)),
        "location": location,
        "description": f"Verified Christian hip-hop event featuring {', '.join(event.get('artists') or []) or 'CHH artists'} at {event.get('venue') or 'a U.S. venue'} in {event.get('city') or ''}, {event.get('state') or ''}.",
        "image": [absolute_url(base_url, event_image(event, lookup, base_path)) if not re.match(r"^https?://", event_image(event, lookup, base_path)) else event_image(event, lookup, base_path)],
        "performer": artists,
        "offers": {"@type": "Offer", "url": official, "availability": "https://schema.org/InStock"},
    }
    if event.get("endDate"):
        data["endDate"] = event["endDate"]
    return data


def artist_json_ld(artist: dict[str, Any], base_url: str, base_path: str) -> dict[str, Any]:
    data: dict[str, Any] = {
        "@context": "https://schema.org",
        "@type": "MusicGroup" if normalize(artist.get("category")) == "group" else "Person",
        "name": artist.get("name"),
        "url": absolute_url(base_url, artist_page_url(str(artist.get("name")), base_path)),
        "sameAs": [url for _, url in platform_links(artist)],
    }
    if artist_image(artist):
        image = local_or_remote_url(artist_image(artist), base_path)
        data["image"] = image if re.match(r"^https?://", image) else absolute_url(base_url, image)
    return data


def write_page(output: Path, relative: str, content: str) -> None:
    path = output / relative.strip("/") / "index.html"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def build_artist_pages(output: Path, artists: list[dict[str, Any]], events: list[dict[str, Any]], base_url: str, base_path: str, preview: bool) -> list[str]:
    lookup = artist_lookup(artists)
    by_artist = artist_events_map(events, lookup)
    paths: list[str] = []
    for artist in artists:
        if artist.get("enabled") is False:
            continue
        name = str(artist.get("name") or "").strip()
        if not name:
            continue
        page_path = f"artists/{artist_slug(name)}"
        canonical_path = artist_page_url(name, base_path)
        canonical = absolute_url(base_url, canonical_path)
        shows = by_artist.get(normalize(name), [])
        image = artist_image(artist)
        visual = f'<div class="profile-visual"><img src="{esc(local_or_remote_url(image, base_path))}" alt="Christian hip-hop artist {esc(name)}" decoding="async" width="900" height="900" referrerpolicy="no-referrer" style="object-position:{esc(artist.get("imagePosition") or "center")}"></div>' if image else ""
        note = "" if image else '<p class="profile-image-note">Artist image pending direct-file verification.</p>'
        links = "".join(f'<a class="profile-platform-card" href="{esc(url)}" target="_blank" rel="noopener"><span class="profile-platform-label">{esc(label)}</span><span class="profile-platform-status">Open verified {esc(label)} profile</span></a>' for label, url in platform_links(artist))
        event_markup = "".join(event_card(event, lookup, base_path, eager=index < 2) for index, event in enumerate(shows)) or '<div class="empty-panel">No upcoming U.S. shows are currently confirmed.</div>'
        body = f'''{breadcrumb([("Home", join_base_path(base_path, "")), ("Artists", join_base_path(base_path, "artists/")), (name, canonical_path)])}
<section class="profile-hero{' profile-hero-no-image' if not image else ''}">{visual}<div><p class="eyebrow">Artist profile</p><h1>{esc(name)}</h1>{note}<div class="profile-platforms">{links}</div><p class="profile-count">{len(shows)} upcoming U.S. show{"" if len(shows) == 1 else "s"} currently listed.</p></div></section>
<section class="calendar"><div class="calendar-heading"><div><p class="eyebrow">Verified listings</p><h2>Upcoming {esc(name)} Shows</h2></div><p class="results-count">{len(shows)} shows</p></div><div class="event-grid">{event_markup}</div></section>'''
        description = f"Find verified {name} tour dates, upcoming Christian hip-hop shows, Spotify, YouTube, Instagram, and official artist links."
        page = html_document(title=f"{name} Tour Dates, Shows & Official Links | The Kingdom Circuit", description=description, canonical=canonical, body=body, base_path=base_path, page="artist-static", structured_data=[artist_json_ld(artist, base_url, base_path)], preview=preview, image=(local_or_remote_url(image, base_path) if image else ""))
        write_page(output, page_path, page)
        paths.append(canonical_path)
    return paths


def build_event_pages(output: Path, events: list[dict[str, Any]], artists: list[dict[str, Any]], base_url: str, base_path: str, preview: bool) -> list[str]:
    lookup = artist_lookup(artists)
    paths: list[str] = []
    for event in events:
        path = event_path(event).strip("/")
        canonical_path = event_page_url(event, base_path)
        canonical = absolute_url(base_url, canonical_path)
        title = str(event.get("title") or "Christian Hip-Hop Event")
        location = ", ".join(item for item in (str(event.get("city") or ""), str(event.get("state") or "")) if item) or "the United States"
        image = event_image(event, lookup, base_path)
        artist_links = " - ".join(f'<a href="{artist_page_url(name, base_path)}">{esc(name)}</a>' for name in event.get("artists") or [])
        state_code = str(event.get("state") or "").upper()
        state_path = join_base_path(base_path, f"shows/{slugify(STATE_NAMES.get(state_code, state_code))}/") if state_code else join_base_path(base_path, "shows/")
        body = f'''{breadcrumb([("Home", join_base_path(base_path, "")), ("Shows", join_base_path(base_path, "shows/")), (STATE_NAMES.get(state_code, state_code) or "Event", state_path), (title, canonical_path)])}
<article class="event-detail"><div class="event-detail-media"><img class="{'event-artwork' if event.get('imageType') == 'event_artwork' else 'artist-photo'}" src="{esc(image)}" alt="{esc(title)}" width="1000" height="1000" style="object-position:{esc(event.get('imagePosition') or 'center')}" onerror="this.onerror=null;this.className='event-artwork';this.src='{join_base_path(base_path, FALLBACK_IMAGE)}';"></div><div class="event-detail-copy"><p class="eyebrow">{'Festival' if normalize(event.get('eventType')) == 'festival' else 'Concert'}</p><h1>{esc(title)}</h1><p class="artist-line">{artist_links}</p><dl class="detail-list"><div><dt>Date</dt><dd>{esc(format_date(event))}</dd></div><div><dt>Venue</dt><dd>{esc(event.get('venue') or 'Venue to be announced')}</dd></div><div><dt>Location</dt><dd>{esc(location)}</dd></div>{f'<div><dt>Price</dt><dd>{esc(event.get("price"))}</dd></div>' if event.get('price') else ''}<div><dt>Source</dt><dd>{esc(source_text(event))}</dd></div>{f'<div><dt>Last verified</dt><dd>{esc(event.get("lastVerified"))}</dd></div>' if event.get('lastVerified') else ''}</dl><a class="primary-button" href="{esc(event.get('officialUrl') or event.get('ticketUrl') or '#')}" target="_blank" rel="noopener" data-official-details>Official details</a><p class="disclaimer">Event details, availability, pricing, and lineups may change. Confirm final information with the official organizer or ticket provider before purchasing or traveling.</p></div></article>
<section class="seo-related"><h2>Keep exploring</h2><div class="seo-link-row"><a href="{state_path}">More CHH shows in {esc(STATE_NAMES.get(state_code, state_code) or 'this area')}</a><a href="{join_base_path(base_path, 'artists/')}">Browse CHH artists</a><a href="{join_base_path(base_path, 'submit/')}?type=correction&amp;event={esc(title)}">Report a correction</a></div></section>'''
        description = f"{title} in {location}. View the verified date, venue, lineup, and official event or ticket source."
        page = html_document(title=f"{title} | The Kingdom Circuit", description=description, canonical=canonical, body=body, base_path=base_path, page="event-static", structured_data=[event_json_ld(event, lookup, base_url, base_path)], preview=preview, image=(image if re.match(r"^https?://", image) else absolute_url(base_url, image)))
        write_page(output, path, page)
        paths.append(canonical_path)
    return paths


def listing_page(*, title: str, heading: str, eyebrow: str, intro: str, canonical_path: str, events: list[dict[str, Any]], artists: list[dict[str, Any]], base_url: str, base_path: str, preview: bool, breadcrumbs: list[tuple[str, str]]) -> str:
    lookup = artist_lookup(artists)
    cards = "".join(event_card(event, lookup, base_path, eager=index < 2) for index, event in enumerate(events)) or '<div class="empty-panel">No upcoming verified shows are currently listed.</div>'
    body = f'''{breadcrumb(breadcrumbs)}<section class="page-hero hero-compact"><p class="eyebrow">{esc(eyebrow)}</p><h1>{esc(heading)}</h1><p class="hero-text">{esc(intro)}</p></section><section class="calendar"><div class="calendar-heading"><div><p class="eyebrow">Verified listings</p><h2>Upcoming Shows</h2></div><p class="results-count">{len(events)} shows</p></div><div class="event-grid">{cards}</div></section>'''
    canonical = absolute_url(base_url, canonical_path)
    data = {"@context":"https://schema.org","@type":"CollectionPage","name":heading,"url":canonical,"description":intro,"mainEntity":{"@type":"ItemList","numberOfItems":len(events),"itemListElement":[{"@type":"ListItem","position":index+1,"url":absolute_url(base_url,event_page_url(event,base_path)),"name":event.get("title")} for index,event in enumerate(events)]}}
    return html_document(title=title, description=intro, canonical=canonical, body=body, base_path=base_path, page="seo-listing", structured_data=[data], preview=preview)


def build_discovery_pages(output: Path, events: list[dict[str, Any]], artists: list[dict[str, Any]], base_url: str, base_path: str, preview: bool, min_city_events: int) -> list[str]:
    paths: list[str] = []
    by_state: dict[str, list[dict[str, Any]]] = defaultdict(list)
    by_city: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    by_month: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for event in events:
        state = str(event.get("state") or "").upper()
        city = str(event.get("city") or "").strip()
        if state:
            by_state[state].append(event)
            if city:
                by_city[(state, city)].append(event)
        start = str(event.get("startDate") or "")
        if re.match(r"^\d{4}-\d{2}", start):
            by_month[start[:7]].append(event)

    for state, state_events in sorted(by_state.items(), key=lambda item: STATE_NAMES.get(item[0], item[0])):
        state_name = STATE_NAMES.get(state, state)
        state_slug = slugify(state_name)
        canonical_path = join_base_path(base_path, f"shows/{state_slug}/")
        page = listing_page(title=f"Christian Hip-Hop Concerts in {state_name} | The Kingdom Circuit", heading=f"Christian Hip-Hop Shows in {state_name}", eyebrow="CHH by state", intro=f"Find verified upcoming Christian hip-hop concerts, festivals, and tour dates across {state_name}.", canonical_path=canonical_path, events=state_events, artists=artists, base_url=base_url, base_path=base_path, preview=preview, breadcrumbs=[("Home", join_base_path(base_path, "")), ("Shows", join_base_path(base_path, "shows/")), (state_name, canonical_path)])
        write_page(output, f"shows/{state_slug}", page)
        paths.append(canonical_path)

    for (state, city), city_events in sorted(by_city.items()):
        if len(city_events) < min_city_events:
            continue
        state_name = STATE_NAMES.get(state, state)
        state_slug, city_slug = slugify(state_name), slugify(city)
        canonical_path = join_base_path(base_path, f"shows/{state_slug}/{city_slug}/")
        page = listing_page(title=f"Christian Hip-Hop Concerts in {city}, {state} | The Kingdom Circuit", heading=f"Christian Hip-Hop Shows in {city}", eyebrow="CHH near you", intro=f"Find verified upcoming Christian hip-hop concerts and festivals in {city}, {state_name}.", canonical_path=canonical_path, events=city_events, artists=artists, base_url=base_url, base_path=base_path, preview=preview, breadcrumbs=[("Home", join_base_path(base_path, "")), ("Shows", join_base_path(base_path, "shows/")), (state_name, join_base_path(base_path, f"shows/{state_slug}/")), (city, canonical_path)])
        write_page(output, f"shows/{state_slug}/{city_slug}", page)
        paths.append(canonical_path)

    for month, month_events in sorted(by_month.items()):
        year, month_number = (int(part) for part in month.split("-"))
        label = f"{calendar.month_name[month_number]} {year}"
        month_slug = f"{calendar.month_name[month_number].casefold()}-{year}"
        canonical_path = join_base_path(base_path, f"shows/{month_slug}/")
        page = listing_page(title=f"Christian Hip-Hop Concerts in {label} | The Kingdom Circuit", heading=f"Christian Hip-Hop Shows in {label}", eyebrow="CHH by month", intro=f"Browse verified Christian hip-hop concerts, festivals, and tour dates scheduled for {label}.", canonical_path=canonical_path, events=month_events, artists=artists, base_url=base_url, base_path=base_path, preview=preview, breadcrumbs=[("Home", join_base_path(base_path, "")), ("Shows", join_base_path(base_path, "shows/")), (label, canonical_path)])
        write_page(output, f"shows/{month_slug}", page)
        paths.append(canonical_path)
    return paths


def build_about_page(output: Path, base_url: str, base_path: str, preview: bool) -> str:
    canonical_path = join_base_path(base_path, "about/listings/")
    body = f'''{breadcrumb([("Home", join_base_path(base_path, "")), ("How We Verify", canonical_path)])}<section class="page-hero hero-compact"><p class="eyebrow">About our listings</p><h1>How The Kingdom Circuit Verifies CHH Shows</h1><p class="hero-text">Kingdom Circuit prioritizes official information so fans can discover Christian hip-hop shows without sorting through duplicate, uncertain, or unrelated listings.</p></section><section class="seo-methodology"><h2>What qualifies</h2><p>We publish U.S. music performances involving monitored Christian hip-hop artists and groups. Festival artists are listed only when an official lineup names them.</p><h2>Source priority</h2><ol><li>Official event or festival</li><li>Venue or ticket seller</li><li>Artist, label, promoter, or official social post</li><li>Aggregator</li></ol><h2>How duplicates are handled</h2><p>Listings merge when the date, city, venue, and artist identity strongly match. The stronger record is retained and useful source links are preserved.</p><h2>Corrections</h2><p>Dates, venues, availability, and lineups can change. Use the official source before purchasing or traveling, and <a href="{join_base_path(base_path, 'submit/')}?type=correction">send a correction</a> when something changes.</p></section>'''
    data = {"@context":"https://schema.org","@type":"AboutPage","name":"How The Kingdom Circuit Verifies CHH Shows","url":absolute_url(base_url, canonical_path),"description":"The Kingdom Circuit listing standards, source priorities, duplicate handling, and correction process."}
    page = html_document(title="How We Verify Christian Hip-Hop Shows | The Kingdom Circuit", description="Learn how The Kingdom Circuit verifies Christian hip-hop concerts, prioritizes official sources, merges duplicates, and handles corrections.", canonical=absolute_url(base_url, canonical_path), body=body, base_path=base_path, page="about-listings", structured_data=[data], preview=preview)
    write_page(output, "about/listings", page)
    return canonical_path


def inject_before_head_close(text: str, markup: str) -> str:
    return text.replace("</head>", f"{markup}\n</head>", 1) if markup not in text else text


def apply_base_path_to_html(text: str, base_path: str) -> str:
    if base_path == "/":
        return text
    prefix = base_path.rstrip("/")
    return re.sub(r'(?P<attr>\b(?:href|src|action)=)(?P<quote>["\'])/(?!/)', rf'\g<attr>\g<quote>{prefix}/', text)


def replace_div_contents(text: str, data_attribute: str, content: str) -> str:
    opening = re.search(
        rf'<div\b(?=[^>]*\b{re.escape(data_attribute)}(?:\s|=|>))[^>]*>',
        text,
        flags=re.I,
    )
    if not opening:
        return text
    depth = 1
    for token in re.finditer(r'<div\b[^>]*>|</div\s*>', text[opening.end():], flags=re.I):
        raw = token.group(0).casefold()
        if raw.startswith('</div'):
            depth -= 1
            if depth == 0:
                closing_start = opening.end() + token.start()
                return text[:opening.end()] + content + text[closing_start:]
        else:
            depth += 1
    raise ValueError(f"Could not locate closing div for {data_attribute}")


def patch_core_pages(output: Path, events: list[dict[str, Any]], artists: list[dict[str, Any]], base_url: str, base_path: str, preview: bool) -> None:
    lookup = artist_lookup(artists)
    by_artist = artist_events_map(events, lookup)
    active_states = sorted({str(event.get("state") or "").upper() for event in events if event.get("state")}, key=lambda code: STATE_NAMES.get(code, code))
    active_months = sorted({str(event.get("startDate") or "")[:7] for event in events if re.match(r"^\d{4}-\d{2}", str(event.get("startDate") or ""))})
    state_links = "".join(f'<a href="{join_base_path(base_path, f"shows/{slugify(STATE_NAMES.get(code, code))}/")}">{esc(STATE_NAMES.get(code, code))}</a>' for code in active_states)
    month_links = ""
    for value in active_months:
        year, month_num = (int(part) for part in value.split("-"))
        label = f"{calendar.month_name[month_num]} {year}"
        month_links += f'<a href="{join_base_path(base_path, f"shows/{calendar.month_name[month_num].casefold()}-{year}/")}">{esc(label)}</a>'
    browse = f'<section class="seo-browse" aria-labelledby="seo-browse-title"><div><p class="eyebrow">Browse the circuit</p><h2 id="seo-browse-title">Find CHH Shows by Place or Month</h2></div><div class="seo-browse-group"><h3>By state</h3><div class="seo-link-row">{state_links}</div></div><div class="seo-browse-group"><h3>By month</h3><div class="seo-link-row">{month_links}</div></div></section>'

    core_files = [
        "index.html", "shows/index.html", "shows/this-month/index.html", "festivals/index.html",
        "new-shows/index.html", "artists/index.html", "artists/profile/index.html",
        "event/index.html", "submit/index.html", "404.html",
    ]
    for relative in core_files:
        path = output / relative
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        text = apply_base_path_to_html(text, base_path)
        text = re.sub(r'app\.js\?v=[^"\']+', "app.js?v=13.0", text)
        seo_href = join_base_path(base_path, "seo.css") + "?v=1.0"
        if "seo.css" not in text:
            text = re.sub(r'(<link\s+rel=["\']stylesheet["\'][^>]*styles\.css[^>]*>)', rf'\1\n  <link rel="stylesheet" href="{seo_href}">', text, count=1)
        if preview:
            text = re.sub(r'<meta\s+name=["\']robots["\']\s+content=["\'][^"\']*["\']\s*/?>', '<meta name="robots" content="noindex,nofollow">', text, count=1, flags=re.I)
        elif relative in {"artists/profile/index.html", "event/index.html"}:
            legacy_robots = '<meta name="robots" content="noindex,follow">'
            if re.search(r'<meta\s+name=["\']robots["\']', text, flags=re.I):
                text = re.sub(r'<meta\s+name=["\']robots["\']\s+content=["\'][^"\']*["\']\s*/?>', legacy_robots, text, count=1, flags=re.I)
            else:
                text = inject_before_head_close(text, legacy_robots)
        if "How We Verify" not in text:
            text = text.replace('<a href="' + join_base_path(base_path, 'submit/') + '">Submit a Show</a></div>', '<a href="' + join_base_path(base_path, 'about/listings/') + '">How We Verify</a><a href="' + join_base_path(base_path, 'submit/') + '">Submit a Show</a></div>')
        path.write_text(text, encoding="utf-8")

    # Pre-render all-shows and home event grids. JavaScript may replace these, but crawlers and no-JS users get complete content.
    mode_by_file = {
        "index.html": events,
        "shows/index.html": events,
        "festivals/index.html": [event for event in events if normalize(event.get("eventType")) == "festival"],
        "new-shows/index.html": [event for event in events if is_new_event(event)],
    }
    today = dt.date.today()
    mode_by_file["shows/this-month/index.html"] = [event for event in events if str(event.get("startDate") or "").startswith(today.strftime("%Y-%m"))]
    for relative, page_events in mode_by_file.items():
        path = output / relative
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        cards = "".join(event_card(event, lookup, base_path, eager=index < 2) for index, event in enumerate(page_events))
        text = replace_div_contents(text, "data-event-grid", cards)
        text = re.sub(r'(data-results-count[^>]*>).*?(</p>)', rf'\g<1>{len(page_events)} shows\2', text, count=1, flags=re.S)
        if relative == "shows/index.html" and "seo-browse-title" not in text:
            text = text.replace("</main>", browse + "</main>", 1)
        path.write_text(text, encoding="utf-8")

    artists_path = output / "artists/index.html"
    if artists_path.is_file():
        text = artists_path.read_text(encoding="utf-8")
        cards = "".join(artist_card(artist, len(by_artist.get(normalize(artist.get("name")), [])), base_path) for artist in artists if artist.get("enabled") is not False)
        text = replace_div_contents(text, "data-artist-grid", cards)
        text = re.sub(r'(data-artist-count[^>]*>).*?(</p>)', rf'\g<1>{len(artists)} artists\2', text, count=1, flags=re.S)
        artists_path.write_text(text, encoding="utf-8")


def patch_app_js(output: Path, base_path: str) -> None:
    path = output / "app.js"
    if not path.is_file():
        return
    text = path.read_text(encoding="utf-8")
    text = re.sub(r'const BASE = ["\'][^"\']*["\'];', f"const BASE = {json.dumps(base_path)};", text, count=1)
    text = re.sub(r'const SITE_BUILD = ["\']([^"\']*)["\'];', lambda match: f'const SITE_BUILD = "{match.group(1)}-seo-static-v1";', text, count=1)
    helper = r'''
function seoSlug(value) {
  return String(value || "").normalize("NFKD").replace(/[\u0300-\u036f]/g, "").toLocaleLowerCase().replace(/&/g, " and ").replace(/[’']/g, "").replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "").replace(/-{2,}/g, "-") || "item";
}
function seoHash(value) {
  let hash = 0x811c9dc5;
  for (const character of String(value || "")) { hash ^= character.charCodeAt(0); hash = Math.imul(hash, 0x01000193) >>> 0; }
  return hash.toString(16).padStart(8, "0");
}
function seoEventSlug(event) {
  const stem = seoSlug([event?.title, event?.city, event?.state, event?.startDate].filter(Boolean).join("-"));
  const identity = event?.id || [event?.title, event?.city, event?.state, event?.startDate, event?.venue].join("|");
  return `${stem.slice(0, 92).replace(/-+$/, "")}-${seoHash(identity).slice(0, 6)}`;
}
'''.strip()
    if "function seoSlug(" not in text:
        text = text.replace("function eventDetailUrl(event) {", helper + "\nfunction eventDetailUrl(event) {", 1)
    text = re.sub(r'function eventDetailUrl\(event\)\s*\{.*?\n\}', 'function eventDetailUrl(event) {\n  const section = normalize(event?.eventType) === "festival" ? "festivals" : "events";\n  return `${BASE}${section}/${seoEventSlug(event)}/`;\n}', text, count=1, flags=re.S)
    text = re.sub(r'function artistProfileUrl\(name\)\s*\{.*?\n\}', 'function artistProfileUrl(name) {\n  return `${BASE}artists/${seoSlug(name)}/`;\n}', text, count=1, flags=re.S)
    text = re.sub(r'ensureCanonical\(`\$\{location\.origin\}\$\{BASE\}artists/profile/\?name=\$\{encodeURIComponent\(artist\.name\)\}`\);', 'ensureCanonical(`${location.origin}${artistProfileUrl(artist.name)}`);', text)
    text = re.sub(r'ensureCanonical\(`\$\{location\.origin\}\$\{BASE\}event/\?id=\$\{encodeURIComponent\(event\.id\)\}`\);', 'ensureCanonical(`${location.origin}${eventDetailUrl(event)}`);', text)
    path.write_text(text, encoding="utf-8")


def build_sitemap(output: Path, base_url: str, paths: Iterable[str]) -> None:
    unique = sorted(set(paths))
    # Omit lastmod rather than claim every generated page changed on every daily build.
    entries = "\n".join(f"  <url><loc>{esc(absolute_url(base_url, path))}</loc></url>" for path in unique)
    sitemap = f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{entries}\n</urlset>\n'
    (output / "sitemap.xml").write_text(sitemap, encoding="utf-8")
    (output / "robots.txt").write_text(f"User-agent: *\nAllow: /\n\nSitemap: {base_url.rstrip('/')}/sitemap.xml\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", default=".")
    parser.add_argument("--output", default="_site")
    parser.add_argument("--base-url", default="https://kingdomcircuit.com")
    parser.add_argument("--base-path", default="/")
    parser.add_argument("--preview", action="store_true")
    parser.add_argument("--min-city-events", type=int, default=2)
    args = parser.parse_args()
    source = Path(args.source).resolve()
    output = Path(args.output).resolve()
    base_path = normalize_base_path(args.base_path)
    base_url = args.base_url.rstrip("/")

    if not output.is_dir():
        raise SystemExit(f"Output directory does not exist: {output}")
    app_source = (source / "app.js").read_text(encoding="utf-8")
    base_artists = json_load(source / "config/artists.json", [])
    if not base_artists:
        base_artists = json_load(source / "artists.json", [])
    artists = merge_artists(base_artists, app_source)
    primary = json_load(source / "events.json", [])
    supplemental = json_load(source / "supplemental-events.json", [])
    events = merge_events(primary if isinstance(primary, list) else [], supplemental if isinstance(supplemental, list) else [], artists)
    if len(artists) < 250:
        raise SystemExit(f"Artist roster unexpectedly small: {len(artists)}")
    if not events:
        raise SystemExit("No event data was available for the SEO build")

    # The source data files copied into the artifact remain untouched. Only presentation and discoverability change.
    shutil.copy2(source / "seo.css", output / "seo.css")
    patch_core_pages(output, events, artists, base_url, base_path, args.preview)
    patch_app_js(output, base_path)

    generated_paths: list[str] = [
        join_base_path(base_path, ""), join_base_path(base_path, "shows/"),
        join_base_path(base_path, "shows/this-month/"), join_base_path(base_path, "festivals/"),
        join_base_path(base_path, "new-shows/"), join_base_path(base_path, "artists/"),
        join_base_path(base_path, "submit/"),
    ]
    generated_paths += build_artist_pages(output, artists, events, base_url, base_path, args.preview)
    generated_paths += build_event_pages(output, events, artists, base_url, base_path, args.preview)
    generated_paths += build_discovery_pages(output, events, artists, base_url, base_path, args.preview, args.min_city_events)
    generated_paths.append(build_about_page(output, base_url, base_path, args.preview))
    build_sitemap(output, base_url, generated_paths)

    manifest = {
        "schemaVersion": 1,
        "builtAt": dt.datetime.now(dt.timezone.utc).isoformat(),
        "baseUrl": base_url,
        "basePath": base_path,
        "preview": args.preview,
        "artistCount": len(artists),
        "verifiedArtistCount": sum(1 for artist in artists if artist.get("sourceRegistryVerified") is True),
        "eventCount": len(events),
        "artistPageCount": len([path for path in generated_paths if "/artists/" in path and path.rstrip("/") != join_base_path(base_path, "artists").rstrip("/")]),
        "eventPageCount": len([path for path in generated_paths if "/events/" in path or ("/festivals/" in path and path.rstrip("/") != join_base_path(base_path, "festivals").rstrip("/"))]),
        "sitemapUrlCount": len(set(generated_paths)),
        "sourceFilesPreserved": ["events.json", "config/artists.json", "supplemental-events.json", "run-status.json"],
    }
    (output / "seo-build-manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
