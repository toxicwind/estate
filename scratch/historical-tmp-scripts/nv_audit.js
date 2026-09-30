// Visible NVIDIA account audit via yote browserless (non-headless). v4: NGC api-keys + login href.
const { chromium } = require('/home/toxic/.browserless/app/node_modules/playwright-core');
const fs = require('fs');

const envText = fs.readFileSync('/home/toxic/.browserless/.env', 'utf8');
const tokenLine = envText.split('\n').find((l) => l.trim().startsWith('BROWSERLESS_TOKEN'));
const token = tokenLine.split('=').slice(1).join('=').trim().replace(/^["']|["']$/g, '');
if (!token) { console.error('FATAL no token'); process.exit(1); }

const dump = async (page, label) => {
  const url = page.url();
  const title = await page.title().catch(() => '?');
  const text = await page.evaluate(() => document.body ? document.body.innerText.slice(0, 2000) : 'NO_BODY').catch((e) => 'EVAL_FAIL ' + e.message);
  const pw = await page.locator('input[type="password"]').count().catch(() => -1);
  const email = await page.locator('input[type="email"], input[name="username"]').count().catch(() => -1);
  console.log(`=== ${label} ===`);
  console.log('URL', url);
  console.log('TITLE', title);
  console.log('PW_FIELDS', pw, 'EMAIL_FIELDS', email);
  console.log('TEXT', JSON.stringify(text));
};

(async () => {
  const launch = encodeURIComponent(JSON.stringify({ args: ['--disable-gpu', '--disable-dev-shm-usage'] }));
  const wsUrl = `ws://127.0.0.1:25130/playwright/chromium?token=${encodeURIComponent(token)}&headless=false&launch=${launch}`;
  console.log('CONNECTING browserless (headed, no-gpu)...');
  const browser = await chromium.connect(wsUrl, { timeout: 90000 });
  console.log('CONNECTED');
  const ctx = await browser.newContext({ viewport: { width: 1600, height: 900 }, locale: 'en-US' });
  const page = await ctx.newPage();

  await page.goto('https://ngc.nvidia.com/setup/api-keys', { waitUntil: 'domcontentloaded', timeout: 60000 }).catch(() => {});
  await page.waitForTimeout(7000);
  await dump(page, 'NGC_API_KEYS');

  await page.goto('https://build.nvidia.com/', { waitUntil: 'domcontentloaded', timeout: 60000 }).catch(() => {});
  await page.waitForTimeout(5000);
  const loginHref = await page.evaluate(() => {
    const els = [...document.querySelectorAll('a')].filter((a) => /log\s*in/i.test(a.innerText));
    return els.map((a) => a.href).slice(0, 3);
  }).catch((e) => 'EVAL_FAIL ' + e.message);
  console.log('LOGIN_HREFS', JSON.stringify(loginHref));

  console.log('HOLDING open 15 min for live viewing...');
  try { await page.waitForTimeout(15 * 60 * 1000); } catch (e) { console.log('HOLD_ENDED', String(e.message).split('\n')[0]); }
  await browser.close().catch(() => {});
  console.log('DONE');
})().catch((e) => { console.error('FATAL', e.message); process.exit(1); });
