from __future__ import annotations

import html
import pathlib
import re
import shutil
import struct
import sys
import xml.etree.ElementTree as ET

EXCLUDED_ARTISTS = {"chad jones", "erica mason", "big holy"}
EXCLUDED_SLUGS = {"chad-jones", "erica-mason", "big-holy"}
SOCIAL_PREVIEW_REL = pathlib.Path("assets/social-preview-wordmark-20260917.png")
SOCIAL_PREVIEW_URL = (
    "https://84lorinw-a11y.github.io/kingdom-circuit-test/assets/social-preview-wordmark-20260917.png"
)
SOCIAL_PREVIEW_ALT = "The Kingdom Circuit — Find Christian Hip-Hop Shows & Festivals"
SOCIAL_PREVIEW_SIZE = (1200, 630)


def normalize_text(value: str) -> str:
    value = html.unescape(value)
    value = re.sub(r"<[^>]+>", " ", value)
    return re.sub(r"\s+", " ", value).strip().casefold()


def contains_excluded_name(value: str) -> bool:
    text = normalize_text(value)
    return any(name in text for name in EXCLUDED_ARTISTS)


def artist_slugs(value: str) -> list[str]:
    return [
        match.casefold()
        for match in re.findall(r'/artists/([^/]+)/', value, flags=re.I)
    ]


def remove_excluded_event_pages(out_dir: pathlib.Path) -> set[str]:
    removed: set[str] = set()
    event_root = out_dir / "event"
    if not event_root.is_dir():
        return removed

    for page in event_root.glob("*/index.html"):
        text = page.read_text(encoding="utf-8")
        h1_match = re.search(r"<h1\b[^>]*>(.*?)</h1>", text, flags=re.I | re.S)
        h1 = h1_match.group(1) if h1_match else ""
        linked_artist_slugs = artist_slugs(text)
        only_excluded_artists = bool(linked_artist_slugs) and all(
            slug in EXCLUDED_SLUGS for slug in linked_artist_slugs
        )
        if contains_excluded_name(h1) or only_excluded_artists:
            removed.add(page.parent.name)
            shutil.rmtree(page.parent)

    return removed


def remove_cards_for_slugs(text: str, card_class: str, path_prefix: str, slugs: set[str]) -> str:
    pattern = re.compile(
        rf'<article\b(?=[^>]*class="[^"]*\b{re.escape(card_class)}\b[^"]*")[^>]*>.*?</article>',
        flags=re.I | re.S,
    )

    def repl(match: re.Match[str]) -> str:
        block = match.group(0)
        lowered = block.casefold()
        if any(f"/{path_prefix}/{slug}/" in lowered for slug in slugs):
            return ""
        return block

    return pattern.sub(repl, text)


def clean_artist_lines(text: str) -> str:
    pattern = re.compile(
        r'(<p\b[^>]*class="[^"]*\bartist-line\b[^"]*"[^>]*>)(.*?)(</p>)',
        flags=re.I | re.S,
    )
    anchor_pattern = re.compile(r'<a\b[^>]*href="[^"]*/artists/([^/]+)/[^"]*"[^>]*>.*?</a>', flags=re.I | re.S)

    def repl(match: re.Match[str]) -> str:
        inner = match.group(2)
        anchors = []
        for anchor in anchor_pattern.finditer(inner):
            if anchor.group(1).casefold() not in EXCLUDED_SLUGS:
                anchors.append(anchor.group(0))
        if anchors:
            return match.group(1) + ", ".join(anchors) + match.group(3)
        if any(f"/artists/{slug}/" in inner.casefold() for slug in EXCLUDED_SLUGS):
            return ""
        return match.group(0)

    return pattern.sub(repl, text)


def get_attr(tag: str, name: str) -> str:
    match = re.search(
        rf'\b{re.escape(name)}\s*=\s*(["\'])(.*?)\1',
        tag,
        flags=re.I | re.S,
    )
    return html.unescape(match.group(2)) if match else ""


def set_attr(tag: str, name: str, value: str) -> str:
    encoded = html.escape(value, quote=True)
    pattern = re.compile(
        rf'\b{re.escape(name)}\s*=\s*(["\']).*?\1',
        flags=re.I | re.S,
    )
    if pattern.search(tag):
        return pattern.sub(f'{name}="{encoded}"', tag, count=1)
    return tag[:-1] + f' {name}="{encoded}">' if tag.endswith(">") else tag


def meta_content(text: str, key: str) -> str:
    pattern = re.compile(
        rf'<meta\b(?=[^>]*\b(?:name|property)=["\']{re.escape(key)}["\'])[^>]*>',
        flags=re.I,
    )
    match = pattern.search(text)
    return get_attr(match.group(0), "content") if match else ""


