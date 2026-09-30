#!/usr/bin/env python3
"""Vex lane: first-class HTML/CSS in squawk UI + CORS on the feed.

Marker-anchored, idempotent. Runs ON YOTE against
/home/toxic/.worktrees/vex-html/projects/mesh/squawk (== /home/toxic/squawk bind mount).
"""
import sys
from pathlib import Path

BASE = Path("/home/toxic/.worktrees/vex-html/projects/mesh/squawk")

NEW_RENDERER = r'''/* markdown + FIRST-CLASS raw HTML/CSS (Chris 2026-09-21, direct order):
   raw HTML passes through untouched and renders as authored — tags, inline
   styles, <style> and <script> blocks all execute. Markdown constructs still
   render around it. Fenced code blocks stay literal (code is code). */
function mdInline(s) {
  // split into raw HTML tags vs text runs; tags pass through, text gets md
  return String(s).split(/(<[^>]*>)/g).map((p, i) => i % 2 ? p : mdText(p)).join('');
}
function mdText(s) {
  let out = esc(s);
  const codes = [];
  out = out.replace(/`([^`\n]+)`/g, (m, c) => { codes.push(c); return '\u0000' + (codes.length - 1) + '\u0000'; });
  out = out.replace(/\*\*([^*\\n]+)\*\*/g, '<strong>$1</strong>');
  out = out.replace(/(^|[^*\w])\*([^*\\n]+)\*/g, '$1<em>$2</em>');
  out = out.replace(/\[([^\]\n]+)\]\(([^)\s\n]+)\)/g, (m, t, u) =>
    /^https?:\/\//i.test(u) ? `<a href="${u}" target="_blank" rel="noopener noreferrer">${t}</a>` : m);
  return out.replace(/\u0000(\d+)\u0000/g, (m, i) => `<code>${codes[+i]}</code>`);
}
function md(src) {
  const lines = String(src).split('\n');
  let html = '', inCode = false, inRaw = null, list = null, para = [];
  const flushP = () => { if (para.length) { html += '<p>' + para.map(mdInline).join('<br>') + '</p>'; para = []; } };
  const closeL = () => { if (list) { html += '</' + list + '>'; list = null; } };
  const openL = t => { if (list !== t) { closeL(); html += '<' + t + '>'; list = t; } };
  const rawClose = tag => new RegExp('<\\/\\s*' + tag + '\\s*>', 'i');
  for (const ln of lines) {
    if (inRaw) { html += ln + '\n'; if (rawClose(inRaw).test(ln)) inRaw = null; continue; }
    if (/^```/.test(ln)) { flushP(); closeL(); html += inCode ? '</code></pre>' : '<pre><code>'; inCode = !inCode; continue; }
    if (inCode) { html += esc(ln) + '\n'; continue; }
    let m;
    if (m = ln.match(/^\s*<(script|style)[\s>]/i)) {
      flushP(); closeL(); inRaw = m[1].toLowerCase(); html += ln + '\n';
      if (rawClose(inRaw).test(ln)) inRaw = null; continue;
    }
    if (/^\s*<!/.test(ln)) { flushP(); closeL(); html += ln + '\n'; continue; }
    if (/^\s*<(div|table|form|section|article|header|footer|main|nav|aside|figure|figcaption|details|dialog|img|hr|input|button|select|textarea|iframe|video|audio|canvas|svg|h[1-6]|p|pre|ul|ol|li|a|span|b|i|u|s|em|strong|code|blockquote)[\s>/]/i.test(ln)) {
      flushP(); closeL(); html += ln + '\n'; continue;
    }
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
'''


def patch_ui():
    p = BASE / "ui.html"
    t = p.read_text()
    start = t.find("/* tiny markdown renderer:")
    end = t.find("\nfunction badges(m) {")
    assert start != -1 and end != -1 and start < end, "ui.html anchors missing"
    if "FIRST-CLASS raw HTML/CSS" in t[start:end]:
        return "ui.html already patched"
    p.write_text(t[:start] + NEW_RENDERER + t[end:])
    return "ui.html patched"


