"""Apply the NATS live-source patch to squawk ui.html.

- Header gets a src toggle button (poll <-> nats).
- ?src=nats selects the NATS live source; default stays long-poll.
- boot(): bounded file snapshot as today, then live messages arrive over
  the NATS websocket (/nats-ws via the funnel). Any WS failure falls back
  to the long-poll loop -- the custom feed is the durable fallback.
- Minimal NATS WS client: INFO/CONNECT/SUB/MSG/PING/PONG. Payloads are
  framed on CRLF lines (json.dumps never emits raw CR/LF inside a string).
"""
import sys

P = "/home/toxic/sovereign/projects/mesh/squawk/ui.html"
s = open(P).read()
assert "/nats-ws" not in s, "already patched"

# 1. header toggle button after the channel input
old = '<input id="channel" value="fleet" size="10" title="channel" aria-label="channel">'
new = (old + '\n  <button id="src" title="live source: click to switch poll/nats" '
       'aria-label="live source">poll</button>')
assert old in s
s = s.replace(old, new, 1)

# 2. srcMode init after the state vars
old = "let since = 0, running = false, failures = 0, booted = false, gen = 0;"
new = old + """
// live source: 'poll' (long-poll, default) or 'nats' (JetStream mirror over websocket).
// ?src=nats selects NATS; the header button toggles at runtime.
let srcMode = 'poll';
try { const qsrc = new URLSearchParams(location.search).get('src');
      if (qsrc === 'nats' || qsrc === 'poll') srcMode = qsrc; } catch (e) {}
function paintSrc() { const b = $('src'); if (b) { b.textContent = srcMode;
  b.title = 'live source: ' + srcMode + ' (click to switch)'; } }"""
assert old in s
s = s.replace(old, new, 1)

# 3. the minimal NATS-over-WebSocket client, before the poll loop
old = "async function poll(myGen) {"
nats_js = r"""// --- NATS live source ------------------------------------------------
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

"""
assert old in s
s = s.replace(old, nats_js + old, 1)

# 4. boot(): close any stale NATS socket, then pick the live source
old = """async function boot() {
  const myGen = ++gen;
  setState('loading');"""
new = """async function boot() {
  const myGen = ++gen;
  if (natsWs) { try { natsWs.close(); } catch (e) {} natsWs = null; }
  setState('loading');"""
assert old in s
s = s.replace(old, new, 1)

# 5. boot(): after the snapshot, go live on the selected source
old = """  poll(myGen);
}

$('go').onclick"""
new = """  if (srcMode === 'nats') natsLive(myGen); else poll(myGen);
}

$('go').onclick"""
assert old in s
s = s.replace(old, new, 1)

# 6. src toggle button behaviour + initial paint
old = """// switching channels re-tunes live: clear, snapshot, resume -- no reload"""
new = """$('src').onclick = () => {
  srcMode = srcMode === 'nats' ? 'poll' : 'nats';
  paintSrc();
  if (!running || !booted) return;
  $('log').innerHTML = '';
  since = 0; failures = 0;
  line(`live source → ${srcMode} — pulling the latest traffic…`, 'sys');
  boot();
};
paintSrc();
// switching channels re-tunes live: clear, snapshot, resume -- no reload"""
assert old in s
s = s.replace(old, new, 1)

open(P, "w").write(s)
print("ui.html NATS patch applied")
