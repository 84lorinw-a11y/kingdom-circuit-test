# Google Sheets shared scores — TEST

Owner-supplied workbook: https://docs.google.com/spreadsheets/d/1YhSyRhnLUFliM8x-ngY1WH8OCvIfxJBGZmt701mWLb4/edit#gid=72099769

Use its dedicated **CHH Show Up** tab for the visible best-session board. Do not modify the Artist Source Registry, Cost, Artist Database, Instagram Focus or Artist Feedback on Site tabs. A dedicated `_CHH Score Data` helper tab holds anonymous player identifiers, session totals and round receipts. It is hidden for readability, not as a security boundary. The workbook's existing sharing permissions remain unchanged. No email addresses or raw bearer tokens are stored in it.

## Setup

1. The bound Apps Script project is **Kingdom Circuit CHH Test Scores**:
   https://script.google.com/home/projects/1c3g7K0pXa02zWQvgk-SsnPGu034IeAUIfjZQnZIJdN0INTtAzVVsa-Iu/edit
2. `Code.gs` is the reviewed source. Run `setupCHHScores` once. Google account authorization must be completed by the owner when Google presents its unverified-app/security screen. Setup preserves nonmatching existing content and does not modify unrelated tabs.
3. Deploy a Web app, executing as the owner, accessible to Anyone. The score endpoint intentionally exposes only nicknames and score components; players need no Google account. The workbook itself does not need to be made public.
4. Copy the resulting HTTPS `/macros/s/.../exec` URL into the test game's `score-service` meta tag. Permit `https://script.google.com` and `https://script.googleusercontent.com` in its CSP `connect-src`. No secret belongs in the page.
5. Verify real anonymous cross-origin requests from the test site. The text/plain POST transport avoids preflight and follows Google's JSON response redirect. A successful editor run alone is not proof that browser CORS, anonymous access or mobile saving works.
6. Verify two independent browser identities, every game, reload persistence, duplicate-response retries, pagination and a fresh session before enabling the shared board on TEST. Keep production unchanged until separately authorized.

## Behavior

- Each of the four games has twenty opportunities and the same 40-point hit plus 10-point clean bonus. Round points are calculated by the service. Session totals continue across replays.
- One board entry per anonymous player contains their best whole session, including zero-point entrants. The Total is the last visible score column. Ranking in the game is descending total with stable ties; every player is available through pagination.
- The browser creates and persists its random token before registering. The service uses its SHA-256 digest as the identifier. Names on different devices are not verified identities.
- Completed, registered rounds are saved in a persistent client outbox before transmission. Temporary failures retry after thirty seconds, on another round, when opening the board or after reloading. Definitively rejected rounds remain on the device with an explicit notice and do not block later games.
- A global script lock plus a small write-ahead journal makes multi-row updates recoverable. Replaying a committed request returns its receipt instead of adding points twice. The journal contains only score records, never raw tokens.
- Offline rounds that never obtained a server start ticket stay device-only. Historical local scores are not silently promoted to verified online scores.
- This is basic score validation, not proof of human play. Anonymous endpoints can still receive automated submissions. It is appropriate for the planned small test; it is not a prize-grade anti-cheat service.
- The 1,009-player automated test verifies ranking and pagination in memory. It is not a Google Sheets concurrency or throughput benchmark.

## Current setup status

Owner authorization and setup completed October 18, 2026. Web app version 1 executes as the owner with anonymous access. The TEST frontend uses:

`https://script.google.com/macros/s/AKfycbwgxvoMy9yCn15p78RPYR2D731bZSstzty33K2Bp4eV-nLSQhpw6DlYLtHucMdUV0-s/exec`

Real browser checks saved all four games for two independent identities (4,080 and 3,280 including journey points), verified duplicate-save handling and displayed both on a third browser's mobile-size game board. A real game round also displayed its successful shared-save confirmation. Short Google 429/503 responses retry automatically up to twice; prolonged failures retain completed registered rounds for later retry. QA players are removed after verification.

The public test entry is `/kingdom-circuit-test/play/?v=save-28`. Production has not been changed. A later Apps Script source change requires **Deploy → Manage deployments → Edit → New version**; keep the existing deployment URL so anonymous player identities remain associated with this service. Ordinary game-only updates do not require redeploying the script.

Scores saved only on devices before this connection are not backfilled. Nicknames are unverified; the same name on another phone is a separate anonymous player. A reset/new game preserves that device's best whole session. No signup or Google sign-in is required for players.

The game menu includes **Save & Exit**. It flushes pending registered rounds, syncs journey progress and compares the server-confirmed current session total with the local total before confirming. New Game offers the same save check before resetting. A refresh may continue the same saved night; starting a new night creates a separate session. Closing a mobile browser is not a reliable opportunity to run a final network request, so completed rounds also save immediately.
