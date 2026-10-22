// Cloudflare-only authentication. Never included in the GitHub Pages game.
// The password is a Cloudflare secret, never a source-code/build variable.
const COOKIE = '__Host-apollo_review';
const SESSION_SECONDS = 8 * 60 * 60;
const MAX_BODY_BYTES = 1024;
const encoder = new TextEncoder();
const LOGIN = '/review/login';
const REVIEW_HOST = 'apollo-game-draft.pages.dev';

const encode = bytes => btoa(String.fromCharCode(...new Uint8Array(bytes))).replaceAll('+', '-').replaceAll('/', '_').replace(/=+$/, '');
function decode(text) {
  if (!/^[A-Za-z0-9_-]{43}$/.test(text)) throw new Error('Invalid signature');
  return Uint8Array.from(atob(text.replaceAll('-', '+').replaceAll('_', '/') + '='), c => c.charCodeAt(0));
}
const keyFor = password => crypto.subtle.importKey('raw', encoder.encode(password), { name: 'HMAC', hash: 'SHA-256' }, false, ['sign', 'verify']);
const sign = (key, text) => crypto.subtle.sign('HMAC', key, encoder.encode(text));
const cookie = (token, age = SESSION_SECONDS) => `${COOKIE}=${token}; Path=/; Secure; HttpOnly; SameSite=Strict; Max-Age=${age}`;

function headers(extra = {}) {
  return {
    'Cache-Control': 'private, no-store, max-age=0',
    'CDN-Cache-Control': 'no-store',
    'Cloudflare-CDN-Cache-Control': 'no-store',
    'X-Robots-Tag': 'noindex, nofollow, noarchive',
    'X-Content-Type-Options': 'nosniff',
    'X-Frame-Options': 'DENY',
    'Referrer-Policy': 'no-referrer',
    'Permissions-Policy': 'camera=(), microphone=(), geolocation=()',
    ...extra,
  };
}

function page(message = '', status = 200, extra = {}, signedIn = false) {
  const form = signedIn
    ? '<a class="button" href="/play/">Open the game</a><form method="post" action="/review/logout"><button class="secondary">Sign out</button></form>'
    : '<form method="post" action="/review/login"><label for="password">Review password</label><input id="password" name="password" type="password" required maxlength="128" autocomplete="current-password" autofocus><button>Enter preview</button></form>';
  const html = `<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex,nofollow"><title>Apollo · Private preview</title><style>
    *{box-sizing:border-box}body{margin:0;min-height:100svh;background:#09121b;color:#f3ead9;font:17px/1.55 system-ui,sans-serif;display:grid;place-items:center;padding:24px}main{width:100%;max-width:420px;padding:32px 26px;border:1px solid #354453;border-radius:20px;background:#101e2b}small{color:#91b6c9;letter-spacing:.18em;font-size:11px;font-weight:700}h1{font-size:30px;line-height:1.15;margin:14px 0}p{color:#c4cdd5}label{display:block;margin-bottom:8px;font-size:15px}input{width:100%;min-height:50px;border:1px solid #627488;border-radius:8px;background:#08121c;color:#fff;font:inherit;padding:10px 12px}input:focus{outline:3px solid #ffce6c;outline-offset:2px}button,.button{display:block;width:100%;min-height:50px;text-align:center;margin-top:16px;padding:12px;border:0;border-radius:8px;background:#ffce6c;color:#13202b;font:700 16px system-ui;cursor:pointer;text-decoration:none}.secondary{background:transparent;color:#e5edf3;border:1px solid #627488}.note{font-size:13px;margin-bottom:0}.message{border-left:3px solid #ffce6c;padding-left:12px;color:#ffe1a5}
    </style></head><body><main><small>APOLLO RECORDS</small><h1>Private preview</h1><p>A first look for the review crew.</p>${message ? `<p class="message" role="status">${message}</p>` : ''}${status === 503 ? '' : form}<p class="note">${signedIn ? 'Access lasts up to 8 hours. Signing out keeps your game progress on this device.' : 'Need access or forgot the password? Contact the person who shared this preview.'}</p></main></body></html>`;
  return new Response(html, { status, headers: headers({
    'Content-Type': 'text/html; charset=utf-8',
    'Content-Security-Policy': "default-src 'none'; style-src 'unsafe-inline'; form-action 'self'; base-uri 'none'; frame-ancestors 'none'",
    ...extra,
  }) });
}

async function authenticated(request, key, origin) {
  const matches = (request.headers.get('Cookie') || '').split(';').map(x => x.trim()).filter(x => x.startsWith(COOKIE + '='));
  if (matches.length !== 1) return false;
  const token = matches[0].slice(COOKIE.length + 1);
  const parts = token.split('.');
  if (parts.length !== 4 || parts[0] !== 'v1' || !/^\d{10}$/.test(parts[1]) || !/^[A-Za-z0-9_-]{22}$/.test(parts[2])) return false;
  const now = Math.floor(Date.now() / 1000), expires = Number(parts[1]);
  if (expires <= now || expires > now + SESSION_SECONDS + 60) return false;
  try {
    return await crypto.subtle.verify('HMAC', key, decode(parts[3]), encoder.encode(`${origin}:${parts.slice(0, 3).join('.')}`));
  } catch { return false; }
}

async function boundedBody(request) {
  if (Number(request.headers.get('Content-Length')) > MAX_BODY_BYTES) return null;
  const reader = request.body?.getReader();
  if (!reader) return '';
  let length = 0, chunks = [];
  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    length += value.length;
    if (length > MAX_BODY_BYTES) { await reader.cancel(); return null; }
    chunks.push(value);
  }
  const result = new Uint8Array(length);
  let offset = 0;
  for (const chunk of chunks) { result.set(chunk, offset); offset += chunk.length; }
  return new TextDecoder().decode(result);
}

