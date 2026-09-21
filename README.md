# Kingdom Circuit Test

This repository publishes an exact content and layout mirror of the latest
successful Kingdom Circuit production deployment at:

https://84lorinw-a11y.github.io/kingdom-circuit-test/

Only deployment safeguards differ: test-site URLs, no search indexing,
production analytics disabled, no production `CNAME`, and no internal build
reports. Generated pages are deployed as a Pages artifact and are never
committed back to this branch. Date-sensitive build steps are pinned to the
successful production release date so an older live deployment can be
recreated faithfully, including the final production image optimization,
public-data hardening, and mobile presentation stages. The mirror runs daily
and can also be started manually.
