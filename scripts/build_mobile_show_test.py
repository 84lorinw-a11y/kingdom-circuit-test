"""Build a separate mobile calendar experiment from the final mirrored pages."""
from __future__ import annotations

import argparse
import datetime as dt
import html
import json
from pathlib import Path
import re
import shutil
from urllib.parse import unquote, urlsplit
from zoneinfo import ZoneInfo

from apply_test_redesign import attribute, clean_text, event_cards, inject_assets

BASE = "/kingdom-circuit-test/"
ROUTE = "test-all-shows/"
FEED_ROUTE = "test-show-feed/"


def match_text(pattern, source, default=""):
    match = re.search(pattern, source, re.S | re.I)
    return match.group(1) if match else default


def field(source, label):
    return clean_text(match_text(r'<dt>\s*' + label + r'\s*</dt>\s*<dd>(.*?)</dd>', source))


def image_fields(source):
    image = match_text(r'(<img\b[^>]*>)', source)
    position = match_text(r'object-position\s*:\s*([^;"\']+)', attribute(image, "style"), "center")
    return {"image": attribute(image, "src"), "srcset": attribute(image, "srcset"),
            "artwork": "event-artwork" in attribute(image, "class"),
            "position": position if re.fullmatch(r"[a-z0-9.% -]+", position, re.I) else "center"}


def billing(source):
    line = match_text(r'<p\b[^>]*class="artist-line"[^>]*>(.*?)</p>', source)
    names = [name.strip() for name in clean_text(line).split(" - ") if name.strip()]
    links = {}
    for anchor in re.findall(r'<a\b[^>]*>.*?</a>', line, re.S):
        href = attribute(anchor, "href")
        if href.startswith(BASE + "artists/"):
            links[clean_text(anchor)] = href
    return names, links


def host_label(source):
    return clean_text(match_text(r'<p\b[^>]*class="host-line"[^>]*>(.*?)</p>', source))


def safe_page(site, href):
    if not href.startswith(BASE + "event/"):
        raise ValueError(f"Not a test event link: {href}")
    relative = href[len(BASE):].strip("/")
    if ".." in relative.split("/"):
        raise ValueError("Invalid event path")
    return site / relative / "index.html"


def valid_official_url(site, url):
    parsed = urlsplit(html.unescape(url))
    if parsed.scheme in ('https', 'http') and parsed.netloc:
        return True
    # Some artist-submitted shows use the saved, approved flyer as their source.
    # Preserve that link without allowing arbitrary relative URLs or traversal.
    path = unquote(parsed.path)
    if parsed.scheme or parsed.netloc or not path.startswith(BASE + 'assets/'):
        return False
    candidate = (site / path[len(BASE):]).resolve()
    return (candidate.is_relative_to((site / 'assets').resolve())
            and candidate.suffix.lower() in {'.jpg', '.jpeg', '.png', '.webp'}
            and candidate.is_file())


def read_detail(site, href):
    source = safe_page(site, href).read_text()
    image_block = match_text(r'<div class="event-detail-media">(.*?)</div>', source)
    original = match_text(r'(<a\b[^>]*class="event-image-enlarge"[^>]*>)', image_block)
    official = next((attribute(a, "href") for a in re.findall(r'<a\b[^>]*>.*?</a>', source, re.S)
                     if clean_text(a) == "Official details"), "")
    if official and not valid_official_url(site, official):
        raise ValueError("Unexpected official URL")
    schemas = [json.loads(s) for s in re.findall(r'<script type="application/ld\+json">(.*?)</script>', source, re.S)]
    schema = next((s for s in schemas if s.get("@type") == "MusicEvent"), {})
    names, links = billing(source)
    return {"key": href.rstrip("/").split("/")[-1], "href": href,
            "title": clean_text(match_text(r'<h1\b[^>]*>(.*?)</h1>', source)),
            "date": str(schema.get("startDate", ""))[:10],
            "endDate": str(schema.get("endDate") or schema.get("startDate", ""))[:10],
            "dateLabel": field(source, "Date"), "venue": field(source, "Venue"),
            "location": field(source, "Location"), "artists": names, "artistLinks": links,
            "hostLabel": host_label(source),
            "official": official, "status": field(source, "Status"),
            "age": field(source, "Age restriction"), "original": attribute(original, "href"),
            **image_fields(image_block)}


def collect(site, today):
    shows = (site / "shows/index.html").read_text()
    result = []
    current_hrefs = set()
    for card in event_cards(shows):
        heading = match_text(r'<h3>\s*(<a\b[^>]*>.*?</a>)', card)
        href = attribute(heading, "href")
        event = read_detail(site, href)
        names, links = billing(card)
        # The final rendered calendar is the authority for current public billing.
        event.update(title=clean_text(heading), date=attribute(card.split(">", 1)[0], "data-date"),
                     endDate=attribute(card.split(">", 1)[0], "data-end-date"),
                     state=attribute(card.split(">", 1)[0], "data-state"),
                     type=attribute(card.split(">", 1)[0], "data-type"),
                     dateLabel=field(card, "Date"), venue=field(card, "Venue"),
                     location=field(card, "Location"), artists=names, artistLinks=links,
                     artistKeys=attribute(card.split(">", 1)[0], "data-artists").split("|"),
                     past=False, **image_fields(card))
        event["endDate"] = event["endDate"] or event["date"]
        result.append(event)
        current_hrefs.add(href)
    archives = set()
    for profile in (site / "artists").glob("*/index.html"):
        for row in re.findall(r'<article\b[^>]*class="[^"]*past-show-row[^\"]*"[^>]*>.*?</article>', profile.read_text(), re.S):
            for anchor in re.findall(r'<a\b[^>]*>.*?</a>', row, re.S):
                href = attribute(anchor, "href")
                if href.startswith(BASE + "event/"):
                    archives.add(href)
    past = []
    for href in sorted(archives - current_hrefs):
        event = read_detail(site, href)
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", event["endDate"]) or event["endDate"] >= today:
            raise ValueError(f"Archive has missing/nonpast date: {href}")
        event.update(state=event["location"].rsplit(",", 1)[-1].strip(), type="archive", past=True)
        past.append(event)
    result.extend(sorted(past, key=lambda e: (e["date"], e["title"]), reverse=True))
    roster = json.loads((site / "config/artists.json").read_text())
    return result, [a["name"] for a in roster if a.get("enabled") is not False]


