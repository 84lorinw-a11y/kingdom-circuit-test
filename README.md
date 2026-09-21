# Kingdom Circuit Test

This repository publishes an exact content and layout mirror of the latest
successful Kingdom Circuit production deployment at:

https://84lorinw-a11y.github.io/kingdom-circuit-test/

Only deployment safeguards differ: test-site URLs, no search indexing,
production analytics disabled, no production `CNAME`, and no internal build
reports. Generated pages are deployed as a Pages artifact and are never
committed back to this branch. The workflow captures the actual deployed live
site, follows its sitemap and local assets to completion, and verifies that the
homepage, sitemap, and event catalog did not change during capture. This keeps
the test environment aligned with the exact optimized images, generated pages,
and mobile presentation that visitors see in production. The mirror runs daily
and can also be started manually.
