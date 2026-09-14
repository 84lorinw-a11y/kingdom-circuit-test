# Kingdom Circuit test site

This repository is the safe proving ground for improvements to Kingdom Circuit. It builds a fresh snapshot from the current production source, adds test-only repairs, validates the complete result, and deploys only to:

<https://84lorinw-a11y.github.io/kingdom-circuit-test/>

The production repository and <https://kingdomcircuit.com/> are not changed by this workflow.

## Test-release safeguards

- The deployed test site is always `noindex,nofollow`, has no custom-domain file, and does not send production analytics.
- The build is uploaded directly as one GitHub Pages artifact. It does not write generated pages back into this branch.
- Visible source labels and internal collection/audit files are removed from the public test artifact. “Official details” links remain so visitors can confirm a listing.
- Sitemap, links, counts, duplicated listings, page metadata, accessibility, forms, and image delivery are checked before deployment.
- Any failed verification stops deployment and leaves the currently published test site in place.

## Editing rule

Make durable test improvements in `scripts/apply_test_audit_repairs.py`, `scripts/apply_test_ux_repairs.py`, and `scripts/optimize_test_images.py`. Keep their matching verifier scripts passing. Do not hand-edit generated pages because the next mirror will replace them.

See [TEST-IMPROVEMENTS.md](TEST-IMPROVEMENTS.md) for the build order and promotion checklist.
