#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import urlparse

GA_ID = "G-N2KK9XF4TJ"


def local_file_for_url(site: Path, url: str, base_url: str) -> Path:
    parsed = urlparse(url)
    base = urlparse(base_url)
    if parsed.netloc != base.netloc:
        raise SystemExit(f"Sitemap URL uses the wrong host: {url}")
    base_path = base.path.rstrip("/")
    path = parsed.path
    if base_path and path.startswith(base_path + "/"):
        path = path[len(base_path):]
    relative = path.strip("/")
    return site / relative / "index.html" if relative else site / "index.html"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("site", nargs="?", default="_site")
    parser.add_argument("--base-url", default="https://kingdomcircuit.com")
    parser.add_argument("--preview", action="store_true")
    args = parser.parse_args()
    site = Path(args.site)

    required = [
        "index.html", "shows/index.html", "artists/index.html", "festivals/index.html",
        "app.js", "seo.css", "sitemap.xml", "robots.txt", "seo-build-manifest.json",
        "about/listings/index.html",
    ]
    missing = [name for name in required if not (site / name).is_file() or (site / name).stat().st_size == 0]
    if missing:
        raise SystemExit("SEO build is missing required files: " + ", ".join(missing))

    manifest = json.loads((site / "seo-build-manifest.json").read_text(encoding="utf-8"))
    if manifest.get("artistCount", 0) < 299:
        raise SystemExit(f"SEO artist count is unexpectedly small: {manifest.get('artistCount')}")
    if manifest.get("artistPageCount", 0) < 250:
        raise SystemExit(f"Too few static artist pages: {manifest.get('artistPageCount')}")
    if manifest.get("eventPageCount", 0) < 1:
        raise SystemExit("No static event pages were generated")

    robots = (site / "robots.txt").read_text(encoding="utf-8")
    expected_sitemap = args.base_url.rstrip("/") + "/sitemap.xml"
    if f"Sitemap: {expected_sitemap}" not in robots:
        raise SystemExit("robots.txt does not declare the expected sitemap")
    if "Disallow: /" in robots:
        raise SystemExit("robots.txt blocks the site")

    root = ET.fromstring((site / "sitemap.xml").read_text(encoding="utf-8"))
    namespace = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    urls = [element.text or "" for element in root.findall("sm:url/sm:loc", namespace)]
    if len(urls) < manifest.get("artistPageCount", 0) + manifest.get("eventPageCount", 0):
        raise SystemExit(f"Sitemap is unexpectedly small: {len(urls)} URLs")
    if len(urls) != len(set(urls)):
        raise SystemExit("Sitemap contains duplicate URLs")
    for url in urls:
        path = local_file_for_url(site, url, args.base_url)
        if not path.is_file():
            raise SystemExit(f"Sitemap URL has no deployed HTML file: {url} -> {path}")

    app = (site / "app.js").read_text(encoding="utf-8")
    for required_text in ["function seoSlug", "function seoEventSlug", "artists/${seoSlug(name)}/", "seo-static-v1"]:
        if required_text not in app:
            raise SystemExit(f"Static-route behavior missing from app.js: {required_text}")
    if "artists/profile/?name=" in re.sub(r"ensureCanonical\([^\n]+", "", app):
        # Legacy route rendering may remain, but new navigation cannot be generated from it.
        event_detail_match = re.search(r"function artistProfileUrl\(name\).*?\n\}", app, flags=re.S)
        if event_detail_match and "artists/profile" in event_detail_match.group(0):
            raise SystemExit("artistProfileUrl still points to the legacy query-string route")

    artist_pages = sorted((site / "artists").glob("*/index.html"))
    artist_pages = [path for path in artist_pages if path.parent.name != "profile"]
    event_pages = sorted((site / "events").glob("*/index.html")) if (site / "events").is_dir() else []
    festival_detail_pages = sorted((site / "festivals").glob("*/index.html"))
    sample_pages = artist_pages[:8] + event_pages[:8] + festival_detail_pages[:5]
    if not sample_pages:
        raise SystemExit("No generated detail pages were found")
    for page in sample_pages:
        text = page.read_text(encoding="utf-8")
        if GA_ID not in text:
            raise SystemExit(f"Analytics missing from generated page: {page}")
        if '<link rel="canonical" href="' not in text:
            raise SystemExit(f"Canonical URL missing from generated page: {page}")
        if 'application/ld+json' not in text:
            raise SystemExit(f"Structured data missing from generated page: {page}")
        if "seo.css" not in text:
            raise SystemExit(f"SEO presentation stylesheet missing from generated page: {page}")
        if args.preview:
            if 'content="noindex,nofollow"' not in text:
                raise SystemExit(f"Preview page is indexable: {page}")
        elif 'content="noindex,nofollow"' in text:
            raise SystemExit(f"Production page is noindex: {page}")

    for page in event_pages[:8] + festival_detail_pages[:5]:
        text = page.read_text(encoding="utf-8")
        if '"@type":"MusicEvent"' not in text:
            raise SystemExit(f"MusicEvent structured data missing from {page}")
        if '"startDate"' not in text or '"location"' not in text or '"offers"' not in text:
            raise SystemExit(f"Required Event fields are missing from {page}")

    core = (site / "artists/index.html").read_text(encoding="utf-8")
    if "data-artist-grid" not in core or core.count("artist-card") < 25:
        raise SystemExit("Artist directory was not pre-rendered with crawlable artist links")
    shows = (site / "shows/index.html").read_text(encoding="utf-8")
    if "seo-browse-title" not in shows:
        raise SystemExit("State/month discovery links are missing from the all-shows page")
    if re.search(r'href="[^\"]*/event/\?id=', shows):
        raise SystemExit("Pre-rendered show cards still link to legacy event query URLs")

    print(
        f"SEO artifact verified: {manifest['artistPageCount']} artist pages, "
        f"{manifest['eventPageCount']} event pages, {len(urls)} sitemap URLs."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
