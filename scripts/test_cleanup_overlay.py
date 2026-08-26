from __future__ import annotations

import html
import pathlib
import re
import shutil
import sys

EXCLUDED_ARTISTS = {"chad jones", "erica mason", "big holy"}
EXCLUDED_SLUGS = {"chad-jones", "erica-mason", "big-holy"}


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


def clean_static_html(out_dir: pathlib.Path, removed_event_slugs: set[str]) -> None:
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

        if text != original:
            page.write_text(text, encoding="utf-8")


def clean_sitemap(out_dir: pathlib.Path, removed_event_slugs: set[str]) -> None:
    sitemap = out_dir / "sitemap.xml"
    if not sitemap.is_file():
        return
    text = sitemap.read_text(encoding="utf-8")
    targets = [f"/artists/{slug}/" for slug in EXCLUDED_SLUGS]
    targets.extend(f"/event/{slug}/" for slug in removed_event_slugs)
    for target in targets:
        text = re.sub(
            rf"<url>.*?{re.escape(target)}.*?</url>\s*",
            "",
            text,
            flags=re.I | re.S,
        )
    sitemap.write_text(text, encoding="utf-8")


def verify(out_dir: pathlib.Path, removed_event_slugs: set[str]) -> None:
    failures: list[str] = []
    for slug in EXCLUDED_SLUGS:
        if (out_dir / "artists" / slug).exists():
            failures.append(f"excluded-artist-page:{slug}")

    for page in out_dir.rglob("*.html"):
        text = page.read_text(encoding="utf-8")
        lowered = text.casefold()
        for slug in EXCLUDED_SLUGS:
            if f"/artists/{slug}/" in lowered:
                failures.append(f"excluded-artist-link:{page.relative_to(out_dir)}:{slug}")
        for event_slug in removed_event_slugs:
            if f"/event/{event_slug}/" in lowered:
                failures.append(f"excluded-event-link:{page.relative_to(out_dir)}:{event_slug}")

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

    removed_event_slugs = remove_excluded_event_pages(out_dir)
    clean_static_html(out_dir, removed_event_slugs)
    clean_sitemap(out_dir, removed_event_slugs)
    verify(out_dir, removed_event_slugs)
    print(f"Static cleanup verified; removed {len(removed_event_slugs)} excluded event page(s).")


if __name__ == "__main__":
    main()
