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
const context = await browser.newContext({
  locale: 'en-US',
  timezoneId: 'America/Chicago',
  viewport: { width: 1440, height: 1200 },
});

async function testDirect(artist) {
  const page = await context.newPage();
  const item = { status: 'unknown', title: '', textSample: '', eventLinks: [], errors: [] };
  try {
    const response = await page.goto(artist.knownUrl, { waitUntil: 'domcontentloaded', timeout: 45000 });
    item.httpStatus = response?.status() ?? null;
    await page.waitForTimeout(3000);
    item.title = await page.title();
    const bodyText = (await page.locator('body').innerText({ timeout: 10000 })).replace(/\s+/g, ' ').trim();
    item.textSample = bodyText.slice(0, 700);
    item.blocked = /access denied|forbidden|captcha|verify you are human|cloudflare|you have been blocked/i.test(`${item.title} ${bodyText}`);
    const links = await page.locator('a[href*="/e/"]').evaluateAll(nodes => nodes.map(a => a.href));
    item.eventLinks = [...new Set(links)].slice(0, 30);
    item.status = !item.blocked && item.httpStatus && item.httpStatus < 400 ? 'accessible' : 'blocked_or_error';
  } catch (error) {
    item.status = 'error';
    item.errors.push(String(error).slice(0, 500));
  } finally {
    await page.close();
  }
  return item;
}

async function testWidget(artist) {
  const page = await context.newPage();
  const encodedName = encodeURIComponent(artist.name);
  const widgetUrl = `https://widgetv3.bandsintown.com/widget_iframe.html?affil_code=js_kingdomcircuit.com&app_id=js_kingdomcircuit.com&artist_id=${artist.id}&artist_name=${encodedName}&came_from_code=700`;
  const item = { url: widgetUrl, status: 'unknown', title: '', textSample: '', eventLinks: [], restResponses: [], errors: [] };

  page.on('response', async response => {
    const url = response.url();
    if (!/rest\.bandsintown\.com|api\.bandsintown\.com/i.test(url)) return;
    const record = { url, status: response.status(), contentType: response.headers()['content-type'] || '' };
    try {
      if (/json/i.test(record.contentType)) {
        const text = await response.text();
        record.bodySample = text.slice(0, 5000);
      }
    } catch {}
    item.restResponses.push(record);
  });

  try {
    const response = await page.goto(widgetUrl, { waitUntil: 'domcontentloaded', timeout: 45000 });
    item.httpStatus = response?.status() ?? null;
    await page.waitForTimeout(7000);
    item.title = await page.title();
    const bodyText = (await page.locator('body').innerText({ timeout: 10000 })).replace(/\s+/g, ' ').trim();
    item.textSample = bodyText.slice(0, 3000);
    item.blocked = /access denied|forbidden|captcha|verify you are human|cloudflare|you have been blocked/i.test(`${item.title} ${bodyText}`);
    const links = await page.locator('a[href*="bandsintown.com/e/"]').evaluateAll(nodes => nodes.map(a => a.href));
    item.eventLinks = [...new Set(links)].slice(0, 40);
    item.status = !item.blocked && item.httpStatus && item.httpStatus < 400 ? 'accessible' : 'blocked_or_error';
  } catch (error) {
    item.status = 'error';
    item.errors.push(String(error).slice(0, 500));
  } finally {
    await page.close();
  }
  return item;
}

for (const artist of artists) {
  const direct = await testDirect(artist);
  const widget = await testWidget(artist);
  const item = { artist: artist.name, artistId: artist.id, direct, widget };
  results.push(item);
  console.log(JSON.stringify({
    artist: artist.name,
    direct: direct.status,
    directHttp: direct.httpStatus,
    widget: widget.status,
    widgetHttp: widget.httpStatus,
    widgetEvents: widget.eventLinks.length,
    restResponses: widget.restResponses.map(r => ({ status: r.status, url: r.url })),
  }));
}

await browser.close();
fs.writeFileSync('bandsintown-browser-test-results.json', JSON.stringify({ generatedAt: new Date().toISOString(), results }, null, 2));
