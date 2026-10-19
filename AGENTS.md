# Kingdom Circuit test-site instructions

## October 19 development boundary

- The owner directs all new development to TEST. Do not promote changes to production without a separate explicit release instruction.
- Start from the current published production baseline, preserving its learned game behavior and normal-site layout. Keep test URL, noindex, analytics and deployment safeguards.
- The existing GitHub Pages TEST and its source repository are public. The earlier password-free authorization covers the existing released CHH game; it does not authorize exposing unreleased songs or private review assets. Keep those local/private until a protected test destination is in place. Do not confuse noindex with access control.
- TEST currently shares the original game's Google score service with production. Do not add synthetic QA scores or mix future campaign data into that live competition. New campaigns need a separate test campaign/backend before online score testing.

## October 18 CHH Show Night test game

- The owner explicitly authorized publishing the game without a password on the existing test site. Keep `/play/` as a direct-link, noindex/nofollow test route, absent from ordinary navigation and sitemaps. This does not authorize a production deployment.
- Durable game source and the exact approved asset inventory are in `test-overrides/chh-show-night/` and `chh-show-night-manifest.json`. Update the manifest when intentionally changing source; never include local `.env`, password-gate files, development artifacts or unused artwork.
- `scripts/build_chh_game.py` adds the game during every daily mirror. Final verification compares every published game file with the manifest-pinned source and retains exact parity for all pre-existing live pages. Do not bypass those checks or expose a Node password gate as a static page.
- October 18 owner-approved rebuild supersedes the old 125 XP ceiling and one-time Eli reward: preserve the approved short music excerpts and free VIP access; four replayable games (Eli, Joz, Steven, Chamblissnation) each have 20 scoring opportunities, 40 base +10 clean bonus, maximum 1,000 per round. Session totals grow across replays, with separate journey rewards. Use the one-screen touch-first mobile layout and detailed illustrated people. Shared scores require a connected backend; never claim device-only scores are a global board. Keep the score server/database outside the public static inventory.

- This repository deploys the test site only. Never push to or change `84lorinw-a11y/kingdom-circuit` unless the user separately and explicitly asks for a production promotion.
- Treat checked-in root HTML/JSON as an old generated snapshot, not the durable implementation. Test-only changes belong in the overlay scripts under `scripts/` and their matching verification scripts.
- Preserve the test safeguards: `/kingdom-circuit-test/` base paths, `noindex,nofollow`, production analytics disabled, no `CNAME`, no operational/source-report files in the deployed artifact, and no workflow commits of generated output.
- Keep “Official details” links working while suppressing visible/internal source attribution from the public artifact.
- A deployment may proceed only after every verifier passes. If a check fails, fix the generator or overlay rather than weakening the check.
- The user has granted standing authorization to deploy verified changes to this test repository and its test website. Do not ask for repeated test-deployment approval; production deployment still requires separate explicit approval.
- Before handoff, verify representative desktop and mobile pages, the artists directory, an artist profile, an event page, the submit/correction flow, navigation keyboard behavior, local links, and responsive images.

- Latest October 18 cast revision: use the identical 30-person cast across exterior, main stage and VIP (8 white, 12 Black, 10 brown-skinned illustrated fans; the owner subsequently replaced two white women with Black women). Steven collects these exact people and keeps the caught crew with him. Merch marker says Merch; keep vendor face clear. Right venue wall has only the orange-rimmed Kingdom Circuit logo matching the VIP room, no door or steps. VIP photo uses the actual lounge backdrop and a prominent player name.

- Latest VIP photo revision: preview and download share a tighter crop around the six-person group beneath the actual VIP banner. Keep Classic and Lean In and add Peace Sign for every selectable player. Jay wears the woodland Chamblissnation “Your People My People We Family” tee in every room and photo pose. This photo crop supersedes the older wide composition including the lounge furniture and side-wall emblem.

- Latest mobile correction: grass, crowds and lounge furniture must never block walking. Keep the main-stage player and friends on the audience floor (y >= 444), below the stage and merch display. Clamp taps above that edge to the floor in front; all activity circles remain reachable. This supersedes unrestricted walking onto the stage/table and the older scenery collision routing. The refreshments/break spot shows a brief message without pausing or locking movement. Music and effects share one gesture-unlocked audio context, a visible master On/Off control, bounded loading and an interruption retry state. Preserve approved songs, excerpts, bass effects and scoring.

