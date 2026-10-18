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
