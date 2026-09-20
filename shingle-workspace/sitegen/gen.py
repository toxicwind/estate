#!/usr/bin/env python3
"""gen.py - generate the GitHub Pages site (docs/) for toxicwind/nvidia-nim-model-probe.
Reproducible from local probe data. Run: python3 gen.py  (writes docs/ next to this file)
"""
import json, os, re, html, sys
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = "/home/hatch/workspace/skills/nvidia-nim-loader"
OUT = os.path.join(HERE, "docs")
DATE = "2026-09-14"
REPO = "https://github.com/toxicwind/nvidia-nim-model-probe"
RAW = "https://raw.githubusercontent.com/toxicwind/nvidia-nim-model-probe/main"

# ---------- load ----------
def load(name):
    with open(os.path.join(DATA, name)) as f:
        return json.load(f)

probe_raw = load("probe_results_all_2026-09-14.json")
PROBE = probe_raw if isinstance(probe_raw, list) else probe_raw.get("results", [])
FUZZ = load("fuzz_max_2026-09-14.json")
TOOLUSE = load("tooluse_probe_2026-09-14.json")
XREF = load("card_xref_2026-09-14.json")

# ---------- sanitize ----------
UUID_RE = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}")
def sanitize(s):
    s = UUID_RE.sub("REDACTED", s)
    assert "nvapi-" not in s, "RAW API KEY MATERIAL DETECTED - aborting"
    return s

def esc(s):
    return html.escape("" if s is None else str(s), quote=True)

# ---------- verdicts ----------
VERDICTS = ["alive-fast", "timeout-fast", "streaming-noheaders",
            "unavailable-503", "error-other", "dead-404-gated"]
VCOLOR = {
    "alive-fast": "#34d399", "timeout-fast": "#fbbf24",
    "streaming-noheaders": "#fb923c", "unavailable-503": "#fb7185",
    "error-other": "#ef4444", "dead-404-gated": "#ef4444",
}
VLABEL = {
    "alive-fast": "alive", "timeout-fast": "timeout",
    "streaming-noheaders": "stream stall", "unavailable-503": "503",
    "error-other": "error", "dead-404-gated": "gated 404",
}

# ---------- categories (first match wins, explicit sets) ----------
def category(mid):
    m = mid.lower()
    if "nemotron-3" in m: return "nemotron-3"
    if any(k in m for k in ("guard", "safety", "nemoguard")): return "guard/safety"
    if any(k in m for k in ("embed", "arctic", "nvclip", "retriever")): return "embedding/retrieval"
    if "reward" in m: return "reward"
    if any(k in m for k in ("-vision", "vila", "neva", "/fuyu")): return "vision"
    if any(k in m for k in ("ising", "synthetic-video", "riva-translate",
                            "nemotron-parse", "diffusiongemma", "cosmos-reason")): return "oddball"
    legacy_kw = ("yi-large", "sea-lion", "starcoder", "dbrx", "codegemma",
                 "gemma-2b", "recurrentgemma", "granite", "codellama",
                 "llama2-70b", "phi-3.5", "mistral-nemo", "mistral-7b",
                 "mistral-large", "mixtral", "codestral", "nemotron-4",
                 "llama3-chatqa", "nemotron-51b", "nemotron-70b",
                 "nemotron-ultra-253b", "nemotron-nano-3", "palmyra",
                 "zamba", "gemma-3-", "deplot", "kosmos-2")
    if any(k in m for k in legacy_kw): return "legacy"
    return "chat"

for r in PROBE:
    r["category"] = category(r["model"])

CATS = ["chat", "nemotron-3", "legacy", "embedding/retrieval", "vision",
        "guard/safety", "reward", "oddball"]

# ---------- shared html ----------
NAV = [("index.html", "Overview"), ("models.html", "Models"),
       ("tooluse.html", "Tool Use"), ("fuzz.html", "Fuzz Matrix"),
       ("cards.html", "Model Cards"), ("methodology.html", "Methodology")]

