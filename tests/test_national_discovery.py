from datetime import date
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import national_discovery_preview as discovery


class NationalDiscoveryTests(unittest.TestCase):
    def test_published_minified_card_metadata_keeps_adjacent_dd(self):
        html = ('<article data-event-card data-date="2026-10-16"><img src="photo.webp">'
                '<h3><a href="/event/test/">Test &amp; Show</a></h3><p class="artist-line">Artist</p>'
                '<div class="event-badges">Sold out</div><dl><dt>Date</dt><dd>Friday</dd>'
                '<dt>Venue</dt><dd>Hall</dd><dt>Location</dt><dd>Dallas, TX</dd></dl></article>')
        record = discovery.card_records(html)[0]
        self.assertEqual(record['meta'], {'Date':'Friday', 'Venue':'Hall', 'Location':'Dallas, TX'})
        self.assertEqual(record['name'], 'Test & Show')

    def test_weekend_includes_friday_through_sunday(self):
        expected = (date(2026, 10, 16), date(2026, 10, 18))
        for day in range(12, 19):
            self.assertEqual(discovery.weekend_window(date(2026, 10, day)), expected)
        self.assertEqual(discovery.weekend_window(date(2026, 10, 19)), (date(2026, 10, 23), date(2026, 10, 25)))

    def test_year_boundary_and_explicit_labels(self):
        self.assertEqual(discovery.weekend_window(date(2027, 1, 1)), (date(2027, 1, 1), date(2027, 1, 3)))
        self.assertEqual(discovery.date_label(date(2027, 12, 31), date(2028, 1, 2)), 'Dec 31, 2027 – Jan 2, 2028')
        self.assertEqual(discovery.date_label(date(2026, 10, 30), date(2026, 11, 1)), 'Oct 30 – Nov 1, 2026')

    def test_weekend_overlap_not_start_date_only(self):
        saturday = date(2026, 10, 17)
        self.assertTrue(discovery.weekend_matches('2026-10-15', '2026-10-18', saturday))
        self.assertFalse(discovery.weekend_matches('2026-10-16', '2026-10-16', saturday))
        self.assertFalse(discovery.weekend_matches('2026-10-19', None, saturday))
        self.assertTrue(discovery.weekend_matches('2026-10-18', None, saturday))

    def test_invalid_dates_fail_build_instead_of_inventing_a_date(self):
        with self.assertRaises(ValueError):
            discovery.weekend_matches('not-a-date', '', date(2026, 10, 13))

    def test_private_school_and_cancelled_shows_are_not_home_features(self):
        record = {'name':'Concert', 'meta':{'Venue':'Music Hall'}, 'badges':'Concert'}
        self.assertTrue(discovery.feature_eligible(record))
        for label in ['Invite Only', 'School', 'Cancelled', 'Sold out', 'Details pending', 'Venue to be announced']:
            self.assertFalse(discovery.feature_eligible({**record, 'name':label}))

    def test_new_sitemap_entry_keeps_all_existing_urls_and_has_no_fake_lastmod(self):
        old = b'<urlset><url><loc>original</loc></url></urlset>'
        new = discovery.transform(Path('sitemap.xml'), old, {})
        self.assertIn(b'<loc>original</loc>', new)
        self.assertIn(b'/shows/this-weekend/', new)
        self.assertNotIn(b'lastmod', new)
        with self.assertRaises(AssertionError):
            discovery.transform(Path('sitemap.xml'), new, {})

    def test_data_images_and_isolated_experiments_are_not_changed(self):
        for path in ['events.json','config/artists.json','assets/image.webp','test-all-shows/index.html']:
            self.assertEqual(discovery.transform(Path(path), b'unchanged', {}), b'unchanged')

    def test_home_preserves_mission_and_has_truthful_empty_fallback_without_js(self):
        source = ('<main><h1>Find shows</h1><p class="mission-statement">Our existing mission.</p></main>'
                  '<script src="/kingdom-circuit-test/app.js?v=old" defer></script>')
        context = {'states': [], 'as_of': date(2026, 10, 13), 'weekend': [], 'active': [],
                   'recent': [], 'artists': [], 'artist_total': 361}
        home = discovery.home_content(source, context)
        self.assertIn('<p class="mission-statement">Our existing mission.</p>', home)
        self.assertIn('Browse all 0 shows', home)
        self.assertIn('data-discovery-empty>', home)
        self.assertNotIn('Artists with upcoming shows', home)
        self.assertNotIn('/app.js', home)
        self.assertIn('/seo-static.js', home)
        self.assertIn('name="q"', home)

    def test_artist_tile_preserves_real_image_and_focal_point_without_duplicate_name(self):
        tile = discovery.artist_tile({'name':'Artist & Co', 'href':'/artists/a/', 'count':2,
            'image':'<img src="real.webp" srcset="real-320.webp 320w" alt="Artist &amp; Co" sizes="100vw" style="object-position:50% 25%">'})
        self.assertIn('src="real.webp"', tile)
        self.assertIn('srcset="real-320.webp 320w"', tile)
        self.assertIn('object-position:50% 25%', tile)
        self.assertIn('alt=""', tile)
        self.assertIn('<strong>Artist &amp; Co</strong>', tile)
        self.assertIn('2 upcoming shows', tile)

    def test_pipeline_runs_national_before_final_artifact_verification(self):
        root = Path(__file__).resolve().parents[1]
        workflow = (root / '.github/workflows/mirror-live.yml').read_text()
        self.assertLess(workflow.index('python scripts/mobile_seo_preview.py _site'), workflow.index('python scripts/national_discovery_preview.py _site'))
        self.assertLess(workflow.index('python scripts/national_discovery_preview.py _site'), workflow.index('python scripts/verify_live_baseline.py _live_site'))


if __name__ == '__main__':
    unittest.main()
