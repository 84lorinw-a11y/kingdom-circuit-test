#!/usr/bin/env python3
"""Apply the narrowly scoped image-presentation overlay to a test artifact.

The live artifact remains the source of truth.  This script only adds the
test-site stylesheet, a truthful responsive-size contract for event cards,
and the two approved focal-point corrections.  It deliberately does not run
or depend on any of the broader test UX overlays.
"""

from __future__ import annotations

import argparse
import dataclasses
import html
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import sys
from typing import Iterable, Optional, Sequence
from urllib.parse import urlsplit, urlunsplit


TEST_BASE = "/kingdom-circuit-test/"
CSS_NAME = "test-image-repairs.css"
CSS_HREF = f"{TEST_BASE}assets/{CSS_NAME}?v=1"
CARD_SIZES = (
    "(max-width: 600px) calc(100vw - 32px), "
    "(max-width: 900px) calc(100vw - 48px), "
    "(max-width: 1180px) 40vw, 453px"
)
CJ_EMULOUS_SOURCE = (
    "https://ugc.production.linktr.ee/"
    "e2e0b25c-780f-4b6f-9a4d-48461885e719_DSC01908.jpeg"
)
IMAGE_JSON_KEYS = {
    "image",
    "imageurl",
    "image_url",
    "artwork",
    "artworkurl",
    "thumbnail",
    "thumbnailurl",
}
PUBLIC_JSON_FILES = (
    "events.json",
    "supplemental-events.json",
    "artist-website-events.json",
    "config/artists.json",
    "config/manual-events.json",
)
VOID_ELEMENTS = {
    "area", "base", "br", "col", "embed", "hr", "img", "input", "link",
    "meta", "param", "source", "track", "wbr",
}


OVERLAY_CSS = r'''/* Kingdom Circuit test-only image presentation repairs. */
.event-card .event-media {
  position: relative !important;
  display: block;
  width: 100%;
  aspect-ratio: 4 / 3 !important;
  height: auto !important;
  min-height: 0 !important;
  align-self: start;
  overflow: hidden;
  background: #090909;
}

.event-card .event-media img {
  position: absolute;
  inset: 0;
  display: block;
  width: 100% !important;
  height: 100% !important;
  min-height: 0 !important;
  background: #090909;
}

.event-card .event-media img.artist-photo {
  object-fit: cover !important;
  padding: 0 !important;
}

.event-card .event-media img.event-artwork {
  object-fit: contain !important;
  padding: 10px !important;
}
'''


@dataclasses.dataclass(frozen=True)
class FocalRule:
    marker: str
    position: str


CJ_RULE = FocalRule("cj-emulous", "center top")
HULVEY_RULE = FocalRule("hulvey", "50% 30%")


@dataclasses.dataclass
class ImageOccurrence:
    start: int
    end: int
    attrs: list[tuple[str, Optional[str]]]
    context_classes: frozenset[str]

    @property
    def attr_map(self) -> dict[str, Optional[str]]:
        return {key.lower(): value for key, value in self.attrs}


class SiteImageParser(HTMLParser):
    """Collect exact image offsets without reserializing the whole page."""

    def __init__(self, text: str):
        super().__init__(convert_charrefs=True)
        self.line_starts = [0]
        self.line_starts.extend(match.end() for match in re.finditer(r"\n", text))
        self.stack: list[tuple[str, frozenset[str]]] = []
        self.images: list[ImageOccurrence] = []

    @staticmethod
    def _classes(attrs: Iterable[tuple[str, Optional[str]]]) -> frozenset[str]:
        for key, value in attrs:
            if key.lower() == "class":
                return frozenset(str(value or "").split())
        return frozenset()

    def _offset(self) -> int:
        line, column = self.getpos()
        return self.line_starts[line - 1] + column

    def _record(self, tag: str, attrs: list[tuple[str, Optional[str]]], push: bool) -> None:
        lowered = tag.lower()
        if lowered == "img":
            raw = self.get_starttag_text() or ""
            context: set[str] = set()
            for _, classes in self.stack:
                context.update(classes)
            start = self._offset()
            self.images.append(
                ImageOccurrence(start, start + len(raw), list(attrs), frozenset(context))
            )
        elif push and lowered not in VOID_ELEMENTS:
            self.stack.append((lowered, self._classes(attrs)))

    def handle_starttag(self, tag: str, attrs: list[tuple[str, Optional[str]]]) -> None:
        self._record(tag, attrs, True)

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, Optional[str]]]) -> None:
        self._record(tag, attrs, False)

    def handle_endtag(self, tag: str) -> None:
        lowered = tag.lower()
        for index in range(len(self.stack) - 1, -1, -1):
            if self.stack[index][0] == lowered:
                del self.stack[index:]
                return


def normalized_remote_url(value: str) -> str:
    raw = html.unescape(str(value or "").strip())
    parsed = urlsplit(raw)
    if parsed.scheme.lower() not in {"http", "https"} or not parsed.hostname:
        return raw
    port = f":{parsed.port}" if parsed.port else ""
    return urlunsplit(
        (parsed.scheme.lower(), (parsed.hostname or "").lower() + port, parsed.path, parsed.query, "")
    )


def focal_rule_for_source(value: str) -> Optional[FocalRule]:
    source = normalized_remote_url(value)
    if source == CJ_EMULOUS_SOURCE:
        return CJ_RULE
    parsed = urlsplit(source)
    lowered = source.casefold()
    if (
        (parsed.hostname or "").casefold() == "s1.ticketm.net"
        and "a49ecab3" in lowered
        and "_source" in lowered
    ):
        return HULVEY_RULE
    return None


