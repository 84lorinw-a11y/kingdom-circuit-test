import copy
import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "scripts"))
from show_information_model import normalize


class ShowInformationModelTests(unittest.TestCase):
    def event(self, **fields):
        return {"title": "A real concert", "startDate": "2027-01-29",
                "startTime": "21:00", "timezone": "America/Chicago", **fields}

    def test_source_is_preserved_without_mutation_and_notes_are_not_description(self):
        source = self.event(country="CA", notes="Internal research, do not publish", artists=["Artist"])
        before = copy.deepcopy(source)
        result = normalize(source)
        self.assertNotIn("description", result)
        self.assertEqual(result["country"], "CA")
        result["artists"].append("Other")
        self.assertEqual(source, before)

    def test_new_source_details_replace_previously_unconfirmed_venue(self):
        placeholder = self.event(venue='RWG TOUR 2026', unconfirmedVenueValue='RWG TOUR 2026')
        self.assertEqual(normalize(placeholder)['venueLabel'], 'Venue not confirmed')
        refreshed = normalize({**placeholder, 'venue': 'Confirmed Hall', 'address': '100 Main St'})
        self.assertEqual(refreshed['venueLabel'], 'Confirmed Hall')
        self.assertEqual(refreshed['address'], '100 Main St')

    def test_public_description_precedes_legacy_description(self):
        result = normalize(self.event(publicDescription=" Public copy ", description="Other", notes="Internal"))
        self.assertEqual(result["description"], "Public copy")
        self.assertEqual(normalize({"description": " Legacy copy "})["description"], "Legacy copy")

    def test_dst_offsets_come_from_event_date(self):
        winter = normalize(self.event())
        summer = normalize(self.event(startDate="2027-07-29"))
        self.assertEqual(winter["schemaStartDate"], "2027-01-29T21:00:00-06:00")
        self.assertEqual(summer["schemaStartDate"], "2027-07-29T21:00:00-05:00")
        self.assertEqual((winter["timezoneLabel"], summer["timezoneLabel"]), ("CST", "CDT"))

    def test_ambiguous_and_nonexistent_clocks_do_not_choose_an_offset(self):
        for day, clock in (("2026-11-01", "01:30"), ("2027-03-14", "02:30")):
            result = normalize(self.event(startDate=day, startTime=clock))
            self.assertEqual(result["schemaStartDate"], day)
        explicit = normalize(self.event(startDateTime="2026-11-01T01:30:00-06:00"))
        self.assertEqual(explicit["schemaStartDate"], "2026-11-01T01:30:00-06:00")

    def test_date_only_and_unknown_zone_never_invent_midnight_or_offset(self):
        result = normalize({"startDate": "2027-01-29", "timezone": "America/Chicago"})
        self.assertEqual(result["schemaStartDate"], "2027-01-29")
        self.assertNotIn("startTimeLabel", result)
        unknown = normalize(self.event(timezone="Invalid/Zone"))
        self.assertEqual(unknown["schemaStartDate"], "2027-01-29")
        self.assertEqual(unknown["startTimeLabel"], "9:00 PM")
        offset = normalize({"startDateTime": "2027-01-29T21:00:00-06:00"})
        self.assertEqual(offset["schemaStartDate"], "2027-01-29T21:00:00-06:00")

    def test_optional_end_and_admission_clocks(self):
        result = normalize(self.event(endTime="22:00", doorsTime="20:00", registrationTime="20:30"))
        self.assertEqual(result["schemaEndDate"], "2027-01-29T22:00:00-06:00")
        self.assertEqual((result["doorsTimeLabel"], result["registrationTimeLabel"], result["endTimeLabel"]), ("8:00 PM CST", "8:30 PM CST", "10:00 PM CST"))
        self.assertNotIn("schemaEndDate", normalize(self.event()))
        self.assertNotIn("schemaEndDate", normalize(self.event(endTime="00:00")))
        overnight = normalize(self.event(endDate="2027-01-30", endTime="00:00"))
        self.assertEqual(overnight["schemaEndDate"], "2027-01-30T00:00:00-06:00")

    def test_private_is_explicit_and_clears_street_but_not_country(self):
        for fields in ({"status": "private"}, {"admission": "invite only"},
                       {"title": "Listening session — Invite-Only"},
                       {"venue": "Private event"}, {"ageRestriction": "Invitation only"}):
            result = normalize(self.event(**fields, address="123 Hidden St", postalCode="A1A 1A1", country="CA", ticketUrl="https://posh.vip/e/a-show"))
            self.assertTrue(result["private"])
            self.assertEqual((result["address"], result["postalCode"], result["country"]), ("", "", "CA"))
            self.assertIsNone(result["offer"])
        self.assertFalse(normalize(self.event(title="Youth Night", ageRestriction="Ages 13–18"))["private"])
        self.assertFalse(normalize(self.event(title="Private Thoughts album tour"))["private"])

    def test_generic_information_and_profiles_are_not_ticket_offers(self):
        for url in ("https://www.bandsintown.com/e/123-an-event", "https://www.eventbrite.com/",
                    "https://www.ticketmaster.com/artist/123", "https://artist.example/",
                    "https://www.instagram.com/artist/", "https://open.spotify.com/artist/123"):
            result = normalize(self.event(ticketUrl=url))
            self.assertIsNone(result["offer"], url)
            self.assertEqual(result["officialDestination"]["kind"], "details")

    def test_direct_ticket_is_preferred_and_label_is_always_official_details(self):
        ticket = "https://www.eventbrite.com/e/a-real-concert-tickets-2000000123456"
        result = normalize(self.event(ticketUrl=ticket, officialUrl="https://artist.example/", ticketLabel="Buy now"))
        self.assertEqual(result["officialDestination"], {"url": ticket, "kind": "tickets", "label": "Official details"})
        self.assertEqual(result["offer"], {"@type": "Offer", "url": ticket})
        verified = normalize(self.event(registrationUrl="https://ready27.events.example/", registrationUrlVerified=True))
        self.assertEqual(verified["officialDestination"]["kind"], "registration")
        self.assertEqual(verified["officialDestination"]["label"], "Official details")
        self.assertIsNotNone(verified["offer"])

    def test_existing_direct_platform_shapes_and_spoofed_hosts(self):
        for url in (
            "https://www.livenation.com/event/rZ7HnEZ1AfGUq7/a-concert",
            "https://dice.fm/partner/tickets/event/abc12-a-concert-tickets",
            "https://wl.eventim.us/event/a-concert/707572?afflky=Venue",
            "https://events.ticketleap.com/tickets/organizer/a-canadian-concert",
        ):
            self.assertEqual(normalize(self.event(ticketUrl=url))["offer"]["url"], url)
        for url in ("https://eventbrite.com.attacker.example/e/a-concert-tickets-123",
                    "https://www.livenation.com/artist/123/", "https://dice.fm/partner/tickets/"):
            self.assertIsNone(normalize(self.event(ticketUrl=url))["offer"])

    def test_verification_flags_are_boolean_and_cannot_turn_social_into_offer(self):
        for flag in ("true", 1, False):
            self.assertIsNone(normalize(self.event(ticketUrl="https://artist.example/", ticketUrlVerified=flag))["offer"])
        result = normalize(self.event(ticketUrl="https://www.instagram.com/artist/", ticketUrlVerified=True))
        self.assertIsNone(result["offer"])
        self.assertIsNone(normalize(self.event(ticketUrl="javascript:alert(1)", ticketUrlVerified=True))["officialDestination"])

    def test_price_strings_are_display_only_and_totals_require_currency_and_fees(self):
        source = self.event(ticketUrl="https://posh.vip/e/a-show", price="Concert only: $15")
        legacy = normalize(source)
        self.assertEqual(legacy["priceLabel"], "Concert only: $15")
        self.assertNotIn("price", legacy["offer"])
        structured = {"amount": "15", "currency": "USD", "ticketType": "Concert only", "includesAllFeesConfirmed": False}
        result = normalize({**source, "price": structured})
        self.assertEqual(result["offer"]["name"], "Concert only")
        self.assertNotIn("price", result["offer"])
        total = normalize({**source, "price": {**structured, "includesAllFeesConfirmed": True}})
        self.assertEqual((total["offer"]["price"], total["offer"]["priceCurrency"]), (15, "USD"))
        for price in ({"amount": "15", "includesAllFeesConfirmed": True},
                      {"amount": "NaN", "currency": "USD", "includesAllFeesConfirmed": True},
                      {"amount": "-1", "currency": "USD", "includesAllFeesConfirmed": True}):
            self.assertNotIn("price", normalize({**source, "price": price})["offer"])
        free = normalize({**source, "price": {"amount": 0, "currency": "CAD", "includesAllFeesConfirmed": True}})
        self.assertEqual(free["offer"]["price"], 0)

    def test_sold_out_is_explicit_and_closed_events_have_no_offer(self):
        source = self.event(ticketUrl="https://posh.vip/e/a-show")
        self.assertNotIn("availability", normalize(source)["offer"])
        for fields in ({"soldOut": True}, {"ticketAvailability": "sold_out"}):
            self.assertEqual(normalize({**source, **fields})["offer"]["availability"], "https://schema.org/SoldOut")
        self.assertNotIn("availability", normalize({**source, "soldOut": "true"})["offer"])
        for status in ("cancelled", "canceled", "postponed", "merged"):
            self.assertIsNone(normalize({**source, "status": status})["offer"])
        self.assertIsNotNone(normalize({**source, "status": "rescheduled"})["offer"])

    def test_organizer_uses_only_supplied_name_and_valid_url(self):
        result = normalize(self.event(organizer={"name": "The venue", "url": "https://venue.example/"}, ageRestriction="All ages"))
        self.assertEqual((result["organizerName"], result["organizerUrl"], result["admissionLabel"]), ("The venue", "https://venue.example/", "All ages"))
        legacy = normalize(self.event(organizer="Real organizer", officialUrl="https://ticket.example/"))
        self.assertEqual(legacy["organizerName"], "Real organizer")
        self.assertNotIn("organizerUrl", legacy)


if __name__ == "__main__":
    unittest.main()
