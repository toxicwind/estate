
const $ = id => document.getElementById(id);
let token = sessionStorage.getItem('squawk-token') || '';
// magic link: ?token=... auto-tunes, no paste needed (scrubbed from the bar after)
try {
  var q = new URLSearchParams(location.search).get('token');
  if (q && !token) {
    token = q.trim();
    sessionStorage.setItem('squawk-token', token);
    history.replaceState(null, '', location.pathname + location.hash);
  }
} catch (e) {}
let since = 0, running = false, failures = 0, booted = false, gen = 0;
// live source: 'poll' (long-poll, default) or 'nats' (JetStream mirror over websocket).
// ?src=nats selects NATS; the header button toggles at runtime.
let srcMode = 'poll';
try { const qsrc = new URLSearchParams(location.search).get('src');
      if (qsrc === 'nats' || qsrc === 'poll') srcMode = qsrc; } catch (e) {}
function paintSrc() { const b = $('src'); if (b) { b.textContent = srcMode;
  b.title = 'live source: ' + srcMode + ' (click to switch)'; } }
const TAIL = 200;       // bounded recent snapshot for initial load
const BATCH_CAP = 50;   // server MAX_MESSAGES: a full batch means backlog

function auth() { return { 'Authorization': 'Bearer ' + token }; }
function chan() { return encodeURIComponent($('channel').value.trim() || 'fleet'); }

// --- connection state: loading / live / catching-up / reconnecting -----
const STATES = {
  'loading':     ['#e0a458', 'loading…'],
  'live':        ['var(--sealed)', 'live'],
  'catching-up': ['#e0a458', 'catching up…'],
  'reconnecting':['#c46a5a', 'reconnecting…'],
};
function setState(name, extra) {
  const s = STATES[name] || STATES.live;
  $('conn').style.color = s[0];
  $('connstat').textContent = s[1] + (extra || '');
}

function line(html, cls) {
  const d = document.createElement('div');
  d.className = cls || 'msg'; d.innerHTML = html;
  const log = $('log');
  const nearBottom = log.scrollHeight - log.scrollTop - log.clientHeight < 60;
  log.appendChild(d);
  while (log.children.length > 500) log.removeChild(log.firstChild);
  if (nearBottom) log.scrollTop = log.scrollHeight;
}
const esc = s => String(s).replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));

/* tiny markdown renderer: escape-first, safe-HTML-only output (user HTML never passes through).
   blocks: fenced code, headings (#-####), blockquotes (>), bullet/numbered lists, paragraphs.
   inline: `code`, **bold**, *italic*, [text](http(s)://url). fail-soft: anything odd stays literal. */
function mdInline(s) {
  let out = esc(s);
  const codes = [];
  out = out.replace(/`([^`\n]+)`/g, (m, c) => { codes.push(c); return '\u0000' + (codes.length - 1) + '\u0000'; });
  out = out.replace(/\*\*([^*\n]+)\*\*/g, '<strong>$1</strong>');
  out = out.replace(/(^|[^*\w])\*([^*\n]+)\*/g, '$1<em>$2</em>');
  out = out.replace(/\[([^\]\n]+)\]\(([^)\s\n]+)\)/g, (m, t, u) =>
    /^https?:\/\//i.test(u) ? `<a href="${u}" target="_blank" rel="noopener noreferrer">${t}</a>` : m);
  return out.replace(/\u0000(\d+)\u0000/g, (m, i) => `<code>${codes[+i]}</code>`);
}
function md(src) {
  const lines = String(src).split('\n');
  let html = '', inCode = false, list = null, para = [];
  const flushP = () => { if (para.length) { html += '<p>' + para.map(mdInline).join('<br>') + '</p>'; para = []; } };
  const closeL = () => { if (list) { html += '</' + list + '>'; list = null; } };
  const openL = t => { if (list !== t) { closeL(); html += '<' + t + '>'; list = t; } };
  for (const ln of lines) {
    if (/^```/.test(ln)) { flushP(); closeL(); html += inCode ? '</code></pre>' : '<pre><code>'; inCode = !inCode; continue; }
    if (inCode) { html += esc(ln) + '\n'; continue; }
    let m;
    if (m = ln.match(/^(#{1,4})\s+(.*)$/)) { flushP(); closeL(); html += `<h${m[1].length}>${mdInline(m[2])}</h${m[1].length}>`; continue; }
    if (m = ln.match(/^>\s?(.*)$/)) { flushP(); closeL(); html += `<blockquote>${mdInline(m[1])}</blockquote>`; continue; }
    if (m = ln.match(/^\s*[-*]\s+(.+)$/)) { flushP(); openL('ul'); html += `<li>${mdInline(m[1])}</li>`; continue; }
    if (m = ln.match(/^\s*\d+[.)]\s+(.+)$/)) { flushP(); openL('ol'); html += `<li>${mdInline(m[1])}</li>`; continue; }
    if (/^\s*$/.test(ln)) { flushP(); closeL(); continue; }
    closeL(); para.push(ln);
  }
  flushP(); closeL();
  if (inCode) html += '</code></pre>';
  return html;
}

