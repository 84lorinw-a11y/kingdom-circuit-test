import fs from 'node:fs/promises';

const APP_ID = 'js_kingdomcircuit.com';
const BASE = 'https://rest.bandsintown.com';
const PROD_BASE = 'https://raw.githubusercontent.com/84lorinw-a11y/kingdom-circuit/main';
const OUTPUT_PATH = 'bandsintown-browser-test-results.json';
const TODAY = new Date().toISOString().slice(0, 10);

const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));

function normalize(value = '') {
  return String(value)
    .normalize('NFKD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase()
    .replace(/&/g, ' and ')
    .replace(/[^a-z0-9]+/g, ' ')
    .trim()
    .replace(/\s+/g, ' ');
}

function dateOnly(value = '') {
  return String(value).slice(0, 10);
}

function isUS(country = '') {
  const value = normalize(country);
  return value === 'united states' || value === 'us' || value === 'usa';
}

function isFestivalLike(event) {
  const text = normalize(`${event.title || ''} ${event.venue || ''}`);
  return /\b(festival|fest|festivale|fastivalle|uprise|holy smoke|onefest|off the charts|immersion music and arts)\b/.test(text);
}

function isIdentityRisk(name = '') {
  const n = normalize(name);
  const compact = n.replace(/\s/g, '');
  const generic = new Set([
    'kb','nf','so','jr','116','350','egr','json','spec','cass','deon','coop','mica','foure','funky','fedel','mission','pishko','brenno','hollyn','reblah','viktory','sevin','canon','propaganda','evangel','brinson','swaizy','deraj'
  ]);
  return generic.has(compact) || (!n.includes(' ') && compact.length <= 7);
}

async function getJson(url, attempts = 3) {
  let last = null;
  for (let attempt = 1; attempt <= attempts; attempt++) {
    try {
      const response = await fetch(url, {
        headers: {
          Accept: 'application/json,text/plain,*/*',
          'User-Agent': 'KingdomCircuitEventDiscovery/1.0 (+https://kingdomcircuit.com)',
          Referer: 'https://kingdomcircuit.com/',
        },
      });
      const text = await response.text();
      if (response.ok) {
        return { ok: true, status: response.status, json: JSON.parse(text) };
      }
      last = { ok: false, status: response.status, body: text.slice(0, 300) };
      if (![429, 500, 502, 503, 504].includes(response.status)) return last;
    } catch (error) {
      last = { ok: false, status: null, body: String(error).slice(0, 300) };
    }
    await sleep(350 * attempt);
  }
  return last || { ok: false, status: null, body: 'unknown error' };
}

async function getProdJson(path) {
  const result = await getJson(`${PROD_BASE}/${path}`, 3);
  if (!result.ok) throw new Error(`Failed production ${path}: ${result.status}`);
  return result.json;
}

function collectUrls(value, out = []) {
  if (typeof value === 'string') {
    if (/^https?:\/\//i.test(value)) out.push(value);
    return out;
  }
  if (Array.isArray(value)) {
    for (const item of value) collectUrls(item, out);
    return out;
  }
  if (value && typeof value === 'object') {
    for (const item of Object.values(value)) collectUrls(item, out);
  }
  return out;
}

function profileToken(url) {
  try {
    const parsed = new URL(url);
    const host = parsed.hostname.toLowerCase().replace(/^www\./, '');
    const parts = parsed.pathname.split('/').filter(Boolean);
    if (host === 'open.spotify.com' && parts[0] === 'artist' && parts[1]) return `spotify:${parts[1].toLowerCase()}`;
    if (host === 'instagram.com' && parts[0]) return `instagram:${parts[0].toLowerCase()}`;
    if ((host === 'x.com' || host === 'twitter.com') && parts[0]) return `twitter:${parts[0].toLowerCase()}`;
    if (host === 'facebook.com' && parts[0]) return `facebook:${parts[0].toLowerCase()}`;
    if (host === 'youtube.com' && parts[0]) return `youtube:${parts.slice(0,2).join('/').toLowerCase()}`;
    if (host && parts.length) return `web:${host}/${parts.slice(0,2).join('/').toLowerCase()}`;
    if (host) return `web:${host}`;
  } catch {}
  return '';
}

function configuredProfileTokens(artist) {
  return new Set(collectUrls(artist).map(profileToken).filter(Boolean));
}

function bandsintownProfileTokens(resolvedArtist) {
  const links = Array.isArray(resolvedArtist?.links) ? resolvedArtist.links : [];
  const urls = links.map(link => String(link?.url || '')).filter(Boolean);
  if (resolvedArtist?.facebook_page_url) urls.push(String(resolvedArtist.facebook_page_url));
  return new Set(urls.map(profileToken).filter(Boolean));
}

function hasProfileMatch(configured, resolvedArtist) {
  const expected = configuredProfileTokens(configured);
  const actual = bandsintownProfileTokens(resolvedArtist);
  for (const token of actual) if (expected.has(token)) return true;
  return false;
}

function mapKnownBandsintownIds(sources) {
  const map = new Map();
  const walk = value => {
    if (Array.isArray(value)) {
      for (const item of value) walk(item);
      return;
    }
    if (!value || typeof value !== 'object') return;
    const url = String(value.url || '');
    const match = url.match(/bandsintown\.com\/a\/(\d+)/i);
    const artist = String(value.artist || value.artistName || '').trim();
    if (match && artist) map.set(normalize(artist), match[1]);
    for (const item of Object.values(value)) if (item && typeof item === 'object') walk(item);
  };
  walk(sources);
  return map;
}

async function resolveArtist(configured) {
  const canonical = String(configured.name || '').trim();
  const aliases = [canonical, ...(Array.isArray(configured.aliases) ? configured.aliases : [])]
    .map(v => String(v || '').trim()).filter(Boolean);
  const accepted = new Set(aliases.map(normalize));
  const tried = [];

  for (const candidate of [...new Set(aliases)].slice(0, 4)) {
    const url = `${BASE}/artists/${encodeURIComponent(candidate)}?app_id=${encodeURIComponent(APP_ID)}`;
    const response = await getJson(url);
    tried.push({ candidate, status: response.status });
    if (!response.ok || !response.json || Array.isArray(response.json)) continue;
    const resolvedName = String(response.json.name || '').trim();
    if (!accepted.has(normalize(resolvedName))) continue;
    return { ok: true, artist: response.json, matchedBy: candidate, tried };
  }
  return { ok: false, tried };
}

function compactEvent(event, trackedArtist, identityConfidence) {
  const venue = event?.venue || {};
  const offers = Array.isArray(event?.offers) ? event.offers : [];
  return {
    id: String(event?.id || ''),
    trackedArtist,
    identityConfidence,
    artistId: String(event?.artist_id || event?.artist?.id || ''),
    datetime: String(event?.datetime || event?.starts_at || ''),
    date: dateOnly(event?.datetime || event?.starts_at || ''),
    title: String(event?.title || ''),
    venue: String(venue.name || ''),
    city: String(venue.city || ''),
    state: String(venue.region || ''),
    country: String(venue.country || ''),
    lineup: Array.isArray(event?.lineup) ? event.lineup.map(String) : [],
    ticketUrl: String(offers.find(o => o?.url)?.url || ''),
    eventUrl: String(event?.url || ''),
  };
}

function eventClusterKey(event) {
  const date = event.date;
  const city = normalize(event.city);
  const state = normalize(event.state);
  const venue = normalize(event.venue);
  const title = normalize(event.title);
  if (venue) return `${date}|${city}|${state}|${venue}`;
  return `${date}|${city}|${state}|${title}`;
}

function eventArtists(event) {
  const values = [];
  if (Array.isArray(event.artists)) values.push(...event.artists);
  if (event.headliner) values.push(event.headliner);
  if (Array.isArray(event.lineup)) values.push(...event.lineup);
  if (Array.isArray(event.trackedArtists)) values.push(...event.trackedArtists);
  if (event.trackedArtist) values.push(event.trackedArtist);
  return new Set(values.map(normalize).filter(Boolean));
}

function overlap(a, b) {
  const aa = eventArtists(a);
  const bb = eventArtists(b);
  for (const value of aa) if (bb.has(value)) return true;
  return false;
}

function samePublishedShow(candidate, published) {
  const publishedDate = dateOnly(published.startDate || published.datetime || published.date || '');
  if (!candidate.date || candidate.date !== publishedDate) return false;
  if (normalize(candidate.state) && normalize(published.state) && normalize(candidate.state) !== normalize(published.state)) return false;
  if (normalize(candidate.city) && normalize(published.city) && normalize(candidate.city) !== normalize(published.city)) return false;
  if (!overlap(candidate, published)) return false;

  const cv = normalize(candidate.venue);
  const pv = normalize(published.venue);
  const ct = normalize(candidate.title);
  const pt = normalize(published.title);
  if (cv && pv && cv === pv) return true;
  if (ct && pt && (ct === pt || ct.includes(pt) || pt.includes(ct))) return true;
  // Same tracked artist, city, state and date is a duplicate unless both records
  // clearly identify different venues.
  if (!(cv && pv) || cv === pv) return true;
  return false;
}

const [artistsConfig, publishedMain, publishedSupplemental, officialSources] = await Promise.all([
  getProdJson('config/artists.json'),
  getProdJson('events.json'),
  getProdJson('supplemental-events.json'),
  getProdJson('config/official-sources.json'),
]);

const artists = artistsConfig.filter(a => a && a.enabled !== false && a.name);
const published = [
  ...(Array.isArray(publishedMain) ? publishedMain : []),
  ...(Array.isArray(publishedSupplemental) ? publishedSupplemental : []),
];
const knownBandsintownIds = mapKnownBandsintownIds(officialSources);

const rawUs = [];
const rejectedIdentities = [];
const perArtistScan = [];
let requestErrors = 0;
let resolvedCount = 0;

for (let i = 0; i < artists.length; i++) {
  const configured = artists[i];
  const name = String(configured.name).trim();
  const resolved = await resolveArtist(configured);
  const row = { name, resolved: false, acceptedIdentity: false, identityReason: '', eventsUS: 0 };

  if (!resolved.ok) {
    row.identityReason = 'unresolved';
    if (resolved.tried.some(x => x.status && x.status >= 400 && x.status !== 404)) requestErrors++;
    perArtistScan.push(row);
    await sleep(45);
    continue;
  }

  resolvedCount++;
  row.resolved = true;
  const resolvedId = String(resolved.artist.id || '');
  const risky = isIdentityRisk(name);
  const profileMatch = hasProfileMatch(configured, resolved.artist);
  const knownId = knownBandsintownIds.get(normalize(name));
  const idMatch = Boolean(knownId && knownId === resolvedId);
  const acceptedIdentity = !risky || profileMatch || idMatch;
  const identityConfidence = profileMatch ? 'profile_match' : idMatch ? 'configured_bandsintown_id' : risky ? 'rejected_ambiguous_name' : 'exact_name_or_alias';
  row.acceptedIdentity = acceptedIdentity;
  row.identityReason = identityConfidence;
  row.bandsintownArtistId = resolvedId;

  if (!acceptedIdentity) {
    rejectedIdentities.push({ artist: name, bandsintownArtistId: resolvedId, reason: identityConfidence });
    perArtistScan.push(row);
    await sleep(45);
    continue;
  }

  const eventsUrl = `${BASE}/artists/id_${encodeURIComponent(resolvedId)}/events/?app_id=${encodeURIComponent(APP_ID)}&date=upcoming`;
  const response = await getJson(eventsUrl);
  if (!response.ok || !Array.isArray(response.json)) {
    row.identityReason += `;events_request_failed:${response.status}`;
    requestErrors++;
    perArtistScan.push(row);
    await sleep(60);
    continue;
  }

  for (const event of response.json) {
    const compact = compactEvent(event, name, identityConfidence);
    if (!isUS(compact.country) || !compact.date || compact.date < TODAY) continue;
    const lineupSet = new Set(compact.lineup.map(normalize));
    const acceptedNames = new Set([name, ...(configured.aliases || [])].map(normalize));
    let performerConfirmed = lineupSet.size === 0;
    for (const candidate of acceptedNames) if (lineupSet.has(candidate)) performerConfirmed = true;
    if (!performerConfirmed) continue;
    rawUs.push(compact);
    row.eventsUS++;
  }

  perArtistScan.push(row);
  await sleep(60);
}

// Internal dedupe: Bandsintown sometimes gives different IDs for the same festival
// appearance. Cluster by date/city/state/venue and merge tracked artists.
const clusters = new Map();
for (const event of rawUs) {
  const key = eventClusterKey(event);
  if (!clusters.has(key)) {
    clusters.set(key, { ...event, trackedArtists: [event.trackedArtist], sourceEventIds: [event.id] });
  } else {
    const current = clusters.get(key);
    if (!current.trackedArtists.includes(event.trackedArtist)) current.trackedArtists.push(event.trackedArtist);
    if (event.id && !current.sourceEventIds.includes(event.id)) current.sourceEventIds.push(event.id);
    current.lineup = [...new Set([...(current.lineup || []), ...(event.lineup || [])])];
    if (!current.ticketUrl && event.ticketUrl) current.ticketUrl = event.ticketUrl;
    if (!current.eventUrl && event.eventUrl) current.eventUrl = event.eventUrl;
  }
}

const uniqueCandidates = [...clusters.values()].sort((a,b) => `${a.date}${a.city}${a.venue}`.localeCompare(`${b.date}${b.city}${b.venue}`));
const duplicates = [];
const festivalNeedsConfirmation = [];
const verifiedNew = [];

for (const candidate of uniqueCandidates) {
  const matches = published.filter(event => samePublishedShow(candidate, event));
  if (matches.length) {
    duplicates.push({ ...candidate, duplicateOf: matches.slice(0,3).map(e => ({ id: e.id || '', title: e.title || '', date: e.startDate || '', city: e.city || '', state: e.state || '' })) });
    continue;
  }
  if (isFestivalLike(candidate)) {
    festivalNeedsConfirmation.push(candidate);
    continue;
  }
  verifiedNew.push(candidate);
}

const newShowsByArtistMap = new Map();
for (const event of verifiedNew) {
  for (const artist of event.trackedArtists || [event.trackedArtist]) {
    newShowsByArtistMap.set(artist, (newShowsByArtistMap.get(artist) || 0) + 1);
  }
}
const newShowsByArtist = [...newShowsByArtistMap.entries()]
  .map(([artist, newShows]) => ({ artist, newShows }))
  .sort((a,b) => b.newShows - a.newShows || a.artist.localeCompare(b.artist));

const summary = {
  generatedAt: new Date().toISOString(),
  productionRosterArtists: artists.length,
  bandsintownArtistsResolvedExactNameOrAlias: resolvedCount,
  rejectedAmbiguousArtistIdentities: rejectedIdentities.length,
  rawAcceptedUSArtistEventRows: rawUs.length,
  uniqueUSCandidatesAfterBandsintownInternalDedupe: uniqueCandidates.length,
  duplicatesAlreadyOnKingdomCircuit: duplicates.length,
  festivalAppearancesHeldForOfficialLineupConfirmation: festivalNeedsConfirmation.length,
  verifiedNewNonFestivalShows: verifiedNew.length,
  artistsWithVerifiedNewShows: newShowsByArtist.length,
  requestErrors,
};

await fs.writeFile(OUTPUT_PATH, JSON.stringify({
  summary,
  newShowsByArtist,
  verifiedNewShows: verifiedNew,
  festivalNeedsConfirmation,
  duplicates,
  rejectedIdentities,
  artistScan: perArtistScan,
}, null, 2));

console.log(JSON.stringify(summary, null, 2));
console.log(JSON.stringify(newShowsByArtist, null, 2));
