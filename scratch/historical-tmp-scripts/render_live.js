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
var body = "# Lumen markdown lane proof\n\nThis body is deliberately longer than five hundred characters so the old server cut would have eaten it. This body is deliberately longer than five hundred characters so the old server cut would have eaten it. This body is deliberately longer than five hundred characters so the old server cut would have eaten it. This body is deliberately longer than five hundred characters so the old server cut would have eaten it. This body is deliberately longer than five hundred characters so the old server cut would have eaten it. This body is deliberately longer than five hundred characters so the old server cut would have eaten it. \n## Features\n\n- bullet one\n- bullet two with **bold** and *italic* and `inline code`\n\n1. first ordered\n2. second ordered\n\n> a blockquote from the lane\n> second line\n\n[a link](https://example.com) and a raw <b>html tag</b> that must stay inert\n\n```\nfenced code block\nwith <script>not rendered</script> inside\n```\n\nunbroken: zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz";
console.log(md(body).slice(0, 900));