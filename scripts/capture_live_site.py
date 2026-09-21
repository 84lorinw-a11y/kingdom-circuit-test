#!/usr/bin/env python3
"""Capture the currently published Kingdom Circuit site as a static artifact."""

from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import html
import json
import pathlib
import re
import shutil
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET


USER_AGENT = "KingdomCircuitTestMirror/2.0"
DEFAULT_ORIGIN = "https://kingdomcircuit.com"
DEFAULT_SEEDS = (
    "/",
    "/404.html",
    "/artists/profile/",
    "/event/",
    "/submit/",
    "/styles.css",
    "/app.js",
    "/seo-static.js",
    "/seo-enhancements.js",
    "/events.json",
    "/supplemental-events.json",
    "/config/artists.json",
    "/robots.txt",
    "/sitemap.xml",
)
OMITTED_OPERATIONAL_PATHS = frozenset(
    {
        "/artwork-audit.json",
        "/run-status.json",
        "/sep12-closeout-report.json",
        "/seo-build-manifest.json",
        "/seo-indexing-policy.json",
        "/seo-overlay-manifest.json",
    }
)

ATTRIBUTE_URL = re.compile(
    r"\b(?:href|src|action|poster)\s*=\s*[\"']([^\"']+)[\"']",
    re.I,
)
SRCSET = re.compile(r"\bsrcset\s*=\s*[\"']([^\"']+)[\"']", re.I)
CSS_URL = re.compile(r"url\(\s*[\"']?([^\"')]+)", re.I)
CSS_IMPORT = re.compile(r"@import\s+(?:url\()?\s*[\"']([^\"']+)", re.I)
QUOTED_NETWORK_URL = re.compile(r"[\"']((?:https?:)?//[^\"'<>\s]+)[\"']", re.I)
QUOTED_SITE_PATH = re.compile(
    r"[\"'`](/(?:assets|artists|config|event|festivals|new-shows|shows|submit)/[^\"'`?#]*)"
)
JSON_LOCAL_PREFIXES = (
    "/",
    "assets/",
    "artists/",
    "config/",
    "event/",
    "festivals/",
    "new-shows/",
    "shows/",
    "submit/",
)
CONSISTENCY_PATHS = ("/", "/sitemap.xml", "/events.json")


def normalize_origin(value: str) -> str:
    parsed = urllib.parse.urlsplit(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError(f"Invalid site origin: {value}")
    return f"{parsed.scheme}://{parsed.netloc}"


def canonical_url(value: str, base_url: str, origin: str) -> str | None:
    value = html.unescape(value).strip()
    if not value or value.startswith(("#", "data:", "mailto:", "tel:", "javascript:")):
        return None
    absolute = urllib.parse.urljoin(base_url, value)
    parsed = urllib.parse.urlsplit(absolute)
    origin_parsed = urllib.parse.urlsplit(origin)
    if parsed.scheme not in {"http", "https"}:
        return None
    origin_host = origin_parsed.netloc.casefold()
    allowed_hosts = {origin_host}
    if origin_host.startswith("www."):
        allowed_hosts.add(origin_host.removeprefix("www."))
    else:
        allowed_hosts.add("www." + origin_host)
    if parsed.netloc.casefold() not in allowed_hosts:
        return None
    path = parsed.path or "/"
    if path in OMITTED_OPERATIONAL_PATHS:
        return None
    return urllib.parse.urlunsplit((origin_parsed.scheme, origin_parsed.netloc, path, "", ""))


def output_path(url: str, content_type: str, output: pathlib.Path) -> pathlib.Path:
    path = urllib.parse.unquote(urllib.parse.urlsplit(url).path)
    relative = pathlib.PurePosixPath(path.lstrip("/"))
    if path.endswith("/") or not relative.name:
        relative = relative / "index.html"
    elif "text/html" in content_type and not relative.suffix:
        relative = relative / "index.html"
    target = (output / pathlib.Path(*relative.parts)).resolve()
    if output.resolve() not in target.parents and target != output.resolve():
        raise ValueError(f"Unsafe output path: {url}")
    return target


def fetch(url: str, attempts: int = 3) -> tuple[str, str, bytes]:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "*/*",
            "Cache-Control": "no-cache",
        },
    )
    last_error: Exception | None = None
    for attempt in range(attempts):
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                content_type = response.headers.get_content_type()
                return response.geturl(), content_type, response.read()
        except urllib.error.HTTPError as error:
            if error.code == 404 and urllib.parse.urlsplit(url).path == "/404.html":
                return url, "text/html", error.read()
            last_error = error
        except (OSError, urllib.error.URLError) as error:
            last_error = error
        if attempt + 1 < attempts:
            time.sleep(0.4 * (attempt + 1))
    raise RuntimeError(f"Unable to capture {url}: {last_error}")


def strings_in_json(value: object):
    if isinstance(value, str):
        yield value
    elif isinstance(value, list):
        for item in value:
            yield from strings_in_json(item)
    elif isinstance(value, dict):
        for item in value.values():
            yield from strings_in_json(item)