function badges(m) {
  let b = '';
  if (m.signature && m.signature !== 'valid')
    b += `<span class="badge unverified" title="signature ${esc(m.signature)} — treat the sender and text as unconfirmed">unverified</span>`;
  if (m.sealed)
    b += '<span class="badge sealed" title="encrypted or unreadable — content withheld">sealed</span>';
  return b;
}

function render(m) {
  const ts = m.ts ? new Date(m.ts).toLocaleTimeString([], {hour:'2-digit', minute:'2-digit'}) : '';
  const relayed = m.relayed_from ? `<span class="relayed">via ${esc(m.relayed_from)}</span>` : '';
  const text = m.text || m.body || '';
  const who = m.from || m.sender || '?';
  const mine = /^(chris|toxic)$/i.test(who) ? ' mine' : '';
  const bodyHtml = text
    ? `<div class="body">${md(text)}</div>`
    : (m.sealed ? '' : '<div class="body empty">(no content)</div>');
  line(`<div class="meta"><span class="who">${esc(who)}</span>` +
       `<span class="ch">#${esc(m.channel || $('channel').value)}</span>` +
       `${badges(m)}${relayed}<span class="ts">${esc(ts)}</span></div>${bodyHtml}`, 'msg' + mine);
}

async function sendMsg() {
  const el = $('msg');
  const text = el.value.trim();
  if (!text || !running) return;
  const btn = $('send');
  btn.disabled = true; el.disabled = true;
  try {
    const r = await fetch('send', {
      method: 'POST',
      headers: Object.assign(auth(), {'Content-Type': 'application/json'}),
      body: JSON.stringify({ channel: $('channel').value.trim() || 'fleet', text }),
    });
    const d = await r.json().catch(() => ({}));
    if (!r.ok || !d.ok) throw new Error(d.error || ('http ' + r.status));
    el.value = '';
    // the long-poll will render it live; no optimistic duplicate needed
  } catch (e) {
    line('send failed: ' + esc(e.message || e) + ' — retrying is safe', 'sys');
  } finally {
    btn.disabled = false; el.disabled = false; el.focus();
  }
}
$('send').onclick = sendMsg;
$('msg').addEventListener('keydown', e => {
  if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMsg(); }
});

// --- NATS live source ------------------------------------------------
// Minimal NATS-over-WebSocket client: INFO/CONNECT/SUB/MSG/PING/PONG only.
// History still comes from the bounded file snapshot in boot(); this socket
// carries live messages published by the nats-tail daemon. Any failure
// falls back to the long-poll loop -- the file feed stays the fallback.
let natsWs = null;
function natsUrl() {
  return (location.protocol === 'https:' ? 'wss://' : 'ws://') + location.host + '/nats-ws';
}
function natsLive(myGen) {
  if (myGen !== gen || !running) return;
  setState('loading');
  let ws;
  try { ws = new WebSocket(natsUrl()); } catch (e) { return pollFallback(myGen, 'ws blocked'); }
  natsWs = ws;
  let buf = '', fails = 0;
  const sid = 'ui-' + myGen;
  const send = t => { if (ws.readyState === 1) ws.send(t + '\r\n'); };
  const dead = why => {
    try { ws.close(); } catch (e) {}
    if (myGen !== gen || !running) return;
    if (++fails > 3) return pollFallback(myGen, why);
    line('nats hiccup — retrying…', 'sys');
    setTimeout(() => natsLive(myGen), Math.min(5000, 500 * fails));
  };
  ws.onmessage = ev => {
    buf += ev.data;
    let i;
    while ((i = buf.indexOf('\r\n')) >= 0) {
      const ln = buf.slice(0, i); buf = buf.slice(i + 2);
      if (ln.startsWith('INFO')) {
        send('CONNECT {"verbose":false,"pedantic":false,"tls_required":false,'
             + '"auth_token":' + JSON.stringify(token)
             + ',"protocol":1,"echo":true,"name":"squawk-ui"}');
        send('SUB ' + chan() + '.messages ' + sid);
        setState('live', ' · nats');
        fails = 0;
      } else if (ln === 'PING') { send('PONG'); }
      else if (ln.startsWith('MSG ')) {
        // payload is one CRLF-terminated line: json.dumps never emits raw
        // CR/LF inside a JSON string, so line framing is exact here.
        const j = buf.indexOf('\r\n');
        if (j < 0) { buf = ln + '\r\n' + buf; break; } // payload still in flight
        const payload = buf.slice(0, j); buf = buf.slice(j + 2);
        try {
          const m = JSON.parse(payload);
          if ((m.seq || 0) > since) {
            render(m); since = m.seq;
            $('seq').textContent = 'seq ' + since;
          }
        } catch (e) { /* malformed envelope: skip */ }
      } else if (ln.startsWith('-ERR')) { line('nats: ' + esc(ln), 'sys'); }
    }
  };
  ws.onerror = () => dead('ws error');
  ws.onclose = () => { if (natsWs === ws) dead('ws closed'); };
};
function pollFallback(myGen, why) {
  natsWs = null;
  srcMode = 'poll'; paintSrc();
  line('nats unavailable (' + esc(why || '?') + ') — back on long-poll, nothing lost', 'sys');
  setState('reconnecting');
  poll(myGen);
}

