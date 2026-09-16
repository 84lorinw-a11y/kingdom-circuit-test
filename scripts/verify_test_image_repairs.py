#!/usr/bin/env python3
"""Verify the test-only image overlay and responsive-image contract."""

from __future__ import annotations

import argparse
import html
import json
from pathlib import Path
import re
import sys
from typing import Iterator, Optional, Sequence
from urllib.parse import urlsplit

from apply_test_image_repairs import (
    CARD_SIZES,
    CJ_RULE,
    CSS_HREF,
    CSS_NAME,
    HULVEY_RULE,
    IMAGE_JSON_KEYS,
    OVERLAY_CSS,
    PUBLIC_JSON_FILES,
    SiteImageParser,
    focal_rule_for_source,
)


FOCAL_RULES = {
    CJ_RULE.marker: CJ_RULE,
    HULVEY_RULE.marker: HULVEY_RULE,
}
SRCSET_WIDTH = re.compile(r"\s([1-9][0-9]*)w(?:\s*$|\s*,)")


def image_basename(value: str) -> str:
    return Path(urlsplit(html.unescape(str(value or ""))).path).name


def style_property(value: Optional[str], name: str) -> str:
    target = name.casefold()
    for declaration in str(value or "").split(";"):
        key, separator, child = declaration.partition(":")
        if separator and key.strip().casefold() == target:
            return child.strip()
    return ""


def iter_json_image_records(value: object) -> Iterator[tuple[dict[str, object], str]]:
    if isinstance(value, dict):
        for key, child in value.items():
            if key.casefold() in IMAGE_JSON_KEYS and isinstance(child, str):
                yield value, child
            yield from iter_json_image_records(child)
    elif isinstance(value, list):
        for child in value:
            yield from iter_json_image_records(child)