def base(title, active, body):
    links = "".join(
        f'<a href="{p}" class="{"on" if p == active else ""}">{t}</a>'
        for p, t in NAV)
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)} — NIM probe</title>
<link rel="stylesheet" href="assets/style.css"></head>
<body>
<header class="top"><div class="wrap">
<div class="brand"><span class="dot"></span> nvidia-nim-model-probe <span class="dim">/ {esc(DATE)}</span></div>
<nav>{links}<a href="{REPO}" class="repo">GitHub ↗</a></nav>
</div></header>
<main class="wrap">
{body}
</main>
<footer class="wrap dim small">Fail-fast probe of NVIDIA NIM's hosted API · {esc(DATE)} ·
<a href="{RAW}/data/probe_results_all_2026-09-14.json">raw sweep JSON</a> ·
<a href="{REPO}">repo</a></footer>
<script src="assets/app.js"></script>
</body></html>"""

def badge(v):
    return (f'<span class="badge" style="--c:{VCOLOR.get(v,"#9ca3af")}">'
            f'{esc(VLABEL.get(v, v))}</span>')

def svg_bars(items, width=560, bar_h=22):
    """items: [(label, value, color)] -> inline svg horizontal bars"""
    mx = max(v for _, v, _ in items) or 1
    h = len(items) * (bar_h + 8) + 6
    rows = []
    for i, (lab, val, col) in enumerate(items):
        y = i * (bar_h + 8) + 4
        w = max(2, width * val / mx * 0.72)
        rows.append(
            f'<text x="0" y="{y+15}" class="sl">{esc(lab)}</text>'
            f'<rect x="{width*0.28:.0f}" y="{y}" width="{w:.0f}" height="{bar_h}" '
            f'fill="{col}" rx="3"/>'
            f'<text x="{width*0.28 + w + 8:.0f}" y="{y+15}" class="sv">{val}</text>')
    return (f'<svg class="bars" viewBox="0 0 {width} {h}" width="100%" '
            f'role="img">{"".join(rows)}</svg>')

# ================= INDEX =================
def gen_index():
    vc = Counter(r["verdict"] for r in PROBE)
    n = len(PROBE)
    native = [t for t in TOOLUSE if t["mode"] == "native"]
    # category x verdict matrix
    mx = defaultdict(Counter)
    for r in PROBE:
        mx[r["category"]][r["verdict"]] += 1
    cats_present = [c for c in CATS if sum(mx[c].values())]
    thead = "".join(f"<th>{esc(VLABEL[v])}</th>" for v in VERDICTS) + "<th>total</th>"
    trows = ""
    for c in cats_present:
        cells = "".join(
            f'<td class="num {"hot" if mx[c][v] else ""}">{mx[c][v] or ""}</td>'
            for v in VERDICTS)
        trows += (f'<tr><td class="cat">{esc(c)}</td>{cells}'
                  f'<td class="num tot">{sum(mx[c].values())}</td></tr>')

    bars = svg_bars([(VLABEL[v], vc[v], VCOLOR[v]) for v in VERDICTS])

    # top usable cards
    usable_order = ["nvidia/nemotron-3-super-120b-a12b", "openai/gpt-oss-20b",
                    "z-ai/glm-5.3-flash", "meta/llama-3.2-11b-vision-instruct",
                    "google/diffusiongemma-26b-a4b-it",
                    "deepseek-ai/deepseek-v4-flash-0731",
                    "nvidia/nemotron-3-ultra-550b-a55b"]
    tmap = {t["model"]: t for t in TOOLUSE}
    cards = ""
    for m in usable_order:
        t = tmap[m]
        mode = t["mode"]
        star = " ⚠ empty response" if mode == "empty" else ""
        ttft = f'{t["ttft_s"]:.2f}s' if t["ttft_s"] else "—"
        cards += (f'<div class="mcard"><div class="mname">{esc(m)}</div>'
                  f'<div class="mrow"><span class="badge" style="--c:'
                  f'{"#34d399" if mode=="native" else "#fbbf24"}">'
                  f'{esc(mode)}</span><span class="dim">TTFT {ttft}</span></div>'
                  f'<div class="dim small">{esc((t.get("text_head") or "")[:110])}'
                  f'{star}</div></div>')

    body = f"""
<section class="hero">
<h1>NVIDIA NIM: the catalog is an unreliable narrator</h1>
<p class="lede">A fail-fast, no-retries probe of every model in NVIDIA's hosted
inference catalog — what <span class="mono">/v1/models</span> claims vs what actually answers.
<strong>{n} models probed</strong>, <strong>{vc["alive-fast"]} answer a ping</strong>,
<strong>{len(native)} do native tool calls</strong>.</p>
<div class="statgrid">
<div class="stat"><b>{n}</b><span>models probed</span></div>
<div class="stat"><b>{vc["alive-fast"]}</b><span>ping alive</span></div>
<div class="stat"><b>{len(native)}</b><span>native tool calls</span></div>
<div class="stat"><b>{vc["dead-404-gated"]}</b><span>gated 404</span></div>
<div class="stat"><b>{vc["timeout-fast"]}</b><span>timeouts</span></div>
<div class="stat"><b>{FUZZ["catalog_n"]}</b><span>models in live catalog</span></div>
</div></section>

<section><h2>Verdict distribution</h2>{bars}
<p class="dim small">Fail-fast ladder: ping first (5s ceiling), then one streaming
request. No retries — a model's first honest answer is the data.</p></section>

<section><h2>Category × verdict</h2>
<div class="tscroll"><table class="matrix"><thead><tr><th></th>{thead}</tr></thead>
<tbody>{trows}</tbody></table></div>
<p class="dim small">The catalog is modality-blind: embeddings, guards, vision, reward
and translation models all sit in the same flat list. Only probing reveals which
ids are chat-capable.</p></section>

<section><h2>Usable models <span class="dim small">— native tool calls, ranked by TTFT</span></h2>
<div class="mgrid">{cards}</div>
<p><a href="tooluse.html">Full tool-use audit →</a></p></section>

