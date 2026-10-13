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
