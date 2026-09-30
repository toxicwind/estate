#!/usr/bin/env node
// MCP stdio e2e test: initialize, list tools, call persistent_status + persistent_navigate.
const { spawn } = require('child_process');

const child = spawn('node', ['/home/toxic/sovereign/projects/mesh/browserless/dist/index.js'], {
  stdio: ['pipe', 'pipe', 'inherit'],
  env: { ...process.env, BROWSER_KEEPER_CDP: 'http://127.0.0.1:9223' },
});

let mid = 0;
const pending = new Map();
let rest = '';
child.stdout.on('data', (chunk) => {
  rest += chunk.toString();
  let idx;
  while ((idx = rest.indexOf('\n')) !== -1) {
    const line = rest.slice(0, idx).trim();
    rest = rest.slice(idx + 1);
    if (!line) continue;
    try {
      const msg = JSON.parse(line);
      if (msg.id !== undefined && pending.has(msg.id)) {
        pending.get(msg.id)(msg);
        pending.delete(msg.id);
      }
    } catch (e) { /* banner lines etc, ignore */ }
  }
});

function send(method, params) {
  return new Promise((resolve, reject) => {
    const id = ++mid;
    pending.set(id, resolve);
    child.stdin.write(JSON.stringify({ jsonrpc: '2.0', id, method, params: params || {} }) + '\n');
    setTimeout(() => { if (pending.has(id)) { pending.delete(id); reject(new Error('timeout ' + method)); } }, 30000);
  });
}
function notify(method, params) {
  child.stdin.write(JSON.stringify({ jsonrpc: '2.0', method, params: params || {} }) + '\n');
}

async function main() {
  await send('initialize', {
    protocolVersion: '2024-11-05',
    capabilities: {},
    clientInfo: { name: 'e2e-test', version: '1.0' },
  });
  notify('notifications/initialized');
  const tools = await send('tools/list');
  const names = tools.result.tools.map((t) => t.name);
  console.log('TOOLS:', JSON.stringify(names));
  const want = ['persistent_status','persistent_navigate','persistent_screenshot','persistent_click','persistent_fill','persistent_text','persistent_evaluate'];
  const missing = want.filter((w) => !names.includes(w));
  console.log('MISSING:', JSON.stringify(missing));

  const status = await send('tools/call', { name: 'persistent_status', arguments: {} });
  const stext = JSON.stringify(status.result).slice(0, 500);
  console.log('STATUS:', stext);

  const nav = await send('tools/call', { name: 'persistent_navigate', arguments: { url: 'about:blank' } });
  console.log('NAVIGATE:', JSON.stringify(nav.result).slice(0, 300));

  child.kill();
  if (missing.length > 0) { console.log('E2E_FAIL missing tools'); process.exit(1); }
  console.log('E2E_OK');
}

main().catch((e) => { console.error('E2E_ERR', e.message); child.kill(); process.exit(2); });
setTimeout(() => { console.error('E2E_TIMEOUT'); child.kill(); process.exit(3); }, 90000).unref();
