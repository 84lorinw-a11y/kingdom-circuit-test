"""Render/schema contract tests for the final test-only information overlay."""
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import show_information_preview as preview
from show_information_model import normalize
from mobile_seo_preview import Document


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


if __name__ == '__main__':
    unittest.main()