- Player entry: every page load or refresh opens name/character selection, with an explicit Continue for saved players. A new game clears the nickname and character, requires both choices, and preserves the device’s best score. Never silently reuse KC or a previous player for a fresh session.

- Eli mobile polish: use the concert’s detailed DJ booth, a responsive four-lane beat board, larger color-matched pads and live-audio timing. Keep controls stationary while the arena reacts to bass; preserve reduced-motion/FX controls, the approved 26-second excerpt and equal 40 + 10 scoring. Every round result offers instant replay and an obvious return to the show.

- All-player scoreboard: show ranked rows with Player, Eli, Joz, Steven, Merch, Journey and Total at the end. Retain each player's best complete session and include zero-score entrants. Pagination must allow access to every player, not just a top-100 list. Preserve nickname-only entry and distinguish different names starting new games on a shared phone. Clearly label browser-only scores until a persistent online service is actually connected; never invent past players or import unverified local game scores as online results.

- Blue Soul player: preserve the higher navy crew neckline in both the normal/leaning and VIP peace-sign poses. Keep her existing saved character ID and other appearance unchanged.

- Latest mobile flow revision: friend invitations explicitly say Bring Jay/Grace along or Keep exploring / Invite later; a premature venue visit offers a direct walk to missing friends. Unvisited circles and destination buttons gently pulse gold, with a readable Next prompt; visited stops stay steady and VIP remains freely accessible. Persist visits separately from scores, including zero-point rounds. Merch has faster drifting drops and alternating sides with a narrower catch window, retaining 20 opportunities and the identical 40 + 10 scoring rule. The VIP water break lasts six seconds with Jay and Grace sipping water; any movement, destination or Done resting cancels it immediately. This supersedes the old toast-only break. Keep dialog cleanup synchronous and ignore stale native close events so the next view cannot be stopped; cap final movement steps and preserve mobile background/return recovery. Shared-score hosting is tabled at the owner's request.

- October 18 shared scores: Google Sheets + Apps Script is authorized and connected on TEST, superseding the earlier decision to table it. Use workbook `1YhSyRhnLUFliM8x-ngY1WH8OCvIfxJBGZmt701mWLb4`, **CHH Show Up** (gid 72099769), and its hidden `_CHH Score Data` helper. Preserve unrelated artist/business tabs and sharing settings. The bound **Kingdom Circuit CHH Test Scores** project runs the reviewed `game-backend/apps-script/Code.gs`. Anonymous browser saves across all four games, duplicate receipts and independent identities were verified. Keep server/helper files outside the static artifact; never store raw player tokens in the sheet. Preserve automatic retries and persistent pending-round saves. Production remains separately authorized. Endpoint and operational notes are in `game-backend/apps-script/README.md`.

- Score exit flow: a session is one saved night including replays; refreshing can continue it. Explain this on entry and the scoreboard. Provide Save & Exit in the menu and save-before-reset for New Game. Only confirm an online save after the service returns the matching current total; distinguish pending, device-only and historical unverified points. Never imply that closing a mobile browser can reliably trigger an online save.

## October 13 mobile-first SEO preview

- The owner explicitly approved broad mobile UX/SEO work on TEST ONLY. Preserve the exact published production content as the input, then apply `scripts/mobile_seo_preview.py` after the isolated experiments. Do not reapply the obsolete global redesign.
- The final baseline gate recomputes the narrowly defined navigation/reading-order transformations and still compares every output file. It independently preserves event cards, full archives, images, original filter forms, canonical URLs, titles and schema. Data and image files remain byte-identical to live. Do not replace these checks with ignored-file exceptions.
- Home has early real state links; All Shows has a compact state directory plus the existing combined filters. State/city calendars show events before featured artists. Posters remain the default; Quick list is optional. Preserve test noindex, analytics isolation, and the live site's unchanged URLs/data. Promoting this feature to production requires a separate user request and a production-specific implementation, never deploying this test harness to live.

## October 13 national discovery preview