async function allowAttempt(request, env, key) {
  // CF-Connecting-IP is supplied by Cloudflare. Do not trust forwarded IPs.
  const ip = request.headers.get('CF-Connecting-IP');
  if (!ip) throw new Error('Missing edge identity');
  const now = Math.floor(Date.now() / 1000), minute = Math.floor(now / 60);
  const bucket = encode(await sign(key, `login-limit:${ip}:${minute}`));
  const result = await env.REVIEW_AUTH_DB.prepare('INSERT INTO review_login_attempts (bucket, attempts, expires_at) VALUES (?, 1, ?) ON CONFLICT(bucket) DO UPDATE SET attempts = attempts + 1 RETURNING attempts').bind(bucket, (minute + 2) * 60).first();
  if (!Number.isSafeInteger(result?.attempts) || result.attempts < 1) throw new Error('Invalid limiter response');
  // Bounded retention: store only HMAC identifiers; never passwords or raw IPs.
  if (result.attempts === 1) await env.REVIEW_AUTH_DB.prepare('DELETE FROM review_login_attempts WHERE expires_at < ?').bind(now).run();
  return { allowed: result.attempts <= 10, retry: 60 - now % 60 };
}

async function handle(request, env) {
  const url = new URL(request.url);
  if (url.protocol !== 'https:') return new Response('HTTPS is required.', { status: 400, headers: headers() });
  // Immutable deployment aliases must never retain access with an old password
  // after the owner resets the active deployment's secret.
  if (url.hostname !== REVIEW_HOST) return new Response('Use the current private-review link.', { status: 403, headers: headers() });
  if (typeof env.APOLLO_REVIEW_PASSWORD !== 'string' || env.APOLLO_REVIEW_PASSWORD.length < 12 || !env.REVIEW_AUTH_DB?.prepare || !env.ASSETS?.fetch) {
    return page('The private preview is being prepared. Please check back with the owner.', 503);
  }
  const key = await keyFor(env.APOLLO_REVIEW_PASSWORD);
  if (request.method === 'POST' && (url.pathname === LOGIN || url.pathname === '/review/logout')) {
    if (request.headers.get('Origin') !== url.origin) return new Response('Request not allowed.', { status: 403, headers: headers() });
    if (url.pathname === '/review/logout') return new Response(null, { status: 303, headers: headers({ Location: LOGIN, 'Set-Cookie': cookie('', 0) }) });
    if (request.headers.get('Content-Type')?.split(';')[0] !== 'application/x-www-form-urlencoded') return new Response('Unsupported form.', { status: 415, headers: headers() });
    const body = await boundedBody(request);
    if (body === null) return new Response('Form too large.', { status: 413, headers: headers() });
    const limit = await allowAttempt(request, env, key);
    if (!limit.allowed) return page('Too many attempts. Wait one minute, then try again.', 429, { 'Retry-After': String(limit.retry) });
    const values = new URLSearchParams(body).getAll('password');
    const supplied = values.length === 1 ? values[0] : '';
    // Use Web Crypto's verification operation rather than a string comparison.
    const expected = await sign(key, `password-check:${env.APOLLO_REVIEW_PASSWORD}`);
    const valid = supplied.length <= 128 && await crypto.subtle.verify('HMAC', key, expected, encoder.encode(`password-check:${supplied}`));
    if (!valid) return page('That password did not match. Please try again.', 401, { 'Set-Cookie': cookie('', 0) });
    const expires = Math.floor(Date.now() / 1000) + SESSION_SECONDS;
    const payload = `v1.${expires}.${encode(crypto.getRandomValues(new Uint8Array(16)))}`;
    const token = `${payload}.${encode(await sign(key, `${url.origin}:${payload}`))}`;
    return new Response(null, { status: 303, headers: headers({ Location: '/play/', 'Set-Cookie': cookie(token) }) });
  }
  if (request.method !== 'GET' && request.method !== 'HEAD') return new Response('Method not allowed.', { status: 405, headers: headers({ Allow: 'GET, HEAD' }) });
  const valid = await authenticated(request, key, url.origin);
  if (url.pathname === LOGIN || url.pathname === '/review' || url.pathname === '/review/') return page('', 200, {}, valid);
  if (!valid) {
    // Do not return media, range bodies, redirects or cache validators to guests.
    if (request.method === 'HEAD') return new Response(null, { status: 401, headers: headers() });
    if (request.headers.get('Sec-Fetch-Dest') === 'document' || request.headers.get('Accept')?.includes('text/html')) return new Response(null, { status: 303, headers: headers({ Location: LOGIN }) });
    return new Response('Private preview. Sign in at /review/login.', { status: 401, headers: headers({ 'Content-Type': 'text/plain; charset=utf-8' }) });
  }
  if (url.pathname.startsWith('/review/')) return new Response('Not found.', { status: 404, headers: headers() });
  const asset = await env.ASSETS.fetch(request);
  const response = new Response(asset.body, asset);
  for (const [name, value] of Object.entries(headers())) response.headers.set(name, value);
  response.headers.delete('Access-Control-Allow-Origin');
  response.headers.delete('Access-Control-Allow-Credentials');
  response.headers.delete('Set-Cookie');
  return response;
}

export default {
  async fetch(request, env) {
    try { return await handle(request, env); }
    catch { return page('The private preview is temporarily unavailable. Please try again shortly.', 503); }
  },
};