async function poll(myGen) {
  if (!running || myGen !== gen) return;
  const t0 = performance.now();
  try {
    const r = await fetch(`wait?since=${since}&channel=${chan()}`, { headers: auth(), signal: AbortSignal.timeout(65000) });
    if (r.status === 401 || r.status === 404) throw new Error('unauthorized');
    const data = await r.json();
    failures = 0;
    if (Array.isArray(data.messages)) {
      // only render messages newer than our cursor (dedup across concurrent wakes)
      const fresh = data.messages.filter(m => (m.seq || 0) > since).sort((a,b) => (a.seq||0) - (b.seq||0));
      fresh.forEach(render);
      if (data.seq > since) since = data.seq;
      // a full batch means the server still has backlog: drain visibly
      const catching = data.messages.length >= BATCH_CAP;
      setState(catching ? 'catching-up' : 'live');
    } else if (data.seq > since) { since = data.seq; setState('live'); }
    else setState('live');
    $('seq').textContent = 'seq ' + since;
    $('lat').textContent = 'wake ' + Math.round(performance.now() - t0) + 'ms';
  } catch (e) {
    failures++;
    setState('reconnecting', failures > 1 ? ` · try ${failures}` : '');
    if (failures === 1) line('feed hiccup — retrying…', 'sys');
    await new Promise(r => setTimeout(r, Math.min(5000, 500 * failures)));
  }
  poll(myGen);
}

// Initial load: one bounded snapshot (the TAIL most recent messages) lands
// us at the live cursor immediately -- no full-history drain, no reload.
async function boot() {
  const myGen = ++gen;
  if (natsWs) { try { natsWs.close(); } catch (e) {} natsWs = null; }
  setState('loading');
  if (!booted) line('tuned in — pulling the latest traffic…', 'sys');
  try {
    const r = await fetch(`wait?since=0&tail=${TAIL}&channel=${chan()}`, { headers: auth(), signal: AbortSignal.timeout(65000) });
    if (r.status === 401 || r.status === 404) throw new Error('unauthorized');
    const data = await r.json();
    if (myGen !== gen) return; // superseded by a channel switch
    if (Array.isArray(data.messages)) {
      data.messages.filter(m => (m.seq || 0) > 0)
                   .sort((a,b) => (a.seq||0) - (b.seq||0))
                   .forEach(render);
      if (data.seq > since) since = data.seq;
      // land at the newest traffic: the snapshot is the tail, so start there
      $('log').scrollTop = $('log').scrollHeight;
    }
    $('seq').textContent = 'seq ' + since;
    setState('live');
    booted = true;
  } catch (e) {
    if (myGen !== gen) return;
    setState('reconnecting');
    await new Promise(r => setTimeout(r, 1500));
    if (running && myGen === gen) return boot();
    return;
  }
  if (srcMode === 'nats') natsLive(myGen); else poll(myGen);
}

$('go').onclick = () => {
  token = $('token').value.trim();
  if (!token) return;
  sessionStorage.setItem('squawk-token', token);
  $('gate').style.display = 'none';
  $('app').style.display = 'flex';
  running = true;
  boot();
};
$('src').onclick = () => {
  srcMode = srcMode === 'nats' ? 'poll' : 'nats';
  paintSrc();
  if (!running || !booted) return;
  $('log').innerHTML = '';
  since = 0; failures = 0;
  line(`live source → ${srcMode} — pulling the latest traffic…`, 'sys');
  boot();
};
paintSrc();
// switching channels re-tunes live: clear, snapshot, resume -- no reload
$('channel').onchange = () => {
  if (!running || !booted) return;
  $('log').innerHTML = '';
  since = 0; failures = 0;
  line(`switched to #${$('channel').value.trim() || 'fleet'} — pulling the latest traffic…`, 'sys');
  boot();
};
if (token) { $('token').value = token; $('go').click(); }
