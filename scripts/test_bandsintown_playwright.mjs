import fs from 'node:fs';
import { chromium } from 'playwright';

const artists = [
  { name: '1K Phew', id: '12546964', knownUrl: 'https://www.bandsintown.com/a/12546964-1k-phew' },
  { name: 'Parris Chariz', id: '14726057', knownUrl: 'https://www.bandsintown.com/a/14726057-parris-chariz' },
  { name: 'KB', id: '165768', knownUrl: 'https://www.bandsintown.com/a/165768-kb' },
  { name: 'NF', id: '11969355', knownUrl: 'https://www.bandsintown.com/a/11969355-nf' },
];

const results = [];
const browser = await chromium.launch({ headless: true });
const context = await browser.newContext({ locale: 'en-US', timezoneId: 'America/Chicago', viewport: { width: 1440, height: 1200 } });

async function testRest(artist) {
  const url = `https://rest.bandsintown.com/artists/id_${artist.id}/events/?app_id=js_kingdomcircuit.com&date=upcoming`;
  const item = { url, status: 'unknown', httpStatus: null, eventCount: null, events: [], errors: [] };
  try {
    const response = await fetch(url, { headers: {
      'Accept': 'application/json,text/plain,*/*',
      'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/140 Safari/537.36',
      'Referer': 'https://kingdomcircuit.com/',
      'Origin': 'https://kingdomcircuit.com',
    }});
    item.httpStatus = response.status;
    const text = await response.text();
    if (!response.ok) {
      item.status = 'blocked_or_error';
      return item;
    }
    const json = JSON.parse(text);
    item.status = 'accessible';
    item.eventCount = Array.isArray(json) ? json.length : null;
    item.events = Array.isArray(json) ? json.map(event => ({
      id: String(event.id || ''),
      datetime: String(event.datetime || event.starts_at || ''),
      title: String(event.title || ''),
      venue: String(event.venue?.name || ''),
      city: String(event.venue?.city || ''),
      state: String(event.venue?.region || ''),
      lineup: Array.isArray(event.lineup) ? event.lineup : [],
      ticketUrl: Array.isArray(event.offers) && event.offers[0] ? String(event.offers[0].url || '') : '',
      eventUrl: String(event.url || ''),
    })) : [];
  } catch (error) {
    item.status = 'error';
    item.errors.push(String(error).slice(0, 500));
  }
  return item;
}

async function testDirect(artist) {
  const page = await context.newPage();
  const item = { status: 'unknown', httpStatus: null, blocked: null };
  try {
    const response = await page.goto(artist.knownUrl, { waitUntil: 'domcontentloaded', timeout: 45000 });
    item.httpStatus = response?.status() ?? null;
    await page.waitForTimeout(1500);
    const title = await page.title();
    const body = (await page.locator('body').innerText({ timeout: 10000 })).replace(/\s+/g, ' ').trim();
    item.blocked = /access denied|forbidden|captcha|verify you are human|cloudflare|you have been blocked/i.test(`${title} ${body}`);
    item.status = !item.blocked && item.httpStatus && item.httpStatus < 400 ? 'accessible' : 'blocked_or_error';
  } catch {
    item.status = 'error';
  } finally {
    await page.close();
  }
  return item;
}

for (const artist of artists) {
  const rest = await testRest(artist);
  const direct = await testDirect(artist);
  results.push({ artist: artist.name, artistId: artist.id, rest, direct });
  console.log(JSON.stringify({ artist: artist.name, rest: rest.status, restHttp: rest.httpStatus, restEvents: rest.eventCount, direct: direct.status, directHttp: direct.httpStatus }));
}

await browser.close();
fs.writeFileSync('bandsintown-browser-test-results.json', JSON.stringify({ generatedAt: new Date().toISOString(), results }, null, 2));