def set_meta(text: str, key: str, value: str) -> str:
    attr_name = "property" if key.startswith("og:") else "name"
    pattern = re.compile(
        rf'<meta\b(?=[^>]*\b(?:name|property)=["\']{re.escape(key)}["\'])[^>]*>',
        flags=re.I,
    )
    match = pattern.search(text)
    if match:
        replacement = set_attr(match.group(0), "content", value)
        replacement = re.sub(
            r'\b(?:name|property)\s*=\s*(["\']).*?\1',
            f'{attr_name}="{html.escape(key, quote=True)}"',
            replacement,
            count=1,
            flags=re.I | re.S,
        )
        return text[:match.start()] + replacement + text[match.end():]
    tag = f'<meta {attr_name}="{html.escape(key, quote=True)}" content="{html.escape(value, quote=True)}">'
    return text.replace("</head>", tag + "</head>", 1)


def uses_replaceable_default_social_image(text: str) -> bool:
    values = (meta_content(text, "og:image"), meta_content(text, "twitter:image"))
    return any(
        re.search(
            r"/assets/(?:(?:logo|logo-wordmark)\.(?:png|svg)|social-preview\.png)(?:[?#]|$)",
            value,
            flags=re.I,
        )
        for value in values
    )


def apply_social_preview(text: str, rel: pathlib.Path) -> tuple[str, bool]:
    if rel != pathlib.Path("index.html") and not uses_replaceable_default_social_image(text):
        return text, False

    original = text
    for key, value in (
        ("og:image", SOCIAL_PREVIEW_URL),
        ("og:image:secure_url", SOCIAL_PREVIEW_URL),
        ("og:image:type", "image/png"),
        ("og:image:width", str(SOCIAL_PREVIEW_SIZE[0])),
        ("og:image:height", str(SOCIAL_PREVIEW_SIZE[1])),
        ("og:image:alt", SOCIAL_PREVIEW_ALT),
        ("twitter:card", "summary_large_image"),
        ("twitter:image", SOCIAL_PREVIEW_URL),
        ("twitter:image:alt", SOCIAL_PREVIEW_ALT),
    ):
        text = set_meta(text, key, value)
    return text, text != original


def png_dimensions(path: pathlib.Path) -> tuple[int, int]:
    data = path.read_bytes()[:24]
    if len(data) < 24 or data[:8] != b"\x89PNG\r\n\x1a\n" or data[12:16] != b"IHDR":
        raise ValueError(f"Not a valid PNG: {path}")
    return struct.unpack(">II", data[16:24])


def install_social_preview(out_dir: pathlib.Path) -> None:
    source = pathlib.Path(__file__).resolve().parents[1] / "test-overrides" / SOCIAL_PREVIEW_REL
    if not source.is_file():
        raise SystemExit(f"Missing test social-preview source: {source}")
    if png_dimensions(source) != SOCIAL_PREVIEW_SIZE:
        raise SystemExit(
            f"Test social preview must be {SOCIAL_PREVIEW_SIZE[0]}x{SOCIAL_PREVIEW_SIZE[1]}: {source}"
        )
    destination = out_dir / SOCIAL_PREVIEW_REL
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)


def clean_static_html(out_dir: pathlib.Path, removed_event_slugs: set[str]) -> int:
    social_pages_updated = 0
    for page in out_dir.rglob("*.html"):
        text = page.read_text(encoding="utf-8")
        original = text
        text = remove_cards_for_slugs(text, "artist-card", "artists", EXCLUDED_SLUGS)
        if removed_event_slugs:
            text = remove_cards_for_slugs(text, "event-card", "event", removed_event_slugs)
        text = clean_artist_lines(text)

        if page == out_dir / "artists" / "index.html":
            count = len(re.findall(r'<article\b[^>]*\bdata-artist-card\b', text, flags=re.I))
            text = re.sub(
                r'(<p\b[^>]*data-artist-count[^>]*>)\s*\d+\s+artists\s*(</p>)',
                rf'\g<1>{count} artists\g<2>',
                text,
                count=1,
                flags=re.I,
            )

        text, social_updated = apply_social_preview(text, page.relative_to(out_dir))
        social_pages_updated += int(social_updated)

        if text != original:
            page.write_text(text, encoding="utf-8")
    return social_pages_updated


def clean_sitemap(out_dir: pathlib.Path, removed_event_slugs: set[str]) -> None:
    sitemap = out_dir / "sitemap.xml"
    if not sitemap.is_file():
        return
    targets = [f"/artists/{slug}/" for slug in EXCLUDED_SLUGS]
    targets.extend(f"/event/{slug}/" for slug in removed_event_slugs)
    namespace = "http://www.sitemaps.org/schemas/sitemap/0.9"
    ET.register_namespace("", namespace)
    tree = ET.parse(sitemap)
    root = tree.getroot()
    for url_node in list(root.findall(f"{{{namespace}}}url")):
        loc = url_node.find(f"{{{namespace}}}loc")
        if loc is not None and any(target in (loc.text or "").casefold() for target in targets):
            root.remove(url_node)
    tree.write(sitemap, encoding="utf-8", xml_declaration=True)


