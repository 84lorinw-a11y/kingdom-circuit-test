from __future__ import annotations

import argparse
import html
import json
import pathlib
import re
import sys
from dataclasses import dataclass, field
from html.parser import HTMLParser
from typing import Iterable


TEST_BASE = "/kingdom-circuit-test/"
PRODUCTION_GA = "G-N2KK9XF4TJ"
REDESIGN_CSS = pathlib.Path("assets/kc-redesign-v1.css")
REDESIGN_JS = pathlib.Path("assets/kc-redesign-v1.js")
MANIFEST = pathlib.Path("test-redesign-manifest.json")
MANIFEST_MODE = "mobile-first-test-redesign-v1"
TITLE_LINES = ["Find Christian", "Hip Hop Shows", "Near You!"]
OLD_HEADER_CLASSES = {"site-header", "menu-toggle", "menu-drawer"}
VOID_TAGS = {
    "area",
    "base",
    "br",
    "col",
    "embed",
    "hr",
    "img",
    "input",
    "link",
    "meta",
    "param",
    "source",
    "track",
    "wbr",
}


@dataclass
class Node:
    tag: str
    attrs: dict[str, str]
    children: list["Node"] = field(default_factory=list)
    data: list[str] = field(default_factory=list)

    @property
    def classes(self) -> set[str]:
        return {part for part in self.attrs.get("class", "").split() if part}

    def descendants(self, *, include_self: bool = False) -> Iterable["Node"]:
        if include_self:
            yield self
        for child in self.children:
            yield child
            yield from child.descendants()

    def text_content(self) -> str:
        pieces = list(self.data)
        for child in self.children:
            pieces.append(child.text_content())
        return " ".join(piece for piece in pieces if piece)


class DocumentParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.roots: list[Node] = []
        self.nodes: list[Node] = []
        self.stack: list[Node] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        node = Node(
            tag.casefold(),
            {str(key).casefold(): "" if value is None else str(value) for key, value in attrs},
        )
        self.nodes.append(node)
        if self.stack:
            self.stack[-1].children.append(node)
        else:
            self.roots.append(node)
        if node.tag not in VOID_TAGS:
            self.stack.append(node)

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.handle_starttag(tag, attrs)
        if self.stack and self.stack[-1].tag == tag.casefold():
            self.stack.pop()

    def handle_endtag(self, tag: str) -> None:
        wanted = tag.casefold()
        for index in range(len(self.stack) - 1, -1, -1):
            if self.stack[index].tag == wanted:
                del self.stack[index:]
                return

    def handle_data(self, data: str) -> None:
        if self.stack:
            self.stack[-1].data.append(data)


@dataclass
class ParsedPage:
    path: pathlib.Path
    relative: pathlib.Path
    source: str
    document: DocumentParser

    def by_class(self, class_name: str) -> list[Node]:
        return [node for node in self.document.nodes if class_name in node.classes]

    def by_attr(self, name: str, value: str | None = None) -> list[Node]:
        key = name.casefold()
        if value is None:
            return [node for node in self.document.nodes if key in node.attrs]
        return [node for node in self.document.nodes if node.attrs.get(key) == value]


def normalized_text(value: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(value)).strip()


def parse_page(path: pathlib.Path, root: pathlib.Path) -> ParsedPage:
    source = path.read_text(encoding="utf-8", errors="strict")
    parser = DocumentParser()
    parser.feed(source)
    parser.close()
    return ParsedPage(path, path.relative_to(root), source, parser)


def count_marker_articles(source: str, marker: str) -> int:
    return len(
        re.findall(
            rf"<article\b(?=[^>]*\b{re.escape(marker)}\b)[^>]*>",
            source,
            flags=re.I,
        )
    )


def integer_from(node: Node | None) -> int | None:
    if node is None:
        return None
    match = re.search(r"\d[\d,]*", normalized_text(node.text_content()))
    return int(match.group(0).replace(",", "")) if match else None


def internal_path_failures(page: ParsedPage) -> list[str]:
    failures: list[str] = []
    allowed_root = TEST_BASE.rstrip("/")
    for node in page.document.nodes:
        for name in ("href", "src", "action", "poster"):
            value = node.attrs.get(name, "").strip()
            if value.startswith("/") and not value.startswith("//"):
                if value != allowed_root and not value.startswith(TEST_BASE):
                    failures.append(f"{page.relative}:{node.tag}[{name}]={value}")
        srcset = node.attrs.get("srcset", "")
        for candidate in srcset.split(","):
            value = candidate.strip().split(" ", 1)[0]
            if value.startswith("/") and not value.startswith("//"):
                if value != allowed_root and not value.startswith(TEST_BASE):
                    failures.append(f"{page.relative}:{node.tag}[srcset]={value}")
    return failures


