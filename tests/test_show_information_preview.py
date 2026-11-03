"""Render/schema contract tests for the final test-only information overlay."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import show_information_preview as preview
from show_information_model import normalize
from mobile_seo_preview import Document
import build_mobile_show_test as reviews


def fixture():
    schema = {'@context': 'https://schema.org', '@type': 'MusicEvent', 'name': 'Sample concert',
              'startDate': '2027-01-29T21:00', 'url': 'https://example.com/event/sample/',
              'location': {'@type': 'Place', 'name': 'Chapel', 'address': {'@type': 'PostalAddress', 'addressCountry': 'US'}},
              'offers': {'@type': 'Offer', 'url': 'https://example.com/info'}}
    return ('<html><head><meta name="robots" content="noindex,nofollow"><link rel="canonical" href="https://example.com/event/sample/">'
            '<script type="application/ld+json">' + json.dumps(schema) + '</script></head><body>'
            '<div class="event-detail-media"><img src="/kingdom-circuit-test/assets/flyer.webp" alt="Full flyer"></div>'
            '<div class="event-detail-copy"><h1>Sample concert</h1><dl class="detail-list">'
            '<div><dt>Status</dt><dd>Scheduled</dd></div><div><dt>Date</dt><dd>Jan 29</dd></div>'
            '<div><dt>Venue</dt><dd>Chapel</dd></div><div><dt>Location</dt><dd>Kansas City, MO</dd></div></dl>'
            '<a class="primary-button" href="https://example.com/info">Official details</a>'
            '<p class="disclaimer">Confirm details.</p></div></body></html>')


def listing_fixture(kind, path='/kingdom-circuit-test/event/sample/'):
    if kind == 'event-card':
        return (f'<article class="event-card" data-event-card data-date="2027-01-29" data-end-date="2027-01-29" '
                'data-state="MO" data-type="concert" data-artists="artist" data-search="sample concert artist chapel jan 29">'
                '<img class="event-artwork" src="/kingdom-circuit-test/assets/flyer.webp">'
                f'<h3><a href="{path}">Sample concert</a></h3><p class="artist-line">Artist</p>'
                '<dl class="event-meta"><div><dt>Date</dt><dd>Jan 29</dd></div>'
                '<div><dt>Venue</dt><dd>Chapel</dd></div><div><dt>Location</dt><dd>Kansas City, MO</dd></div></dl></article>')
    if kind == 'kc-discovery-show':
        return (f'<article class="kc-discovery-show"><h3><a href="{path}">Sample concert</a></h3>'
                '<p class="kc-teaser-date" title="Jan 29">Jan 29</p>'
                '<p class="kc-teaser-venue" title="Chapel">Chapel</p></article>')
    venue_class = 'kc-rd-show-venue' if kind == 'kc-rd-show-row' else 'kc-rd-next-venue'
    return (f'<a class="{kind}" href="{path}" aria-label="Jan 29, Chapel | Sample concert">'
            f'<span class="{venue_class}">Chapel</span><span class="kc-rd-event-title">Sample concert</span>'
            '<span class="kc-rd-chevron" aria-hidden="true">›</span></a>')


class ShowInformationPreviewTests(unittest.TestCase):
    def record(self, **changes):
        return normalize({'title': 'Sample concert', 'startDate': '2027-01-29', 'startTime': '21:00',
                          'endTime': '22:00', 'timezone': 'America/Chicago', 'city': 'Kansas City', 'state': 'MO',
                          'address': '5001 N Oak Trafficway', 'postalCode': '64118', 'country': 'US',
                          'officialUrl': 'https://example.com/info', **changes})

    def test_one_ticket_action_matches_schema_without_invented_fee_total(self):
        record = self.record(registrationUrl='https://example.com/register', registrationUrlVerified=True,
                             price={'amount': '15', 'currency': 'USD', 'ticketType': 'Concert only'},
                             organizer={'name': 'College', 'url': 'https://example.com/college'},
                             publicDescription='Friday concert.', registrationTime='20:30')
        text = preview.detail_transform(fixture(), record)
        doc = Document(text)
        buttons = [n for n in doc.nodes if n.has('primary-button')]
        self.assertEqual(len(buttons), 1)
        self.assertEqual(doc.text(buttons[0]), 'Official details')
        self.assertEqual(buttons[0].attrs['href'], 'https://example.com/register')
        schema = next(preview.event_schemas(preview.schema_blocks(text)[0][1]))
        self.assertEqual(schema['offers']['url'], buttons[0].attrs['href'])
        self.assertNotIn('price', schema['offers'])
        self.assertEqual(schema['startDate'], '2027-01-29T21:00:00-06:00')
        self.assertEqual(schema['endDate'], '2027-01-29T22:00:00-06:00')
        self.assertIn('9:00 PM CST', text)
        self.assertEqual(schema['location']['address']['postalCode'], '64118')
        self.assertIn('5001 N Oak Trafficway', text)
        panel = doc.one(lambda n: n.tag == 'details')
        self.assertIn('15 USD', doc.text(panel))
        self.assertIn('College', doc.text(panel))
        self.assertIn('Friday concert.', doc.text(panel))
        self.assertNotIn('open', panel.attrs)
        self.assertNotIn('Directions', text)
        self.assertNotIn('Full schedule', text)
        self.assertNotIn('Final total', text)

    def test_information_link_is_not_an_offer_and_unknown_details_are_omitted(self):
        text = preview.detail_transform(fixture(), self.record(endTime=''))
        schema = next(preview.event_schemas(preview.schema_blocks(text)[0][1]))
        self.assertNotIn('offers', schema)
        self.assertNotIn('kc-more-details', text)
        self.assertNotIn('All ages', text)
        self.assertNotIn('Free', text)

    def test_missing_core_facts_are_clear_without_placeholder_schema_or_admission_claims(self):
        record = self.record(venue='RWG TOUR 2026', address='', postalCode='',
                             startTime='', endTime='', unconfirmedVenueValue='RWG TOUR 2026')
        text = preview.detail_transform(fixture(), record)
        self.assertIn('Venue not confirmed', text)
        self.assertIn('Address not confirmed', text)
        self.assertIn('Start time not confirmed', text)
        self.assertNotIn('kc-admission-restriction', text)
        schema = next(preview.event_schemas(preview.schema_blocks(text)[0][1]))
        self.assertEqual(schema['startDate'], '2027-01-29')
        self.assertNotIn('name', schema['location'])
        self.assertNotIn('not confirmed', json.dumps(schema))
        self.assertNotIn('RWG TOUR', json.dumps(schema))
        path = '/kingdom-circuit-test/event/sample/'
        card = preview.listing_transform(listing_fixture('event-card'), {'paths': {path: record}})
        self.assertIn('Venue not confirmed', card)
        self.assertNotIn('Address not confirmed', card)

    def test_primary_doors_time_appears_once_and_does_not_become_performance_time(self):
        record = self.record(startDate='2026-11-21', startTime='', endTime='',
                             doorsTime='18:30', timezone='America/Los_Angeles', primaryTimeKind='doors')
        text = preview.detail_transform(fixture(), record)
        self.assertEqual(text.count('6:30 PM PST'), 1)
        self.assertIn('Doors 6:30 PM PST', text)
        self.assertIn('Start time not confirmed', text)
        self.assertNotIn('kc-more-details', text)
        schema = next(preview.event_schemas(preview.schema_blocks(text)[0][1]))
        self.assertEqual(schema['startDate'], '2026-11-21')
        self.assertNotIn('endDate', schema)
        path = '/kingdom-circuit-test/event/sample/'
        for kind in ('event-card', 'kc-discovery-show', 'kc-rd-show-row', 'kc-rd-next-show'):
            with self.subTest(kind=kind):
                card = preview.listing_transform(listing_fixture(kind), {'paths': {path: record}})
                doc = Document(card)
                self.assertIn('Doors 6:30 PM PST', doc.text(doc.nodes[0]))
                self.assertNotIn('data-start-time', doc.nodes[0].attrs)

    def test_legacy_tbd_address_and_venue_not_provided_are_not_factual_schema(self):
        record = self.record(venue='Venue not provided', address='TBD', postalCode='TBA')
        text = preview.detail_transform(fixture(), record)
        self.assertIn('Venue not confirmed', text)
        self.assertIn('Address not confirmed', text)
        schema = next(preview.event_schemas(preview.schema_blocks(text)[0][1]))
        self.assertNotIn('name', schema['location'])
        self.assertNotIn('streetAddress', schema['location']['address'])
        self.assertNotIn('postalCode', schema['location']['address'])

    def test_private_removes_nested_event_schema_and_does_not_display_address(self):
        record = self.record(title='Album session (Invite Only)', address='PRIVATE STREET', postalCode='SECRETZIP')
        text = preview.detail_transform(fixture(), record)
        self.assertFalse(preview.schema_blocks(text))
        self.assertIn('Private Event', text)
        self.assertIn('Private / invite-only event', text)
        self.assertNotIn('PRIVATE STREET', text)
        self.assertNotIn('SECRETZIP', text)
        graph = {'@graph': [{'@type': 'BreadcrumbList'}, {'@type': 'MusicEvent', 'offers': {}}]}
        self.assertEqual(preview.patched_schema(graph, record), {'@graph': [{'@type': 'BreadcrumbList'}]})

    def test_one_admission_line_and_canadian_address_preserved(self):
        record = self.record(ageRestriction='Ages 18+', city='Toronto', state='ON', country='CA', postalCode='M5V 2T6')
        text = preview.detail_transform(fixture(), record)
        self.assertEqual(text.count('Ages 18+'), 1)
        self.assertIn('Toronto, ON M5V 2T6', text)
        self.assertIn('Canada', text)
        self.assertLess(text.index('Ages 18+'), text.index('Official details'))

    def test_listing_only_changes_ticket_target_and_admission(self):
        path = '/kingdom-circuit-test/event/sample/'
        text = f'<article class="event-card"><h3><a href="{path}">Sample</a></h3><div class="event-footer"><a class="official-button" href="https://example.com/info">Official details</a></div></article>'
        record = self.record(ticketUrl='https://www.eventbrite.com/e/example-tickets-1234', ageRestriction='18+')
        result = preview.listing_transform(text, {'paths': {path: record}})
        self.assertIn('https://www.eventbrite.com/e/example-tickets-1234', result)
        self.assertIn('18+', result)
        self.assertIn(path, result)
        self.assertNotIn('5001 N Oak', result)
        self.assertNotIn('More show details', result)

    def test_description_and_organizer_are_escaped_not_executed(self):
        record = self.record(publicDescription='<script>alert(1)</script>', organizer='<img src=x onerror=alert(1)>')
        result = preview.more_details(record)
        self.assertNotIn('<script>', result)
        self.assertNotIn('<img', result)
        self.assertIn('&lt;script&gt;', result)

    def test_existing_schedule_moves_into_one_disclosure_without_losing_prejam(self):
        schedule = '<section data-kc-event-schedule><h2>Schedule</h2><dl class="detail-list"><div><dt>Pre-Jam</dt><dd>6 PM</dd></div></dl></section>'
        text = fixture().replace('<a class="primary-button"', schedule + '<a class="primary-button"')
        result = preview.detail_transform(text, self.record(scheduleDetails=[{'label': 'Pre-Jam', 'text': '6 PM'}]))
        self.assertEqual(result.count('Pre-Jam'), 1)
        self.assertNotIn('data-kc-event-schedule', result)
        self.assertIn('6 PM', Document(result).text(Document(result).one(lambda n: n.has('kc-more-details'))))

    def test_verified_venue_and_time_agree_in_detail_schema_and_date_metadata(self):
        title = 'Sample concert — Kansas City, MO — Jan 29 | Kingdom Circuit'
        metadata = ('<title>' + title + '</title><meta property="og:title" content="' + title + '">'
                    '<meta name="twitter:title" content="' + title + '">'
                    '<meta name="description" content="Artist live on Jan 29. Verified official show details.">'
                    '<meta property="og:description" content="Artist live on Jan 29. Verified official show details.">'
                    '<meta name="twitter:description" content="Artist live on Jan 29. Verified official show details.">')
        source = fixture().replace('</head>', metadata + '</head>')
        record = self.record(venue='New Hall & Chapel', startTime='19:30', endTime='')
        result = preview.detail_transform(source, record)
        doc = Document(result)
        schema = next(preview.event_schemas(preview.schema_blocks(result)[0][1]))
        self.assertEqual(reviews.field(result, 'Venue'), 'New Hall & Chapel')
        self.assertEqual(reviews.field(result, 'Date'), 'Fri, Jan 29, 2027 - 7:30 PM CST')
        self.assertEqual(schema['location']['name'], 'New Hall & Chapel')
        self.assertEqual(schema['startDate'], '2027-01-29T19:30:00-06:00')
        for n in doc.nodes:
            if n.tag == 'title' or n.attrs.get('name') in {'twitter:title', 'description', 'twitter:description'} or n.attrs.get('property') in {'og:title', 'og:description'}:
                self.assertIn('Fri, Jan 29, 2027 - 7:30 PM CST', doc.text(n) if n.tag == 'title' else n.attrs['content'])
        self.assertEqual(schema['name'], 'Sample concert')
        self.assertEqual(schema['url'], 'https://example.com/event/sample/')
        before = Document(source)
        for tag in ('h1', 'img'):
            self.assertEqual([doc.raw(n) for n in doc.nodes if n.tag == tag],
                             [before.raw(n) for n in before.nodes if n.tag == tag])
        self.assertIn('<link rel="canonical" href="https://example.com/event/sample/">', result)

    def test_every_compact_layout_shows_new_time_and_venue_without_street_address(self):
        path = '/kingdom-circuit-test/event/sample/'
        record = self.record(venue='Verified Hall & Stage', startTime='19:30', endTime='')
        for kind in ('event-card', 'kc-discovery-show', 'kc-rd-show-row', 'kc-rd-next-show'):
            with self.subTest(kind=kind):
                result = preview.listing_transform(listing_fixture(kind), {'paths': {path: record}})
                doc = Document(result)
                self.assertIn('Verified Hall &amp; Stage', result)
                self.assertIn('7:30 PM CST', doc.text(doc.nodes[0]))
                self.assertEqual(doc.nodes[0].attrs['data-start-time'], '19:30')
                self.assertNotIn('5001 N Oak', result)
                self.assertNotIn('64118', result)
                self.assertIn('Sample concert', result)
                self.assertIn(path, result)
                for n in doc.nodes:
                    if n.has('kc-teaser-date') or n.has('kc-teaser-venue'):
                        self.assertEqual(n.attrs['title'], doc.text(n))
                if kind.startswith('kc-rd-'):
                    self.assertIn('7:30 PM CST', doc.nodes[0].attrs['aria-label'])
                    self.assertIn('Verified Hall & Stage', doc.nodes[0].attrs['aria-label'])
                if kind == 'event-card':
                    self.assertIn('verified hall & stage', doc.nodes[0].attrs['data-search'])
                    self.assertNotIn('chapel', doc.nodes[0].attrs['data-search'])
                self.assertEqual(preview.listing_transform(result, {'paths': {path: record}}), result)

    def test_unmatched_listings_and_unknown_times_are_not_filled(self):
        path = '/kingdom-circuit-test/event/sample/'
        source = listing_fixture('event-card')
        self.assertEqual(preview.listing_transform(source, {'paths': {}}), source)
        record = self.record(venue='Verified Hall', startTime='', endTime='', timezone='')
        result = preview.listing_transform(source, {'paths': {path: record}})
        self.assertNotIn('data-start-time', result)
        self.assertNotIn('PM', result)
        self.assertNotIn('AM', result)
        schema = next(preview.event_schemas(preview.schema_blocks(preview.detail_transform(fixture(), record))[0][1]))
        self.assertEqual(schema['startDate'], '2027-01-29')

    def test_artist_row_accessible_names_keep_material_status(self):
        path = '/kingdom-circuit-test/event/sample/'
        cases = [
            ({'private': True}, '', 'Private Event — not open to the public'),
            ({'soldOut': True}, '', 'Sold out'),
            ({'status': 'cancelled', 'displayStatus': 'Cancelled'}, '', 'Cancelled'),
            ({}, 'Private / invite-only event', 'Private / invite-only event'),
            ({}, 'Sold out', 'Sold out'),
            ({'displayStatus': 'Scheduled'}, 'This show has been cancelled', 'This show has been cancelled'),
        ]
        for kind in ('kc-rd-show-row', 'kc-rd-next-show'):
            for facts, existing, expected in cases:
                with self.subTest(kind=kind, facts=facts, existing=existing):
                    source = listing_fixture(kind)
                    if existing:
                        source = source.replace('<span class="kc-rd-chevron"',
                                                '<span class="kc-rd-event-status">' + existing + '</span><span class="kc-rd-chevron"')
                    record = self.record(venue='Verified Hall', startTime='19:30', **facts)
                    result = preview.listing_transform(source, {'paths': {path: record}})
                    label = Document(result).nodes[0].attrs['aria-label']
                    self.assertIn(expected, label)
                    self.assertIn('Sample concert', label)
                    self.assertIn('Verified Hall', label)
                    self.assertIn('7:30 PM CST', label)
                    self.assertEqual(preview.listing_transform(result, {'paths': {path: record}}), result)

    def test_exact_override_reaches_both_review_variants_without_changing_source_catalog(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            live, site = root / 'live', root / 'site'
            rel = Path('event/sample/index.html')
            for base in (live, site):
                (base / rel).parent.mkdir(parents=True)
                (base / rel).write_text(fixture())
            source = {'id': 'manual:sample', 'title': 'Sample concert', 'canonicalPath': '/event/sample/',
                      'startDate': '2027-01-29', 'startTime': '', 'venue': 'Chapel',
                      'city': 'Kansas City', 'state': 'MO', 'country': 'US', 'officialUrl': 'https://example.com/info'}
            original = json.dumps([source]).encode()
            (live / 'events.json').write_bytes(original)
            (live / 'supplemental-events.json').write_text('[]')
            (root / 'test-overrides').mkdir()
            additions = {'startDate': '2027-01-29', 'venue': 'Verified Hall', 'startTime': '19:30', 'timezone': 'America/Chicago',
                         'provenance': [{'url': 'https://example.com/official-event'}]}
            overrides = root / 'test-overrides/show-information-overrides.json'
            overrides.write_text(json.dumps({'manual:sample': additions}))
            with patch.object(preview, 'ROOT', root):
                ctx = preview.context(live)
                # The same ID on another occurrence must not receive this time.
                overrides.write_text(json.dumps({'manual:sample': dict(additions, startDate='2027-01-30')}))
                self.assertNotIn('startTimeLabel', preview.context(live)['pages'][rel.as_posix()])
            (site / rel).write_bytes(preview.transform(rel, fixture().encode(), ctx))
            (site / 'shows').mkdir()
            (site / 'shows/index.html').write_bytes(preview.transform('shows/index.html', listing_fixture('event-card').encode(), ctx))
            (site / 'config').mkdir()
            (site / 'config/artists.json').write_text('[{"name":"Artist"}]')
            (site / 'assets').mkdir()
            reviews.build(site, isolated=True)
            for route in (reviews.ROUTE, reviews.FEED_ROUTE):
                html = (site / route / 'index.html').read_text()
                payload = json.loads(reviews.match_text(r'<script id="mobile-calendar-data" type="application/json">(.*?)</script>', html))
                self.assertEqual(payload['events'][0]['venue'], 'Verified Hall')
                self.assertEqual(payload['events'][0]['dateLabel'], 'Fri, Jan 29, 2027 - 7:30 PM CST')
                self.assertEqual(payload['events'][0]['href'], '/kingdom-circuit-test/event/sample/')
                self.assertEqual(payload['events'][0]['title'], 'Sample concert')
            self.assertEqual((live / 'events.json').read_bytes(), original)


if __name__ == '__main__':
    unittest.main()