def verify(site: Path) -> tuple[list[str], dict[str, object]]:
    failures: list[str] = []
    css_path = site / "assets" / CSS_NAME
    if not css_path.is_file():
        failures.append(f"missing:assets/{CSS_NAME}")
        css = ""
    else:
        css = css_path.read_text(encoding="utf-8")
        for name, needle in {
            "uniform-4-by-3": "aspect-ratio: 4 / 3 !important",
            "artist-cover": ".event-card .event-media img.artist-photo",
            "artist-cover-fit": "object-fit: cover !important",
            "poster-contain": ".event-card .event-media img.event-artwork",
            "poster-contain-fit": "object-fit: contain !important",
        }.items():
            if needle not in css:
                failures.append(f"overlay-css:{name}")
        if css != OVERLAY_CSS:
            failures.append("overlay-css:unexpected-content")

    html_pages = 0
    event_card_images = 0
    focal_html_counts = {marker: 0 for marker in FOCAL_RULES}
    marker_basenames: dict[str, set[str]] = {marker: set() for marker in FOCAL_RULES}
    optimized_1280_candidates = 0
    optimized_1280_present = 0
    for page in sorted(site.rglob("*.html")):
        relative = page.relative_to(site).as_posix()
        text = page.read_text(encoding="utf-8")
        html_pages += 1
        if re.search(r"<head\b", text, re.I):
            if CSS_HREF not in text or "data-kc-test-image-overlay" not in text:
                failures.append(f"overlay-link:{relative}")
        parser = SiteImageParser(text)
        parser.feed(text)
        for occurrence in parser.images:
            attrs = occurrence.attr_map
            source = str(attrs.get("src") or "")
            source_rule = focal_rule_for_source(source)
            marker = str(attrs.get("data-kc-image-focal") or "")
            if "event-media" in occurrence.context_classes:
                event_card_images += 1
                if attrs.get("sizes") != CARD_SIZES:
                    failures.append(f"event-card-sizes:{relative}:{source[:80]}")
            if source_rule is not None and marker != source_rule.marker:
                failures.append(f"unmarked-focal-source:{relative}:{source_rule.marker}")
            if not marker:
                continue
            rule = FOCAL_RULES.get(marker)
            if rule is None:
                failures.append(f"unknown-focal-marker:{relative}:{marker}")
                continue
            focal_html_counts[marker] += 1
            marker_basenames[marker].add(image_basename(source))
            classes = set(str(attrs.get("class") or "").split())
            if "artist-photo" not in classes or "event-artwork" in classes:
                failures.append(f"focal-class:{relative}:{marker}")
            if style_property(attrs.get("style"), "object-position") != rule.position:
                failures.append(f"focal-position:{relative}:{marker}")
            try:
                rendered_width = int(str(attrs.get("width") or "0"))
            except ValueError:
                rendered_width = 0
            optimized_source = "/assets/optimized/" in urlsplit(
                html.unescape(source)
            ).path
            if optimized_source and rendered_width >= 1280:
                optimized_1280_candidates += 1
                srcset_widths = {
                    int(match.group(1))
                    for match in SRCSET_WIDTH.finditer(str(attrs.get("srcset") or "") + ",")
                }
                if 1280 in srcset_widths:
                    optimized_1280_present += 1
                else:
                    failures.append(f"focal-srcset-missing-1280:{relative}:{marker}")

    for marker, count in focal_html_counts.items():
        if count == 0:
            failures.append(f"focal-html-missing:{marker}")
    if event_card_images == 0:
        failures.append("event-card-images-missing")

    json_counts = {marker: 0 for marker in FOCAL_RULES}
    json_files = 0
    for relative in PUBLIC_JSON_FILES:
        path = site / relative
        if not path.is_file():
            continue
        json_files += 1
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            failures.append(f"invalid-json:{relative}:{exc.lineno}")
            continue
        seen_records: set[int] = set()
        for record, source in iter_json_image_records(value):
            rule = focal_rule_for_source(source)
            if rule is None:
                basename = image_basename(source)
                matching = [
                    FOCAL_RULES[marker]
                    for marker, basenames in marker_basenames.items()
                    if basename and basename in basenames
                ]
                rule = matching[0] if len(matching) == 1 else None
            if rule is None or id(record) in seen_records:
                continue
            seen_records.add(id(record))
            json_counts[rule.marker] += 1
            if record.get("imageType") != "artist":
                failures.append(f"focal-json-class:{relative}:{rule.marker}")
            if record.get("imagePosition") != rule.position:
                failures.append(f"focal-json-position:{relative}:{rule.marker}")

    for marker, count in json_counts.items():
        if count == 0:
            failures.append(f"focal-json-missing:{marker}")

    manifest_path = site / "assets" / "optimized" / "manifest.json"
    requested_widths: list[int] = []
    if manifest_path.is_file():
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            requested_widths = [int(width) for width in manifest.get("requestedWidths", [])]
        except (json.JSONDecodeError, TypeError, ValueError):
            failures.append("optimized-manifest-invalid")
        else:
            if 1280 not in requested_widths:
                failures.append("optimized-manifest-missing-1280")

    report: dict[str, object] = {
        "htmlPages": html_pages,
        "eventCardImages": event_card_images,
        "focalHtmlImages": focal_html_counts,
        "jsonFiles": json_files,
        "focalJsonRecords": json_counts,
        "requestedWidths": requested_widths,
        "optimizedFocalImagesEligibleFor1280": optimized_1280_candidates,
        "optimizedFocalImagesWith1280": optimized_1280_present,
    }
    return failures, report


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("site", type=Path, help="completed test artifact")
    args = parser.parse_args(argv)
    site = args.site.expanduser().resolve()
    if not site.is_dir() or not (site / "index.html").is_file():
        print(f"error: not a completed test artifact: {site}", file=sys.stderr)
        return 2
    failures, report = verify(site)
    if failures:
        print("Image repair verification failed:", file=sys.stderr)
        for failure in failures[:100]:
            print(f"- {failure}", file=sys.stderr)
        return 1
    print(json.dumps({"verified": True, **report}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
