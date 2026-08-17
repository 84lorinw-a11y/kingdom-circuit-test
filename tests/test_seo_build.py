from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "build_seo_site.py"
SPEC = importlib.util.spec_from_file_location("build_seo_site", MODULE_PATH)
SEO = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(SEO)


class SeoBuildTests(unittest.TestCase):
    def test_slug_helpers_are_stable(self):
        self.assertEqual(SEO.artist_slug("Da' T.R.U.T.H."), "da-t-r-u-t-h")
        event = {
            "id": "manual:caleb-gordon-pomona-2026-08-16",
            "title": "Caleb Gordon - The Eden Experience",
            "city": "Pomona",
            "state": "CA",
            "startDate": "2026-08-16",
        }
        self.assertRegex(SEO.event_slug(event), r"^caleb-gordon-the-eden-experience-pomona-ca-2026-08-16-[0-9a-f]{6}$")
        self.assertEqual(SEO.event_slug(event), SEO.event_slug(dict(event)))

    def test_duplicate_events_merge_and_keep_stronger_record(self):
        artists = [{"name": "Caleb Gordon", "aliases": []}]
        generic = {
            "id": "ticketmaster:generic",
            "title": "Caleb Gordon",
            "artists": ["Caleb Gordon"],
            "startDate": "2026-08-16",
            "city": "Pomona",
            "state": "CA",
            "venue": "Venue to be announced",
            "officialUrl": "https://example.com/events/caleb",
            "sources": [{"name": "Aggregator", "url": "https://example.com/events/caleb", "priority": 20}],
        }
        verified = {
            "id": "manual:verified",
            "title": "Caleb Gordon - The Eden Experience",
            "artists": ["Caleb Gordon"],
            "startDate": "2026-08-16",
            "startTime": "19:00",
            "city": "Pomona",
            "state": "CA",
            "venue": "The Cathedral Pomona",
            "address": "350 N Garey Ave",
            "officialUrl": "https://official.example/caleb-pomona",
            "sourcePriority": 100,
            "sources": [{"name": "Official event", "url": "https://official.example/caleb-pomona", "priority": 100}],
        }
        merged = SEO.merge_events([generic], [verified], artists)
        self.assertEqual(len(merged), 1)
        self.assertEqual(merged[0]["venue"], "The Cathedral Pomona")
        self.assertIn("ticketmaster:generic", merged[0]["mergedIds"])
        self.assertIn("manual:verified", merged[0]["mergedIds"])
        self.assertEqual(merged[0]["officialUrl"], "https://official.example/caleb-pomona")

    def test_known_different_venues_are_not_collapsed(self):
        artists = [{"name": "Caleb Gordon", "aliases": []}]
        left = {"id":"a","title":"Caleb Gordon","artists":["Caleb Gordon"],"startDate":"2026-08-18","city":"Sacramento","state":"CA","venue":"Sunrise Community Church"}
        right = {"id":"b","title":"Caleb Gordon","artists":["Caleb Gordon"],"startDate":"2026-08-18","city":"Sacramento","state":"CA","venue":"Golden 1 Center"}
        self.assertEqual(len(SEO.merge_events([left, right], [], artists)), 2)

    def test_artist_registry_from_app_is_applied_in_roster_order(self):
        app = '''const ARTIST_ROSTER_ORDER = ["Lecrae","Hulvey","indie tribe."];
const VERIFIED_ARTIST_REGISTRY = {"lecrae":{"spotifyProfile":"https://open.spotify.com/artist/test","sourceRegistryVerified":true},"indie tribe.":{"website":"https://indietribe.us/","sourceRegistryVerified":true}};
let EVENTS = [];'''
        base = [{"name":"indie tribe."},{"name":"Lecrae"},{"name":"Hulvey"}]
        merged = SEO.merge_artists(base, app)
        self.assertEqual([item["name"] for item in merged], ["Lecrae", "Hulvey", "indie tribe."])
        self.assertEqual(merged[2]["website"], "https://indietribe.us/")
        self.assertEqual(merged[0]["rosterOrder"], 1)

    def test_sitemap_urls_map_to_generated_files(self):
        with tempfile.TemporaryDirectory() as temp:
            site = Path(temp)
            for relative in ["index.html", "artists/lecrae/index.html", "events/show-abcdef/index.html"]:
                path = site / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("ok", encoding="utf-8")
            SEO.build_sitemap(site, "https://kingdomcircuit.com", ["/", "/artists/lecrae/", "/events/show-abcdef/"])
            text = (site / "sitemap.xml").read_text(encoding="utf-8")
            self.assertIn("https://kingdomcircuit.com/artists/lecrae/", text)
            self.assertIn("Sitemap: https://kingdomcircuit.com/sitemap.xml", (site / "robots.txt").read_text(encoding="utf-8"))

    def test_event_structured_data_uses_verified_visible_fields(self):
        artists = [{"name":"Lecrae","category":"core"}]
        lookup = SEO.artist_lookup(artists)
        event = {"id":"event-1","title":"Lecrae Live","artists":["Lecrae"],"startDate":"2026-10-10","city":"Dallas","state":"TX","venue":"The Factory","officialUrl":"https://tickets.example/show"}
        data = SEO.event_json_ld(event, lookup, "https://kingdomcircuit.com", "/")
        self.assertEqual(data["@type"], "MusicEvent")
        self.assertEqual(data["startDate"], "2026-10-10")
        self.assertEqual(data["location"]["address"]["addressRegion"], "TX")
        self.assertEqual(data["offers"]["url"], "https://tickets.example/show")
        self.assertTrue(data["url"].startswith("https://kingdomcircuit.com/events/"))

    def test_new_show_window_is_fourteen_days(self):
        today = SEO.dt.date(2026, 8, 17)
        self.assertTrue(SEO.is_new_event({"firstSeen": "2026-08-03T12:00:00Z"}, today))
        self.assertFalse(SEO.is_new_event({"firstSeen": "2026-08-02T23:59:59Z"}, today))
        self.assertFalse(SEO.is_new_event({}, today))

    def test_candidate_workflow_preserves_live_pipeline(self):
        root = Path(__file__).resolve().parents[1]
        candidates = [
            root / ".github/workflows/update-and-deploy.yml",
            root / "candidate-workflow/update-and-deploy.yml",
        ]
        workflow = next((path for path in candidates if path.is_file()), None)
        self.assertIsNotNone(workflow, "candidate production workflow is missing")
        text = workflow.read_text(encoding="utf-8")
        for required in [
            "scripts/update_events.py",
            "scripts/build_seo_site.py",
            "scripts/verify_multipage_site.py",
            "scripts/verify_seo_site.py",
            "supplemental-events.json",
            "config/artists.json",
            "run-status.json",
            "CNAME",
            "actions/upload-pages-artifact",
        ]:
            self.assertIn(required, text)

    def test_prerender_replaces_nested_loading_panel_without_extra_div(self):
        source = '<main><div class="event-grid" data-event-grid><div class="loading-panel">Loading</div></div><p>After</p></main>'
        result = SEO.replace_div_contents(source, "data-event-grid", "<article>Show</article>")
        self.assertEqual(result, '<main><div class="event-grid" data-event-grid><article>Show</article></div><p>After</p></main>')


if __name__ == "__main__":
    unittest.main()
