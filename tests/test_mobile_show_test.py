"""Protect complete billing and test-only URL boundaries in the mobile preview."""
import sys
from pathlib import Path
import unittest
import tempfile
import json

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from build_mobile_show_test import billing, collect, host_label, image_fields, safe_page, valid_official_url, read_detail, lineup_notice, verify_billing
from apply_test_redesign import create_history_event_page, history_event_href


class MobileCalendarContentTests(unittest.TestCase):
    def archive_fixture(self, site, status='Cancelled', end_date='2026-10-31'):
        """A current private show and a distinct published cancellation archive."""
        (site / 'shows').mkdir()
        (site / 'config').mkdir()
        (site / 'config/artists.json').write_text('[{"name":"Nate Period"}]')
        profile = site / 'artists/nate-period/index.html'
        profile.parent.mkdir(parents=True)
        profile.write_text('<article class="past-show-row"><a href="/kingdom-circuit-test/event/cancelled/">Archived show</a></article>')
        for slug, event_status, date, date_heading in (
            ('private', 'Private Event', '2026-11-21', 'Date'),
            ('cancelled', status, end_date, 'Originally scheduled'),
        ):
            path = site / 'event' / slug / 'index.html'
            path.parent.mkdir(parents=True)
            schema = {'@type': 'MusicEvent', 'startDate': date, 'endDate': date,
                      'eventStatus': 'https://schema.org/EventCancelled' if event_status in {'Cancelled', 'Canceled'} else 'https://schema.org/EventScheduled'}
            path.write_text('<h1>' + slug + '</h1><p class="artist-line">Nate Period - Guest Artist</p>'
                            '<dl><div><dt>Status</dt><dd>' + event_status + '</dd></div>'
                            '<div><dt>' + date_heading + '</dt><dd>Oct 31, 2026</dd></div>'
                            '<div><dt>Location</dt><dd>Washington, DC</dd></div></dl>'
                            '<script type="application/ld+json">' + json.dumps(schema) + '</script>')
        (site / 'shows/index.html').write_text(
            '<article class="event-card" data-event-card data-date="2026-11-21" data-end-date="2026-11-21" data-state="DC" data-type="concert">'
            '<h3><a href="/kingdom-circuit-test/event/private/">Private school show</a></h3>'
            '<p class="artist-line">Nate Period - Guest Artist</p>'
            '<dl><dt>Date</dt><dd>Nov 21, 2026</dd><dt>Location</dt><dd>Washington, DC</dd></dl></article>')

    def test_cancelled_archive_keeps_original_date_without_becoming_upcoming(self):
        for status in ('Cancelled', 'Canceled'):
            with self.subTest(status=status), tempfile.TemporaryDirectory() as temp:
                site = Path(temp)
                self.archive_fixture(site, status=status)
                for day in ('2026-10-28', '2026-10-31', '2026-11-02'):
                    with self.subTest(day=day):
                        events, artists = collect(site, day)
                        self.assertEqual([e['href'] for e in events], [
                            '/kingdom-circuit-test/event/private/', '/kingdom-circuit-test/event/cancelled/'])
                        self.assertFalse(events[0]['past'])
                        self.assertEqual(events[0]['status'], 'Private Event')
                        self.assertEqual(events[0]['artists'], ['Nate Period', 'Guest Artist'])
                        self.assertTrue(events[1]['past'])
                        self.assertEqual(events[1]['type'], 'archive')
                        self.assertEqual(events[1]['status'], status)
                        self.assertEqual(events[1]['date'], '2026-10-31')
                        self.assertEqual(events[1]['endDate'], '2026-10-31')
                        self.assertEqual(events[1]['dateLabel'], 'Oct 31, 2026')
                        self.assertEqual(events[1]['artists'], ['Nate Period', 'Guest Artist'])
                        self.assertEqual(artists, ['Nate Period'])

    def test_archive_still_requires_dates_and_explicit_cancellation_for_future_dates(self):
        for status, end_date in (('Scheduled', '2026-10-31'), ('Private Event', '2026-10-31'),
                                 ('Cancelled', ''), ('Cancelled', 'unknown')):
            with self.subTest(status=status, date=end_date), tempfile.TemporaryDirectory() as temp:
                site = Path(temp)
                self.archive_fixture(site, status=status, end_date=end_date)
                with self.assertRaisesRegex(ValueError, 'Archive has missing/nonpast date'):
                    collect(site, '2026-10-28')

    def test_community_event_preserves_schema_dates_and_explicit_no_lineup(self):
        with tempfile.TemporaryDirectory() as temp:
            site = Path(temp)
            href = '/kingdom-circuit-test/event/community-evening/'
            path = safe_page(site, href)
            path.parent.mkdir(parents=True)
            schema = {'@type': 'Event', 'startDate': '2026-10-31T18:00:00-04:00',
                      'endDate': '2026-10-31T22:00:00-04:00', 'performer': [],
                      'description': 'Worship, prayer and fellowship. No performer lineup has been announced.'}
            page = '<h1>Community evening</h1><p class="artist-line"></p>'
            for description in (schema['description'], 'Worship, prayer and fellowship.'):
                schema['description'] = description
                path.write_text(page + '<script type="application/ld+json">' + json.dumps(schema) + '</script>')
                event = read_detail(site, href)
                self.assertEqual(event['date'], '2026-10-31')
                self.assertEqual(event['endDate'], '2026-10-31')
                self.assertEqual(event['artists'], [])
                if 'No performer' in description:
                    self.assertEqual(event['lineupNotice'], 'No performer lineup has been announced.')
                    verify_billing(event)
                else:
                    self.assertEqual(event['lineupNotice'], '')
                    with self.assertRaises(AssertionError):
                        verify_billing(event)

    def test_unannounced_lineup_requires_the_explicit_published_notice(self):
        rural = 'August 27–29, 2027. Free admission. Lineup and daily times to be announced.'
        self.assertEqual(lineup_notice('<p data-kc-event-notice>' + rural + '</p>'), rural)
        verify_billing({'href': '/event/rural/', 'artists': [], 'artistLinks': {}, 'lineupNotice': rural})
        source = '<p data-kc-event-notice>Lineup to be announced. Outdoor Fan Fest starts at 3 PM.</p>'
        notice = lineup_notice(source)
        self.assertEqual(notice, 'Lineup to be announced. Outdoor Fan Fest starts at 3 PM.')
        event = {'href': '/event/festival/', 'artists': [], 'artistLinks': {}, 'lineupNotice': notice}
        verify_billing(event)
        for invalid in ('', 'Doors open at 5 PM', 'Artist name missing'):
            with self.assertRaises(AssertionError): verify_billing(dict(event, lineupNotice=invalid))
        with self.assertRaises(AssertionError): verify_billing(dict(event, artistLinks={'Invented': '/artist/'}))
        verify_billing(dict(event, artists=['Confirmed Artist'], lineupNotice=''))

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
