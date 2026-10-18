# CHH score service — test deployment

The game can run as a static test on GitHub Pages. A board shared between phones requires this service and persistent storage. It is prepared and locally testable; no public database has been connected.

Run from the repository root with Node 24 or later:

```sh
node game-backend/server.mjs
```

Open `http://127.0.0.1:4329/play/`. The server serves the game and its same-origin `/play-api` endpoints. The page receives the score-service configuration automatically. No password or player signup is required.

For an online TEST installation, run this server on a Node host with a persistent volume. Set `HOST=0.0.0.0`, the host's `PORT`, `PUBLIC_ORIGIN` to the exact HTTPS test origin, and `SCORE_DATA_DIR` to the persistent directory. Put HTTPS in front of the service. Back up the SQLite file. Never place database files inside the static game directory or GitHub Pages artifact. Production is not authorized.

The browser stores a random bearer token for its anonymous player. The server stores its hash, nickname, sessions, completed rounds and best-session components. Public results contain nicknames and scores, never tokens. A new session keeps the previous best. Names are display labels, not verified identities; clearing browser storage makes a new player. No email or signup is collected.

The server recomputes totals, rejects duplicate rounds, bounds every game at 1,000, enforces elapsed duration, validates session ownership and preserves complete best-session rows. It does not detect automated play or prove that submitted hits came from a human. Add rate limiting, nickname moderation and stronger input replay validation before using it for prizes or a public competition. Local/device scores are never silently imported into the shared board.

The static Pages version clearly labels its board as device-only while the shared service is unconfigured. Connecting the hosted service is the remaining setup step, not something a static file can provide by itself.

## All-player scoreboard

The board now includes each anonymous player’s best complete session, including players who have just started at zero. All four games, Journey and Total are retained from that same session. Scores are ranked by Total; ties use a stable player order. `/play-api/scores?offset=0&limit=50` returns `{rows, totalPlayers, nextOffset}`. Continue with `nextOffset` until it is null; there is no top-100 exclusion. Only display names and score data are public.

Different nicknames entered for new games on one phone receive separate anonymous profiles. A returning nickname on that browser reuses its profile. A nickname is not an account: two people with the same name on different phones remain separate, and clearing browser storage creates a new profile. The local fallback preserves best sessions for names seen in that browser and is explicitly labeled device-only. Previously uncollected scores on other phones cannot be reconstructed.

### Connect the GitHub Pages test to a hosted service

1. Host this Node service with a persistent `SCORE_DATA_DIR`, HTTPS and `PUBLIC_ORIGIN` set to the service origin. The service must stay running when the owner’s computer is off.
2. Set `ALLOWED_ORIGINS=https://84lorinw-a11y.github.io`. This enables only that browser origin for API requests and preflight. Keep database storage outside the deployed static files.
3. In the durable game `index.html`, add `<meta name="score-service" content="https://YOUR-SERVICE/play-api">` and add only that HTTPS origin to the existing CSP `connect-src` directive. Do not allow arbitrary origins or put a secret in the page.
4. Regenerate the pinned game manifest, pass the full test deployment checks and publish to the test repository. Verify two independent browsers register and see each other’s scores, then restart the service and verify persistence.

The frontend waits for pending score saves before loading the board. Saved visitors can restore their journey on the service; historical browser-only minigame points are never silently imported as verified scores. Online requests have bounded timeouts, a visible retry, and preserve local progress on failure.