<section><h2>Key findings</h2>
<ul class="findings">
<li><b>The catalog endpoint is public.</b> <span class="mono">GET /v1/models</span>
with no bearer — or a wrong one — returns 200 with the full list. Per-model gating
happens at inference time, not at listing.</li>
<li><b>Availability flaps.</b> super-120b went alive → 503 → alive with native tools
across runs; ultra-550b went timeout → alive; deepseek-v4-pro went alive → timeout →
<strong>delisted from the catalog entirely</strong> (82 → 81 models in ~10 min).</li>
<li><b>Deprecation lives in headers, not docs.</b> super-120b serves
<span class="mono">deprecation: 2026-10-03T09:00:00Z</span>; its model card says nothing.</li>
<li><b>The "physics model" is a VLM.</b> <span class="mono">nvidia/ising-calibration-1.5-31b</span>
is a Gemma-4-based vision model for quantum calibration plots. Weird name, normal chat endpoint.</li>
<li><b>Malformed JSON → 500.</b> The Go gateway leaks struct internals
(<span class="mono">openAIRequestBody.Model</span>) instead of returning 400.</li>
<li><b>No rate limiting observed.</b> 20 parallel requests: zero 429s.</li>
<li><b>Embedding models output "Floats".</b> Card-admitted — yet they sit in the chat
catalog and 404 on chat completions. <a href="cards.html">Card audit →</a></li>
</ul></section>

<section><h2>Data</h2>
<ul class="datalinks">
<li><a href="{RAW}/data/probe_results_all_2026-09-14.json">probe_results_all_2026-09-14.json</a> — 82-model sweep</li>
<li><a href="{RAW}/data/fuzz_max_2026-09-14.json">fuzz_max_2026-09-14.json</a> — 187-case fuzz matrix</li>
<li><a href="{RAW}/data/tooluse_probe_2026-09-14.json">tooluse_probe_2026-09-14.json</a> — 10-model tool-use audit</li>
<li><a href="{RAW}/data/card_xref_2026-09-14.json">card_xref_2026-09-14.json</a> — 51 model cards × verdicts</li>
</ul>
<p class="dim small">Account IDs and request UUIDs redacted. Probe scripts:
<span class="mono">probe.py</span>, <span class="mono">fuzz_max.py</span>,
<span class="mono">tooluse_probe.py</span> in the repo.</p></section>
"""
    return base("Overview", "index.html", body)

# ================= MODELS =================
def phase_txt(ph):
    if not ph: return ""
    h = ph.get("headers") or {}
    hh = "".join(f"<div><span class=hk>{esc(k)}:</span> <span class=mono>{esc(v)[:90]}</span></div>"
                 for k, v in h.items())
    det = esc((ph.get("detail") or "")[:900])
    return (f'<div class="ph"><b>phase</b> status={ph.get("status")} '
            f'lat={ph.get("lat_ms")}ms ttfb={ph.get("ttfb_ms")}ms'
            + (f' ttft={ph.get("ttft_ms")}ms' if ph.get("ttft_ms") else "") +
            f'<div class="detail mono">{det}</div>{hh}</div>')

def gen_models():
    rows = ""
    for r in sorted(PROBE, key=lambda x: (VERDICTS.index(x["verdict"]), x["model"])):
        mid = r["model"]
        anchor = mid.replace("/", "__")
        pa = r.get("phase_a", {})
        pb = r.get("phase_b")
        ttft = pb.get("ttft_ms") if pb and pb.get("ttft_ms") else "—"
        card = next((c for c in XREF if c["model"] == mid), None)
        card_html = ""
        if card:
            card_html = (f'<div class="carddesc"><b>card:</b> {esc(card["desc"])}'
                         f'<br><span class=dim>card input: {esc(card["card_input"])} · '
                         f'output: {esc(card["card_output"])}</span></div>')
        rows += f"""
<tr class="mrow" id="row-{esc(anchor)}" data-v="{esc(r["verdict"])}"
    data-c="{esc(r["category"])}" data-m="{esc(mid.lower())}">
<td class="mono mid"><a href="#model={esc(anchor)}" class="anchor">#</a> {esc(mid)}</td>
<td>{esc(r["category"])}</td><td>{badge(r["verdict"])}</td>
<td class="num">{pa.get("lat_ms")}</td><td class="num">{ttft}</td>
<td class="exp">▸</td></tr>
<tr class="detail-row" data-for="{esc(anchor)}" hidden>
<td colspan="6"><div class="deep">
<a id="model-{esc(anchor)}"></a>
{phase_txt(pa)}{phase_txt(pb)}{card_html}
</div></td></tr>"""
    body = f"""