def render_tag(
    attrs: list[tuple[str, Optional[str]]],
    updates: dict[str, Optional[str]],
) -> str:
    order: list[str] = []
    values: dict[str, Optional[str]] = {}
    for key, value in attrs:
        lowered = key.lower()
        if lowered not in values:
            order.append(lowered)
        values[lowered] = value
    for key, value in updates.items():
        lowered = key.lower()
        if value is None:
            values.pop(lowered, None)
            if lowered in order:
                order.remove(lowered)
        else:
            if lowered not in values:
                order.append(lowered)
            values[lowered] = value
    rendered = ["<img"]
    for key in order:
        if key not in values:
            continue
        value = values[key]
        if value is None:
            rendered.append(f" {key}")
        else:
            rendered.append(f' {key}="{html.escape(str(value), quote=True)}"')
    rendered.append(">")
    return "".join(rendered)


def artist_class(value: Optional[str]) -> str:
    classes = [
        item for item in str(value or "").split()
        if item not in {"artist-photo", "event-artwork"}
    ]
    classes.append("artist-photo")
    return " ".join(classes)


def style_with_position(value: Optional[str], position: str) -> str:
    declarations = []
    for item in str(value or "").split(";"):
        item = item.strip()
        if not item or item.split(":", 1)[0].strip().casefold() == "object-position":
            continue
        declarations.append(item)
    declarations.append(f"object-position:{position}")
    return ";".join(declarations)


def patch_html(text: str, *, focal_only: bool = False) -> tuple[str, int, int]:
    parser = SiteImageParser(text)
    parser.feed(text)
    replacements: list[tuple[int, int, str]] = []
    card_images = 0
    focal_images = 0
    for occurrence in parser.images:
        attrs = occurrence.attr_map
        updates: dict[str, Optional[str]] = {}
        if not focal_only and "event-media" in occurrence.context_classes:
            updates["sizes"] = CARD_SIZES
            card_images += 1
        rule = focal_rule_for_source(str(attrs.get("src") or ""))
        if rule is not None:
            updates.update(
                {
                    "class": artist_class(attrs.get("class")),
                    "style": style_with_position(attrs.get("style"), rule.position),
                    "data-kc-image-focal": rule.marker,
                }
            )
            focal_images += 1
        if updates:
            replacements.append(
                (occurrence.start, occurrence.end, render_tag(occurrence.attrs, updates))
            )
    for start, end, replacement in sorted(replacements, reverse=True):
        text = text[:start] + replacement + text[end:]
    if (
        not focal_only
        and "data-kc-test-image-overlay" not in text
        and re.search(r"</head>", text, re.I)
    ):
        text = re.sub(
            r"</head>",
            f'<link rel="stylesheet" href="{CSS_HREF}" data-kc-test-image-overlay>\n</head>',
            text,
            count=1,
            flags=re.I,
        )
    return text, card_images, focal_images


def patch_json(value: object, counts: dict[str, int]) -> None:
    if isinstance(value, dict):
        matched: Optional[FocalRule] = None
        for key, child in value.items():
            if key.casefold() in IMAGE_JSON_KEYS and isinstance(child, str):
                rule = focal_rule_for_source(child)
                if rule is not None:
                    matched = rule
                    break
        if matched is not None:
            value["imageType"] = "artist"
            value["imagePosition"] = matched.position
            counts[matched.marker] = counts.get(matched.marker, 0) + 1
        for child in value.values():
            patch_json(child, counts)
    elif isinstance(value, list):
        for child in value:
            patch_json(child, counts)


def validate_target(site: Path) -> None:
    if not site.is_dir() or not (site / "index.html").is_file():
        raise SystemExit(f"Not a completed test artifact: {site}")
    if (site / ".git").exists():
        raise SystemExit("Refusing to modify a Git worktree. Pass a generated artifact such as _site.")
    try:
        Path(__file__).resolve().relative_to(site.resolve())
    except ValueError:
        return
    raise SystemExit("Refusing to modify the directory containing this overlay script.")


def apply(site: Path, *, focal_only: bool = False) -> dict[str, object]:
    validate_target(site)
    if not focal_only:
        assets = site / "assets"
        assets.mkdir(parents=True, exist_ok=True)
        (assets / CSS_NAME).write_text(OVERLAY_CSS, encoding="utf-8")

    html_pages = 0
    changed_pages = 0
    card_images = 0
    focal_images = 0
    for path in sorted(site.rglob("*.html")):
        original = path.read_text(encoding="utf-8")
        updated, page_cards, page_focals = patch_html(original, focal_only=focal_only)
        html_pages += 1
        card_images += page_cards
        focal_images += page_focals
        if updated != original:
            path.write_text(updated, encoding="utf-8")
            changed_pages += 1

    json_counts: dict[str, int] = {}
    json_files = 0
    for relative in PUBLIC_JSON_FILES:
        path = site / relative
        if not path.is_file():
            continue
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise SystemExit(f"Invalid public JSON: {relative}: {exc}") from exc
        patch_json(value, json_counts)
        path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        json_files += 1

    return {
        "scope": "focal-preparation" if focal_only else "test-image-only",
        "htmlPages": html_pages,
        "htmlPagesChanged": changed_pages,
        "eventCardImagesSized": card_images,
        "focalHtmlImagesNormalized": focal_images,
        "jsonFilesChecked": json_files,
        "focalJsonRecordsNormalized": dict(sorted(json_counts.items())),
    }


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("site", type=Path, help="completed mirrored test artifact")
    parser.add_argument(
        "--focal-only",
        action="store_true",
        help="prepare focal metadata before optimization without adding test CSS or card sizing",
    )
    args = parser.parse_args(argv)
    report = apply(args.site.expanduser().resolve(), focal_only=args.focal_only)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