def discovered_urls(
    url: str,
    content_type: str,
    payload: bytes,
    origin: str,
) -> tuple[set[str], set[str]]:
    references: set[str] = set()
    optional_references: set[str] = set()
    text_types = ("html", "css", "javascript", "json", "xml", "text")
    if not any(marker in content_type for marker in text_types):
        return references, optional_references
    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError:
        return references, optional_references

    raw_values: list[str] = []
    optional_values: list[str] = []
    if "html" in content_type:
        raw_values.extend(ATTRIBUTE_URL.findall(text))
        # Social-image metadata and JSON-LD use content fields or quoted URL
        # values rather than href/src attributes. Missing metadata images are
        # preserved as missing when the live site itself returns 404.
        optional_values.extend(QUOTED_NETWORK_URL.findall(text))
        for srcset in SRCSET.findall(text):
            raw_values.extend(
                candidate.strip().split()[0]
                for candidate in srcset.split(",")
                if candidate.strip()
            )
        raw_values.extend(CSS_URL.findall(text))
    elif "css" in content_type:
        raw_values.extend(CSS_URL.findall(text))
        raw_values.extend(CSS_IMPORT.findall(text))
    elif "json" in content_type:
        try:
            raw_values.extend(
                value
                for value in strings_in_json(json.loads(text))
                if value.strip().startswith(("http://", "https://") + JSON_LOCAL_PREFIXES)
            )
        except json.JSONDecodeError:
            pass
    elif "javascript" in content_type:
        raw_values.extend(QUOTED_SITE_PATH.findall(text))

    for value in raw_values:
        reference_base = url
        if "json" in content_type and not value.strip().startswith(
            ("http://", "https://", "/")
        ):
            # Runtime JSON stores site-root asset paths without a leading slash,
            # including config/artists.json. Resolve those from the origin rather
            # than from the JSON document's directory.
            reference_base = origin + "/"
        normalized = canonical_url(value, reference_base, origin)
        if normalized:
            references.add(normalized)
    for value in optional_values:
        normalized = canonical_url(value, url, origin)
        if normalized:
            optional_references.add(normalized)
    optional_references.difference_update(references)
    return references, optional_references


def sitemap_urls(origin: str) -> set[str]:
    sitemap_url = origin + "/sitemap.xml"
    _, _, payload = fetch(sitemap_url)
    root = ET.fromstring(payload)
    urls: set[str] = {sitemap_url}
    for element in root.iter():
        if element.tag.rsplit("}", 1)[-1] != "loc" or not element.text:
            continue
        normalized = canonical_url(element.text, sitemap_url, origin)
        if normalized:
            urls.add(normalized)
    return urls


def capture(
    origin: str,
    output: pathlib.Path,
    *,
    workers: int = 16,
    min_html: int = 1,
    min_files: int = 1,
) -> dict[str, object]:
    origin = normalize_origin(origin)
    if output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True)

    pending = sitemap_urls(origin)
    pending.update(origin + path for path in DEFAULT_SEEDS)
    required_urls = set(pending)
    seen: set[str] = set()
    failures: list[str] = []
    optional_failures: dict[str, str] = {}
    html_files = 0

    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
        while pending:
            batch = sorted(pending - seen)
            if not batch:
                break
            pending.clear()
            seen.update(batch)
            future_urls = {executor.submit(fetch, url): url for url in batch}
            for future in concurrent.futures.as_completed(future_urls):
                requested = future_urls[future]
                try:
                    final_url, content_type, payload = future.result()
                except RuntimeError as error:
                    if requested in required_urls:
                        failures.append(str(error))
                    else:
                        optional_failures[requested] = str(error)
                    continue
                target = output_path(requested, content_type, output)
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(payload)
                if "html" in content_type:
                    html_files += 1
                required, optional = discovered_urls(
                    final_url, content_type, payload, origin
                )
                required_urls.update(required)
                pending.update((required | optional) - seen)

    failures.extend(
        error
        for url, error in optional_failures.items()
        if url in required_urls
    )

    required = (
        "index.html",
        "404.html",
        "styles.css",
        "app.js",
        "seo-static.js",
        "seo-enhancements.js",
        "events.json",
        "supplemental-events.json",
        "config/artists.json",
        "robots.txt",
        "sitemap.xml",
        "artists/index.html",
        "artists/profile/index.html",
        "event/index.html",
        "submit/index.html",
    )
    missing = [relative for relative in required if not (output / relative).is_file()]
    consistency_failures: list[str] = []
    for path in CONSISTENCY_PATHS:
        saved = output / ("index.html" if path == "/" else path.lstrip("/"))
        if not saved.is_file():
            consistency_failures.append(f"missing-anchor:{path}")
            continue
        _, _, current = fetch(origin + path)
        if hashlib.sha256(saved.read_bytes()).digest() != hashlib.sha256(current).digest():
            consistency_failures.append(f"changed-during-capture:{path}")
    file_count = sum(1 for path in output.rglob("*") if path.is_file())
    if (
        missing
        or failures
        or consistency_failures
        or html_files < min_html
        or file_count < min_files
    ):
        raise SystemExit(
            json.dumps(
                {
                    "missing": missing,
                    "failures": failures[:50],
                    "consistencyFailures": consistency_failures,
                    "htmlFiles": html_files,
                    "fileCount": file_count,
                    "minimumHtml": min_html,
                    "minimumFiles": min_files,
                },
                indent=2,
            )
        )
    result = {
        "origin": origin,
        "htmlFiles": html_files,
        "fileCount": file_count,
        "capturedUrls": len(seen),
        "consistencyChecks": len(CONSISTENCY_PATHS),
        "optionalMissingMetadataFiles": sum(
            1 for url in optional_failures if url not in required_urls
        ),
    }
    print(json.dumps(result, indent=2))
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("origin")
    parser.add_argument("output", type=pathlib.Path)
    parser.add_argument("--workers", type=int, default=16)
    parser.add_argument("--min-html", type=int, default=800)
    parser.add_argument("--min-files", type=int, default=900)
    arguments = parser.parse_args()
    capture(
        arguments.origin,
        arguments.output,
        workers=arguments.workers,
        min_html=arguments.min_html,
        min_files=arguments.min_files,
    )


if __name__ == "__main__":
    main()