<h1>All {len(PROBE)} models</h1>
<div class="controls">
<input id="q" type="search" placeholder="search models… (e.g. nemotron, vision)">
<select id="fv"><option value="">all verdicts</option>
{''.join(f'<option value="{v}">{esc(VLABEL[v])}</option>' for v in VERDICTS)}</select>
<select id="fc"><option value="">all categories</option>
{''.join(f'<option>{esc(c)}</option>' for c in CATS)}</select>
<span class="dim small" id="count"></span></div>
<div class="tscroll"><table class="models" id="mtable">
<thead><tr><th data-s="m">model ⇅</th><th data-s="c">category ⇅</th>
<th data-s="v">verdict ⇅</th><th data-s="a" class="num">ping ms ⇅</th>
<th data-s="t" class="num">TTFT ms ⇅</th><th></th></tr></thead>
<tbody>{rows}</tbody></table></div>
<p class="dim small">Click a row for the deep dive: phase-A/B timing, headers
(redacted), error detail, and the model card's own description. Deep links:
<span class="mono">#model=&lt;org&gt;__&lt;name&gt;</span></p>
"""
    return base("Models", "models.html", body)

# ================= TOOLUSE =================
def gen_tooluse():
    items = sorted([t for t in TOOLUSE],
                   key=lambda t: (t["ttft_s"] is None, t["ttft_s"] or 0))
    native = [t for t in TOOLUSE if t["mode"] == "native"]
    bars = svg_bars(
        [(t["model"].split("/")[-1][:34],
          round(t["ttft_s"], 2) if t["ttft_s"] else 0,
          "#34d399" if t["mode"] == "native" else ("#fbbf24" if t["mode"] == "empty" else "#ef4444"))
         for t in items if t["ttft_s"]],
        width=640)
    cards = ""
    for t in items:
        m, mode = t["model"], t["mode"]
        col = {"native": "#34d399", "empty": "#fbbf24"}.get(mode, "#ef4444")
        ttft = f'{t["ttft_s"]:.2f}s' if t["ttft_s"] else "no response"
        tot = f'{t["total_s"]:.1f}s' if t["total_s"] else "—"
        snip = esc((t.get("text_head") or "")[:220])
        note = ""
        if mode == "empty":
            note = ("<p class=warn>Answered the ping fine, but this request returned "
                    "zero text and zero tool calls — the weirdest result in the audit.</p>")
        if mode.startswith("error"):
            note = ("<p class=warn>No usable output in 30s. Same models also timed out "
                    "in the 82-model sweep — consistently unreachable, not flapping.</p>")
        if m == "deepseek-ai/deepseek-v4-flash-0731":
            note = ("<p class=warn>Streaming stalled before headers in the sweep; given "
                    "15s here it emits native tool calls. Slow but real.</p>")
        cards += f"""
<div class="tcard"><div class="mname mono">{esc(m)}</div>
<div class="mrow"><span class="badge" style="--c:{col}">{esc(mode)}</span>
<span class="dim">TTFT {ttft} · total {tot} · native calls {t.get("native_calls",0)}</span></div>
{f'<div class="snip mono">“{snip}…”</div>' if snip else ""}{note}</div>"""
    body = f"""
<h1>Tool-use audit</h1>
<p class="lede">One streaming tool-call request per model, in parallel — can it emit a
<strong>native</strong> function call, a textual pseudo-call, or nothing at all?
<strong>{len(native)} of {len(TOOLUSE)} do native tool calls.</strong></p>
<h2>Time to first token (tool request)</h2>{bars}
<div class="tgrid">{cards}</div>
<h2>What "usable" means here</h2>
<ul class="findings">
<li><b>native</b> — the model returned a real <span class="mono">tool_calls</span> block
with callable arguments. This is the only mode that counts for agentic work.</li>
<li><b>empty</b> — HTTP 200, stream opened, but zero text and zero calls.
ultra-550b did this: reachable, unresponsive to the task.</li>
<li><b>error</b> — nothing usable inside the timeout window.</li>
<li>Only ~4 of the 7 native models are plausible general chat models; the rest are
guards, translators, vision, diffusion and parsing specialists that happen to speak tools.</li>
</ul>"""
    return base("Tool Use", "tooluse.html", body)

# ================= FUZZ =================
def status_cell(s):
    col = {200: "#34d399", 400: "#fbbf24", 401: "#fbbf24", 403: "#fbbf24",
           404: "#6b7280", 405: "#60a5fa", 410: "#9ca3af", 429: "#f59e0b",
           500: "#ef4444", 503: "#fb7185"}.get(s, "#9ca3af")
    return f'<span class="st" style="--c:{col}">{esc(s)}</span>'

def gen_fuzz():
    cases = FUZZ["cases"]
    by = defaultdict(list)
    for c in cases:
        by[c["section"]].append(c)

    # discovery
    disc = "".join(
        f'<tr><td class="mono">{esc(c["method"])} {esc(c["path"])}</td>'
        f'<td>{status_cell(c["status"])}</td><td class="num">{c["ms"]}</td>'
        f'<td class="mono small">{esc((c["body"] or "")[:120])}</td></tr>'
        for c in sorted(by["discovery"], key=lambda x: x["path"]))

    # method matrix: rows=method, cols=path
    paths = ["/v1/models", "/v1/chat/completions"]
    methods = ["HEAD", "OPTIONS", "GET", "POST", "PUT", "DELETE", "PATCH"]
    mlook = {(c["method"], c["path"]): c["status"] for c in by["methods"]}
    mrows = "".join(
        f'<tr><td class="mono">{m}</td>' + "".join(
            f"<td>{status_cell(mlook.get((m, p), '?'))}</td>" for p in paths) + "</tr>"
        for m in methods)

    # auth edges
    auth = "".join(
        f'<tr><td class="mono">{esc(c["name"])}</td>'
        f'<td class="mono">{esc(c["method"])} {esc(c["path"])}</td>'
        f'<td>{status_cell(c["status"])}</td>'
        f'<td class="mono small">{esc((c["body"] or "")[:140])}</td></tr>'
        for c in by["auth"])

    # capability matrix: chat cases grouped by param tag
    tag2model = {}
    for t in TOOLUSE:
        tag2model[t["model"].split("/")[-1][:18]] = t["model"]
    # also map sweep models
    for r in PROBE:
        tag2model.setdefault(r["model"].split("/")[-1][:18], r["model"])
    chat = by["chat"]
    params, models_seen, grid = [], [], {}
    for c in chat:
        nm = c["name"]
        # name is "<tag> <param>"
        tag = next((tg for tg in tag2model if nm.startswith(tg)), None)
        if not tag:
            continue
        param = nm[len(tag):].strip()
        models_seen.append(tag2model[tag])
        if param not in params:
            params.append(param)
        grid[(param, tag2model[tag])] = c
    models_seen = sorted(set(models_seen))
    chead = "".join(f"<th class='mono'>{esc(m.split('/')[-1][:22])}</th>"
                    for m in models_seen)
    crows = ""
    for p in params:
        cells = ""
        for m in models_seen:
            c = grid.get((p, m))
            cells += f"<td>{status_cell(c['status']) if c else ''}</td>" if c else "<td></td>"
        crows += f'<tr><td class="mono">{esc(p)}</td>{cells}</tr>'

    # error gallery
    def find(sec, namefrag):
        return next((c for c in by[sec] if namefrag in c["name"]), None)
    gal = []
    for sec, frag, cap in [
        ("chat", "super-1 bad-json", "Malformed JSON → 500, not 400"),
        ("chat", "super-1 model-as-number", "Wrong type → 500 with Go internals"),
        ("chat", "super-1 n=2", "n=2 rejected — validator A"),
        ("chat", "gpt-oss-20b n=2", "n=2 rejected — validator B (different backend)"),
        ("chat", "super-1 parallel_tools=false", "parallel_tool_calls=false → 500"),
        ("family", "vision+image_url", "Vision model + image → actually decodes it"),
        ("family", "text-model+image_url", "Text model + image → 200, image ignored"),
        ("family", "images/generations", "Images route EXISTS (400, not 404)"),
        ("family", "EOL", "nv-embed-v1 → 410 with EOL date"),
    ]:
        c = find(sec, frag)
        if c:
            gal.append((cap, c))
    gal_html = "".join(
        f'<div class="gcard"><b>{esc(cap)}</b> '
        f'<span class="mono dim">{esc(c["method"])} {esc(c["path"])}</span> '
        f'{status_cell(c["status"])}'
        f'<pre class="mono">{esc((c["body"] or "")[:420])}</pre></div>'
        for cap, c in gal)

    burst = [c for c in by["ratelimit"]]
    n429 = sum(1 for c in burst if c["status"] == 429)

    body = f"""
