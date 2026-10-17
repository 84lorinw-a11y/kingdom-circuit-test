# Kingdom Circuit test-site instructions

- This repository deploys the test site only. Never push to or change `84lorinw-a11y/kingdom-circuit` unless the user separately and explicitly asks for a production promotion.
- Treat checked-in root HTML/JSON as an old generated snapshot, not the durable implementation. Test-only changes belong in the overlay scripts under `scripts/` and their matching verification scripts.
- Preserve the test safeguards: `/kingdom-circuit-test/` base paths, `noindex,nofollow`, production analytics disabled, no `CNAME`, no operational/source-report files in the deployed artifact, and no workflow commits of generated output.
- Keep “Official details” links working while suppressing visible/internal source attribution from the public artifact.
- A deployment may proceed only after every verifier passes. If a check fails, fix the generator or overlay rather than weakening the check.
- The user has granted standing authorization to deploy verified changes to this test repository and its test website. Do not ask for repeated test-deployment approval; production deployment still requires separate explicit approval.
- Before handoff, verify representative desktop and mobile pages, the artists directory, an artist profile, an event page, the submit/correction flow, navigation keyboard behavior, local links, and responsive images.

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
