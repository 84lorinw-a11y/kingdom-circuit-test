from __future__ import annotations

import hashlib
import html
import json
import pathlib
import re
import shutil
import sys

TEST_BASE = "/kingdom-circuit-test/"
TEST_ORIGIN = "https://84lorinw-a11y.github.io"
TEST_SITE = TEST_ORIGIN + TEST_BASE.rstrip("/")
LIVE_SITE = "https://kingdomcircuit.com"
LIVE_GA = "G-N2KK9XF4TJ"
TEST_GA = "G-TEST-DISABLED"

EXCLUDED_ARTISTS = {"chad jones", "erica mason", "big holy"}

REGISTRY_UPDATES = {
    "marty": {
        "name": "Marty",
        "aliases": ["Marty", "Marty of Social Club Misfits", "Marty Mar"],
        "category": "solo",
        "monitoringPriority": 2,
        "ticketmasterEnabled": False,
        "textMatchEnabled": False,
        "website": "https://www.instagram.com/deathbymartymar/?hl=en",
        "instagramProfile": "https://www.instagram.com/deathbymartymar/",
        "spotifyProfile": "https://open.spotify.com/artist/5BfKKSmpGmj2moMNlaWeJK",
        "youtubeProfile": "https://www.youtube.com/@deathbymartymar",
        "officialImageSource": "https://open.spotify.com/artist/5BfKKSmpGmj2moMNlaWeJK",
        "imageUrl": "https://i.scdn.co/image/ab6761610000e5eb3d2d9f74de93906d1f5996f3",
        "imagePosition": "center",
        "preferArtistImage": True,
        "sourceRegistryVerified": True,
        "sourceRegistryRosterOrder": 25,
    },
    "caleb gordon": {
        "name": "Caleb Gordon",
        "aliases": ["Caleb Gordon"],
        "category": "core",
        "monitoringPriority": 1,
        "ticketmasterEnabled": True,
        "textMatchEnabled": True,
        "website": "https://tprlive.co/collections/caleb-gordon-the-eden-experience",
        "instagramProfile": "https://www.instagram.com/calebfromeden/",
        "spotifyProfile": "https://open.spotify.com/artist/6s3XaJkcT7464G4oII9V41",
        "youtubeProfile": "https://www.youtube.com/@CalebGordon",
        "officialImageSource": "https://tprlive.co/collections/caleb-gordon-the-eden-experience",
        "imageUrl": "https://tprlive.co/cdn/shop/files/ARTIST_HEADSHOT_36.jpg?v=1776887171&width=1797",
        "imagePosition": "center",
        "preferArtistImage": True,
        "sourceRegistryVerified": True,
        "sourceRegistryRosterOrder": 4,
    },
    "kelo": {
        "name": "Kelo",
        "aliases": ["Kelo"],
        "category": "core",
        "monitoringPriority": 2,
        "ticketmasterEnabled": False,
        "textMatchEnabled": False,
        "website": "https://www.instagram.com/cutthecho/",
        "instagramProfile": "https://www.instagram.com/cutthecho/",
        "spotifyProfile": "https://open.spotify.com/artist/6j8t8rQzrAtRx5tYImodgd",
        "youtubeProfile": "https://www.youtube.com/channel/UCAvlfmD2aiqXxxknr-9VSVg",
        "officialImageSource": "https://www.instagram.com/cutthecho/",
        "sourceRegistryVerified": True,
        "sourceRegistryRosterOrder": 79,
    },
    "dkg kie": {
        "name": "DKG Kie",
        "aliases": ["DKG Kie"],
        "category": "core",
        "monitoringPriority": 1,
        "ticketmasterEnabled": False,
        "textMatchEnabled": True,
        "website": "https://www.dkgkiemerch.com/",
        "instagramProfile": "https://www.instagram.com/dkg.kie",
        "spotifyProfile": "https://open.spotify.com/artist/1eeYg6dFkaRT5GA0lsCVHA",
        "youtubeProfile": "https://www.youtube.com/@dkgkie",
        "officialImageSource": "https://www.instagram.com/dkg.kie",
        "sourceRegistryVerified": True,
        "sourceRegistryRosterOrder": 80,
    },
    "braille": {
        "name": "Braille",
        "aliases": ["Braille"],
        "category": "legacy",
        "monitoringPriority": 3,
        "ticketmasterEnabled": False,
        "textMatchEnabled": True,
        "website": "https://www.humblebeast.com/music/braille",
        "instagramProfile": "https://www.instagram.com/bryanbraille/",
        "spotifyProfile": "https://open.spotify.com/artist/6RYTz1tFNDF2qP0mwqEwDO",
        "youtubeProfile": "https://www.youtube.com/@bryanbraille",
        "officialImageSource": "https://www.humblebeast.com/music/braille",
        "sourceRegistryVerified": True,
        "sourceRegistryRosterOrder": 81,
    },
    "canton jones": {
        "name": "Canton Jones",
        "aliases": ["Canton Jones"],
        "category": "legacy",
        "monitoringPriority": 3,
        "ticketmasterEnabled": True,
        "textMatchEnabled": True,
        "website": "https://www.instagram.com/thecantonjones/?hl=en",
        "instagramProfile": "https://www.instagram.com/thecantonjones/?hl=en",
        "spotifyProfile": "https://open.spotify.com/artist/3nzEXHMRFWTw4zt3pVRv6V",
        "youtubeProfile": "https://www.youtube.com/@CantonJones1",
        "officialImageSource": "https://www.instagram.com/thecantonjones/?hl=en",
        "sourceRegistryVerified": True,
        "sourceRegistryRosterOrder": 82,
    },
    "jay-way": {
        "name": "Jay-Way",
        "aliases": ["Jay-Way", "Jay Way"],
        "category": "core",
        "monitoringPriority": 1,
        "ticketmasterEnabled": False,
        "textMatchEnabled": True,
        "website": "https://www.jaywaythealien.com/",
        "instagramProfile": "https://www.instagram.com/JayWayTheAlien",
        "spotifyProfile": "https://open.spotify.com/artist/1RDbE3dM2bNNSTh88R4MQ7",
        "youtubeProfile": "https://www.youtube.com/@JayWayTheAlien",
        "officialImageSource": "https://www.jaywaythealien.com/",
        "sourceRegistryVerified": True,
        "sourceRegistryRosterOrder": 83,
    },
    "stixx aka conejo": {
        "name": "Stixx aka Conejo",
        "aliases": ["Stixx aka Conejo", "Stixx"],
        "category": "core",
        "monitoringPriority": 2,
        "ticketmasterEnabled": True,
        "textMatchEnabled": True,
        "website": "https://linktr.ee/stixxwym",
        "instagramProfile": "https://www.instagram.com/stixxwym",
        "spotifyProfile": "https://open.spotify.com/artist/3khYLvZ6GmLlPMPlTfMTBr",
        "youtubeProfile": "https://www.youtube.com/@stixxwym/videos",
        "officialImageSource": "https://linktr.ee/stixxwym",
        "sourceRegistryVerified": True,
        "sourceRegistryRosterOrder": 84,
    },
    "ruslan": {
        "name": "Ruslan",
        "aliases": ["Ruslan", "Ruslan KD"],
        "category": "core",
        "monitoringPriority": 1,
        "ticketmasterEnabled": False,
        "textMatchEnabled": False,
        "website": "https://www.instagram.com/ruslankd/?hl=en",
        "instagramProfile": "https://www.instagram.com/ruslankd/?hl=en",
        "spotifyProfile": "https://open.spotify.com/artist/2GEXrCflKZ5S5ZHBM4LNcV",
        "youtubeProfile": "https://www.youtube.com/@RuslanKD/featured",
        "officialImageSource": "https://www.instagram.com/ruslankd/?hl=en",
        "sourceRegistryVerified": True,
        "sourceRegistryRosterOrder": 85,
    },
}