<h1>Fuzz matrix</h1>
<p class="lede"><strong>{len(cases)} cases</strong> in 19.2s, 5s per-request ceiling,
8 workers. Discovery routes, method matrix, per-model oracle, family endpoints,
chat capability matrix, auth edges, and a bounded rate-limit burst.</p>

<h2>Discovery</h2>
<div class="tscroll"><table><thead><tr><th>route</th><th>status</th><th>ms</th><th>body</th></tr></thead>
<tbody>{disc}</tbody></table></div>
<p class="dim small"><span class="mono">/health</span> returns 200 — undocumented.
No public OpenAPI/Swagger document exists.</p>

<h2>Method matrix</h2>
<div class="tscroll"><table class="matrix"><thead><tr><th></th>
<th class="mono">/v1/models</th><th class="mono">/v1/chat/completions</th></tr></thead>
<tbody>{mrows}</tbody></table></div>
<p class="dim small">405 = route exists, verb wrong — the cheapest existence oracle.
<span class="mono">GET /v1/chat/completions</span> 405s, confirming the route is real.</p>

<h2>Auth edges</h2>
<div class="tscroll"><table><thead><tr><th>case</th><th>request</th><th>status</th><th>body</th></tr></thead>
<tbody>{auth}</tbody></table></div>
<p class="warnline"><b>Finding:</b> <span class="mono">GET /v1/models</span> needs no auth —
no bearer or a wrong bearer both return 200 with the full catalog. Gating happens
per-model at inference, never at listing.</p>

<h2>Chat capability matrix</h2>
<div class="tscroll"><table class="matrix cap"><thead><tr><th>parameter</th>{chead}</tr></thead>
<tbody>{crows}</tbody></table></div>

<h2>Rate-limit burst</h2>
<p>{len(burst)} parallel <span class="mono">GET /v1/models</span> →
<strong>{n429} × 429</strong>. No rate limiting observed at this level; no
<span class="mono">Retry-After</span> headers seen.</p>

<h2>Error-shape gallery</h2>
<div class="ggrid">{gal_html}</div>
"""
    return base("Fuzz Matrix", "fuzz.html", body)

# ================= CARDS =================
def gen_cards():
    vmap = {r["model"]: r["verdict"] for r in PROBE}
    have = {c["model"] for c in XREF}
    missing = sorted(set(vmap) - have)
    rows = ""
    for c in sorted(XREF, key=lambda x: x["model"]):
        v = vmap.get(c["model"], "?")
        rows += (f'<tr><td class="mono">{esc(c["model"])}</td><td>{badge(v)}</td>'
                 f'<td>{esc(c["card_input"])}</td><td>{esc(c["card_output"])}</td>'
                 f'<td class="small">{esc(c["desc"][:150])}</td></tr>')
    miss = "".join(
        f'<tr><td class="mono">{esc(m)}</td><td>{badge(vmap[m])}</td></tr>'
        for m in missing)
    body = f"""
