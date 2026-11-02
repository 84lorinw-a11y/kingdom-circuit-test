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
