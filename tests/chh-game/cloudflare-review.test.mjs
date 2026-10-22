import test from 'node:test';
import assert from 'node:assert/strict';
import worker from '../../game-backend/cloudflare-review/worker.mjs';

const ORIGIN = 'https://apollo-game-draft.pages.dev';
const PASSWORD = 'test-fixture-only-strong-password';
function fixture() {
  const counts = new Map();
  const assetCalls = [];
  return {
    APOLLO_REVIEW_PASSWORD: PASSWORD,
    counts, assetCalls,
    REVIEW_AUTH_DB: { prepare(sql) { return { bind(...args) { return {
      async first() {
        const attempts = (counts.get(args[0]) || 0) + 1;
        counts.set(args[0], attempts);
        return { attempts };
      },
      async run() { return { success: true }; },
    }; } }; } },
    ASSETS: { async fetch(request) {
      assetCalls.push(request);
      return new Response('protected fixture bytes', { status: request.headers.has('Range') ? 206 : 200,
        headers: { 'Content-Type': 'audio/mpeg', 'Cache-Control': 'public,max-age=31536000', 'Access-Control-Allow-Origin': '*' } });
    } },
  };
}
const req = (path, opts = {}) => new Request(ORIGIN + path, opts);
const login = (env, password = PASSWORD, extra = {}) => worker.fetch(req('/review/login', {
  method: 'POST', body: new URLSearchParams({ password }),
  headers: { Origin: ORIGIN, 'Content-Type': 'application/x-www-form-urlencoded', 'CF-Connecting-IP': '192.0.2.15', ...extra },
}), env);
const session = response => response.headers.get('Set-Cookie').split(';')[0];

test('every unauthenticated file path is blocked before the asset service', async () => {
  const env = fixture();
  for (const path of ['/', '/play/', '/play/game.mjs', '/play/assets/song.mp3', '/play/assets/video.mp4', '/_worker.js', '/404.html', '/anything?password=ignored']) {
    for (const method of ['GET', 'HEAD']) {
      const r = await worker.fetch(req(path, { method, headers: { Range: 'bytes=0-100', 'If-None-Match': 'known-tag' } }), env);
      assert.equal(r.status, 401, path);
      assert.match(r.headers.get('Cache-Control'), /no-store/);
      assert.doesNotMatch(await r.text(), /protected fixture/);
    }
  }
  assert.equal(env.assetCalls.length, 0);
});

test('browser navigation redirects to an accessible password page', async () => {
  const env = fixture();
  const redirect = await worker.fetch(req('/play/', { headers: { Accept: 'text/html' } }), env);
  assert.equal(redirect.status, 303);
  assert.equal(redirect.headers.get('Location'), '/review/login');
  const r = await worker.fetch(req('/review/login'), env);
  assert.equal(r.status, 200);
  const html = await r.text();
  assert.match(html, /type="password"/);
  assert.match(html, /label for="password"/);
  assert.doesNotMatch(html, new RegExp(PASSWORD));
  assert.equal(env.assetCalls.length, 0);
});

test('missing secrets, short secrets, missing limiter or missing assets fail closed', async () => {
  for (const change of [{ APOLLO_REVIEW_PASSWORD: '' }, { APOLLO_REVIEW_PASSWORD: 'short' }, { REVIEW_AUTH_DB: undefined }, { ASSETS: undefined }]) {
    const env = { ...fixture(), ...change };
    const r = await worker.fetch(req('/play/assets/song.mp3'), env);
    assert.equal(r.status, 503);
    assert.doesNotMatch(await r.text(), /<form/);
    assert.equal(env.assetCalls.length, 0);
  }
});

test('correct password issues secure host-only expiring cookie and preserves range playback', async () => {
  const env = fixture();
  const r = await login(env);
  assert.equal(r.status, 303);
  assert.equal(r.headers.get('Location'), '/play/');
  assert.match(r.headers.get('Set-Cookie'), /^__Host-apollo_review=.+; Path=\/; Secure; HttpOnly; SameSite=Strict; Max-Age=28800$/);
  const asset = await worker.fetch(req('/play/assets/song.mp3', { headers: { Cookie: session(r), Range: 'bytes=0-99' } }), env);
  assert.equal(asset.status, 206);
  assert.equal(await asset.text(), 'protected fixture bytes');
  assert.match(asset.headers.get('Cache-Control'), /private, no-store/);
  assert.equal(asset.headers.get('Access-Control-Allow-Origin'), null);
  assert.equal(env.assetCalls[0].headers.get('Range'), 'bytes=0-99');
});

test('wrong passwords are refused and never echoed or stored', async () => {
  const env = fixture();
  const wrong = '<script>bad-password</script>';
  const r = await login(env, wrong);
  assert.equal(r.status, 401);
  assert.doesNotMatch(await r.text(), /bad-password/);
  assert.match(r.headers.get('Set-Cookie'), /Max-Age=0/);
  assert.equal(env.assetCalls.length, 0);
  for (const key of env.counts.keys()) assert.match(key, /^[A-Za-z0-9_-]{43}$/);
});

