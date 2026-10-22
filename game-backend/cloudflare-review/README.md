# Apollo private review

Cloudflare-only shared-password gate, requested October 21, 2026. The owner
provided the password in chat; it must never be copied into this repository,
build artifacts, reports, screenshots, logs, URLs, or public GitHub secrets files.
GitHub TEST continues to contain released previews only. This gate does not
make public GitHub files private and does not prevent authorized recording.

## Deployment contract

- Project: `apollo-game-draft`, canonical host `apollo-game-draft.pages.dev`.
- Automatic production and preview deployments remain disabled.
- Build command: `python3 game-backend/cloudflare-review/build_review.py .cloudflare-dist --game-revision 807d91edb73b5525c37dfa4907955b5ae1ddc0e5`.
- Output: `.cloudflare-dist`. The owner approved publishing this GitHub TEST
  game batch (runtime `apollo-25`) to protected Cloudflare on October 21. This
  replaces the initial security-only pin at `2bb401c`. Change the pin only when
  a newer Cloudflare game batch is explicitly approved.
- Production secret: `APOLLO_REVIEW_PASSWORD`, entered by the owner as **Secret**
  in Settings > Variables and secrets. Never use a public client/build constant.
- Production D1 binding: `REVIEW_AUTH_DB` -> `apollo-review-login`, database
  `b3e45f44-7efc-48ac-9a51-4a07620d346b`; schema is in `schema.sql`.
- Set Pages **Fail open/closed** to **Fail closed** for production and previews.
- `_routes.json` sends every path to the Worker with no static exclusions.
- All new deployment aliases are rejected; use the canonical review hostname.
  This prevents an old protected deployment alias from accepting an old password
  after a reset. Existing pre-gate deployments contain released/public files;
  their historical aliases are not retroactively protected by this Worker.
- Do not roll back to an unprotected static deployment once private files exist.

No secrets or music are stored in D1. It records only opaque HMAC identifiers,
attempt counts, and expiry times. Expired counters are removed on later logins.
Ten attempts per IP per fixed minute are allowed; the next minute recovers.
Missing secrets/bindings, limiter failures and handler errors deny access.
An authorized session uses an 8-hour, host-only Secure/HttpOnly/SameSite cookie.
Protected responses use private/no-store cache headers, including media ranges.
The same-origin referrer policy preserves the Origin on native login/logout
forms while suppressing referrers to external sites. Null, missing and foreign
Origins remain rejected; do not loosen this check to compensate for a header.

## Owner recovery

The game password is separate from the Cloudflare account login.

1. For a wrong-password cooldown, wait one minute and try again. This does not
   lock the Cloudflare account or erase game progress.
2. For a forgotten/shared password, sign into the normal Cloudflare dashboard.
   Open Workers & Pages > apollo-game-draft > Settings > Production >
   Variables and secrets. Replace `APOLLO_REVIEW_PASSWORD` with a new Secret.
3. Make a deliberate deployment using the protected build, keeping automatic
   publishing disabled. Environment changes take effect on the next deployment.
   Existing sessions on the active hostname become invalid after this change.
4. Test the new password and confirm the old password, old cookie, anonymous
   audio URL, and deployment aliases cannot access protected content.

Never remove the gate or set Fail open as a recovery shortcut. Loss of the
Cloudflare account itself requires Cloudflare's account-recovery process.

## Verification and private-file boundary

`node --test tests/chh-game/cloudflare-review.test.mjs` exercises correct/wrong
passwords, cooldown/recovery, cookie forgery/expiry/rotation, host aliases, CSRF,
oversized forms, direct assets/ranges/HEAD, missing settings and backend failure.
`python3 -m unittest discover -s tests -p 'test_cloudflare_game.py'` verifies
both packages, media identity, exact inventories and the SQL counter schema.

Cloudflare Functions and D1 have request quotas. This setup is for the small
review group, not an approved 100,000-person password-gated launch. No paid plan
was enabled. At quota exhaustion it must deny service, never expose the files.

Before adding unreleased music, establish a separate private-file input/storage
path and verify the live gate. The public repository must continue to contain
only approved released media. The current packager has no private-music input.
