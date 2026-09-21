#!/usr/bin/env python3
"""Apply the mobile-first Kingdom Circuit redesign to a captured test artifact.

The test deployment is rebuilt from the published production site every day.  This
overlay intentionally changes presentation and test-only submission UX after the
live artifact has passed its exact-mirror checks.
"""

from __future__ import annotations

import datetime as dt
import html
import json
import pathlib
import re
import shutil
import sys
from typing import Iterable


TEST_BASE = "/kingdom-circuit-test/"
INSTAGRAM_URL = "https://www.instagram.com/thekingdomcircuit/"
FORM_ENDPOINT = "https://formspree.io/f/mljreawj"
VERSION = "mobile-first-test-redesign-v1"


def clean_text(value: str) -> str:
    value = re.sub(r"<[^>]+>", " ", value)
    return " ".join(html.unescape(value).split())


def attribute(fragment: str, name: str) -> str:
    match = re.search(rf"\b{re.escape(name)}=(?:\"([^\"]*)\"|'([^']*)')", fragment)
    if not match:
        return ""
    return html.unescape(match.group(1) if match.group(1) is not None else match.group(2))


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


def full_header(relative: pathlib.PurePath) -> str:
    follow_icon = instagram_icon(token="follow")
    button_icon = instagram_icon(token="button")
    return f'''<header class="kc-rd-header">
  <div class="kc-rd-followbar">
    <a class="kc-rd-follow-link" href="{INSTAGRAM_URL}" target="_blank" rel="noopener" aria-label="Follow The Kingdom Circuit on Instagram (opens in new tab)">
      {follow_icon}<span>Follow @thekingdomcircuit</span><span aria-hidden="true">↗</span>
    </a>
    <span class="kc-rd-follow-tagline">Christian hip-hop, live and connected</span>
  </div>
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
  <div class="kc-rd-primary">
    <a class="kc-rd-brand" href="{TEST_BASE}" aria-label="Kingdom Circuit home">
      <img src="{TEST_BASE}assets/logo-wordmark.svg?v=1" alt="Kingdom Circuit">
    </a>
    <a class="kc-rd-follow-link" href="{INSTAGRAM_URL}" target="_blank" rel="noopener" aria-label="Follow The Kingdom Circuit on Instagram (opens in new tab)">
      {instagram_icon(token="profile")}<span>Follow @thekingdomcircuit</span><span aria-hidden="true">↗</span>
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
    css = f'{TEST_BASE}assets/kc-redesign-v1.css?v=1'
    js = f'{TEST_BASE}assets/kc-redesign-v1.js?v=1'
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
    document = document[: match.start()] + hero + document[match.end() :]
    document = re.sub(
        r'<p class="eyebrow">\s*Verified listings\s*</p>\s*',
        "",
        document,
        count=1,
        flags=re.I | re.S,
    )
    return document


def transform_directory(document: str, artist_count: int) -> str:
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
  <div>
    <h1 id="kc-rd-directory-title" class="sr-only">Christian Hip-Hop Artists</h1>
    <p class="kc-rd-directory-count"><strong>{artist_count}</strong><span>CHH Artists Tracked</span></p>
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
    return document


def event_metadata(card: str) -> dict[str, str]:
    opening = card[: card.find(">") + 1]
    date_iso = attribute(opening, "data-date")
    href_match = re.search(r'<h3>\s*<a\b[^>]*href="([^"]+)"', card, re.S)
    if not href_match:
        href_match = re.search(r'<a\b[^>]*href="([^"]+)"', card, re.S)
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
        "date": date_text,
        "month": month,
        "day": day,
        "venue": values.get("venue", "Venue to be announced"),
        "location": values.get("location", "Location to be announced"),
        "time": time,
    }


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
      <div class="kc-rd-profile-visual">{image_html}</div>
      <h1 class="kc-rd-profile-name" id="kc-rd-artist-name">{artist_escaped}</h1>
    </section>
    {actions_html}
    {next_html}
    <section class="kc-rd-profile-shows" aria-labelledby="kc-rd-shows-title">
      <div class="kc-rd-profile-section-title"><h2 id="kc-rd-shows-title">All {artist_escaped} Shows</h2><span>{len(events)} upcoming</span></div>
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
      <input type="hidden" name="environment" value="test">
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
        and "seo-artist-profile" in document
    )


def copy_assets(site: pathlib.Path, repo: pathlib.Path) -> None:
    asset_dir = site / "assets"
    asset_dir.mkdir(parents=True, exist_ok=True)
    for filename in ("kc-redesign-v1.css", "kc-redesign-v1.js"):
        source = repo / "test-overrides" / filename
        if not source.is_file():
            raise ValueError(f"missing redesign asset: {source}")
        shutil.copy2(source, asset_dir / filename)


def iter_html(site: pathlib.Path) -> Iterable[pathlib.Path]:
    return sorted(path for path in site.rglob("*.html") if path.is_file())


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: apply_test_redesign.py SITE_ROOT")
    site = pathlib.Path(sys.argv[1]).resolve()
    repo = pathlib.Path(__file__).resolve().parent.parent
    home_path = site / "index.html"
    directory_path = site / "artists" / "index.html"
    if not home_path.is_file() or not directory_path.is_file():
        raise SystemExit("captured home page or artists directory is missing")

    home_source = home_path.read_text(encoding="utf-8")
    directory_source = directory_path.read_text(encoding="utf-8")
    show_count = len(re.findall(r'\bdata-event-card(?:\s|>)', home_source))
    artist_count = len(re.findall(r'\bdata-artist-card(?:\s|>)', directory_source))
    if show_count < 1 or artist_count < 1:
        raise SystemExit(f"invalid published counts: shows={show_count}, artists={artist_count}")

    copy_assets(site, repo)
    create_artist_submit_page(site)

    profile_pages = 0
    profile_show_rows = 0
    profile_pages_with_past = 0
    header_pages = 0
    for page in iter_html(site):
        relative = page.relative_to(site)
        document = page.read_text(encoding="utf-8")
        profile = is_profile_page(relative, document)
        if relative.as_posix() == "index.html":
            document = transform_home(document, show_count, artist_count)
        elif relative.as_posix() == "artists/index.html":
            document = transform_directory(document, artist_count)
        if profile:
            document, event_rows, has_past = transform_artist_profile(document)
            profile_pages += 1
            profile_show_rows += event_rows
            profile_pages_with_past += int(has_past)
        document = replace_legacy_header(document, profile_header() if profile else full_header(relative))
        document = inject_assets(document)
        page.write_text(document, encoding="utf-8")
        header_pages += 1

    mirror_path = site / "test-live-mirror-manifest.json"
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
        "source": "published live-site capture after exact baseline verification",
        "testBase": TEST_BASE,
        "showCount": show_count,
        "artistCount": artist_count,
        "profilePageCount": profile_pages,
        "profileShowRowCount": profile_show_rows,
        "profilePagesWithPastShows": profile_pages_with_past,
        "headerPageCount": header_pages,
        "artistSubmissionPath": f"{TEST_BASE}submit/artist/",
        "productionChanged": False,
    }
    (site / "test-redesign-manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
