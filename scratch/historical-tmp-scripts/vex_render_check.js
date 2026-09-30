// Vex lane: renderer proof — extract md()/mdInline()/mdText()/esc from the
// SERVED ui.html on yote and assert first-class HTML + intact markdown.
const fs = require('fs');
const html = fs.readFileSync('/home/toxic/sovereign/projects/mesh/squawk/ui.html', 'utf8');
const start = html.indexOf('const esc =');
const end = html.indexOf('\nfunction badges(m) {');
if (start === -1 || end === -1 || start >= end) { console.error('EXTRACTION FAILED'); process.exit(2); }
const src = html.slice(start, end);
if (!src.includes('FIRST-CLASS raw HTML/CSS')) { console.error('NOT THE NEW RENDERER'); process.exit(2); }
eval(src);
let pass = 0, fail = 0;
const t = (name, cond, detail) => {
  if (cond) { pass++; console.log('ok  -', name); }
  else { fail++; console.log('FAIL-', name, detail || ''); }
};
t('b tag passthrough', md('<b>bold</b>').includes('<b>bold</b>'));
t('b tag not escaped', !md('<b>bold</b>').includes('&lt;b&gt;'));
t('inline style passthrough', md('<div style="color:red">x</div>').includes('style="color:red"'));
t('style block passthrough', md('<style>.a{color:red}</style>').includes('<style>.a{color:red}</style>'));
const scr = md('<script>\nwindow.__vex=1;\n</script>');
t('script block multiline passthrough', scr.includes('<script>') && scr.includes('window.__vex=1;') && scr.includes('</script>'));
t('script not escaped', !scr.includes('&lt;script'));
t('img passthrough', md('<img src="x.png">').includes('<img src="x.png">'));
t('md bold + html mix', (() => { const o = md('**b** and <i>i</i>'); return o.includes('<strong>b</strong>') && o.includes('<i>i</i>'); })());
t('heading', md('# hi').includes('<h1>hi</h1>'));
t('blockquote', md('> q').includes('<blockquote>q</blockquote>'));
t('ul', md('- a\n- b').includes('<ul>') && md('- a\n- b').includes('<li>a</li>'));
t('inline code', md('`c`').includes('<code>c</code>'));
t('fenced code stays literal', md('```\n<b>x</b>\n```').includes('&lt;b&gt;'));
t('https link', md('[t](https://example.com)').includes('<a href="https://example.com"'));
t('javascript: link inert', !md('[t](javascript:alert(1))').includes('<a href'));
t('600-char body untruncated', md('y'.repeat(600)).includes('y'.repeat(600)));
t('300-char unbroken string', md('x'.repeat(300)).includes('x'.repeat(300)));
t('two paragraphs', (md('p1\n\np2').match(/<p>/g) || []).length === 2);
t('list item html', md('- <b>x</b>').includes('<li><b>x</b></li>'));
console.log(`\n${pass} passed, ${fail} failed`);
process.exit(fail ? 1 : 0);
