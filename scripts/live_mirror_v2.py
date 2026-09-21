from __future__ import annotations

import hashlib
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

INTERNAL_PATH_PREFIXES = (
    "assets/",
    "artists/",
    "config/",
    "event/",
    "festivals/",
    "new-shows/",
    "shows/",
    "submit/",
)
INTERNAL_ROOT_FILES = (
    "app.js",
    "events.json",
    "robots.txt",
    "run-status.json",
    "seo-enhancements.js",
    "seo-static.js",
    "sitemap.xml",
    "styles.css",
    "supplemental-events.json",
)
PARITY_DATA_FILES = (
    "events.json",
    "supplemental-events.json",
    "config/artists.json",
)
OMITTED_REPORT_FILES = frozenset(
    {
        "artwork-audit.json",
        "run-status.json",
        "sep12-closeout-report.json",
        "seo-build-manifest.json",
        "seo-indexing-policy.json",
        "seo-overlay-manifest.json",
    }
)
ROOT_SITE_TARGET = (
    r"(?:(?:assets|artists|config|event|festivals|new-shows|shows|submit)/)"
    r"|(?:app\.js|events\.json|robots\.txt|run-status\.json|"
    r"seo-enhancements\.js|seo-static\.js|sitemap\.xml|styles\.css|"
    r"supplemental-events\.json)"
)
ROOT_SITE_REFERENCE = re.compile(
    rf"(?P<prefix>[\"'`(=,\s]|&#x27;|&quot;)/(?P<path>{ROOT_SITE_TARGET})",
    re.I,
)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def rewrite_site_urls(text: str) -> str:
    return text.replace(LIVE_SITE + "/", TEST_SITE + "/").replace(LIVE_SITE, TEST_SITE)


def rewrite_root_paths(text: str) -> str:
    # Prefix root-relative site references in attributes, JavaScript strings,
    # HTML-encoded event handlers, CSS url() values, and every srcset candidate.
    # The prefix requirement avoids touching /assets/ inside third-party URLs.
    return ROOT_SITE_REFERENCE.sub(
        lambda match: match.group("prefix") + TEST_BASE + match.group("path"),
        text,
    )


def rewrite_html(text: str) -> str:
    text = rewrite_site_urls(text).replace(LIVE_GA, TEST_GA)
    text = re.sub(
        r'(?P<prefix>\b(?:href|src|action)=["\'])/(?!/)',
        lambda match: match.group("prefix") + TEST_BASE,
        text,
    )
    text = rewrite_root_paths(text)
    robots = re.compile(
        r'<meta\s+name=["\']robots["\']\s+content=["\'][^"\']*["\']\s*/?>',
        re.I,
    )
    if robots.search(text):
        text = robots.sub('<meta name="robots" content="noindex,nofollow">', text)
    elif "<head>" in text:
        text = text.replace(
            "<head>",
            '<head>\n  <meta name="robots" content="noindex,nofollow">',
            1,
        )
    return text


def rewrite_js(text: str) -> str:
    text = rewrite_site_urls(text).replace(LIVE_GA, TEST_GA)
    text = text.replace('const BASE = "/";', f'const BASE = "{TEST_BASE}";')
    text = re.sub(
        r"const LIVE_EVENTS_URL\s*=\s*[^;]+;",
        'const LIVE_EVENTS_URL = `${BASE}events.json`;',
        text,
        count=1,
    )
    text = re.sub(
        r"const LIVE_ARTISTS_URL\s*=\s*[^;]+;",
        'const LIVE_ARTISTS_URL = `${BASE}config/artists.json`;',
        text,
        count=1,
    )
    return rewrite_root_paths(text)


def rewrite_css(text: str) -> str:
    text = rewrite_site_urls(text)
    text = re.sub(
        r"url\((?P<quote>['\"]?)/(?P<path>assets/)",
        lambda match: f"url({match.group('quote')}{TEST_BASE}{match.group('path')}",
        text,
        flags=re.I,
    )
    return rewrite_root_paths(text)


def rewrite_xml(text: str) -> str:
    return rewrite_site_urls(text)


def transformed_bytes(relative: pathlib.Path, source: bytes) -> bytes:
    if relative.as_posix() == "robots.txt":
        return b"User-agent: *\nDisallow: /\n"

    suffix = relative.suffix.casefold()
    if suffix not in {".html", ".js", ".css", ".xml"}:
        return source

    text = source.decode("utf-8")
    if suffix == ".html":
        text = rewrite_html(text)
    elif suffix == ".js":
        text = rewrite_js(text)
    elif suffix == ".css":
        text = rewrite_css(text)
    else:
        text = rewrite_xml(text)
    return text.encode("utf-8")


def write_test_copy(live_dir: pathlib.Path, out_dir: pathlib.Path) -> int:
    changed_for_environment = 0
    for live_path in sorted(live_dir.rglob("*")):
        if not live_path.is_file():
            continue
        relative = live_path.relative_to(live_dir)
        if relative.as_posix() == "CNAME" or relative.as_posix() in OMITTED_REPORT_FILES:
            continue
        source = live_path.read_bytes()
        output = transformed_bytes(relative, source)
        if output != source:
            changed_for_environment += 1
        target = out_dir / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(output)
    return changed_for_environment