<h1>Model-card audit</h1>
<p class="lede">Every <span class="mono">build.nvidia.com</span> model page carries
<span class="mono">&lt;link rel="alternate" type="text/markdown"&gt;</span> — a fetchable
card. <strong>{len(XREF)} of {len(vmap)} catalog models have one</strong>;
{len(missing)} have no public card at all.</p>

<h2>What the cards prove</h2>
<ul class="findings">
<li><b>The catalog is modality-blind.</b> <span class="mono">nemotron-3-embed-1b</span>'s
card says its output is <i>"Floats"</i>; nvclip outputs a <i>"Float tensor"</i>; the omni
model takes <i>Video, Audio, Image, Text</i> — yet all sit in the chat catalog and 404 on
chat completions. The API never declares which ids are chat-capable. Only probing does.</li>
<li><b>The "physics model" is a VLM.</b> <span class="mono">nvidia/ising-calibration-1.5-31b</span>
is a dense multimodal vision-language model built on Gemma 4 31B for quantum calibration
plot analysis — Text+Image in, structured text out. Weird name, normal chat endpoint.
It timed out in the sweep (cold), not dead.</li>
<li><b>Deprecation lives in headers, not cards.</b> super-120b serves
<span class="mono">deprecation: 2026-10-03T09:00:00Z</span>; its card says nothing about
retirement. Cards are marketing-fresh; headers are ops-fresh.</li>
<li><b>Coverage is a subset.</b> Guards, translators, legacy models — 30 ids have no card
page. The website is an unreliable narrator in the other direction.</li>
</ul>

<h2>Card × probe cross-reference</h2>
<div class="tscroll"><table><thead><tr><th>model</th><th>verdict</th>
<th>card input</th><th>card output</th><th>card description</th></tr></thead>
<tbody>{rows}</tbody></table></div>

<h2>{len(missing)} models with no public card</h2>
<div class="tscroll"><table><thead><tr><th>model</th><th>verdict</th></tr></thead>
<tbody>{miss}</tbody></table></div>
"""
    return base("Model Cards", "cards.html", body)

# ================= METHODOLOGY =================
def gen_methodology():
    body = """
<h1>Methodology — read this before trusting the data</h1>
<p class="lede">This page exists because the numbers above are only as honest as the
method that produced them. Everything here was probed, not scraped.</p>

<h2>The fail-fast ladder (as designed)</h2>
<ol class="findings">
<li><b>Phase A — ping:</b> minimal chat-completions request, 5s ceiling, no retries.
Classifies reachability and gating.</li>
<li><b>Phase B — streaming:</b> one streaming request measuring time-to-first-byte,
time-to-first-token, and completion. Distinguishes <i>headers-arrive-but-no-content</i>
from <i>no-headers</i> from <i>mid-stream stall</i> — three different failures.</li>
<li><b>Verdicts:</b> alive-fast · timeout-fast · streaming-noheaders · unavailable-503 ·
error-other · dead-404-gated. A verdict describes observed HTTP behavior, not validated
usable output.</li>
</ol>

<h2>Known limitations (flagged openly)</h2>
<ul class="findings">
<li><b>Phase B in the 82-model sweep ran up to 25s</b>, not the 5s the ladder specifies —
the sweep script had a hard-coded 25s streaming timeout that survived into the published
run. Two "alive" verdicts (diffusiongemma, GLM) rest on 8–15s streaming observations.
The later <b>fuzz_max</b> and <b>tool-use</b> audits enforce a strict 5s per-request ceiling.</li>
<li><b>"Alive" means HTTP-responsive</b>, not validated usable output. The tool-use audit
is the usability layer; only 7 of 10 ping-alive models emit native tool calls.</li>
<li>Diagnostics are captured untruncated in private logs; public copies redact account
IDs and request UUIDs (<span class="mono">REDACTED</span>).</li>
</ul>

<h2>Nondeterminism is a finding, not noise</h2>
<p>Availability flaps run to run. Observed within hours on 2026-09-14:</p>
<ul class="findings">
<li><span class="mono">nemotron-3-ultra-550b-a55b</span>: timeout → alive</li>
<li><span class="mono">nemotron-3-super-120b-a12b</span>: alive → 503 → alive (native tools)</li>
<li><span class="mono">deepseek-ai/deepseek-v4-pro-0813</span>: alive → timeout →
<strong>delisted from /v1/models</strong> (catalog shrank 82 → 81 in ~10 min)</li>
<li><span class="mono">z-ai/glm-5.3-flash</span>: subsecond headers in one run, 3.5s in another</li>
</ul>
<p>Verdicts are snapshots with timestamps, not permanent labels. Re-run before trusting.</p>

<h2>Auth and ethics</h2>
<ul class="findings">
<li>All requests used the operator's own API key via a credential surrogate — raw keys
never appear in code, logs, or data.</li>
<li>Rate limits are <b>audited, never bypassed</b>: the burst probe records 429s and
<span class="mono">Retry-After</span> values and stops. No IP rotation, no batching tricks.</li>
<li>Fuzzing was benign surface characterization of a public API: discovery routes, method
matrices, request-shape validation, error-shape differentials. No exploitation, no
destructive payloads.</li>
<li>DNS in this environment is hostile (resolver sinkholing); all requests go through
DoH-pinned resolution so a "timeout" means the API timed out, not the network lying.</li>
</ul>

