#!/usr/bin/env node
// CDP driver: navigate keeper page, evaluate, print safe metadata only.
const http = require('http');
const WebSocket = require('ws');

const CDP = 'http://127.0.0.1:9223';

function get(path) {
  return new Promise((resolve, reject) => {
    http.get(CDP + path, (res) => {
      let d = '';
      res.on('data', (c) => d += c);
      res.on('end', () => { try { resolve(JSON.parse(d)); } catch (e) { reject(e); } });
    }).on('error', reject);
  });
}

async function main() {
  const action = process.argv[2];
  const targets = await get('/json/list');
  const page = targets.find((t) => t.type === 'page');
  if (!page) { console.log('NO_PAGE'); process.exit(1); }

  if (action === 'info') {
    console.log(JSON.stringify({ id: page.id, title: page.title, url: page.url }));
    return;
  }

  const ws = new WebSocket(page.webSocketDebuggerUrl, { maxPayload: 64 * 1024 * 1024 });
  await new Promise((res, rej) => { ws.on('open', res); ws.on('error', rej); });
  let mid = 0;
  const pending = new Map();
  ws.on('message', (data) => {
    const msg = JSON.parse(data.toString());
    if (msg.id && pending.has(msg.id)) { pending.get(msg.id)(msg); pending.delete(msg.id); }
  });
  const send = (method, params) => new Promise((resolve, reject) => {
    const id = ++mid;
    pending.set(id, resolve);
    ws.send(JSON.stringify({ id, method, params: params || {} }));
    setTimeout(() => { if (pending.has(id)) { pending.delete(id); reject(new Error('timeout ' + method)); } }, 25000);
  });
  const evaluate = async (expr) => {
    const r = await send('Runtime.evaluate', { expression: expr, returnByValue: true, awaitPromise: true });
    return r.result && r.result.result ? r.result.result.value : null;
  };

  if (action === 'navigate') {
    await send('Page.navigate', { url: process.argv[3] });
    console.log('NAVIGATED');
  } else if (action === 'text') {
    const t = await evaluate('document.documentElement ? document.documentElement.innerText.slice(0,4000) : "NO_DOC"');
    console.log(t);
  } else if (action === 'url') {
    console.log(await evaluate('location.href'));
  } else if (action === 'click') {
    // click first element matching text
    const r = await evaluate(`(() => { const els=[...document.querySelectorAll('button,a,[role="button"]')]; const el=els.find(e=>(e.innerText||'').includes(${JSON.stringify(process.argv[3])})); if(!el) return 'NOT_FOUND'; el.click(); return 'CLICKED'; })()`);
    console.log(r);
  }
  ws.close();
}

main().catch((e) => { console.error('ERR', e.message); process.exit(2); });
