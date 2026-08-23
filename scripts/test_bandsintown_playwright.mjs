import fs from 'node:fs/promises';

const APP_ID = 'js_kingdomcircuit.com';
const ARTISTS_PATH = 'config/artists.json';
const OUTPUT_PATH = 'bandsintown-browser-test-results.json';
const BASE = 'https://rest.bandsintown.com';

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

function isIdentityRisk(name) {
  const compact = normalize(name).replace(/\s/g, '');
  return compact.length <= 3 || /^(116|350|kb|nf|so|jr)$/i.test(compact);
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
    await sleep(400 * attempt);
  }
  return last || { ok: false, status: null, body: 'unknown error' };
}

async function resolveArtist(artist) {
  const canonical = String(artist.name || '').trim();
  const aliases = [canonical, ...(Array.isArray(artist.aliases) ? artist.aliases : [])]
    .map(v => String(v || '').trim())
    .filter(Boolean);
  const accepted = new Set(aliases.map(normalize));
  const tried = [];

  for (const candidate of [...new Set(aliases)].slice(0, 4)) {
    const url = `${BASE}/artists/${encodeURIComponent(candidate)}?app_id=${encodeURIComponent(APP_ID)}`;
    const response = await getJson(url);
    tried.push({ candidate, status: response.status });
    if (!response.ok || !response.json || Array.isArray(response.json)) continue;

    const resolvedName = String(response.json.name || '').trim();
    if (!accepted.has(normalize(resolvedName))) continue;

    return {
      ok: true,
      artist: response.json,
      matchedBy: candidate,
      identityRisk: isIdentityRisk(canonical),
      tried,
    };
  }
  return { ok: false, tried };
}

function compactEvent(event, trackedArtist) {
  const venue = event?.venue || {};
  const offers = Array.isArray(event?.offers) ? event.offers : [];
  return {
    id: String(event?.id || ''),
    trackedArtist,
    artistId: String(event?.artist_id || event?.artist?.id || ''),
    datetime: String(event?.datetime || event?.starts_at || ''),
    title: String(event?.title || ''),
    venue: String(venue.name || ''),
    city: String(venue.city || ''),
    state: String(venue.region || ''),
    country: String(venue.country || ''),
    lineup: Array.isArray(event?.lineup) ? event.lineup : [],
    ticketUrl: String(offers.find(o => o?.url)?.url || ''),
    eventUrl: String(event?.url || ''),
  };
}

const artistConfig = JSON.parse(await fs.readFile(ARTISTS_PATH, 'utf8'));
const artists = artistConfig.filter(a => a && a.enabled !== false && a.name);
const perArtist = [];
const uniqueUsEvents = new Map();
const uniqueAllEvents = new Map();
let rawArtistEventRows = 0;
let rawUsArtistEventRows = 0;
let requestErrors = 0;
let resolvedCount = 0;
let artistsWithUsEvents = 0;
let identityRiskResolved = 0;

for (let i = 0; i < artists.length; i++) {
  const configured = artists[i];
  const name = String(configured.name).trim();
  const resolved = await resolveArtist(configured);
  const row = {
    name,
    resolved: false,
    resolvedName: '',
    bandsintownArtistId: '',
    identityRisk: false,
    upcomingEventsAllCountries: 0,
    upcomingEventsUS: 0,
    eventsUS: [],
    error: '',
  };

  if (!resolved.ok) {
    row.error = `artist_not_resolved:${resolved.tried.map(x => `${x.candidate}:${x.status}`).join(',')}`;
    if (resolved.tried.some(x => x.status && x.status >= 400 && x.status !== 404)) requestErrors++;
    perArtist.push(row);
    console.log(`[${i + 1}/${artists.length}] ${name}: unresolved`);
    await sleep(50);
    continue;
  }

  resolvedCount++;
  row.resolved = true;
  row.resolvedName = String(resolved.artist.name || '');
  row.bandsintownArtistId = String(resolved.artist.id || '');
  row.identityRisk = resolved.identityRisk;
  if (row.identityRisk) identityRiskResolved++;

  const eventsUrl = `${BASE}/artists/id_${encodeURIComponent(row.bandsintownArtistId)}/events/?app_id=${encodeURIComponent(APP_ID)}&date=upcoming`;
  const response = await getJson(eventsUrl);
  if (!response.ok || !Array.isArray(response.json)) {
    row.error = `events_request_failed:${response.status}`;
    requestErrors++;
    perArtist.push(row);
    console.log(`[${i + 1}/${artists.length}] ${name}: resolved, events request failed ${response.status}`);
    await sleep(75);
    continue;
  }

  const events = response.json;
  row.upcomingEventsAllCountries = events.length;
  rawArtistEventRows += events.length;
  for (const event of events) {
    const compact = compactEvent(event, name);
    if (compact.id) uniqueAllEvents.set(compact.id, compact);
    const country = normalize(compact.country);
    const isUS = country === 'united states' || country === 'us' || country === 'usa';
    if (!isUS) continue;
    rawUsArtistEventRows++;
    row.eventsUS.push(compact);
    if (compact.id) {
      const existing = uniqueUsEvents.get(compact.id);
      if (!existing) uniqueUsEvents.set(compact.id, { ...compact, trackedArtists: [name] });
      else if (!existing.trackedArtists.includes(name)) existing.trackedArtists.push(name);
    }
  }
  row.upcomingEventsUS = row.eventsUS.length;
  if (row.upcomingEventsUS > 0) artistsWithUsEvents++;
  perArtist.push(row);
  console.log(`[${i + 1}/${artists.length}] ${name}: ${row.upcomingEventsUS} US / ${row.upcomingEventsAllCountries} all`);
  await sleep(75);
}

const uniqueUs = [...uniqueUsEvents.values()].sort((a, b) => String(a.datetime).localeCompare(String(b.datetime)));
const summary = {
  generatedAt: new Date().toISOString(),
  artistsConfigured: artists.length,
  artistsResolvedExactNameOrAlias: resolvedCount,
  artistsWithUpcomingUSEvents: artistsWithUsEvents,
  identityRiskArtistsResolved: identityRiskResolved,
  rawArtistEventRowsAllCountries: rawArtistEventRows,
  rawArtistEventRowsUS: rawUsArtistEventRows,
  uniqueUpcomingEventsAllCountries: uniqueAllEvents.size,
  uniqueUpcomingUSEvents: uniqueUsEvents.size,
  requestErrors,
};

await fs.writeFile(OUTPUT_PATH, JSON.stringify({ summary, uniqueUpcomingUSEvents: uniqueUs, artists: perArtist }, null, 2));
console.log(JSON.stringify(summary, null, 2));