def patch_feed():
    p = BASE / "squawk_feed.py"
    t = p.read_text()
    if "_send_cors" in t:
        return "squawk_feed.py already patched"
    anchor = ('    def _send_404(self):\n'
              '        # Never reveal the endpoint exists: bare 404, empty body.\n'
              '        self.send_response(404)\n'
              '        self.send_header("Content-Length", "0")\n'
              '        self.end_headers()\n')
    assert t.count(anchor) == 1, "feed _send_404 anchor not unique"
    cors_block = anchor + '''
    # CORS (2026-09-21, Chris's direct order): the feed is fetchable
    # cross-origin under a simple open policy. Auth still via Bearer <redacted>
    # preflight is answered explicitly; actual responses carry ACAO too.
    def _send_cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers",
                         "Authorization, Content-Type")
        self.send_header("Access-Control-Max-Age", "86400")

    def do_OPTIONS(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path.startswith("/squawk-feed/"):
            self.send_response(204)
            self._send_cors()
            self.send_header("Content-Length", "0")
            self.end_headers()
            return
        self._send_404()
'''
    t = t.replace(anchor, cors_block)
    anchor2 = ('    def _send_json(self, code: int, obj: dict):\n'
               '        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")\n'
               '        self.send_response(code)\n'
               '        self.send_header("Content-Type", "application/json")')
    assert t.count(anchor2) == 1, "feed _send_json anchor not unique"
    t = t.replace(anchor2, anchor2.replace(
        "self.send_response(code)",
        "self.send_response(code)\n        self._send_cors()"))
    anchor3 = ('        self.send_response(200)\n'
               '        self.send_header("Content-Type", "text/html; charset=utf-8")')
    assert t.count(anchor3) == 1, "feed _send_ui anchor not unique"
    t = t.replace(anchor3,
                  '        self.send_response(200)\n'
                  '        self._send_cors()\n'
                  '        self.send_header("Content-Type", "text/html; charset=utf-8")')
    anchor4 = ('        self.send_response(404)\n'
               '        self.send_header("Content-Length", "0")\n'
               '        self.end_headers()\n'
               '\n'
               '    # CORS')
    assert t.count(anchor4) == 1, "feed _send_404+cors anchor not unique"
    t = t.replace(anchor4,
                  '        self.send_response(404)\n'
                  '        self._send_cors()\n'
                  '        self.send_header("Content-Length", "0")\n'
                  '        self.end_headers()\n'
                  '\n'
                  '    # CORS')
    p.write_text(t)
    return "squawk_feed.py patched"


def patch_tests():
    p = BASE / "tests" / "test_squawk_feed.py"
    t = p.read_text()
    if "test_html_body_served_verbatim" in t:
        return "tests already patched"
    anchor = ("        self.assertEqual(text, body)\n"
              "        self.assertGreater(len(text), 500)\n")
    assert t.count(anchor) == 1, "test anchor not unique"
    new_tests = anchor + '''
    def test_html_body_served_verbatim(self):
        # Chris 2026-09-21: HTML/CSS is first-class -- bodies carrying tags,
        # inline styles, style/script blocks survive end to end byte-identical
        # (rendering happens client-side in ui.html).
        port = self._serve()
        base = self._high(port)
        body = ("<div style=\\"color:red\\">hi</div>\\n"
                "<style>.x{color:blue}</style>\\n"
                "<script>window.__vex_html=1</script>")
        self._post(body)
        _status, obj = _get(port, "/squawk-feed/wait?since=%d" % base,
                            token=TOKEN)
        self.assertEqual(obj["messages"][-1]["body"], body)

    def test_cors_preflight_and_headers(self):
        # Chris 2026-09-21: the feed is fetchable cross-origin.
        port = self._serve()
        req = urllib.request.Request(
            "http://127.0.0.1:%d/squawk-feed/send" % port, method="OPTIONS")
        req.add_header("Origin", "https://example.com")
        req.add_header("Access-Control-Request-Method", "POST")
        req.add_header("Access-Control-Request-Headers",
                       "Authorization, Content-Type")
        with urllib.request.urlopen(req, timeout=10) as r:
            self.assertEqual(r.status, 204)
            self.assertEqual(r.headers.get("Access-Control-Allow-Origin"), "*")
            self.assertIn("POST",
                          r.headers.get("Access-Control-Allow-Methods"))
            allow_h = r.headers.get("Access-Control-Allow-Headers") or ""
            self.assertIn("Authorization", allow_h)
        # actual responses carry ACAO too
        req = urllib.request.Request(
            "http://127.0.0.1:%d/squawk-feed/seq?channel=fleet" % port)
        req.add_header("Origin", "https://example.com")
        with urllib.request.urlopen(req, timeout=10) as r:
            self.assertEqual(r.status, 200)
            self.assertEqual(r.headers.get("Access-Control-Allow-Origin"), "*")
'''
    t = t.replace(anchor, new_tests)
    p.write_text(t)
    return "tests patched"


def main():
    for fn in (patch_ui, patch_feed, patch_tests):
        print(fn(), flush=True)


if __name__ == "__main__":
    main()