- The owner subsequently requested whole-site mobile UX/SEO improvements, still TEST ONLY. Apply `scripts/national_discovery_preview.py` after the mobile preview and before final verification.
- This deliberately replaces the homepage's duplicated full calendar with at most 13 accurate show previews, six real artist portraits, search and when/where/who discovery routes. The owner's later request moves the exact existing mission to the new `/about-us/` page, not a shortened or rewritten mission. Home uses the exact heading “Find CHH Shows Near You!” on one line. The latest owner request removes “CHH Live and Connected” and shortens the subtitle to “CHH concerts, christian rap shows and festivals!”, sized to fit one line on phones. The Instagram strip is 18px (25% shorter than 24px), and navigation boxes are 32px tall. Every original home listing must remain in the complete All Shows calendar. The full artist roster and original profiles, schedules, archives, event details, billing, status labels, images and data remain intact.
- The two approved new destinations are `/about-us/` and evergreen `/shows/this-weekend/`, using Friday–Sunday overlap, inclusive end dates and the catalog's existing America/Los_Angeles expiration boundary. Empty and expired windows must not silently expand to the full calendar. Primary navigation has the six original links plus This Weekend and About Us, compact enough for mobile. Preserve real official-details links and avoid fabricated dates, popularity claims or lastmod timestamps.
- The owner's subsequent spacing request compacts the homepage intro, keeps a single show/artist action row and labeled search, and reduces the state finder to its picker plus complete state-link disclosure. Do not restore duplicate weekend/month/artist buttons or a second visible “Find your next show” heading above the listings; those destinations remain in primary navigation. Preserve all state URLs, the full show inventory and the exact approved brand copy.
- Final verification recomputes both approved transformations for every source file, plus independent homepage-selection, full-calendar, directory/profile, metadata/schema, weekend-content, mission-transfer and eight-link navigation invariants. The original mobile homepage full-calendar invariant is superseded only by this stricter selection-plus-complete-calendar contract; the previous mission-on-home check is superseded by exact preservation on About Us. All other protections remain. Never ignore files to pass a build.
- Test remains blocked from indexing. Do not deploy this test harness to production or infer ranking improvements from test-site checks.

## October 15 fan-first redesign

- The owner approved a full TEST-only layout redesign while keeping the existing theme, colors and logo. The top finder combines location, dates and search. Nationwide is the default; location/date choices narrow the calendar without location permission prompts.
- Homepage previews now use two nonoverlapping shelves: Happening This Week (today through Sunday) and Coming Up Next (starts after Sunday), six eligible shows each, then up to six artists. This supersedes the prior 13-card weekend/festival/recent selection. Do not invent trending/popularity or depend on firstSeen. Keep the existing This Weekend URL and Friday–Sunday semantics unchanged.
- Keep the original eight navigation destinations and all permanent state links. State directory and total-count actions may appear after the previews to prioritize actual shows. Use the unchanged owner-approved heading/subtitle.
- Progressive calendar enhancements may rearrange existing filter controls and add artist-name search results, date choices and removable filter labels. Static forms/cards/profiles and data remain preserved byte-for-byte by the existing independent checks. Existing canonical URLs, title/meta/schema, full schedules/archives and production isolation remain mandatory.
- `fan-discovery.css` and `fan-discovery.js` are applied by the national discovery layer. Match event eligibility, date overlap and empty results across server-rendered shelves and client filters; no autoplay. Verify mobile/desktop, keyboard navigation, zero-show artists and empty-state filters before deploying.

## October 17 owner-approved refinements (TEST ONLY)

- Supersedes the six-item weekly shelf/artist limits: include every eligible public show from today through Sunday, then up to 40 real artists with upcoming shows, then Coming Up Next. Preserve eligibility and all source data.
- Rename the homepage location selector State, add a search magnifier and direct artist-profile suggestions, and retain directional carousel/dropdown arrows. Search submission remains a combined-results search; choosing a profile suggestion opens that profile.
- Remove Posters/Quick list switching; keep the normal complete event cards. Recommend actual bordering states with nonzero current inventory for empty states; never silently replace a selected state or claim distance-based proximity.
- Restore exact full national-calendar event cards below each compact artist schedule, before its unchanged Past Shows. Verify the added cards exactly against the source calendar and verify the original profile after removing only the new section. No data/schema/canonical changes.
- Orange Instagram strip is half its former 18px height, with reduced text/icon sizes and enlarged keyboard-focus state.
- The compact portrait card is ONE isolated Brenno comparison at `/test-card-preview/`. Do not apply that sizing to other show cards until the owner approves the sample.

