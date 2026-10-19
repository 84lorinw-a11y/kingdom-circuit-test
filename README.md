# Kingdom Circuit Test

## Development boundary — October 19

All new development stays in TEST; production promotion requires a
separate owner instruction. The starting point is the current published
production site and game, converted only for test deployment identity.
This GitHub Pages site and repository are public. Keep unreleased audio
and private review assets local/private until a protected review environment
exists. `noindex` does not restrict access. The original game currently shares
production's Google score service; use a separate campaign/backend for future
campaign test scores and never add synthetic players to the live board.

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
# CHH Show Night — test game

Game URL: https://84lorinw-a11y.github.io/kingdom-circuit-test/play/

The owner approved password-free testing on October 18, 2026. This route is intentionally absent from site navigation and sitemaps and includes `noindex,nofollow`. It is publicly accessible to anyone with the address; there is no server or shared password on GitHub Pages.

Edit `test-overrides/chh-show-night/` and update the SHA-256 inventory in `test-overrides/chh-show-night-manifest.json` for intentional source changes. The mirror workflow runs `scripts/build_chh_game.py _site` before the final release verifier. That script rewrites `/play/` asset URLs for the test base path and verifies exact file contents, imports, the asset inventory, indexing policy and absence of password endpoints. Existing site pages remain an exact environment-adjusted copy of the published site. Keep the local password server, `.env`, development artifacts and obsolete art out of the public game inventory. The separate `game-backend/` source is intentionally outside the Pages artifact.

Game behavior checks: `node --test tests/chh-game/*.test.mjs`. Deployment checks: `python -m unittest discover -s tests -p 'test_*.py'`, followed by the full mirror workflow. Publishing this test branch does not promote the game to KingdomCircuit.com.

## October 18 rebuild

The game uses a single-screen touch layout, detailed illustrated scenes and people, and four replayable challenges: Eli, Joz, Steven and Chamblissnation. Every challenge has the same hit/clean-hit scoring. **No session score cap:** completed rounds add to each activity subtotal and the total forever; 1,000-point intervals are celebrations, never a finish line. Music-backed rounds stay 21–26 seconds and keep the approved excerpts. Nickname entry requires no signup. Chamblissnation’s 25-second round plays Joz’s “Bounce Back,” restarts the excerpt on replay, and stops the music on exit.

The larger opening marquee names Steven Malcolm, Eli Williams and Joz. The right venue wall carries Kingdom Circuit’s logo. Chamblissnation’s supplied products, logo and family message appear in merch; two fans wear the supplied outfits. VIP photos include the full wall emblem and six people under the @thekingdomcircuit banner.

The static board saves the best complete session on the device and says so. The optional Node 24/SQLite service in [game-backend](game-backend/README.md) has been implemented and tested locally; it needs online hosting and persistent storage before the published test has shared scores. No server/database or token is shipped inside the static artifact.

Built-in image generation produced the new scene, crowd and item assets. Selected paths and the prompt specifications are recorded in `docs/chh-rebuild-art.json`. Existing artist artwork and approved audio are preserved.
