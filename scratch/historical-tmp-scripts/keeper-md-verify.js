// Keeper verification: markdown rendering + no truncation on live feed.
// Reads the feed token from yote config; never prints it.
const { execSync } = require('child_process');
const { chromium } = require('/home/toxic/.browserless/app/node_modules/playwright-core');

(async () => {
  const token = execSync("cat /home/toxic/.shingle/squawk-relay/feed-token",
    { encoding: 'utf8' }
  ).trim().split('\n').pop().trim();

  const browser = await chromium.connectOverCDP('http://127.0.0.1:9223');
  const ctx = browser.contexts()[0] || await browser.newContext();
  const page = await ctx.newPage();
  const errors = [];
  page.on('pageerror', e => errors.push('page:' + e.message));
  page.on('console', m => { if (m.type() === 'error') errors.push('console:' + m.text()); });

  await page.goto(`http://127.0.0.1:25135/squawk-feed/ui?token=${encodeURIComponent(token)}`, { waitUntil: 'domcontentloaded', timeout: 20000 });
  await page.waitForTimeout(4000);

  const res = await page.evaluate(async () => {
    const out = {};
    // find the markdown test card (seq 12720) in the DOM
    const cards = [...document.querySelectorAll('.msg')];
    out.cardCount = cards.length;
    const test = cards.find(c => c.textContent.includes('Markdown render test'));
    out.testFound = !!test;
    if (test) {
      const body = test.querySelector('.body');
      out.bodyHTML = body.innerHTML.slice(0, 400);
      out.hasH1 = !!body.querySelector('h1');
      out.hasStrong = body.querySelectorAll('strong').length;
      out.hasEm = body.querySelectorAll('em').length;
      out.hasCode = body.querySelectorAll('code').length;
      out.hasUL = !!body.querySelector('ul');
      out.hasOL = !!body.querySelector('ol');
      out.hasQuote = !!body.querySelector('blockquote');
      out.hasPre = !!body.querySelector('pre');
      out.hasGoodLink = !!body.querySelector('a[href^="https://example.com"]');
      out.badLinkLiteral = body.textContent.includes('[bad one](javascript:alert(1))');
      out.codeEscaped = body.innerHTML.includes('&lt;angles&gt;');
      out.plainTextLen = body.textContent.length;
    }
    return out;
  });

  console.log(JSON.stringify({ dom: res, errors }, null, 1));
  await page.close();
})().catch(e => { console.error('KEEPER FAIL', e.message); process.exit(1); });
