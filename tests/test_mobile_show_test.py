"""Protect complete billing and test-only URL boundaries in the mobile preview."""
import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from build_mobile_show_test import billing, image_fields, safe_page


class MobileCalendarContentTests(unittest.TestCase):
    def test_full_billing_keeps_unlisted_artists_and_order(self):
        names, links = billing('<p class="artist-line"><a href="/kingdom-circuit-test/artists/kb/">KB</a> - Independent &amp; Friends - DJ Eli Williams</p>')
        self.assertEqual(names, ['KB', 'Independent & Friends', 'DJ Eli Williams'])
        self.assertEqual(links, {'KB': '/kingdom-circuit-test/artists/kb/'})

    def test_artist_link_cannot_escape_test_site(self):
        names, links = billing('<p class="artist-line"><a href="https://kingdomcircuit.com/artists/kb/">KB</a> - Guest</p>')
        self.assertEqual(names, ['KB', 'Guest'])
        self.assertEqual(links, {})

    def test_event_path_is_test_only(self):
        for path in ['/event/show/', '/kingdom-circuit-test/event/../../private/', 'https://kingdomcircuit.com/event/show/']:
            with self.assertRaises(ValueError):
                safe_page(Path('/tmp/test'),path)
        self.assertEqual(safe_page(Path('/tmp/test'),'/kingdom-circuit-test/event/show/'),Path('/tmp/test/event/show/index.html'))

    def test_poster_and_existing_photo_crop_are_preserved(self):
        result = image_fields('<img class="event-artwork" src="/kingdom-circuit-test/assets/flyer.webp" srcset="/kingdom-circuit-test/assets/flyer.webp 640w" style="object-position:50% 30%">')
        self.assertTrue(result['artwork'])
        self.assertEqual(result['position'],'50% 30%')
        self.assertIn('640w',result['srcset'])