def verify_exact_mirror(live_dir: pathlib.Path, out_dir: pathlib.Path) -> dict[str, object]:
    failures: list[str] = []
    source_files = {
        path.relative_to(live_dir)
        for path in live_dir.rglob("*")
        if path.is_file()
        and path.relative_to(live_dir).as_posix() != "CNAME"
        and path.relative_to(live_dir).as_posix() not in OMITTED_REPORT_FILES
    }
    output_files = {
        path.relative_to(out_dir)
        for path in out_dir.rglob("*")
        if path.is_file()
    }
    if source_files != output_files:
        for relative in sorted(source_files - output_files):
            failures.append(f"missing:{relative}")
        for relative in sorted(output_files - source_files):
            failures.append(f"unexpected:{relative}")

    adjusted_files = 0
    binary_assets = 0
    for relative in sorted(source_files):
        live_path = live_dir / relative
        test_path = out_dir / relative
        if not test_path.is_file():
            continue
        source = live_path.read_bytes()
        expected = transformed_bytes(relative, source)
        actual = test_path.read_bytes()
        if actual != expected:
            failures.append(f"content-mismatch:{relative}")
        if expected != source:
            adjusted_files += 1
        if relative.parts and relative.parts[0] == "assets" and relative.suffix.casefold() not in {".html", ".js", ".css", ".xml"}:
            binary_assets += 1
            if sha256_bytes(actual) != sha256_bytes(source):
                failures.append(f"binary-asset-mismatch:{relative}")

    for relative in PARITY_DATA_FILES:
        live_path = live_dir / relative
        test_path = out_dir / relative
        if not live_path.is_file() or not test_path.is_file():
            failures.append(f"parity-data-missing:{relative}")
        elif sha256_bytes(live_path.read_bytes()) != sha256_bytes(test_path.read_bytes()):
            failures.append(f"parity-data-mismatch:{relative}")

    bad_root = re.compile(
        r'\b(?:href|src|action)=["\']/(?!kingdom-circuit-test(?:/|["\']))'
    )
    html_files = 0
    for page in out_dir.rglob("*.html"):
        html_files += 1
        text = page.read_text(encoding="utf-8")
        relative = page.relative_to(out_dir)
        if '<meta name="robots" content="noindex,nofollow">' not in text:
            failures.append(f"indexable:{relative}")
        if bad_root.search(text):
            failures.append(f"bad-root-path:{relative}")
        if ROOT_SITE_REFERENCE.search(text):
            failures.append(f"unprefixed-site-path:{relative}")
        if LIVE_GA in text:
            failures.append(f"live-analytics:{relative}")

    app = (out_dir / "app.js").read_text(encoding="utf-8")
    if f'const BASE = "{TEST_BASE}";' not in app:
        failures.append("app-base-not-rewritten")
    if (out_dir / "CNAME").exists():
        failures.append("cname-present")
    for relative in sorted(OMITTED_REPORT_FILES):
        if (out_dir / relative).exists():
            failures.append(f"operational-report-present:{relative}")
    robots = (out_dir / "robots.txt").read_text(encoding="utf-8")
    if robots != "User-agent: *\nDisallow: /\n":
        failures.append("robots-policy")

    if failures:
        raise SystemExit(json.dumps({"failures": failures[:100]}, indent=2))
    return {
        "sourceFileCount": len(source_files),
        "htmlPageCount": html_files,
        "environmentAdjustedFileCount": adjusted_files,
        "byteIdenticalBinaryAssetCount": binary_assets,
    }


def main() -> None:
    if len(sys.argv) not in {4, 5}:
        raise SystemExit(
            "usage: live_mirror_v2.py LIVE_ARTIFACT TEST_OUTPUT LIVE_SHA [LIVE_RUN_ID]"
        )
    live_dir = pathlib.Path(sys.argv[1]).resolve()
    out_dir = pathlib.Path(sys.argv[2]).resolve()
    live_sha = sys.argv[3]
    live_run_id = sys.argv[4] if len(sys.argv) == 5 else ""
    if not (live_dir / "index.html").is_file():
        raise SystemExit(f"Missing live artifact: {live_dir}")

    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True)
    changed_for_environment = write_test_copy(live_dir, out_dir)
    parity = verify_exact_mirror(live_dir, out_dir)
    if parity["environmentAdjustedFileCount"] != changed_for_environment:
        raise SystemExit("Environment-adjusted file count changed during verification")

    manifest = {
        "mode": "exact-live-artifact-mirror",
        "liveCommit": live_sha,
        "liveDeploymentRunId": live_run_id,
        "source": "https://kingdomcircuit.com (deployed site snapshot)",
        "captureAuthority": "published-live-site",
        "testBase": TEST_BASE,
        "contentAndLayoutParity": True,
        "dataFilesByteIdentical": True,
        "binaryAssetsByteIdentical": True,
        "testRegistryOverlayApplied": False,
        "testOnlyDifferences": [
            "GitHub Pages project-path URLs",
            "test-site canonical URLs",
            "noindex,nofollow and robots Disallow",
            "production analytics disabled",
            "production CNAME omitted",
            "operational build reports omitted",
        ],
        "omittedOperationalReports": sorted(OMITTED_REPORT_FILES),
        "testNoindex": True,
        "liveAnalyticsDisabled": True,
        "cnameRemoved": True,
        **parity,
    }
    (out_dir / ".nojekyll").touch()
    (out_dir / "test-live-mirror-manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