## October 17 artwork-adaptive cards (approved)

- Owner approved the Brenno sample and applying it to both homepage show shelves on TEST ONLY. Use 180px cards with compact details. Standard portrait, square and landscape images retain their natural proportions; tall Story images fit inside a capped 3:4 frame with side margins. Never stretch or crop away flyer details. Cards align at the top and may be shorter for square/wide artwork.
- Preserve original image files, srcset, intrinsic dimensions, alt text, event details and destinations. Only responsive `sizes` changes to match the smaller preview. Keep normal full calendars, artist detail cards and artist tiles unchanged. The existing `/test-card-preview/` now demonstrates all four real formats, using the same styles as homepage shelves.

## October 17 uniform Brenno standard (latest owner correction)

- Supersedes adaptive card heights: EVERY homepage show preview must be 180px wide by 350px high, using Brenno's 1092:1440 image-frame ratio for all artwork shapes. All image bottoms, text rows and card bottoms align. Preserve contain/no stretching; square and wide artwork have black margins in the shared portrait frame.
- Use fixed preview text rows (date, two-line title, artist, location, venue) with ellipses where needed. Preserve complete text and links in HTML, accessible names, hover titles, event pages and full listings. Never force all cards to a taller size merely to fit the longest copy.

## October 17 safe image enlargement (latest approval)

- Owner approved enlarging preview artwork: fill frames with plain artist photos and remove visually reviewed empty/decorative flyer borders with CSS-only framing. Retain 180×350 cards and Brenno's image frame. Never stretch images or cut off important flyer text. Text-heavy or unreviewed flyers default to contain; some margins are intentional.
- Bind reviewed bounds to the exact source asset/dimensions, not artist or event names. Preserve original files, full event-page posters, image metadata, URLs and all other content. Responsive sizes must reflect the enlarged image, and broken-image fallbacks must not inherit a crop. Test only.

## October 17 About Us story (TEST ONLY)

- Owner supplied the founding story (July2026), catalog/source description, community quote and exploratory Canada outreach. Add these to the existing About Us route with readable mobile sections, preserving the original mission without a redundant restatement.
- Use actual unexpired catalog/artist totals from the same build as the listings, with an honest as-of date; never freeze the draft136+/361 figures or fabricate a refresh timestamp. Keep the supplied quote anonymous and Canada wording exploratory, not an announced partnership. Link existing show/artist submission routes, official website and Instagram. Do not invent founder names, contact details, testimonials or policies.
- Latest owner correction: remove the entire Canada outreach section (including Canada4Christ) from About Us. Keep the other five sections, catalog totals, mission, quote and links unchanged. This is a copy-only test-site change; do not remove Canadian artists or shows from the catalog.

## October 17 compact full show listings (TEST ONLY)

- Owner requested the regular show listings use a compact portrait image treatment similar to Happening This Week, removing wasted image space. This supersedes the earlier layout-only restriction on full calendars: CSS may present portrait artwork beside full details, one listing per row on phones and two on wide desktop screens.
- Keep every original calendar card byte-for-byte, including full billing, dates, venue/location, status labels, image metadata and working official/event/artist links. Do not truncate full-listing text. Flyers retain contain/no stretching and artist photos may fill; preserve original files. Keep hidden filter results hidden and maintain accessible metadata labels and 44px official-details actions.
- Scope these styles to `.calendar`; homepage shelves, artist profile detail cards and event detail posters retain their existing presentation. No URL, canonical, schema, data or production changes. Existing exact-card and source-baseline gates remain mandatory.

## October 17 artist portraits in search (TEST ONLY)

