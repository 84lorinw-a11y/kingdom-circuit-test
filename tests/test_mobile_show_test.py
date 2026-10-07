"""Protect complete billing and test-only URL boundaries in the mobile preview."""
import sys
from pathlib import Path
import unittest
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from build_mobile_show_test import billing, host_label, image_fields, safe_page, valid_official_url, read_detail
from apply_test_redesign import create_history_event_page, history_event_href


class MobileCalendarContentTests(unittest.TestCase):
    def test_renamed_archive_reuses_reviewed_title_and_artwork(self):
        with tempfile.TemporaryDirectory() as temp:
            site = Path(temp)
            old = {'id':'same-event', 'title':'Old artist listing', 'artists':['Artist'], 'startDate':'2026-10-06','city':'Nashville','state':'TN'}
            corrected = dict(old, title='Reviewed festival name')
            path = safe_page(site, history_event_href(corrected))
            path.parent.mkdir(parents=True)
            page = '<h1>Reviewed festival name</h1><img src="approved-poster.jpg">'
            path.write_text(page)
            self.assertTrue(create_history_event_page(site, old))
            self.assertEqual(safe_page(site, history_event_href(old)).read_text(), page)

    def test_generated_archive_keeps_exact_dates_for_calendar_preview(self):
        with tempfile.TemporaryDirectory() as temp:
            site = Path(temp)
            event = {'id':'archive-test', 'title':'Past festival', 'artists':['Artist'], 'startDate':'2026-10-02','endDate':'2026-10-04','city':'Nashville','state':'TN'}
            create_history_event_page(site, event)
            result = read_detail(site, history_event_href(event))
            self.assertEqual(result['date'], '2026-10-02')
            self.assertEqual(result['endDate'], '2026-10-04')

    def test_approved_local_flyer_is_a_valid_source_without_path_escape(self):
        with tempfile.TemporaryDirectory() as temp:
            site = Path(temp)
            (site / 'assets/events').mkdir(parents=True)
            (site / 'assets/events/flyer.png').write_bytes(b'flyer')
            self.assertTrue(valid_official_url(site, '/kingdom-circuit-test/assets/events/flyer.png'))
            self.assertTrue(valid_official_url(site, 'https://tickets.example/event'))
            for url in ['/kingdom-circuit-test/assets/events/missing.png', '/kingdom-circuit-test/assets/%2e%2e/private.png', 'javascript:alert(1)', '/event/elsewhere/', '//unknown.example/flyer.png']:
                self.assertFalse(valid_official_url(site, url), url)

    def test_hosts_remain_separate_from_performing_lineup(self):
        source = '<p class="artist-line">ADIA - JustCordell</p><p class="host-line">Hosted by DJ Focus and Keal K</p>'
        self.assertEqual(billing(source)[0], ['ADIA', 'JustCordell'])
        self.assertEqual(host_label(source), 'Hosted by DJ Focus and Keal K')
        self.assertEqual(host_label('<p>No hosts</p>'), '')

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
