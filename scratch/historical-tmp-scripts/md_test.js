const esc = s => String(s).replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
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
var NL = String.fromCharCode(10), BT = String.fromCharCode(96), BT3 = BT+BT+BT;
var R = [];
function t(n, c) { R.push((c ? "PASS " : "FAIL ") + n); }
t("para", md("hello world") === "<p>hello world</p>");
t("two-paras", md("a"+NL+NL+"b") === "<p>a</p><p>b</p>");
t("h1", md("# T") === "<h1>T</h1>");
t("h2", md("## T") === "<h2>T</h2>");
t("ul", md("- a"+NL+"- b") === "<ul><li>a</li><li>b</li></ul>");
t("ol", md("1. a"+NL+"2. b") === "<ol><li>a</li><li>b</li></ol>");
t("link", md("[x](https://example.com)") === "<p><a href=\"https://example.com\" target=\"_blank\" rel=\"noopener noreferrer\">x</a></p>");
t("link-js-inert", md("[x](javascript:alert(1))").indexOf("<a") === -1);
t("quote", md("> q") === "<blockquote>q</blockquote>");
t("inline", md("**b** and *i* and "+BT+"c"+BT) === "<p><strong>b</strong> and <em>i</em> and <code>c</code></p>");
t("bold-in-heading", md("# **T**") === "<h1><strong>T</strong></h1>");
var fz = md(BT3+NL+"code <b>x</b>"+NL+BT3);
t("fenced", fz.indexOf("<pre><code>") === 0 && fz.indexOf("&lt;b&gt;") > -1 && fz.indexOf("<b>") === -1);
var xs = md("<script>alert(1)</script>");
t("xss-script", xs.indexOf("<script>") === -1 && xs.indexOf("&lt;script&gt;") > -1);
t("xss-img", md("<img src=x onerror=alert(1)>").indexOf("<img") === -1);
var lg = md("y".repeat(600));
t("long-600", lg.length > 600 && lg.indexOf("y".repeat(600)) > -1);
t("unbroken-300", md("z".repeat(300)).indexOf("z".repeat(300)) > -1);
R.forEach(function(r){ console.log(r); });
if (R.some(function(r){ return r.indexOf("FAIL") === 0; })) process.exit(1);
