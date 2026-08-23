import fs from 'node:fs';
import { chromium } from 'playwright';

const artists = [
  { name: '1K Phew', knownUrl: 'https://www.bandsintown.com/a/12546964-1k-phew' },
  { name: 'Parris Chariz', knownUrl: 'https://www.bandsintown.com/a/14726057-parris-chariz' },
  { name: 'KB', knownUrl: 'https://www.bandsintown.com/a/165768-kb' },
  { name: 'NF', knownUrl: 'https://www.bandsintown.com/a/11969355-nf' },
];

const results = [];
const browser = await chromium.launch({ headless: true });
const context = await browser.newContext({
  locale: 'en-US',
  timezoneId: 'America/Chicago',
  viewport: { width: 1440, height: 1200 },
});

for (const artist of artists) {
  const page = await context.newPage();
  const item = { artist: artist.name, url: artist.knownUrl, status: 'unknown', title: '', textSample: '', eventLinks: [], errors: [] };
  try {
    const response = await page.goto(artist.knownUrl, { waitUntil: 'domcontentloaded', timeout: 45000 });
    item.httpStatus = response?.status() ?? null;
    await page.waitForTimeout(4000);
    item.title = await page.title();
    const bodyText = (await page.locator('body').innerText({ timeout: 10000 })).replace(/\s+/g, ' ').trim();
    item.textSample = bodyText.slice(0, 1200);
    item.blocked = /access denied|forbidden|captcha|verify you are human|cloudflare/i.test(`${item.title} ${bodyText}`);
    const links = await page.locator('a[href*="/e/"]').evaluateAll(nodes => nodes.map(a => a.href));
    item.eventLinks = [...new Set(links)].slice(0, 30);
    item.status = !item.blocked && item.httpStatus && item.httpStatus < 400 ? 'accessible' : 'blocked_or_error';
  } catch (error) {
    item.status = 'error';
    item.errors.push(String(error).slice(0, 500));
  } finally {
    await page.close();
  }
  results.push(item);
  console.log(JSON.stringify({ artist: item.artist, status: item.status, httpStatus: item.httpStatus, events: item.eventLinks.length, title: item.title }));
}

await browser.close();
fs.writeFileSync('bandsintown-browser-test-results.json', JSON.stringify({ generatedAt: new Date().toISOString(), results }, null, 2));