- Owner requested clickable circular artist-profile photos in search, like the homepage upcoming-artist circles, while retaining matching shows below. Add the same original artist-directory photo to both homepage suggestions and calendar matching-artist results, with an explicit profile action. Preserve name/count metadata, zero-show profile results, keyboard access, filters and all event cards.
- Use a small existing optimized image variant and the original focal position; no invented/replacement photos or new image files. Missing/broken images fall back to initials without breaking the profile link. Keep test isolation and exact source-content/SEO-identity checks.

## October 17 uniform regular listings (latest owner correction, TEST ONLY)

- All regular calendar cards must match their peers at Brenno's compact size: 218px high on mobile and 237px on desktop, with equal grid widths. This supersedes variable-height full listings and the earlier no-clamping/44px-button presentation rule, not exact source-card preservation.
- Remove category chips (Concert, Appearance, etc.) from the visible calendar preview, but preserve sold-out/cancellation/pending warnings. Smaller readable type, bounded two-line title/artist previews and a 30px Official details pill keep cards compact. Keep all original text/links in HTML and the full event page; focused artist links must remain usable inside their bounded preview.
- CSS remains calendar-scoped. Preserve original flyers with contain/no stretching, existing artist-photo fill, all filters, source cards, URLs, metadata, schema, production isolation and independent verification gates.

## October 17 full Coming Up Next week (TEST ONLY)

- Owner requested the whole week in Coming Up Next. Include every eligible show starting the following Monday through Sunday, without the former six-card cap. Show the exact date range; retain horizontal scrolling, uniform Brenno cards, existing eligibility and the current-week/40-artists/next-week order.
- The existing `dates=upcoming` calendar filter and its View all link must match that bounded next-week window. Label the date choice Next week. Empty weeks must stay empty with a useful all-shows link, not silently extend into later weeks. Preserve full catalog data, all existing URLs/SEO identities and production isolation.

## October 17 mobile artist heading (TEST ONLY)

- Keep the exact heading Artists with upcoming shows on one line on mobile. Give it the full section width with fluid, readable type; place All artists beside the Follow the music eyebrow above it. Preserve the full heading text without clipping/ellipsis, the accessible heading/link, desktop layout and all cards.

## October 17 Facebook header link (TEST ONLY)

- Add a blue Facebook icon immediately right of the large Instagram button wherever that shared header action is present. Destination is exactly https://www.facebook.com/profile.php?id=61593510924754, opening in a new tab with a descriptive accessible label and noopener/noreferrer.
- Match the Instagram button's44px target/38px icon; keep social icons beside each other without overlap. On very narrow phones, the logo and Submit a Show may stack to their left so the logo stays readable. Preserve the orange Instagram strip, existing Instagram/submit links, compact profile-header behavior, all artist socials, navigation and source data/SEO identities. No production change.

## October 17 readable follow bar and tighter header spacing (TEST ONLY)

- Owner requested undoing the tiny orange strip: use a 24px bar, 11px text and 14px Instagram icon, retaining the orange theme and existing copy/link. This supersedes the earlier 9px strip.
- Tighten vertical padding between the bar and header controls, and below the eight navigation boxes before the homepage intro. Preserve social-button hit targets, all eight links, narrow-phone layout, page content and SEO identities. Keep anchor/focus clearance compatible with the taller fixed bar. Production remains unchanged.

## October 17 production promotion (supersedes TEST ONLY status above)

- Owner explicitly approved production deployment. The reviewed layout from test36be2c60 is now live through production288c967b7ea0b570676e86f4704dcc8728bba076, successful run39063884533. Earlier TEST ONLY labels describe history, not the current deployment. Preserve all latest reviewed layout/content requirements above.
- Production uses native scripts/mobile_discovery.py, scripts/national_discovery.py and scripts/finalize_fan_discovery.py after the retained legacy SEO/design pipeline. Do not copy this test harness or test identity settings into production.
- Once capture detects the complete promoted production layout, test must mirror that artifact exactly with environment-only safety conversion; do not apply mobile/national overlays a second time. Preserve the three isolated test experiments, noindex/nofollow, blocked robots, disabled analytics, test paths and absent CNAME. Incomplete promotion detection fails closed.
- Existing 1,178 production pages and all previous sitemap URLs were preserved; only /about-us/ and /shows/this-weekend/ were added. Public release verification passed57pages and6assets. Counts are a dated snapshot; continue mirroring current published content rather than freezing it.
