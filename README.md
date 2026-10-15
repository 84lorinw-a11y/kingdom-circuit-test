# Kingdom Circuit Test

This repository captures the latest successful Kingdom Circuit production
deployment, then applies approved **test-only** UX/SEO previews at:

https://84lorinw-a11y.github.io/kingdom-circuit-test/

Deployment safeguards include test-site URLs, no search indexing,
production analytics disabled, no production `CNAME`, and no internal build
reports. Generated pages are deployed as a Pages artifact and are never
committed back to this branch. The workflow captures the actual deployed live
site, follows its sitemap and local assets to completion, and verifies that the
homepage, sitemap, and event catalog did not change during capture. This keeps
the test environment aligned with the exact optimized images, generated pages,
and source content that visitors see in production. The preview rebuilds daily
and can also be started manually.

The existing experiments remain isolated at `/test-all-shows/`,
`/test-show-feed/` (Feed, Split, and Grid), and `/test-artist-intake/`.
They use the current mirrored show data. The normal preview adds mobile state
discovery, clearer calendar reading order and an optional Quick list view.
The national discovery layer turns Home into a compact front door, preserves
the complete All Shows calendar and artist roster, and adds an evergreen
This Weekend calendar, homepage artist portraits and artist breadcrumbs.
The owner's mission now lives unchanged on a compact About Us page. The eight
primary navigation links include This Weekend and About Us; the Instagram strip
and navigation use less space, and Home has a single-line “Find CHH Shows Near You!” heading.
The homepage intro now uses tighter spacing, one compact show/artist action row,
search and a small state picker; repeated navigation is removed so listings appear sooner.
The latest header refinement removes the homepage tagline, uses the one-line
“CHH concerts, christian rap shows and festivals!” subtitle, and reduces the
Instagram strip to 18px and navigation boxes to 32px tall.
The mission, original page identities, official details, event/artist data,
photos and full schedules/archives are preserved.

The October 15 fan-first layout keeps the brand palette and adds a compact
location/date/search finder, horizontal This Week and Coming Up Next shelves,
and artist portraits. Shelves use real event dates, never popularity or firstSeen.
Calendar pages use smaller headings, grouped filters and searchable artist
profiles even when no upcoming shows match. No existing URL is renamed.

The final release gate recomputes the approved transformations for every
source file, compares data and binary assets byte-for-byte, and independently
checks content, date handling, metadata, schema and test safeguards. It does
not ignore changed files. Do not reapply the older global redesign or deploy
this test harness to production. Production promotion requires a separate
request and production-specific implementation; this preview cannot measure
Google rankings because indexing is intentionally disabled.
