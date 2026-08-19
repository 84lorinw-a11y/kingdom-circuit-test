from __future__ import annotations

import json
import pathlib
import re
import urllib.parse
import urllib.request

REPO = pathlib.Path.cwd()
OUT = REPO / "_site"
LIVE_APP_URL = "https://raw.githubusercontent.com/84lorinw-a11y/kingdom-circuit/main/app.js"
LIVE_ARTISTS_URL = "https://raw.githubusercontent.com/84lorinw-a11y/kingdom-circuit/main/config/artists.json"
LIVE_SITE = "https://kingdomcircuit.com/"
DEFAULT_IMAGE_ENDPOINT = "https://open.voidware.de/artist/"


def fetch_text(url: str) -> str:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Kingdom-Circuit-Test-Artist-Sync/1.0",
            "Accept": "text/plain,application/json;q=0.9,*/*;q=0.8",
        },
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read().decode("utf-8")


def norm(value) -> str:
    return str(value or "").strip().casefold()


def extract_object(source: str, marker: str) -> dict:
    marker_at = source.index(marker)
    start = source.index("{", marker_at + len(marker))
    depth = 0
    in_string = False
    escaped = False
    for index in range(start, len(source)):
        ch = source[index]
        if in_string:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == '"':
                in_string = False
            continue
        if ch == '"':
            in_string = True
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return json.loads(source[start:index + 1])
    raise ValueError(f"Could not find closing brace for {marker}")


def spotify_id(profile: str) -> str:
    match = re.search(r"open\.spotify\.com/artist/([^/?#]+)", str(profile or ""), re.I)
    return urllib.parse.unquote(match.group(1)) if match else ""


def absolute_live_image(value: str) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    if text.startswith("http://"):
        return "https://" + text[len("http://"):]
    if text.startswith("https://"):
        return text
    return urllib.parse.urljoin(LIVE_SITE, text.lstrip("/"))


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)

    app_source = fetch_text(LIVE_APP_URL)
    registry = extract_object(app_source, "const VERIFIED_ARTIST_REGISTRY =")
    live_artists = json.loads(fetch_text(LIVE_ARTISTS_URL))
    if not isinstance(live_artists, list):
        raise TypeError("Live artist config is not a list")

    endpoint_match = re.search(
        r'const\s+VERIFIED_ARTIST_IMAGE_ENDPOINT\s*=\s*["\']([^"\']+)["\']',
        app_source,
    )
    image_endpoint = endpoint_match.group(1) if endpoint_match else DEFAULT_IMAGE_ENDPOINT

    registry_lookup: dict[str, dict] = {}
    for key, profile in registry.items():
        if not isinstance(profile, dict) or profile.get("sourceRegistryVerified") is not True:
            continue
        for candidate in [key, *(profile.get("aliases") or [])]:
            if candidate:
                registry_lookup[norm(candidate)] = profile

    enriched = []
    verified_count = 0
    image_count = 0
    social_count = 0
    fully_linked_count = 0

    for raw_artist in live_artists:
        artist = dict(raw_artist)
        candidates = [artist.get("name"), *(artist.get("aliases") or [])]
        profile = next((registry_lookup.get(norm(candidate)) for candidate in candidates if registry_lookup.get(norm(candidate))), None)

        if profile and profile.get("sourceRegistryVerified") is True:
            original_aliases = list(artist.get("aliases") or [])
            profile_aliases = list(profile.get("aliases") or [])
            for key, value in profile.items():
                if key != "aliases":
                    artist[key] = value
            artist["aliases"] = list(dict.fromkeys([*original_aliases, *profile_aliases]))
            artist["liveRegistryVerified"] = True
            verified_count += 1

            image = absolute_live_image(artist.get("imageUrl"))
            if not image:
                sid = spotify_id(artist.get("spotifyProfile"))
                if sid:
                    image = image_endpoint.rstrip("/") + "/" + urllib.parse.quote(sid, safe="")
            if image:
                artist["imageUrl"] = image
                artist["livePrimaryImageVerified"] = True
                image_count += 1

            links = [
                artist.get("instagramProfile"),
                artist.get("spotifyProfile"),
                artist.get("youtubeProfile"),
                artist.get("website") or artist.get("officialWebsite") or artist.get("officialProfile"),
            ]
            populated = sum(bool(str(value or "").strip()) for value in links)
            if populated:
                social_count += 1
            if populated >= 4:
                fully_linked_count += 1

        enriched.append(artist)

    manifest = {
        "source": "84lorinw-a11y/kingdom-circuit@main",
        "liveRegistryEntries": len(registry),
        "verifiedRegistryProfiles": verified_count,
        "verifiedProfilesWithPrimaryImage": image_count,
        "verifiedProfilesWithSocialOrWebsite": social_count,
        "verifiedProfilesWithInstagramSpotifyYouTubeWebsite": fully_linked_count,
        "artistConfigCount": len(enriched),
        "imageEndpoint": image_endpoint,
    }

    (OUT / "artists.json").write_text(json.dumps(enriched, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (OUT / "live-artist-sync-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2))

    if verified_count < 40:
        raise RuntimeError(f"Expected at least 40 verified live artist profiles; found {verified_count}")
    if image_count < 40:
        raise RuntimeError(f"Expected at least 40 verified primary artist images; found {image_count}")
    if social_count < 40:
        raise RuntimeError(f"Expected at least 40 verified artist profiles with links; found {social_count}")


if __name__ == "__main__":
    main()