def normalize(value: object) -> str:
    return str(value or "").strip().casefold()


def slugify(value: str) -> str:
    value = value.lower().replace("&", " and ")
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-")


def sha256(path: pathlib.Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def rewrite_html(text: str) -> str:
    text = text.replace(LIVE_SITE + "/", TEST_SITE + "/")
    text = text.replace(LIVE_SITE, TEST_SITE)
    text = text.replace(LIVE_GA, TEST_GA)
    text = re.sub(
        r'(?P<prefix>\b(?:href|src|action)=["\'])/(?!/)',
        lambda m: m.group("prefix") + TEST_BASE,
        text,
    )
    robots = re.compile(r'<meta\s+name=["\']robots["\']\s+content=["\'][^"\']*["\']\s*/?>', re.I)
    if robots.search(text):
        text = robots.sub('<meta name="robots" content="noindex,nofollow">', text)
    elif "<head>" in text:
        text = text.replace("<head>", '<head>\n  <meta name="robots" content="noindex,nofollow">', 1)
    return text


def rewrite_js(text: str) -> str:
    text = text.replace(LIVE_SITE + "/", TEST_SITE + "/")
    text = text.replace(LIVE_SITE, TEST_SITE)
    text = text.replace(LIVE_GA, TEST_GA)
    text = text.replace('const BASE = "/";', f'const BASE = "{TEST_BASE}";')
    text = re.sub(r'const LIVE_EVENTS_URL\s*=\s*[^;]+;', 'const LIVE_EVENTS_URL = `${BASE}events.json`;', text, count=1)
    text = re.sub(r'const LIVE_ARTISTS_URL\s*=\s*[^;]+;', 'const LIVE_ARTISTS_URL = `${BASE}config/artists.json`;', text, count=1)

    if "function enhanceVerifiedArtistImages()" not in text:
        marker = "function renderEventDetail()"
        enhancement = r'''
function enhanceVerifiedArtistImages() {
  document.querySelectorAll("[data-artist-card]").forEach(card => {
    const name = card.querySelector("h2 a")?.textContent || "";
    const artist = artistConfig(name);
    const visual = card.querySelector(".artist-visual");
    if (!visual || !artist?.imageUrl) return;
    visual.classList.remove("artist-visual-empty");
    visual.innerHTML = `<img src="${esc(localAssetUrl(artist.imageUrl))}" alt="${esc(artist.name)}" loading="lazy" onerror="this.onerror=null;this.src='${FALLBACK_EVENT_IMAGE}';">`;
  });

  const root = document.querySelector("[data-artist-profile]");
  if (!root) return;
  const name = new URLSearchParams(location.search).get("name") || "";
  const artist = artistConfig(name);
  const hero = root.querySelector(".profile-hero");
  if (!hero || !artist?.imageUrl || hero.querySelector(".profile-visual")) return;
  hero.classList.remove("profile-hero-no-image");
  hero.insertAdjacentHTML("afterbegin", `<div class="profile-visual"><img src="${esc(localAssetUrl(artist.imageUrl))}" alt="${esc(artist.name)}" onerror="this.onerror=null;this.src='${FALLBACK_EVENT_IMAGE}';"></div>`);
  hero.querySelector(".profile-image-note")?.remove();
}
'''
        if marker in text:
            text = text.replace(marker, enhancement + "\n" + marker, 1)
        call_marker = "  renderArtistProfile();"
        if call_marker in text:
            text = text.replace(call_marker, call_marker + "\n  enhanceVerifiedArtistImages();", 1)
    return text


def rewrite_css(text: str) -> str:
    text = text.replace(LIVE_SITE + "/", TEST_SITE + "/")
    text = text.replace(LIVE_SITE, TEST_SITE)
    return text


def patch_artists(path: pathlib.Path) -> list[dict]:
    artists = json.loads(path.read_text(encoding="utf-8"))
    artists = [artist for artist in artists if normalize(artist.get("name")) not in EXCLUDED_ARTISTS]
    by_name = {normalize(artist.get("name")): artist for artist in artists}
    next_order = max((int(a.get("rosterOrder") or 0) for a in artists), default=0) + 1

    for key, update in REGISTRY_UPDATES.items():
        artist = by_name.get(key)
        if artist is None:
            artist = {
                "name": update["name"],
                "aliases": update["aliases"],
                "enabled": True,
                "ticketmasterEnabled": update["ticketmasterEnabled"],
                "category": update["category"],
                "monitoringPriority": update["monitoringPriority"],
                "topStreamingPriority": False,
                "socialSearchEnabled": update["monitoringPriority"] <= 2,
                "activeStatus": "active_or_unknown",
                "textMatchEnabled": update["textMatchEnabled"],
                "rosterOrder": next_order,
            }
            next_order += 1
            artists.append(artist)
            by_name[key] = artist
        artist.update(update)
        artist["enabled"] = True

    path.write_text(json.dumps(artists, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return artists


def patch_events(path: pathlib.Path) -> None:
    if not path.is_file():
        return
    events = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(events, list):
        return
    cleaned = []
    for event in events:
        if event.get("id") == "supplemental:marty-project-nation-kuna-2026":
            event["image"] = REGISTRY_UPDATES["marty"]["imageUrl"]
            event["imageType"] = "artist"
            event["imagePosition"] = REGISTRY_UPDATES["marty"]["imagePosition"]
        original_artists = list(event.get("artists") or [])
        remaining = [name for name in original_artists if normalize(name) not in EXCLUDED_ARTISTS]
        removed = len(remaining) != len(original_artists)
        title = normalize(event.get("title"))
        title_names_excluded = any(name in title for name in EXCLUDED_ARTISTS)
        if removed and not remaining:
            continue
        if title_names_excluded:
            continue
        if removed:
            event["artists"] = remaining
            if normalize(event.get("headliner")) in EXCLUDED_ARTISTS:
                if remaining:
                    event["headliner"] = remaining[0]
                else:
                    event.pop("headliner", None)
        cleaned.append(event)
    path.write_text(json.dumps(cleaned, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def patch_marty_event_pages(out_dir: pathlib.Path) -> None:
    old_image = "https://img1.wsimg.com/isteam/ip/6ed0aa91-488e-49ff-a53b-8d885654844e/DSC07306%20Edited.jpg/:/cr=t:0%25,l:0%25,w:100%25,h:100%25/rs=w:600,cg:true"
    for page in out_dir.rglob("*.html"):
        text = page.read_text(encoding="utf-8")
        if old_image not in text:
            continue
        page.write_text(text.replace(old_image, REGISTRY_UPDATES["marty"]["imageUrl"]), encoding="utf-8")


def artist_link_html(artist: dict) -> str:
    links = []
    fields = [
        ("Instagram", artist.get("instagramProfile")),
        ("Spotify", artist.get("spotifyProfile")),
        ("YouTube", artist.get("youtubeProfile")),
        ("Website", artist.get("website") or artist.get("officialWebsite") or artist.get("officialProfile")),
    ]
    seen = set()
    for label, url in fields:
        if not url or url in seen:
            continue
        seen.add(url)
        links.append(f'<a class="secondary-button" href="{html.escape(str(url), quote=True)}" target="_blank" rel="noopener">{html.escape(label)}</a>')
    return "".join(links)


def patch_static_artist_pages(out_dir: pathlib.Path, artists: list[dict]) -> None:
    by_name = {normalize(a.get("name")): a for a in artists}
    for key in REGISTRY_UPDATES:
        artist = by_name.get(key)
        if not artist:
            continue
        page = out_dir / "artists" / slugify(artist["name"]) / "index.html"
        if not page.is_file():
            continue
        text = page.read_text(encoding="utf-8")
        links = artist_link_html(artist)
        text = re.sub(r'<div class="profile-links">.*?</div>', f'<div class="profile-links">{links}</div>', text, count=1, flags=re.S)
        image_url = artist.get("imageUrl")
        if image_url and "profile-hero-no-image" in text:
            src = str(image_url)
            if not re.match(r"^https?://", src, re.I):
                src = TEST_BASE + src.lstrip("/")
            image_html = f'<div class="profile-visual"><img src="{html.escape(src, quote=True)}" alt="{html.escape(artist["name"], quote=True)}"></div>'
            text = text.replace('<section class="profile-hero profile-hero-no-image"><div>', f'<section class="profile-hero">{image_html}<div>', 1)
        page.write_text(text, encoding="utf-8")


def remove_excluded_static_pages(out_dir: pathlib.Path) -> None:
    artists_dir = out_dir / "artists"
    for name in EXCLUDED_ARTISTS:
        page_dir = artists_dir / slugify(name)
        if page_dir.exists():
            shutil.rmtree(page_dir)
    sitemap = out_dir / "sitemap.xml"
    if sitemap.is_file():
        text = sitemap.read_text(encoding="utf-8")
        for name in EXCLUDED_ARTISTS:
            slug = slugify(name)
            text = re.sub(rf"<url>.*?/artists/{re.escape(slug)}/.*?</url>\s*", "", text, flags=re.S | re.I)
        sitemap.write_text(text, encoding="utf-8")


def verify_overlay(out_dir: pathlib.Path) -> list[str]:
    failures: list[str] = []
    artists = json.loads((out_dir / "config" / "artists.json").read_text(encoding="utf-8"))
    names = {normalize(a.get("name")) for a in artists}
    for name in EXCLUDED_ARTISTS:
        if name in names:
            failures.append(f"excluded-artist-present:{name}")
    for key, expected in REGISTRY_UPDATES.items():
        artist = next((a for a in artists if normalize(a.get("name")) == key), None)
        if not artist:
            failures.append(f"registry-artist-missing:{key}")
            continue
        for field in ("website", "instagramProfile", "spotifyProfile", "youtubeProfile", "officialImageSource"):
            if expected.get(field) and artist.get(field) != expected[field]:
                failures.append(f"registry-field-mismatch:{key}:{field}")
        if not artist.get("sourceRegistryVerified"):
            failures.append(f"registry-not-verified:{key}")
    for relative in ("events.json", "supplemental-events.json"):
        path = out_dir / relative
        if not path.is_file():
            continue
        text = normalize(path.read_text(encoding="utf-8"))
        for name in EXCLUDED_ARTISTS:
            if name in text:
                failures.append(f"excluded-artist-in-{relative}:{name}")
    app = (out_dir / "app.js").read_text(encoding="utf-8")
    if 'const LIVE_ARTISTS_URL = `${BASE}config/artists.json`;' not in app:
        failures.append("test-artists-not-local")
    if 'const LIVE_EVENTS_URL = `${BASE}events.json`;' not in app:
        failures.append("test-events-not-local")
    if "function enhanceVerifiedArtistImages()" not in app:
        failures.append("artist-image-enhancement-missing")
    caleb_page = out_dir / "artists" / "caleb-gordon" / "index.html"
    if caleb_page.is_file() and "profile-visual" not in caleb_page.read_text(encoding="utf-8"):
        failures.append("caleb-static-image-missing")
    return failures


def main() -> None:
    if len(sys.argv) != 4:
        raise SystemExit("usage: live_mirror_v2.py LIVE_ARTIFACT TEST_OUTPUT LIVE_SHA")
    live_dir = pathlib.Path(sys.argv[1]).resolve()
    out_dir = pathlib.Path(sys.argv[2]).resolve()
    live_sha = sys.argv[3]
    if not (live_dir / "index.html").is_file():
        raise SystemExit(f"Missing live artifact: {live_dir}")
    if out_dir.exists():
        shutil.rmtree(out_dir)
    shutil.copytree(live_dir, out_dir)
    cname = out_dir / "CNAME"
    if cname.exists():
        cname.unlink()

    for path in out_dir.rglob("*"):
        if not path.is_file():
            continue
        suffix = path.suffix.lower()
        if suffix == ".html":
            path.write_text(rewrite_html(path.read_text(encoding="utf-8")), encoding="utf-8")
        elif suffix == ".js":
            path.write_text(rewrite_js(path.read_text(encoding="utf-8")), encoding="utf-8")
        elif suffix == ".css":
            path.write_text(rewrite_css(path.read_text(encoding="utf-8")), encoding="utf-8")
        elif suffix == ".xml":
            text = path.read_text(encoding="utf-8")
            text = text.replace(LIVE_SITE + "/", TEST_SITE + "/").replace(LIVE_SITE, TEST_SITE)
            path.write_text(text, encoding="utf-8")

    artists = patch_artists(out_dir / "config" / "artists.json")
    patch_events(out_dir / "events.json")
    patch_events(out_dir / "supplemental-events.json")
    patch_static_artist_pages(out_dir, artists)
    patch_marty_event_pages(out_dir)
    remove_excluded_static_pages(out_dir)
    (out_dir / "robots.txt").write_text("User-agent: *\nDisallow: /\n", encoding="utf-8")

    failures: list[str] = []
    live_css = live_dir / "styles.css"
    test_css = out_dir / "styles.css"
    if not test_css.is_file() or sha256(live_css) != sha256(test_css):
        failures.append("changed:styles.css")
    for live_asset in (live_dir / "assets").rglob("*"):
        if not live_asset.is_file():
            continue
        relative = live_asset.relative_to(live_dir)
        test_asset = out_dir / relative
        if not test_asset.is_file() or sha256(live_asset) != sha256(test_asset):
            failures.append(f"asset:{relative}")
    bad_root = re.compile(r'\b(?:href|src|action)=["\']/(?!kingdom-circuit-test(?:/|["\']))')
    for html_file in out_dir.rglob("*.html"):
        text = html_file.read_text(encoding="utf-8")
        rel = html_file.relative_to(out_dir)
        if '<meta name="robots" content="noindex,nofollow">' not in text:
            failures.append(f"indexable:{rel}")
        if bad_root.search(text):
            failures.append(f"bad-root-path:{rel}")
        if LIVE_GA in text:
            failures.append(f"live-analytics:{rel}")
    app = (out_dir / "app.js").read_text(encoding="utf-8")
    if f'const BASE = "{TEST_BASE}";' not in app:
        failures.append("app-base-not-rewritten")
    if (out_dir / "CNAME").exists():
        failures.append("cname-present")
    failures.extend(verify_overlay(out_dir))
    if failures:
        raise SystemExit(json.dumps({"failures": failures[:100]}, indent=2))

    manifest = {
        "mode": "live-baseline-with-test-registry-overlay",
        "liveCommit": live_sha,
        "source": "84lorinw-a11y/kingdom-circuit@main",
        "testBase": TEST_BASE,
        "liveStylesByteIdentical": True,
        "liveAssetsByteIdentical": True,
        "testRegistryOverlayApplied": True,
        "excludedArtists": sorted(EXCLUDED_ARTISTS),
        "verifiedRegistryUpdates": [REGISTRY_UPDATES[k]["name"] for k in REGISTRY_UPDATES],
        "testNoindex": True,
        "liveAnalyticsDisabled": True,
        "cnameRemoved": True,
        "seoPhase2OverlayApplied": False,
    }
    (out_dir / "test-live-mirror-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