def has_asset_reference(page: ParsedPage, relative: pathlib.Path) -> bool:
    wanted = TEST_BASE + relative.as_posix()
    for node in page.document.nodes:
        value = node.attrs.get("href") or node.attrs.get("src") or ""
        if value == wanted or value.startswith(wanted + "?"):
            return True
    return False


def anchors_within(node: Node) -> list[Node]:
    return [item for item in node.descendants(include_self=True) if item.tag == "a"]


def first_anchor_href(node: Node) -> str:
    anchors = anchors_within(node)
    return anchors[0].attrs.get("href", "") if anchors else ""


def is_first_level_artist_profile(page: ParsedPage) -> bool:
    parts = page.relative.parts
    if len(parts) != 3 or parts[0] != "artists" or parts[2] != "index.html":
        return False
    if parts[1] == "profile":
        return False
    classes = {name for node in page.document.nodes for name in node.classes}
    return bool({"seo-artist-profile", "kc-rd-artist-profile"} & classes)


def audit_site(site_root: pathlib.Path | str) -> dict[str, object]:
    root = pathlib.Path(site_root).resolve()
    failures: list[str] = []

    def expect(condition: bool, message: str) -> None:
        if not condition:
            failures.append(message)

    expect(root.is_dir(), f"missing-site-root:{root}")
    css_path = root / REDESIGN_CSS
    js_path = root / REDESIGN_JS
    expect(css_path.is_file() and css_path.stat().st_size > 0, f"missing:{REDESIGN_CSS}")
    expect(js_path.is_file() and js_path.stat().st_size > 0, f"missing:{REDESIGN_JS}")
    css = css_path.read_text(encoding="utf-8", errors="ignore") if css_path.is_file() else ""
    expect(".kc-rd-header" in css, "redesign-css:missing-header-rule")
    expect(".kc-rd-directory-intro" in css, "redesign-css:missing-directory-intro-rule")
    expect(".kc-rd-profile-page" in css, "redesign-css:missing-profile-rule")

    pages: list[ParsedPage] = []
    for path in sorted(root.rglob("*.html")):
        try:
            pages.append(parse_page(path, root))
        except (OSError, UnicodeError) as exc:
            failures.append(f"unreadable-html:{path.relative_to(root)}:{exc}")
    expect(bool(pages), "no-html-pages")

    for page in pages:
        nodes = page.document.nodes
        all_classes = {class_name for node in nodes for class_name in node.classes}
        old = sorted(all_classes & OLD_HEADER_CLASSES)
        expect(not old, f"old-header:{page.relative}:{','.join(old)}")
        expect(bool(page.by_class("kc-rd-header")), f"missing-redesign-header:{page.relative}")
        followbars = page.by_class("kc-rd-followbar")
        expect(len(followbars) == 1, f"followbar-count:{page.relative}:{len(followbars)}")
        if len(followbars) == 1:
            expect("↗" not in followbars[0].text_content(), f"followbar-arrow:{page.relative}")
        robots = [
            node
            for node in nodes
            if node.tag == "meta" and node.attrs.get("name", "").casefold() == "robots"
        ]
        expect(
            any("noindex" in node.attrs.get("content", "").casefold() for node in robots),
            f"missing-noindex:{page.relative}",
        )
        expect(PRODUCTION_GA not in page.source, f"production-analytics:{page.relative}")
        expect(TEST_BASE in page.source, f"missing-test-base:{page.relative}")
        expect(has_asset_reference(page, REDESIGN_CSS), f"missing-redesign-css-link:{page.relative}")
        expect(has_asset_reference(page, REDESIGN_JS), f"missing-redesign-js-link:{page.relative}")
        failures.extend(f"unprefixed-local-link:{item}" for item in internal_path_failures(page))

    page_by_relative = {page.relative.as_posix(): page for page in pages}
    home = page_by_relative.get("index.html")
    directory = page_by_relative.get("artists/index.html")
    artist_submit = page_by_relative.get("submit/artist/index.html")
    expect(home is not None, "missing:index.html")
    expect(directory is not None, "missing:artists/index.html")
    expect(artist_submit is not None, "missing:submit/artist/index.html")

    home_show_count = 0
    home_artist_stat: int | None = None
    home_show_stat: int | None = None
    if home is not None:
        expect(bool(home.by_class("kc-rd-home")), "home:missing-kc-rd-home")
        line_nodes = home.by_class("kc-rd-title-line")
        if line_nodes:
            lines = [normalized_text(node.text_content()) for node in line_nodes]
        else:
            titles = home.by_class("kc-rd-home-title")
            lines = (
                [normalized_text(node.text_content()) for node in titles[0].children if node.tag == "span"]
                if len(titles) == 1
                else []
            )
        expect(lines == TITLE_LINES, f"home:title-lines:{lines!r}")
        home_classes = {name for node in home.document.nodes for name in node.classes}
        expect("trust-line" not in home_classes, "home:trust-line-present")
        expect("home-paths" not in home_classes, "home:home-paths-present")
        expect("hero-text" not in home_classes, "home:hero-text-present")
        expect("Verified listings".casefold() not in normalized_text(home.source).casefold(), "home:verified-listings-present")
        home_show_count = count_marker_articles(home.source, "data-event-card")
        show_nodes = home.by_attr("data-kc-rd-stat", "shows")
        artist_nodes = home.by_attr("data-kc-rd-stat", "artists")
        expect(len(show_nodes) == 1, f"home:show-stat-count:{len(show_nodes)}")
        expect(len(artist_nodes) == 1, f"home:artist-stat-count:{len(artist_nodes)}")
        home_show_stat = integer_from(show_nodes[0] if len(show_nodes) == 1 else None)
        home_artist_stat = integer_from(artist_nodes[0] if len(artist_nodes) == 1 else None)
        expect(home_show_stat == home_show_count, f"home:show-stat:{home_show_stat}!={home_show_count}")

    directory_artist_count = 0
    if directory is not None:
        expect(not directory.by_class("seo-directory-hero"), "directory:old-hero-present")
        expect(
            "Christian Hip-Hop Artists, Rappers & Upcoming Shows".casefold()
            not in normalized_text(directory.source).casefold(),
            "directory:old-title-present",
        )
        expect(
            "Browse the Kingdom Circuit directory of Christian hip-hop and Christian rap artists".casefold()
            not in normalized_text(directory.source).casefold(),
            "directory:old-description-present",
        )
        intros = directory.by_class("kc-rd-directory-intro")
        expect(len(intros) == 1, f"directory:intro-count:{len(intros)}")
        if len(intros) == 1:
            intro_text = normalized_text(intros[0].text_content())
            expect(len(intro_text) >= 20, "directory:intro-too-short")
            ctas = {
                normalized_text(anchor.text_content()): anchor.attrs.get("href", "")
                for anchor in anchors_within(intros[0])
            }
            expect(ctas.get("Submit a Show") == TEST_BASE + "submit/", "directory:submit-show-link")
            expect(
                ctas.get("Submit a CHH Artist to Be Listed") == TEST_BASE + "submit/artist/",
                "directory:submit-artist-link",
            )
        checkboxes = [
            node
            for node in directory.by_attr("data-has-shows-filter")
            if node.tag == "input" and node.attrs.get("type", "").casefold() == "checkbox"
        ]
        expect(len(checkboxes) == 1, f"directory:upcoming-checkbox-count:{len(checkboxes)}")
        directory_artist_count = count_marker_articles(directory.source, "data-artist-card")
        expect(directory_artist_count > 0, "directory:no-artist-cards")
        count_nodes = directory.by_class("kc-rd-directory-count")
        expect(len(count_nodes) == 1, f"directory:count-blocks:{len(count_nodes)}")
        expect(
            integer_from(count_nodes[0] if len(count_nodes) == 1 else None) == directory_artist_count,
            "directory:displayed-count-mismatch",
        )
        for index, next_show in enumerate(directory.by_class("seo-card-next")):
            expect(
                not re.search(r"\b\d{1,2}:\d{2}\s*(?:AM|PM)\b", next_show.text_content(), re.I),
                f"directory:next-show-time:{index}",
            )
        expect(
            home_artist_stat == directory_artist_count,
            f"home:artist-stat:{home_artist_stat}!={directory_artist_count}",
        )

    if artist_submit is not None:
        forms = [node for node in artist_submit.by_class("kc-rd-artist-submit") if node.tag == "form"]
        expect(len(forms) == 1, f"artist-submit:form-count:{len(forms)}")
        if len(forms) == 1:
            fields = [node for node in forms[0].descendants() if node.tag in {"input", "textarea", "select"}]
            by_name = {node.attrs.get("name", ""): node for node in fields}
            artist_name = by_name.get("artistName")
            official_url = by_name.get("officialUrl")
            environment = by_name.get("environment")
            expect(artist_name is not None and "required" in artist_name.attrs, "artist-submit:artist-name-required")
            expect(
                official_url is not None
                and "required" in official_url.attrs
                and official_url.attrs.get("type", "").casefold() == "url",
                "artist-submit:official-url-required",
            )
            expect(
                environment is not None
                and environment.attrs.get("type", "").casefold() == "hidden"
                and environment.attrs.get("value") == "test",
                "artist-submit:test-environment-hidden",
            )

    profile_pages = [page for page in pages if is_first_level_artist_profile(page)]
    profile_show_rows = 0
    profile_pages_with_past = 0
    for page in profile_pages:
        new_profiles = page.by_class("kc-rd-artist-profile")
        expect(len(new_profiles) == 1, f"profile:marker-count:{page.relative}:{len(new_profiles)}")
        expect(not page.by_class("seo-artist-profile"), f"profile:old-layout-present:{page.relative}")
        upcoming_totals = page.by_class("kc-rd-upcoming-total")
        expect(len(upcoming_totals) == 1, f"profile:upcoming-total-count:{page.relative}:{len(upcoming_totals)}")
        if len(upcoming_totals) == 1:
            expect(
                bool(re.fullmatch(r"\d+\s+upcoming", normalized_text(upcoming_totals[0].text_content()), re.I)),
                f"profile:upcoming-total-text:{page.relative}",
            )
        rows = page.by_class("kc-rd-show-row")
        profile_show_rows += len(rows)
        for index, row in enumerate(rows):
            expect(bool(normalized_text(row.text_content())), f"profile:empty-show-row:{page.relative}:{index}")
            expect(bool(first_anchor_href(row)), f"profile:unlinked-show-row:{page.relative}:{index}")
        if rows:
            next_blocks = page.by_class("kc-rd-next-show")
            lists = page.by_class("kc-rd-show-list")
            expect(len(next_blocks) == 1, f"profile:next-count:{page.relative}:{len(next_blocks)}")
            expect(len(lists) == 1, f"profile:list-count:{page.relative}:{len(lists)}")
            if len(next_blocks) == 1:
                next_href = first_anchor_href(next_blocks[0])
                expect(bool(next_href), f"profile:next-unlinked:{page.relative}")
                expect(
                    next_href == first_anchor_href(rows[0]),
                    f"profile:next-not-repeated-first:{page.relative}",
                )
        past_blocks = page.by_class("kc-rd-past-shows")
        profile_pages_with_past += int(bool(past_blocks))
        for past in past_blocks:
            details = [node for node in past.descendants(include_self=True) if node.tag == "details"]
            expect(len(details) == 1, f"profile:past-details-count:{page.relative}:{len(details)}")
            if len(details) == 1:
                expect("open" not in details[0].attrs, f"profile:past-open-by-default:{page.relative}")
                expect(
                    any(node.tag == "summary" for node in details[0].descendants()),
                    f"profile:past-summary-missing:{page.relative}",
                )

    manifest_path = root / MANIFEST
    manifest: dict[str, object] = {}
    expect(manifest_path.is_file(), f"missing:{MANIFEST}")
    if manifest_path.is_file():
        try:
            loaded = json.loads(manifest_path.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                manifest = loaded
            else:
                failures.append("manifest:not-object")
        except (OSError, json.JSONDecodeError) as exc:
            failures.append(f"manifest:invalid-json:{exc}")
    expected_manifest = {
        "mode": MANIFEST_MODE,
        "showCount": home_show_count,
        "artistCount": directory_artist_count,
        "profilePageCount": len(profile_pages),
        "profileShowRowCount": profile_show_rows,
        "profilePagesWithPastShows": profile_pages_with_past,
        "headerPageCount": len(pages),
        "artistSubmissionPath": TEST_BASE + "submit/artist/",
        "productionChanged": False,
    }
    for key, expected in expected_manifest.items():
        expect(manifest.get(key) == expected, f"manifest:{key}:{manifest.get(key)!r}!={expected!r}")
    if "htmlPageCount" in manifest:
        expect(manifest.get("htmlPageCount") == len(pages), f"manifest:htmlPageCount:{manifest.get('htmlPageCount')}!={len(pages)}")

    return {
        "mode": MANIFEST_MODE,
        "siteRoot": str(root),
        "htmlPageCount": len(pages),
        "showCount": home_show_count,
        "artistCount": directory_artist_count,
        "profilePageCount": len(profile_pages),
        "profileShowRowCount": profile_show_rows,
        "profilePagesWithPastShows": profile_pages_with_past,
        "failures": failures,
    }


def verify_site(site_root: pathlib.Path | str) -> dict[str, object]:
    report = audit_site(site_root)
    failures = report["failures"]
    if failures:
        raise AssertionError("Test redesign verification failed:\n" + "\n".join(str(item) for item in failures))
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Verify the Kingdom Circuit test-only redesign artifact.")
    parser.add_argument("site_root", type=pathlib.Path)
    args = parser.parse_args(argv)
    report = audit_site(args.site_root)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 1 if report["failures"] else 0


if __name__ == "__main__":
    sys.exit(main())
