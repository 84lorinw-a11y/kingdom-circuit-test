# Verified show information in TEST

This change preserves the existing event layout and adds known attendance facts. It applies to canonical upcoming event pages and relevant listing destinations using the exact captured production catalog. It does not perform a new show discovery scan or publish production changes.

## Publication contract

- Status, Date, Venue and Location remain the primary facts. Public Location includes available street, suite, postal code and country. Confirmed local times include their time zone.
- Official details is the single main event outbound button. Confirmed event-specific ticket/registration URLs take priority. Any structured Offer uses that same URL; information pages alone do not create offers.
- Native More show details contains available description, price, organizer/promoter, secondary times, roles and attendance information. Existing schedule sections move into it without losing content. Its HTML is present before interaction.
- Known material age/admission restrictions remain visible near the button. Unknown optional fields are omitted. There is no inferred free admission, all-ages policy, public access, ticket stock or fee total.
- Numeric Offer prices require a confirmed fee-inclusive amount and currency. A verified base price can remain visible without a numeric Offer price. Shai Linne's concert-only $15 amount is such a case.
- Private events remain listed and labeled. Their detail HTML omits street/postal addresses and public Event/Offer objects. The original captured JSON is byte-preserved; this overlay is not a redaction of pre-existing public source JSON.
- Calendar cards stay compact. They do not gain full addresses or disclosures; official destinations and material admission labels remain consistent with the detail page.
- No Directions link, extra schedule/event source buttons or checkout-total filler is added.

## Implementation and checks

`scripts/show_information_model.py` derives shared display/schema facts from a copy of each collected record. The overlay uses exact canonical paths/IDs and dates, with current primary catalog data taking precedence over supplemental fields. Reviewed additions require provenance in `test-overrides/show-information-overrides.json`.

The workflow applies this overlay after fan engagement and before building isolated show-layout experiments. `verify_live_baseline.py` independently reconstructs the expected output and retains strict source-data/media parity, URL identity, Canada, archive, noindex, robots and analytics checks.

The November 2 local capture enhanced 172 event pages, including 134 details disclosures, 55 direct ticket Offers, 3 private pages and 5 Canadian pages. All 412 artist profiles and source artwork remained present. Counts are a dated snapshot, not constants.

Validation: 176 Python tests, 48 relevant JavaScript tests and the complete artifact baseline gate passed. Browser checks cover mobile and desktop event views, native disclosure interaction, All Shows search and retained destinations, private labeling/schema, Canada and narrow 320px overflow. Screenshots and logs are retained outside Git under Kingdom Circuit Audits/2026-11-02/show-information-test.

The build also repairs existing test-mirror failures: future cancelled archive entries, their Originally scheduled date label, and the explicit Rural Music Festival lineup-pending placeholder. Regression checks retain strict archive and lineup validation.

TEST remains noindex/nofollow with blocked robots, no CNAME and no Google Analytics loader or test logging. Production publishing and Cloudflare game configuration are unchanged. Future production work should integrate the model into the native publishing pipeline, not copy test identity conversion.

## November 2 address and start-time research

Reviewed all 85 public shows in the missing-information queue. Added sourced venue/street/postal facts to 65 exact ID/date records, including confirmed performance starts for Hulvey at ITOWN Madison (7 PM November 13) and FOLLOW Conference (9 PM December 29). Resolved all originally missing fields for 56 shows; 29 still have gaps (16 addresses, 19 start times, six overlap). Sources and field-specific evidence are retained in the test overrides.

Unknown performance times remain unknown when only doors, registration, admission windows, previous-year schedules or syndicated metadata are available. The CJ Emulous Cocoa conference location requires organizer confirmation before using a possible Orlando venue. Artist roster, source catalogs/media, Canadian records, archive history and private-address protections remain unchanged.

Verified corrections now flow consistently into visible detail facts, compact listing facts, artist next-show rows, event schema and generated date metadata. Material private/sold-out/cancelled warnings remain in accessible row labels. Event names and URLs are retained. This is TEST-only research and publication, not production promotion.

## November 3 owner review of unconfirmed facts

Missing core facts now display `Venue not confirmed`, `Address not confirmed`, or `Start time not confirmed` in the existing detail slots. These are display labels only: placeholder source values such as TBD and Venue not provided are omitted from factual schema. Missing optional facts and unknown public-access status do not gain boilerplate warnings; explicit private events and known material admission restrictions remain visible.

The four November RWG dates for 808 BEEZY retain their supplied dates/times and city/state. Their repeated tour-title venue values are treated as unconfirmed through an exact value match, so a later real venue from the source replaces the label automatically. EGR Bradley retains Miracle House Ministries and displays its missing address/start time as unconfirmed. Kaden Jordan's November 21 page and compact cards show the confirmed `Doors 6:30 PM PST` once; the actual performance start remains unconfirmed and schema stays date-only. If an actual start arrives later, it takes priority and doors returns to secondary details.

Six accepted-unknown records remain factual gaps, not completed verification. The refreshed owner report keeps 23 other records for review and two separate venue-evidence follow-ups. The owner subsequently supplied Ignite's official tour source; the update below resolves its two missing start times. TEST only.


## November 3 Ignite and Unite source follow-up

The owner supplied `https://www.igniteandunitetour.com/` for all four tour stops. Each Official details button now uses that site as an information destination (no invented ticket offer). The DeLand and Daytona Beach original city flyers confirm doors at 5:30 PM and a 6 PM Eastern start; Daytona also gains Suite 110. All four official schedule entries and the newer dated Jacksonville venue announcement support free admission. Jacksonville retains the October 29 no-ticket announcement, with a visible note that the older prices on the selected tour flyer do not apply. Previously confirmed guest billing is preserved where a smaller flyer is not evidence of cancellation.

Four local WebPs and two smaller responsive variants per city are optimized from the saved original 1080/1122px official PNGs without changing flyer contents or cropping. Exact ID/date overrides control detail, calendar and homepage images, enlargement links, share metadata and event image schema. Original captured JSON/media are preserved byte-for-byte; the baseline explicitly permits and hash-verifies only these new declared assets. Billing, notices and descriptions refresh only for fields explicitly reviewed in an exact override. Completed time records lose obsolete Pending labels while private/sold-out/cancelled/postponed states remain protected.

The owner review queue now has 21 shows needing research and six accepted unknowns (27 records with factual gaps), plus the same two separate venue-evidence follow-ups. The 85 original research records remain available. This is a TEST-only change.
