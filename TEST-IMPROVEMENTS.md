# Test improvement and promotion guide

## Purpose

The test site is deliberately isolated from production. Every deployment begins with the current `kingdom-circuit@main` site, applies the approved production SEO layer, converts all routes to the test subpath, and then applies the test-only improvement overlays.

## Build order

1. Check out the test harness, production source, and pinned approved SEO source.
2. Run production unit tests and build the current production artifact without collecting or writing new event data.
3. Convert the artifact for `/kingdom-circuit-test/`, disable indexing and production analytics, and remove the production custom domain.
4. Apply content/SEO/privacy repairs, optimize the sanitized image set, and then apply accessibility/usability repairs.
5. Run all structural, privacy, usability, performance, JavaScript, and local-link checks.
6. Upload and deploy one immutable GitHub Pages artifact.

## Privacy boundary

The public artifact does not publish collector status files, audit reports, source labels, or internal source metadata. Public event facts and the destination of an “Official details” link can still be observed by any visitor; a static public website cannot make those items secret. Stronger source confidentiality would require moving collection data to a private repository or backend before production promotion.

## Promoting later

Do not copy the generated `_site` directory into production. Review each test overlay, move the approved behavior into the appropriate production generator or source file, run the production test suite plus these regression checks, deploy once, and verify the public site. This keeps improvements durable through future automated refreshes.