def build(site):
    repo = Path(__file__).resolve().parents[1]
    today = dt.datetime.now(ZoneInfo("America/Los_Angeles")).date().isoformat()
    events, artists = collect(site, today)
    payload = json.dumps({"events": events, "artists": artists, "snapshotDate": today}, ensure_ascii=False).replace("</", "<\\/")
    for route, template_name in ((ROUTE, "mobile-show-test.html"), (FEED_ROUTE, "show-feed-samples.html")):
        template = (repo / "test-overrides" / template_name).read_text()
        document = inject_assets(template.replace("__BASE__", BASE).replace("__PAYLOAD__", payload))
        page = site / route / "index.html"
        page.parent.mkdir(exist_ok=True)
        page.write_text(document)
    for name in ("mobile-show-test.css", "mobile-show-test.js", "show-feed-samples.css", "kingdom-circuit-mobile-preview.zip"):
        shutil.copy2(repo / "test-overrides" / name, site / "assets" / name)
    # Keep the page discoverable without changing ordinary navigation or calendars.
    home = site / "index.html"
    text = home.read_text()
    link = f'<a data-mobile-test-link href="{BASE}{ROUTE}">Test All Shows Page</a>'
    if "data-mobile-test-link" not in text:
        text = text.replace('<div class="footer-links">', '<div class="footer-links">' + link, 1)
        if "data-mobile-test-link" not in text:
            raise ValueError("Home footer not found")
    if "data-show-feed-link" not in text:
        text = text.replace('<div class="footer-links">', '<div class="footer-links">' +
                            f'<a data-show-feed-link href="{BASE}{FEED_ROUTE}">Image-first show samples</a>', 1)
        if "data-show-feed-link" not in text:
            raise ValueError("Home footer not found for feed samples")
    home.write_text(text)
    manifest_path = site / "test-redesign-manifest.json"
    manifest = json.loads(manifest_path.read_text())
    count = len(list(site.rglob("*.html")))
    manifest["headerPageCount"] = count
    if "htmlPageCount" in manifest:
        manifest["htmlPageCount"] = count
    manifest["mobileCalendarTestPath"] = BASE + ROUTE
    manifest["showFeedSamplesPath"] = BASE + FEED_ROUTE
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"Built Test All Shows Page: {sum(not e['past'] for e in events)} upcoming, {sum(e['past'] for e in events)} archived, {len(artists)} curated artists")


def verify(site):
    page = (site / ROUTE / "index.html").read_text()
    payload = json.loads(match_text(r'<script id="mobile-calendar-data" type="application/json">(.*?)</script>', page))
    events = payload["events"]
    current = [e for e in events if not e["past"]]
    expected, artists = collect(site, payload["snapshotDate"])
    assert events == expected and payload["artists"] == artists
    assert len({e["href"] for e in events}) == len(events)
    assert len(current) == len(event_cards((site / "shows/index.html").read_text()))
    for e in events:
        assert e["title"] and e["artists"] and e["image"] and e["dateLabel"], e["href"]
        assert safe_page(site, e["href"]).is_file()
        for link in e["artistLinks"].values():
            assert (site / link[len(BASE):].strip("/") / "index.html").is_file(), link
        for source in [e["image"], e["original"]]:
            if source.startswith(BASE):
                assert (site / urlsplit(source).path[len(BASE):]).is_file(), source
    assert 'content="noindex,nofollow"' in page and "G-N2KK9XF4TJ" not in page
    assert 'data-mobile-test-link' in (site / "index.html").read_text()
    assert (site / "assets/kingdom-circuit-mobile-preview.zip").stat().st_size > 0
    feed = (site / FEED_ROUTE / "index.html").read_text()
    feed_payload = json.loads(match_text(r'<script id="mobile-calendar-data" type="application/json">(.*?)</script>', feed))
    assert feed_payload == payload, "Feed samples must use the complete identical calendar"
    assert 'content="noindex,nofollow"' in feed and "G-N2KK9XF4TJ" not in feed
    assert all(f'id="mt-{view}"' in feed for view in ("feed", "split", "grid"))
    assert (site / "assets/show-feed-samples.css").stat().st_size > 0
    assert f'{BASE}{FEED_ROUTE}' in page
    assert 'data-show-feed-link' in (site / "index.html").read_text()
    print("Mobile test page verified: current card parity, archived shows, full billing/roster, local assets, and test identity")
    print("Three image-first samples verified: same calendar, approved images, filters and test identity")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("site", type=Path)
    parser.add_argument("--verify-only", action="store_true")
    args = parser.parse_args()
    if not args.verify_only:
        build(args.site)
    verify(args.site)