def verify(out_dir: pathlib.Path, removed_event_slugs: set[str]) -> None:
    failures: list[str] = []
    social_preview = out_dir / SOCIAL_PREVIEW_REL
    if not social_preview.is_file():
        failures.append("social-preview:missing")
    else:
        try:
            dimensions = png_dimensions(social_preview)
        except (OSError, ValueError) as exc:
            failures.append(f"social-preview:invalid:{exc}")
        else:
            if dimensions != SOCIAL_PREVIEW_SIZE:
                failures.append(f"social-preview:dimensions:{dimensions[0]}x{dimensions[1]}")

    for slug in EXCLUDED_SLUGS:
        if (out_dir / "artists" / slug).exists():
            failures.append(f"excluded-artist-page:{slug}")

    for page in out_dir.rglob("*.html"):
        text = page.read_text(encoding="utf-8")
        lowered = text.casefold()
        rel = page.relative_to(out_dir)
        for slug in EXCLUDED_SLUGS:
            if f"/artists/{slug}/" in lowered:
                failures.append(f"excluded-artist-link:{page.relative_to(out_dir)}:{slug}")
        for event_slug in removed_event_slugs:
            if f"/event/{event_slug}/" in lowered:
                failures.append(f"excluded-event-link:{page.relative_to(out_dir)}:{event_slug}")

        for key in ("og:image", "twitter:image"):
            value = meta_content(text, key)
            if "logo-wordmark.svg" in value.casefold():
                failures.append(f"social-preview:legacy-wordmark:{rel}:{key}")
            if re.search(r"/assets/social-preview\.png(?:[?#]|$)", value, flags=re.I):
                failures.append(f"social-preview:legacy-old-logo-card:{rel}:{key}")

        if meta_content(text, "og:image") == SOCIAL_PREVIEW_URL:
            expected = {
                "og:image:secure_url": SOCIAL_PREVIEW_URL,
                "og:image:type": "image/png",
                "og:image:width": str(SOCIAL_PREVIEW_SIZE[0]),
                "og:image:height": str(SOCIAL_PREVIEW_SIZE[1]),
                "og:image:alt": SOCIAL_PREVIEW_ALT,
                "twitter:card": "summary_large_image",
                "twitter:image": SOCIAL_PREVIEW_URL,
                "twitter:image:alt": SOCIAL_PREVIEW_ALT,
            }
            for key, wanted in expected.items():
                if meta_content(text, key) != wanted:
                    failures.append(f"social-preview:metadata:{rel}:{key}")

    homepage = out_dir / "index.html"
    if not homepage.is_file():
        failures.append("social-preview:homepage-missing")
    else:
        text = homepage.read_text(encoding="utf-8")
        if meta_content(text, "og:image") != SOCIAL_PREVIEW_URL:
            failures.append("social-preview:homepage-og-image")
        if meta_content(text, "twitter:image") != SOCIAL_PREVIEW_URL:
            failures.append("social-preview:homepage-twitter-image")

    sitemap = out_dir / "sitemap.xml"
    if sitemap.is_file():
        lowered = sitemap.read_text(encoding="utf-8").casefold()
        for slug in EXCLUDED_SLUGS:
            if f"/artists/{slug}/" in lowered:
                failures.append(f"excluded-artist-sitemap:{slug}")
        for event_slug in removed_event_slugs:
            if f"/event/{event_slug}/" in lowered:
                failures.append(f"excluded-event-sitemap:{event_slug}")

    if failures:
        raise SystemExit("Static cleanup verification failed:\n" + "\n".join(failures[:100]))


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: test_cleanup_overlay.py TEST_OUTPUT")
    out_dir = pathlib.Path(sys.argv[1]).resolve()
    if not out_dir.is_dir():
        raise SystemExit(f"Missing test output: {out_dir}")

    install_social_preview(out_dir)
    removed_event_slugs = remove_excluded_event_pages(out_dir)
    social_pages_updated = clean_static_html(out_dir, removed_event_slugs)
    clean_sitemap(out_dir, removed_event_slugs)
    verify(out_dir, removed_event_slugs)
    print(
        "Static cleanup verified; "
        f"removed {len(removed_event_slugs)} excluded event page(s); "
        f"updated {social_pages_updated} social preview page(s)."
    )


if __name__ == "__main__":
    main()
