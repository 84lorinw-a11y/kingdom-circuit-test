# Artist discovery and fan analytics — test release

This release is confined to the GitHub Pages **test** site. It does not alter production, photographs, artist records, event records or the game. The daily mirror applies `fan_engagement_preview.py` after copying the current live site. The final parity gate reconstructs every permitted change and verifies the extra assets byte for byte.

## Visitor experience

Profiles without upcoming dates keep their artist image, official profiles, schedule heading and archive. The empty schedule gains two links: **Explore [count] CHH shows / Choose your state**, and **Follow for / CHH Show Updates**. Mobile stacks the links; desktop presents two columns. Explore opens the All Shows state list and moves keyboard focus there.

The count comes from the exact All Shows catalog, with unique event URLs and inclusive final dates in America/Los_Angeles, matching the current calendar. Build-time rendering works without JavaScript. Client-side refresh removes expired dates while the page stays open, rechecks the catalog on return to the tab and at five-minute intervals, and receives new listings after the daily mirror (or a manual test refresh). It does not invent shows or fetch the artist roster separately. Unknown artist-event mappings are treated conservatively as active. Date rollover can reveal the panel when the last known upcoming date expires.

## Test verification

The owner clarified that Google should hold production data, but **must not be set up for the test website**. Test pages load no Google collection script and retain no local event log. The temporary test property was moved to Google Trash. `/test-analytics/` is a guide, not a separate reporting database. Thirty-minute source-artist attribution remains in session storage only to connect navigation steps.

Latest approval: finish the test audits, then promote to production and configure the existing Kingdom Circuit GA4 property (549068474, measurement G-N2KK9XF4TJ). Test delivery stays disabled permanently. Mocked production delivery tests verify the events before the live connection is enabled.

## Event contract

| Event | Meaning |
|---|---|
| artist_view / show_view | Opened a profile or individual event |
| empty_shows_impression | At least half of the panel visible; once per page load |
| empty_shows_click | Explore or Instagram selected; source artist recorded |
| event_select | Click to an individual show from another site page |
| ticket_referral | Click to official details/tickets; never claims a purchase |
| instagram_referral | Click to Kingdom Circuit's Instagram; never claims a follow |
| artist_social_click | Artist Instagram, Spotify, YouTube, Facebook, TikTok or official website |
| search_results | Debounced filters/search, resulting count, including zero |
| state_select | Opened a state show page |
| form_start / form_attempt | First field interaction; submitted a valid form attempt |
| form_success / form_error | Actual server acknowledgment or failure; not submit-button clicks |
| traffic_arrival | External referring domain and optional UTM source/medium/campaign |
| page_engagement | Visible seconds and furthest scroll; hidden time excluded |
| web_performance | LCP, cumulative layout-shift sum, maximum observed interaction duration (diagnostics, not certified CLS/INP) |
| site_error | Error category only; never exception messages, form contents or stack traces |

No submitted names, email addresses, freeform form values, query strings, tokens or full referral URLs are collected. Search terms and UTM values are bounded and redact obvious contact details/URLs/phone numbers. Content names come from published pages. No fingerprinting or session replay. Empty-panel attribution expires after 30 minutes and records downstream show views/referrals.

## Production rollout (not performed)

1. Promote the approved overlay to the production generator with the correct production base; do not copy the test repository or its dummy analytics identity.
2. Enable the production adapter only on kingdomcircuit.com, retaining the existing consent behavior and GA4 property. Existing legacy artist-social events must continue to have one owner to prevent double counting.
3. Verify DebugView, then register event-scoped dimensions: page_type, artist_name, show_name, placement, action, platform, destination_host, form_type, error_type, source_artist, source_action. Use GA's built-in Page path and device category where possible; viewport is a layout breakpoint, not a hardware classification. Register numeric custom metrics for result_count, show_count, visible_seconds and diagnostic performance values as needed.
4. Mark **ticket_referral** and **form_success** as primary key events; Instagram referral is a secondary intent measure. Do not relabel any as sales or confirmed followers. Audit GA enhanced form/search/outbound measurement before promotion so built-in events and custom events are not summed as duplicates.
5. Build a weekly GA exploration with visitors, ticket-referral users / event-view users, top artist/show views and referrals, zero-result searches, panel impressions and click rate, Instagram referrals, successful submissions and form completion rate. Segment every section mobile/desktop; source/medium/campaign and country/state use existing GA acquisition/coarse geography. Form abandonment is a funnel estimate, not a certain individual outcome.

Production Google settings remain unchanged during this test-only release. No historical custom events are backfilled. Blocking analytics or declining consent limits coverage.

## Verification recorded October 24

- Fresh live capture: 1,226 HTML pages, 3,565 files; 377 artist profiles; 222 currently empty profiles; 167 catalog shows at the captured Pacific date.
- Exact parity gate passed: source data and 2,308 binary assets unchanged, all transformed pages compared, new generated assets checked.
- Existing suite: 247 JavaScript tests and 150 Python tests passed; subsequent focused suite: 15 tests passed (including eight server-response/form retry scenarios and the new host/path sanitation regression).
- Browser: 320px content width, 375px content width, and 1440px desktop; no horizontal overflow or broken profile images. Both CTAs, state-list expansion/focus, search with zero results, show selection and official referral, active artist without panel, preserved archive expansion, and invalid form submission checked. No browser errors reported. Successful submission branches verified with mocked responses; no fake submissions sent externally.
- Screenshots saved locally in `Kingdom Circuit Audits/2026-10-24/no-shows-analytics/`.
- Instagram SVG uses the site's existing icon; the two arrow SVGs use Heroicons (MIT), retained from the approved draft.
