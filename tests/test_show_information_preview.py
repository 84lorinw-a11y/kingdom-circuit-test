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
import finalize_artist_details as artist_details


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

    def artwork(self, name='jacksonville', **changes):
        return {'src': f'assets/ignite-tour/{name}.webp', 'width': 800, 'height': 1000,
                'alt': f'Ignite and Unite Tour — {name} showcard', **changes}

    def test_reviewed_artwork_replaces_full_detail_schema_and_social_surfaces(self):
        artwork = self.artwork(srcset='assets/ignite-tour/jacksonville-small.webp 320w, assets/ignite-tour/jacksonville.webp 800w')
        record = self.record(artwork=artwork)
        source = fixture().replace('</head>', '<meta property="og:image" content="https://example.com/old.webp">'
                                  '<meta name="twitter:image" content="https://example.com/old.webp"></head>')
        source = source.replace('<img src="/kingdom-circuit-test/assets/flyer.webp" alt="Full flyer">',
                                '<a class="event-image-enlarge" href="/kingdom-circuit-test/assets/old.png">'
                                '<img src="/kingdom-circuit-test/assets/flyer.webp" srcset="old.webp 800w" '
                                'alt="Full flyer" loading="eager" fetchpriority="high" sizes="475px"></a>')
        source = source.replace('<body>', '<body><img class="logo" src="logo.webp">')
        result = preview.detail_transform(source, record)
        doc = Document(result)
        hero = doc.one(lambda n: n.tag == 'img' and n.has('event-artwork'))
        self.assertEqual(hero.attrs['src'], preview.TEST_BASE + artwork['src'])
        self.assertEqual(hero.attrs['srcset'], preview.TEST_BASE + 'assets/ignite-tour/jacksonville-small.webp 320w, ' + preview.TEST_BASE + artwork['src'] + ' 800w')
        self.assertEqual((hero.attrs['width'], hero.attrs['height']), ('800', '1000'))
        self.assertEqual((hero.attrs['loading'], hero.attrs['fetchpriority'], hero.attrs['sizes']), ('eager', 'high', '475px'))
        self.assertIn('object-fit:contain', hero.attrs['style'])
        self.assertIn('<img class="logo" src="logo.webp">', result)
        self.assertEqual(doc.one(lambda n: n.has('event-image-enlarge')).attrs['href'], preview.TEST_BASE + artwork['src'])
        absolute = preview.TEST_ORIGIN + preview.TEST_BASE + artwork['src']
        schema = next(preview.event_schemas(preview.schema_blocks(result)[0][1]))
        self.assertEqual(schema['image'], [absolute])
        self.assertEqual([n.attrs['content'] for n in doc.nodes if n.tag == 'meta' and
                          (n.attrs.get('property') or n.attrs.get('name')) in {'og:image', 'twitter:image'}], [absolute, absolute])

    def test_shared_source_flyer_is_replaced_per_event_and_stale_srcset_is_removed(self):
        first = '/kingdom-circuit-test/event/deland/'
        second = '/kingdom-circuit-test/event/daytona/'
        untouched = listing_fixture('event-card', '/kingdom-circuit-test/event/other/')
        source = listing_fixture('event-card', first) + listing_fixture('event-card', second) + untouched
        source = source.replace('src="/kingdom-circuit-test/assets/flyer.webp"',
                                'src="/kingdom-circuit-test/assets/flyer.webp" srcset="old-small.webp 320w, old.webp 800w"')
        ctx = {'paths': {first: self.record(artwork=self.artwork('deland')),
                         second: self.record(artwork=self.artwork('daytona'))}}
        result = preview.listing_transform(source, ctx)
        doc = Document(result)
        cards = [n for n in doc.nodes if n.has('event-card')]
        for card, name in zip(cards[:2], ('deland', 'daytona')):
            image = Document(doc.raw(card)).one(lambda n: n.tag == 'img')
            self.assertEqual(image.attrs['src'], preview.TEST_BASE + f'assets/ignite-tour/{name}.webp')
            self.assertNotIn('srcset', image.attrs)
        self.assertEqual(doc.raw(cards[2]), Document(source).raw([n for n in Document(source).nodes if n.has('event-card')][2]))
        self.assertEqual(preview.listing_transform(result, ctx), result)

    def test_new_teaser_artwork_resets_old_crop_but_keeps_approved_frame(self):
        path = '/kingdom-circuit-test/event/sample/'
        source = ('<article class="kc-discovery-show" data-artwork-shape="square" style="--kc-artwork-ratio:1092 / 1440">'
                  f'<a class="kc-teaser-image" href="{path}" data-artwork-treatment="border-trim" style="--kc-art-x:-10%">'
                  '<img class="event-artwork" src="old.webp" loading="lazy" sizes="178px"></a></article>')
        result = preview.listing_transform(source, {'paths': {path: self.record(artwork=self.artwork())}})
        doc = Document(result)
        self.assertEqual(doc.nodes[0].attrs['data-artwork-shape'], 'portrait')
        self.assertEqual(doc.nodes[0].attrs['style'], '--kc-artwork-ratio:1092 / 1440')
        anchor = doc.one(lambda n: n.has('kc-teaser-image'))
        self.assertEqual((anchor.attrs['data-artwork-treatment'], anchor.attrs['style']), ('contain', ''))
        self.assertEqual(doc.one(lambda n: n.tag == 'img').attrs['loading'], 'lazy')

    def test_artwork_assets_are_explicit_local_additions_and_hash_checked(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            live, site = root / 'live', root / 'site'
            live.mkdir(); site.mkdir()
            directory = root / 'test-overrides/assets/ignite-tour'
            directory.mkdir(parents=True)
            artwork = self.artwork()
            source = directory / 'jacksonville.webp'
            source.write_bytes(b'approved-source-bytes')
            (root / 'test-overrides/show-information-overrides.json').write_text(json.dumps({'event': {'startDate': '2027-01-29', 'artwork': artwork}}))
            with patch.object(preview, 'ROOT', root):
                preview.copy_artwork(site, live)
                self.assertEqual(preview.verify_artwork_files(site, live), 1)
                (site / artwork['src']).write_bytes(b'changed')
                with self.assertRaisesRegex(AssertionError, 'Artwork bytes differ'):
                    preview.verify_artwork_files(site, live)
                (live / artwork['src']).parent.mkdir(parents=True)
                (live / artwork['src']).write_bytes(b'production-source')
                with self.assertRaisesRegex(ValueError, 'collides'):
                    preview.copy_artwork(site, live)
                self.assertEqual((live / artwork['src']).read_bytes(), b'production-source')
                (live / artwork['src']).unlink()
                source.unlink()
                source.symlink_to(root / 'outside.webp')
                (root / 'outside.webp').write_bytes(b'outside')
                with self.assertRaisesRegex(ValueError, 'unsafe'):
                    preview.copy_artwork(site, live)
        for path in ('../outside.webp', 'assets/ignite-tour/../outside.webp',
                     'https://example.com/image.webp', '/assets/ignite-tour/a.webp',
                     'assets/ignite-tour/a.webp?x=1', 'assets/ignite-tour/a.svg'):
            with self.subTest(path=path), self.assertRaises(ValueError):
                preview.artwork_definition({'artwork': self.artwork(src=path)})

    def test_reviewed_pending_status_refresh_preserves_material_statuses(self):
        source = fixture().replace('<dd>Scheduled</dd>', '<dd>Announced — details pending</dd>')
        record = self.record(_refreshPendingStatus=True, detailsPending=False)
        self.assertEqual(reviews.field(preview.detail_transform(source, record), 'Status'), 'Scheduled')
        for fields, existing, expected in (({'private': True}, 'Announced — details pending', 'Private Event — not open to the public'),
                                            ({'soldOut': True}, 'Announced — details pending', 'Sold out'),
                                            ({'status': 'cancelled'}, 'Announced — details pending', 'Cancelled'),
                                            ({'status': 'postponed'}, 'Announced — details pending', 'Postponed'),
                                            ({'status': 'cancelled'}, 'Sold out', 'Cancelled'),
                                            ({'status': 'postponed'}, 'Cancelled', 'Postponed'),
                                            ({}, 'Cancelled — details pending', 'Cancelled — details pending')):
            record = self.record(_refreshPendingStatus=True, detailsPending=False, **fields)
            text = fixture().replace('<dd>Scheduled</dd>', f'<dd>{existing}</dd>')
            self.assertEqual(reviews.field(preview.detail_transform(text, record), 'Status'), expected)

    def test_resolved_pending_artist_rows_match_finalized_detail_status_contract(self):
        path = '/kingdom-circuit-test/event/sample/'
        with tempfile.TemporaryDirectory() as temp:
            site = Path(temp)
            detail = site / 'event/sample/index.html'
            detail.parent.mkdir(parents=True)
            for fields in ({}, {'private': True}, {'soldOut': True}, {'status': 'cancelled'}, {'status': 'postponed'}):
                record = self.record(_refreshPendingStatus=True, detailsPending=False, **fields)
                source_detail = fixture().replace('<dd>Scheduled</dd>', '<dd>Announced — details pending</dd>')
                detail.write_text(preview.detail_transform(source_detail, record))
                title, expected_status = artist_details.event_details(site, path, preview.TEST_BASE)
                for kind in ('kc-rd-show-row', 'kc-rd-next-show'):
                    with self.subTest(kind=kind, fields=fields):
                        source = listing_fixture(kind).replace('<span class="kc-rd-chevron"',
                                   '<span class="kc-rd-event-status">Announced — details pending</span><span class="kc-rd-chevron"')
                        result = preview.listing_transform(source, {'paths': {path: record}})
                        doc = Document(result)
                        statuses = [doc.text(n) for n in doc.nodes if n.has('kc-rd-event-status')]
                        self.assertEqual(statuses, [expected_status] if expected_status else [])
                        label = doc.nodes[0].attrs['aria-label']
                        self.assertIn(title, label)
                        self.assertNotIn('details pending', result)
                        self.assertNotIn('Scheduled', label)
                        if expected_status:
                            self.assertIn(expected_status.casefold(), label.casefold())
                        self.assertEqual(preview.listing_transform(result, {'paths': {path: record}}), result)

    def test_reviewed_confirmed_start_removes_only_stale_pending_time_row(self):
        source = fixture().replace('<div><dt>Venue</dt>', '<div><dt>Time</dt><dd>Pending</dd></div><div><dt>Venue</dt>')
        record = self.record(_refreshPendingStatus=True, detailsPending=False)
        result = preview.detail_transform(source, record)
        self.assertNotIn('<dt>Time</dt>', result)
        self.assertIn('9:00 PM CST', result)
        for record in (self.record(), self.record(_refreshPendingStatus=True, detailsPending=False, startTime='')):
            with self.subTest(record=record):
                self.assertEqual(reviews.field(preview.detail_transform(source, record), 'Time'), 'Pending')
        known = source.replace('<dd>Pending</dd>', '<dd>9:00 PM CST</dd>')
        self.assertEqual(reviews.field(preview.detail_transform(known, self.record(_refreshPendingStatus=True)), 'Time'), '9:00 PM CST')

    def test_reviewed_bill_preserves_exact_artist_links_and_schema_identity(self):
        line = ('<p class="artist-line"><a href="/kingdom-circuit-test/artists/altar-ego/">Altar Ego</a> - '
                '<a href="/kingdom-circuit-test/artists/brother-bo/">Brother Bo</a> - '
                '<a href="/kingdom-circuit-test/artists/k-nek/">K&#x27;nek</a> - <span>Pastor Host</span></p>')
        source = fixture().replace('<h1>Sample concert</h1>', '<h1>Sample concert</h1>' + line + '<p class="host-line">Hosted by Pastor Host</p>')
        source = source.replace('"offers":', '"performer": [{"@type":"MusicGroup","name":"Altar Ego","url":"https://example.com/altar-ego"}, '
                                '{"@type":"Person","name":"Pastor Host"}], "offers":')
        bill = ['Madigan', 'Altar Ego', 'Bo', 'K’nek']
        record = self.record(_refreshOfficialBill=True, officialBill=bill,
                             advertisedBilling=['Outdated'], artists=['Bo Fisher', 'Justo Chalaire', 'Altar Ego'])
        result = preview.detail_transform(source, record)
        names, links = reviews.billing(result)
        self.assertEqual(names, bill)
        self.assertEqual(links, {'Altar Ego': '/kingdom-circuit-test/artists/altar-ego/', 'K’nek': '/kingdom-circuit-test/artists/k-nek/'})
        self.assertIn('<span>Madigan</span> - ', result)
        self.assertIn('<span>Bo</span>', result)
        self.assertIn('<p class="host-line">Hosted by Pastor Host</p>', result)
        self.assertNotIn('Bo Fisher', result)
        self.assertNotIn('Justo Chalaire', result)
        schema = next(preview.event_schemas(preview.schema_blocks(result)[0][1]))
        self.assertEqual(schema['performer'], [{'@type': 'Person', 'name': 'Madigan'},
                                             {'@type': 'MusicGroup', 'name': 'Altar Ego', 'url': 'https://example.com/altar-ego'},
                                             {'@type': 'Person', 'name': 'Bo'}, {'@type': 'Person', 'name': 'K’nek'}])
        unreviewed = self.record(officialBill=bill, advertisedBilling=bill)
        self.assertEqual(preview.billing_notice_transform(source, unreviewed, detail=True), source)

    def test_reviewed_bill_and_notices_refresh_only_matched_compact_cards(self):
        path = '/kingdom-circuit-test/event/sample/'
        source = listing_fixture('event-card').replace('Artist</p>', '<a href="/kingdom-circuit-test/artists/artist/">Artist</a></p>')
        source = source.replace('</article>', '<p data-kc-event-notice>Free admission — no tickets needed.</p></article>')
        other = source.replace(path, '/kingdom-circuit-test/event/other/')
        record = self.record(_refreshOfficialBill=True, officialBill=['Madigan', 'Artist'], _refreshPublicNotice=True,
                             publicNotice='Free outdoor outreach. Indoor concert: $10 advance / $12 day-of.')
        result = preview.listing_transform(source + other, {'paths': {path: record}})
        doc = Document(result)
        cards = [n for n in doc.nodes if n.has('event-card')]
        self.assertEqual(reviews.billing(doc.raw(cards[0]))[0], ['Madigan', 'Artist'])
        self.assertIn('madigan', cards[0].attrs['data-search'])
        self.assertEqual(cards[0].attrs['data-artists'], 'artist')
        self.assertIn('$10 advance / $12 day-of.', doc.raw(cards[0]))
        self.assertNotIn('no tickets needed', doc.raw(cards[0]))
        self.assertEqual(doc.raw(cards[1]), other)
        self.assertEqual(preview.listing_transform(result, {'paths': {path: record}}), result)

    def test_public_notice_explicit_replace_remove_add_and_absent_preservation(self):
        notice = '<p data-kc-event-notice>Free admission — no tickets needed.</p>'
        source = fixture().replace('<dl class="detail-list">', notice + '<dl class="detail-list">')
        self.assertEqual(preview.billing_notice_transform(source, self.record(publicNotice='Source field only'), detail=True), source)
        for text, expected in (('Outdoor only is free. Indoor tickets $10 & fees.', 'Outdoor only is free. Indoor tickets $10 &amp; fees.'), ('', '')):
            record = self.record(_refreshPublicNotice=True, publicNotice=text)
            result = preview.billing_notice_transform(source, record, detail=True)
            self.assertNotIn('no tickets needed', result)
            self.assertIn(expected, result)
            self.assertEqual('data-kc-event-notice' in result, bool(text))
            self.assertEqual(preview.billing_notice_transform(result, record, detail=True), result)
        record = self.record(_refreshPublicNotice=True, publicNotice='Tickets required.')
        self.assertIn('<p data-kc-event-notice>Tickets required.</p>', preview.billing_notice_transform(fixture(), record, detail=True))
        self.assertEqual(preview.billing_notice_transform(listing_fixture('event-card'), record), listing_fixture('event-card'))

    def test_empty_reviewed_bill_removes_performer_without_adding_source_members(self):
        source = fixture().replace('<h1>Sample concert</h1>', '<h1>Sample concert</h1><p class="artist-line">Artist</p>')
        source = source.replace('"offers":', '"performer": [{"@type":"MusicGroup","name":"Artist"}], "offers":')
        record = self.record(_refreshOfficialBill=True, officialBill=[], artists=['Artist'])
        result = preview.detail_transform(source, record)
        self.assertNotIn('class="artist-line"', result)
        self.assertNotIn('performer', next(preview.event_schemas(preview.schema_blocks(result)[0][1])))

    def test_exact_reviewed_description_refreshes_stale_admission_metadata(self):
        tags = ('<meta name="description" content="Free admission — no tickets needed.">'
                '<meta property="og:description" content="Free admission — no tickets needed.">'
                '<meta name="twitter:description" content="Free admission — no tickets needed.">')
        source = fixture().replace('</head>', tags + '</head>')
        description = 'Outdoor outreach is free. Indoor tickets are $10 advance & $12 day-of.'
        record = self.record(_refreshPublicDescription=True, publicDescription=description)
        result = preview.detail_transform(source, record)
        self.assertNotIn('no tickets needed', result)
        doc = Document(result)
        self.assertEqual([n.attrs['content'] for n in doc.nodes if n.tag == 'meta' and
                          (n.attrs.get('name') or n.attrs.get('property')) in {'description', 'og:description', 'twitter:description'}], [description] * 3)
        schema = next(preview.event_schemas(preview.schema_blocks(result)[0][1]))
        self.assertEqual(schema['description'], description)
        self.assertIn(tags, preview.detail_transform(source, self.record(publicDescription=description)))

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
                      'officialBill': ['Source bill'], 'advertisedBilling': ['Source bill'], 'publicNotice': 'Source notice',
                      'city': 'Kansas City', 'state': 'MO', 'country': 'US', 'officialUrl': 'https://example.com/info'}
            original = json.dumps([source]).encode()
            (live / 'events.json').write_bytes(original)
            (live / 'supplemental-events.json').write_text('[]')
            (root / 'test-overrides').mkdir()
            additions = {'startDate': '2027-01-29', 'venue': 'Verified Hall', 'startTime': '19:30', 'timezone': 'America/Chicago',
                         'artwork': self.artwork(), 'detailsPending': False,
                         'officialBill': ['Madigan', 'Artist'], 'publicNotice': '',
                         'publicDescription': 'Reviewed concert description.',
                         'provenance': [{'url': 'https://example.com/official-event'}]}
            overrides = root / 'test-overrides/show-information-overrides.json'
            overrides.write_text(json.dumps({'manual:sample': additions}))
            with patch.object(preview, 'ROOT', root):
                ctx = preview.context(live)
                self.assertEqual(ctx['pages'][rel.as_posix()]['artwork'], self.artwork())
                self.assertTrue(ctx['pages'][rel.as_posix()]['_refreshPendingStatus'])
                self.assertEqual(preview.official_bill(ctx['pages'][rel.as_posix()]), ['Madigan', 'Artist'])
                self.assertEqual(preview.public_notice(ctx['pages'][rel.as_posix()]), '')
                self.assertTrue(ctx['pages'][rel.as_posix()]['_refreshPublicDescription'])
                # The same ID on another occurrence must not receive this time.
                overrides.write_text(json.dumps({'manual:sample': dict(additions, startDate='2027-01-30')}))
                different_date = preview.context(live)['pages'][rel.as_posix()]
                self.assertNotIn('startTimeLabel', different_date)
                self.assertNotIn('artwork', different_date)
                self.assertNotIn('_refreshPendingStatus', different_date)
                self.assertIsNone(preview.official_bill(different_date))
                self.assertIsNone(preview.public_notice(different_date))
                self.assertNotIn('_refreshPublicDescription', different_date)
                # Inherited source bill and advertisedBilling-only updates do not
                # authorize replacing the reviewed officialBill display.
                overrides.write_text(json.dumps({'manual:sample': {'startDate': '2027-01-29', 'advertisedBilling': ['Not authoritative']}}))
                self.assertIsNone(preview.official_bill(preview.context(live)['pages'][rel.as_posix()]))
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
                self.assertEqual(payload['events'][0]['artists'], ['Madigan', 'Artist'])
                self.assertEqual(payload['events'][0]['image'], preview.TEST_BASE + self.artwork()['src'])
                self.assertTrue(payload['events'][0]['artwork'])
            self.assertEqual((live / 'events.json').read_bytes(), original)


if __name__ == '__main__':
    unittest.main()