<h2>Reproduce it</h2>
<p>Scripts in the repo: <span class="mono">probe.py</span> (82-model sweep),
<span class="mono">fuzz_max.py</span> (187-case matrix), <span class="mono">tooluse_probe.py</span>
(tool-call audit). This site is generated by <span class="mono">sitegen/gen.py</span> from the
<span class="mono">data/</span> JSONs — no frameworks, no CDNs.</p>
"""
    return base("Methodology", "methodology.html", body)

# ================= CSS =================
CSS = r"""
:root{--bg:#0b0e13;--bg2:#11151d;--line:#1f2632;--txt:#dbe2ec;--dim:#8b94a3;
--green:#34d399;--amber:#fbbf24;--red:#ef4444;--blue:#60a5fa;--mono:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--txt);
font:15px/1.6 system-ui,-apple-system,Segoe UI,Roboto,sans-serif;
background-image:linear-gradient(rgba(255,255,255,.018) 1px,transparent 1px),
linear-gradient(90deg,rgba(255,255,255,.018) 1px,transparent 1px);background-size:32px 32px}
.wrap{max-width:1180px;margin:0 auto;padding:0 20px}
.top{position:sticky;top:0;z-index:50;background:rgba(11,14,19,.92);backdrop-filter:blur(8px);border-bottom:1px solid var(--line)}
.top .wrap{display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;padding-top:10px;padding-bottom:10px}
.brand{font-family:var(--mono);font-size:14px}.dot{display:inline-block;width:9px;height:9px;border-radius:50%;background:var(--green);margin-right:8px;box-shadow:0 0 8px var(--green)}
nav a{color:var(--dim);text-decoration:none;margin-left:16px;font-size:14px}
nav a:hover,nav a.on{color:var(--txt)}nav a.repo{color:var(--blue)}
main{padding:28px 0 60px}h1{font-size:30px;margin:.4em 0}h2{font-size:20px;margin:1.8em 0 .6em;border-bottom:1px solid var(--line);padding-bottom:6px}
.lede{font-size:17px;color:var(--txt);max-width:70ch}.dim{color:var(--dim)}.small{font-size:13px}.mono{font-family:var(--mono);font-size:.92em}
a{color:var(--blue)}
.hero{padding:18px 0 6px}.statgrid{display:grid;grid-template-columns:repeat(auto-fit,minmax(120px,1fr));gap:10px;margin:20px 0}
.stat{background:var(--bg2);border:1px solid var(--line);border-radius:10px;padding:14px;text-align:center}
.stat b{display:block;font-size:30px;font-family:var(--mono)}.stat span{color:var(--dim);font-size:12px}
.bars{margin:8px 0}.sl{fill:var(--dim);font-size:12px}.sv{fill:var(--txt);font-size:12px;font-family:var(--mono)}
.tscroll{overflow-x:auto;border:1px solid var(--line);border-radius:10px;background:var(--bg2)}
table{border-collapse:collapse;width:100%;font-size:14px}th,td{padding:8px 12px;text-align:left;border-bottom:1px solid var(--line);white-space:nowrap}
thead th{position:sticky;top:57px;background:var(--bg2);z-index:5;cursor:pointer}
td.num,th.num{text-align:right;font-family:var(--mono)}.tot{font-weight:700}.hot{color:var(--amber);font-weight:600}
.cat{font-family:var(--mono);font-size:13px}
.badge{display:inline-block;padding:2px 10px;border-radius:20px;font-size:12px;font-weight:600;color:var(--c);border:1px solid var(--c);background:color-mix(in srgb,var(--c) 12%,transparent);white-space:nowrap}
.st{display:inline-block;min-width:38px;text-align:center;padding:1px 8px;border-radius:6px;font-family:var(--mono);font-size:13px;color:var(--c);border:1px solid var(--c)}
.mgrid,.tgrid{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:12px}
.mcard,.tcard{background:var(--bg2);border:1px solid var(--line);border-radius:10px;padding:14px}
.mname{font-family:var(--mono);font-size:13px;margin-bottom:8px;word-break:break-all}
.mrow{display:flex;gap:10px;align-items:center;margin-bottom:6px;flex-wrap:wrap}
.snip{color:var(--dim);font-size:13px;margin-top:6px}.warn{color:var(--amber);font-size:13px}
.warnline{background:rgba(251,191,36,.08);border:1px solid rgba(251,191,36,.35);border-radius:10px;padding:12px 16px}
.findings li{margin:10px 0;max-width:78ch}.findings b{color:var(--txt)}
.datalinks li{margin:6px 0;font-family:var(--mono);font-size:14px}
.controls{display:flex;gap:10px;margin:16px 0;flex-wrap:wrap;align-items:center}
.controls input,.controls select{background:var(--bg2);color:var(--txt);border:1px solid var(--line);border-radius:8px;padding:8px 12px;font-size:14px}
.controls input{min-width:280px}
tr.mrow{cursor:pointer}tr.mrow:hover td{background:rgba(255,255,255,.03)}
.detail-row td{background:#0d1117;white-space:normal}
.deep{padding:6px 4px}.ph{margin:8px 0;font-size:13px}.hk{color:var(--dim);font-family:var(--mono)}
.detail{color:var(--dim);word-break:break-all;white-space:pre-wrap;margin:4px 0}
.carddesc{margin-top:8px;font-size:13px;border-left:3px solid var(--blue);padding-left:10px}
.anchor{color:var(--line);text-decoration:none;margin-right:6px}tr.mrow:hover .anchor{color:var(--blue)}
.ggrid{display:grid;grid-template-columns:repeat(auto-fill,minmax(340px,1fr));gap:12px}
.gcard{background:var(--bg2);border:1px solid var(--line);border-radius:10px;padding:14px}
.gcard pre{background:#0d1117;border:1px solid var(--line);border-radius:8px;padding:10px;overflow-x:auto;font-size:12px;white-space:pre-wrap;word-break:break-all}
footer{border-top:1px solid var(--line);padding:18px 0 40px;color:var(--dim)}
@media(max-width:700px){thead th{top:101px}.stat b{font-size:24px}}
"""

# ================= JS =================
JS = r"""
(function(){
function norm(s){return (s||"").toLowerCase();}
var q=document.getElementById("q"), fv=document.getElementById("fv"),
    fc=document.getElementById("fc"), tb=document.querySelector("#mtable tbody");
if(tb){
  var rows=[].slice.call(tb.querySelectorAll("tr.mrow"));
  var det={}; [].slice.call(tb.querySelectorAll("tr.detail-row")).forEach(function(r){det[r.getAttribute("data-for")]=r;});
  function apply(){
    var qq=norm(q&&q.value), vv=fv&&fv.value, cc=fc&&fc.value, n=0;
    rows.forEach(function(r){
      var ok=(!qq||r.getAttribute("data-m").indexOf(qq)>=0)&&(!vv||r.getAttribute("data-v")===vv)&&(!cc||r.getAttribute("data-c")===cc);
      r.style.display=ok?"":"none";
      var d=det[r.id.replace("row-","")]; if(d&&!ok)d.hidden=true;
      if(ok)n++;
    });
    var c=document.getElementById("count"); if(c)c.textContent=n+" shown";
  }
  if(q)q.addEventListener("input",apply);
  if(fv)fv.addEventListener("change",apply);
  if(fc)fc.addEventListener("change",apply);
  rows.forEach(function(r){
    r.addEventListener("click",function(e){
      if(e.target.tagName==="A")return;
      var d=det[r.id.replace("row-","")]; if(d)d.hidden=!d.hidden;
    });
  });
  // sortable headers
  var idx={m:0,c:1,v:2,a:3,t:4};
  document.querySelectorAll("#mtable thead th[data-s]").forEach(function(th){
    th.addEventListener("click",function(){
      var k=th.getAttribute("data-s"), col=idx[k], asc=th.classList.toggle("asc");
      var arr=rows.slice();
      function val(r){
        var t=r.children[col].textContent.trim();
        if(k==="a"||k==="t"){var f=parseFloat(t);return isNaN(f)?(asc?1e18:-1e18):f;}
        if(k==="v"){var o=["alive-fast","timeout-fast","streaming-noheaders","unavailable-503","error-other","dead-404-gated"];return o.indexOf(r.getAttribute("data-v"));}
        return t.toLowerCase();
      }
      arr.sort(function(a,b){var x=val(a),y=val(b);return (x<y?-1:x>y?1:0)*(asc?1:-1);});
      arr.forEach(function(r){tb.appendChild(r);tb.appendChild(det[r.id.replace("row-","")]);});
    });
  });
  // deep link #model=org__name
  function hash(){
    var m=location.hash.match(/^#model=(.+)$/);
    if(!m)return;
    var row=document.getElementById("row-"+m[1]);
    if(row){if(q)q.value="";if(fv)fv.value="";if(fc)fc.value="";apply();
      var d=det[m[1]]; if(d)d.hidden=false;
      row.scrollIntoView({block:"center"});row.style.outline="1px solid #60a5fa";}
  }
  window.addEventListener("hashchange",hash);hash();apply();
}
})();
"""

# ================= MAIN =================
def main():
    os.makedirs(os.path.join(OUT, "assets"), exist_ok=True)
    pages = {
        "index.html": sanitize(gen_index()),
        "models.html": sanitize(gen_models()),
        "tooluse.html": sanitize(gen_tooluse()),
        "fuzz.html": sanitize(gen_fuzz()),
        "cards.html": sanitize(gen_cards()),
        "methodology.html": sanitize(gen_methodology()),
    }
    for name, content in pages.items():
        p = os.path.join(OUT, name)
        with open(p, "w") as f:
            f.write(content)
        print("wrote", p, len(content), "bytes")
    with open(os.path.join(OUT, "assets", "style.css"), "w") as f:
        f.write(CSS)
    with open(os.path.join(OUT, "assets", "app.js"), "w") as f:
        f.write(JS)
    print("wrote assets")
    # final safety scan
    bad = []
    for root, _, files in os.walk(OUT):
        for fn in files:
            fp = os.path.join(root, fn)
            t = open(fp).read()
            if "nvapi-" in t:
                bad.append(fp)
            if UUID_RE.search(t):
                bad.append(fp + " (UUID!)")
    if bad:
        print("SANITIZATION FAILURE:", bad); sys.exit(1)
    print("sanitization scan clean")

if __name__ == "__main__":
    main()
