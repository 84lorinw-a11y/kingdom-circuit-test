from __future__ import annotations

import html
import json
import pathlib
import re
import sys

TEST_ORIGIN = "https://84lorinw-a11y.github.io"


def visible_artists(text: str) -> list[tuple[str, str]]:
    cards = re.findall(
        r'<article class="artist-card seo-artist-card".*?<h2><a href="([^"]+)">(.*?)</a></h2>',
        text,
        flags=re.S,
    )
    artists: list[tuple[str, str]] = []
    for href, raw_name in cards:
        name = html.unescape(re.sub(r'<[^>]+>', '', raw_name)).strip()
        artists.append((href, name))
    return artists


def align(root: pathlib.Path) -> None:
    path = root / "artists/index.html"
    if not path.exists():
        raise SystemExit("Missing artists/index.html")

    text = path.read_text(encoding="utf-8")
    artists = visible_artists(text)
    if len(artists) < 250:
        raise SystemExit(f"Expected at least 250 visible artist cards; found {len(artists)}")

    ordered = [
        {
            "@type": "ListItem",
            "position": index,
            "url": TEST_ORIGIN + href,
            "name": name,
        }
        for index, (href, name) in enumerate(artists, start=1)
    ]

    pattern = re.compile(r'(<script type="application/ld\+json">)(.*?)(</script>)', re.S)
    found = False

    def replace(match: re.Match[str]) -> str:
        nonlocal found
        try:
            data = json.loads(match.group(2))
        except json.JSONDecodeError:
            return match.group(0)
        if data.get("@type") != "ItemList" or data.get("name") != "Christian Hip-Hop Artists":
            return match.group(0)
        data["itemListElement"] = ordered
        found = True
        payload = json.dumps(data, separators=(",", ":"), ensure_ascii=False).replace("</", "<\\/")
        return match.group(1) + payload + match.group(3)

    updated = pattern.sub(replace, text)
    if not found:
        raise SystemExit("Christian Hip-Hop Artists ItemList schema not found")
    path.write_text(updated, encoding="utf-8")

    check = path.read_text(encoding="utf-8")
    schema = None
    for match in pattern.finditer(check):
        try:
            candidate = json.loads(match.group(2))
        except json.JSONDecodeError:
            continue
        if candidate.get("@type") == "ItemList" and candidate.get("name") == "Christian Hip-Hop Artists":
            schema = candidate
            break
    if schema is None:
        raise SystemExit("Aligned artist ItemList schema missing after write")

    schema_names = [item.get("name") for item in schema.get("itemListElement", [])]
    visible_names = [name for _, name in artists]
    if schema_names != visible_names:
        raise SystemExit("Artist ItemList schema order does not match visible directory order")

    if len(schema_names) != len(set(schema_names)):
        raise SystemExit("Artist ItemList schema contains duplicate artist names")

    print(f"Artist SEO ItemList aligned to {len(schema_names)} visible artists; first 10: {schema_names[:10]}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Usage: align_artist_schema.py SITE_ROOT")
    align(pathlib.Path(sys.argv[1]).resolve())