test('11th attempt is throttled and a new minute recovers without a permanent lockout', async t => {
  const env = fixture();
  const timestamp = 1792600020000;
  t.mock.method(Date, 'now', () => timestamp);
  for (let i = 0; i < 10; i++) assert.equal((await login(env, 'incorrect')).status, 401);
  const blocked = await login(env);
  assert.equal(blocked.status, 429);
  assert.ok(Number(blocked.headers.get('Retry-After')) <= 60);
  t.mock.method(Date, 'now', () => timestamp + 60000);
  assert.equal((await login(env)).status, 303);
});

test('one IP cooldown does not lock out another IP', async () => {
  const env = fixture();
  for (let i = 0; i < 11; i++) await login(env, 'incorrect');
  assert.equal((await login(env, PASSWORD, { 'CF-Connecting-IP': '192.0.2.16' })).status, 303);
});

test('unavailable limiter and absent trusted IP deny login', async () => {
  const env = fixture();
  env.REVIEW_AUTH_DB.prepare = () => { throw new Error('offline'); };
  assert.equal((await login(env)).status, 503);
  assert.equal((await login(fixture(), PASSWORD, { 'CF-Connecting-IP': '' })).status, 503);
});

test('forged, duplicate, malformed and altered cookies cannot bypass authentication', async () => {
  const env = fixture();
  const good = session(await login(env));
  const forged = good.slice(0, -4) + 'AAAA';
  for (const value of [forged, good + '; ' + good, '__Host-apollo_review=admin', good.replace('v1.', 'v2.')]) {
    assert.equal((await worker.fetch(req('/play/', { headers: { Cookie: value } }), env)).status, 401);
  }
  assert.equal(env.assetCalls.length, 0);
});

test('expired sessions and password changes require a new sign-in', async t => {
  const env = fixture();
  const start = Date.now();
  const good = session(await login(env));
  env.APOLLO_REVIEW_PASSWORD = 'replacement-test-password';
  assert.equal((await worker.fetch(req('/play/', { headers: { Cookie: good } }), env)).status, 401);
  env.APOLLO_REVIEW_PASSWORD = PASSWORD;
  t.mock.method(Date, 'now', () => start + 9 * 3600000);
  assert.equal((await worker.fetch(req('/play/', { headers: { Cookie: good } }), env)).status, 401);
});

test('a session cannot be replayed on a different deployment hostname', async () => {
  const env = fixture();
  const good = session(await login(env));
  assert.equal((await worker.fetch(new Request('https://another.example/play/', { headers: { Cookie: good } }), env)).status, 403);
  assert.equal((await worker.fetch(new Request('https://old.apollo-game-draft.pages.dev/play/'), env)).status, 403);
});

test('cross-origin, oversized, unsupported and duplicate-field login forms fail', async () => {
  const env = fixture();
  assert.equal((await login(env, PASSWORD, { Origin: 'https://other.example' })).status, 403);
  assert.equal((await login(env, PASSWORD, { Origin: '' })).status, 403);
  assert.equal((await login(env, PASSWORD, { 'Content-Type': 'application/json' })).status, 415);
  assert.equal((await login(env, 'x'.repeat(2048))).status, 413);
  const duplicate = req('/review/login', { method: 'POST', body: `password=${PASSWORD}&password=${PASSWORD}`, headers: { Origin: ORIGIN, 'CF-Connecting-IP': '192.0.2.15', 'Content-Type': 'application/x-www-form-urlencoded' } });
  assert.equal((await worker.fetch(duplicate, env)).status, 401);
});

test('logout expires the browser cookie and cannot be triggered by a cross-origin form', async () => {
  const env = fixture();
  const good = session(await login(env));
  const r = await worker.fetch(req('/review/logout', { method: 'POST', headers: { Origin: ORIGIN, Cookie: good } }), env);
  assert.equal(r.status, 303);
  assert.match(r.headers.get('Set-Cookie'), /Max-Age=0/);
  const bad = await worker.fetch(req('/review/logout', { method: 'POST', headers: { Origin: 'https://other.example', Cookie: good } }), env);
  assert.equal(bad.status, 403);
});

test('HTTP, unexpected methods and asset backend failures do not expose files', async () => {
  const env = fixture();
  assert.equal((await worker.fetch(new Request('http://preview.example/play/'), env)).status, 400);
  assert.equal((await worker.fetch(req('/play/', { method: 'POST' }), env)).status, 405);
  const good = session(await login(env));
  env.ASSETS.fetch = () => { throw new Error('offline'); };
  assert.equal((await worker.fetch(req('/play/', { headers: { Cookie: good } }), env)).status, 503);
});
