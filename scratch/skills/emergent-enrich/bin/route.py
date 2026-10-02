#!/usr/bin/env python3
"""Routed emergent enrichment: free sources first, Exa only with explicit opt-in.

Routing order:
  1. GitHub code search (free, authenticated via custom.github) - best-match
     relevance order, NEVER star-sorted.
  2. Literature, unblinded (all free, no auth):
     - arXiv (relevance-sorted; throttles aggressively, first-class limiter)
     - OpenAlex (250M+ works incl. arXiv content; generous limits)
     - Semantic Scholar (200M+ papers; abstracts + citation counts + PDFs)
     If arXiv is throttling, OpenAlex/S2 carry the literature leg.
  3. Exa (costs credits) - only when --exa-ok is passed, which requires the
     user's explicit approval for that call.

Prints a JSON result with per-source blocks and a credits_spent flag.
"""
import argparse
import json
import os
import re
import sys
import time
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET

sys.path.insert(0, "/opt/hatch/skills/skill-creator/bin")
# dynamic_credentials (Hatch cell surrogate auth) is optional: on hosts
# without /opt/hatch (e.g. awrawr-pc) authenticated legs degrade gracefully
# and all keyless paper legs keep working.
try:
    from dynamic_credentials import add_surrogate_to_request, read_response_body
except (ImportError, ModuleNotFoundError, OSError):  # noqa: BLE001
    def add_surrogate_to_request(req, _name, allowed_hosts=None):
        return req

    def read_response_body(response, chunk_size=65536):
        return response.read()

# Shared first-class arXiv rate limiter (interval enforcement, fast timeout,
# 429 backoff, JSONL timing audit) - one budget across both skills.
sys.path.insert(0, os.path.expanduser("~/workspace/skills/arxiv-mcp/bin"))
from arxiv_rl import ArxivRateLimiter

GITHUB_HOSTS = ["api.github.com"]
EXA_HOSTS = ["api.exa.ai"]
ARXIV_BASE = "https://export.arxiv.org"
OPENALEX_BASE = "https://api.openalex.org"
S2_BASE = "https://api.semanticscholar.org"
USER_AGENT = "shingle-emergent-enrich/1.0"
# Polite contact for OpenAlex's polite pool (better response times, no key needed).
POLITE_MAILTO = "shingle@localhost"


def _throttle(key, min_interval=1.0):
    """Light per-host client-side throttle, persisted across invocations."""
    os.makedirs(os.path.expanduser("~/.cache/shingle"), exist_ok=True)
    state_file = os.path.expanduser("~/.cache/shingle/lit_%s.json" % key)
    try:
        with open(state_file, "r", encoding="utf-8") as f:
            last = json.load(f).get("last", 0.0)
    except (OSError, ValueError):
        last = 0.0
    wait = min_interval - (time.time() - last)
    if wait > 0:
        time.sleep(wait)
    tmp = state_file + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump({"last": time.time()}, f)
    os.replace(tmp, state_file)


def github_code_search(query, per_page):
    """GitHub code search. No sort param -> GitHub returns best-match
    relevance order, not star order. Authenticated via surrogate."""
    params = urllib.parse.urlencode({"q": query, "per_page": per_page})
    url = "https://api.github.com/search/code?%s" % params
    req = urllib.request.Request(url)
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("User-Agent", USER_AGENT)
    req.add_header("X-GitHub-Api-Version", "2022-11-28")
    add_surrogate_to_request(req, "custom.github", allowed_hosts=GITHUB_HOSTS)
    with urllib.request.urlopen(req, timeout=25) as resp:
        data = json.loads(read_response_body(resp).decode("utf-8"))
    items = []
    for it in data.get("items", []):
        repo = it.get("repository") or {}
        items.append({
            "name": it.get("name"),
            "path": it.get("path"),
            "repo": repo.get("full_name"),
            "html_url": it.get("html_url"),
            "score": it.get("score"),
        })
    return {
        "ok": True,
        "total_count": data.get("total_count"),
        "items": items,
        "cost": "free",
        "ranking": "best-match relevance (not stars)",
    }


def arxiv_search(query, max_results, timeout=12, max_retries=3):
    """arXiv API: free, no auth, relevance-sorted.

    Rate limiting is first-class and shared with the arxiv-mcp skill via
    arxiv_rl.ArxivRateLimiter: client-side 1 req / ~3.5s interval (persisted
    across invocations), fast timeout, 429/503 backoff honoring
    Retry-After, and every attempt appended to a JSONL timing audit log
    (~/.cache/shingle/arxiv_audit.jsonl).

    Pass timeout=3, max_retries=0 for extreme fail-fast (single attempt)."""
    params = urllib.parse.urlencode({
        "search_query": "all:%s" % query,
        "start": 0,
        "max_results": max_results,
        "sortBy": "relevance",
        "sortOrder": "descending",
    })
    url = "%s/api/query?%s" % (ARXIV_BASE, params)
    rl = ArxivRateLimiter(timeout=timeout, max_retries=max_retries)
    xml_text, timing = rl.get(url)
    xml_text = xml_text.decode("utf-8")
    ns = {"a": "http://www.w3.org/2005/Atom"}
    root = ET.fromstring(xml_text)
    items = []
    for e in root.findall("a:entry", ns):
        title_el = e.find("a:title", ns)
        pub_el = e.find("a:published", ns)
        id_el = e.find("a:id", ns)
        sum_el = e.find("a:summary", ns)
        authors = []
        for a in e.findall("a:author", ns):
            n = a.find("a:name", ns)
            if n is not None and n.text:
                authors.append(n.text.strip())
        summary = (sum_el.text or "").strip().replace("\n", " ") if sum_el is not None else ""
        items.append({
            "title": (title_el.text or "").strip().replace("\n", " ") if title_el is not None else "",
            "authors": authors,
            "published": (pub_el.text or "")[:10] if pub_el is not None else "",
            "url": id_el.text.strip() if id_el is not None and id_el.text else None,
            "summary": summary[:500],
        })
    return {"ok": True, "items": items, "cost": "free", "ranking": "relevance",
            "timing_ms": timing["duration_ms"],
            "rate_limited_retries": timing["retries"]}


def _oa_abstract(inv_index):
    """Reconstruct abstract text from OpenAlex's inverted index."""
    if not inv_index:
        return ""
    positions = []
    for word, idxs in inv_index.items():
        for i in idxs:
            positions.append((i, word))
    positions.sort()
    return " ".join(w for _, w in positions)[:600]


def _oa_work_to_item(w):
    """Normalize one OpenAlex work dict into a router paper item."""
    authors = [a.get("author", {}).get("display_name", "")
               for a in w.get("authorships", [])[:6]]
    loc = w.get("primary_location") or {}
    src = loc.get("source") or {}
    doi = w.get("doi")
    # ids.arxiv looks like https://arxiv.org/abs/2211.17192 -- surfacing
    # a real arxiv_id lets paper_key dedupe across legs (arxiv, S2,
    # HF, alphaXiv) instead of falling back to title keys.
    ids = w.get("ids") or {}
    arxiv_id = None
    m = re.search(r"arxiv\.org/(?:abs|pdf)/([^\s\"'<>]+)",
                  ids.get("arxiv") or "")
    if m:
        arxiv_id = m.group(1)
    doi_bare = (doi or "").replace("https://doi.org/", "") or None
    return {
        "title": w.get("title"),
        "authors": [a for a in authors if a],
        "year": w.get("publication_year"),
        "cited_by_count": w.get("cited_by_count"),
        "venue": src.get("display_name"),
        "arxiv_id": arxiv_id,
        "doi": doi_bare,
        "url": doi or w.get("id"),
        "openalex_id": w.get("id"),
        "summary": _oa_abstract(w.get("abstract_inverted_index")),
    }


def openalex_lookup_doi(doi, timeout=10):
    """Direct OpenAlex work lookup by DOI (exact, not a search) -- the
    right call for --id DOI mode. Free, no key."""
    _throttle("openalex", 1.0)
    doi = doi.strip()
    if doi.lower().startswith("doi:"):
        doi = doi[4:]
    url = ("%s/works/doi:%s?%s"
           % (OPENALEX_BASE, urllib.parse.quote(doi, safe=""),
              urllib.parse.urlencode({
                  "mailto": POLITE_MAILTO,
                  "select": "id,doi,ids,title,publication_year,authorships,"
                            "abstract_inverted_index,cited_by_count,"
                            "primary_location",
              })))
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    t0 = time.monotonic()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            w = json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        return {"ok": False, "items": [], "error": str(e)[:80]}
    if not w.get("id"):
        return {"ok": False, "items": [], "error": "not found"}
    dur_ms = int((time.monotonic() - t0) * 1000)
    return {"ok": True, "items": [_oa_work_to_item(w)], "cost": "free",
            "timing_ms": dur_ms, "note": "exact DOI lookup"}


def openalex_search(query, max_results, timeout=15):
    """OpenAlex: 250M+ works (incl. arXiv content), free, no key.

    Keyless + mailto polite pool. Generous limits (100 req/s ceiling), so a
    light 1s client-side throttle is plenty. This is the unblinded fallback
    when arXiv itself is throttling us."""
    _throttle("openalex", 1.0)
    params = urllib.parse.urlencode({
        "search": query,
        "per-page": max(1, min(25, max_results)),
        "mailto": POLITE_MAILTO,
        "select": "id,doi,ids,title,publication_year,authorships,"
                  "abstract_inverted_index,cited_by_count,primary_location",
    })
    url = "%s/works?%s" % (OPENALEX_BASE, params)
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    t0 = time.monotonic()
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    dur_ms = int((time.monotonic() - t0) * 1000)
    items = [_oa_work_to_item(w) for w in data.get("results", [])]
    return {"ok": True, "items": items, "cost": "free",
            "ranking": "relevance", "timing_ms": dur_ms,
            "note": "covers arXiv + journals + preprints"}


def s2_free_lookup(doi, timeout=10):
    """Semantic Scholar's free anonymous paper endpoint by DOI. Even the
    anonymous tier returns S2's own tldr for many papers -- the real thing,
    not a dupe. 100 req/5min anonymous; degrades on 429."""
    _throttle("semanticscholar", 1.0)
    doi = doi.strip()
    if doi.lower().startswith("doi:"):
        doi = doi[4:]
    params = urllib.parse.urlencode({
        "fields": "title,abstract,tldr,citationCount,"
                  "influentialCitationCount",
    })
    url = "%s/graph/v1/paper/DOI:%s?%s" % (
        S2_BASE, urllib.parse.quote(doi, safe=""), params)
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    t0 = time.monotonic()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            w = json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        return {"ok": False, "error": str(e)[:80]}
    tldr = (w.get("tldr") or {}).get("text")
    return {
        "ok": True,
        "title": w.get("title"),
        "abstract": w.get("abstract"),
        "tldr": tldr,
        "citationCount": w.get("citationCount"),
        "influentialCitationCount": w.get("influentialCitationCount"),
        "timing_ms": int((time.monotonic() - t0) * 1000),
        "cost": "free",
    }


def s2_search(query, max_results, timeout=15):
    """Semantic Scholar Graph API: 200M+ papers, free, no key required.

    Anonymous tier allows ~100 req / 5min - plenty for enrichment. Returns
    abstracts, citation counts, arXiv IDs and open-access PDF links, i.e.
    strictly more signal than arXiv's own API."""
    _throttle("semanticscholar", 1.0)
    params = urllib.parse.urlencode({
        "query": query,
        "limit": max(1, min(25, max_results)),
        "fields": "title,abstract,authors,year,url,openAccessPdf,"
                  "citationCount,externalIds",
    })
    url = "%s/graph/v1/paper/search?%s" % (S2_BASE, params)
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    t0 = time.monotonic()
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    dur_ms = int((time.monotonic() - t0) * 1000)
    items = []
    for p in data.get("data", []):
        ext = p.get("externalIds") or {}
        pdf = p.get("openAccessPdf") or {}
        items.append({
            "title": p.get("title"),
            "authors": [a.get("name", "") for a in p.get("authors", [])[:6]],
            "year": p.get("year"),
            "citation_count": p.get("citationCount"),
            "arxiv_id": ext.get("ArXiv"),
            "doi": ext.get("DOI"),
            "url": p.get("url"),
            "pdf_url": pdf.get("url"),
            "summary": (p.get("abstract") or "")[:600],
        })
    return {"ok": True, "items": items, "cost": "free",
            "ranking": "relevance", "timing_ms": dur_ms}


def dblp_search(query, max_results, timeout=15):
    """DBLP computer-science bibliography: 6.5M+ CS publications, free, no key.

    No abstracts (title/venue/year/DOI only), but excellent for venue-aware
    CS research and author disambiguation. CC0 metadata. Be polite: ~5 RPS
    community guidance, we throttle to 1s.

    NOTE 2026-09-14: dblp.org currently serves a bot-check wall to our shared
    egress IP, so this leg degrades gracefully until that clears. Kept wired
    because it works from unflagged networks."""
    _throttle("dblp", 1.0)
    params = urllib.parse.urlencode({
        "q": query,
        "format": "json",
        "h": max(1, min(30, max_results)),
        "c": 0,
    })
    url = "https://dblp.org/search/publ/api?%s" % params
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    t0 = time.monotonic()
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    dur_ms = int((time.monotonic() - t0) * 1000)
    hits = data.get("result", {}).get("hits", {}).get("hit", [])
    items = []
    for h in hits:
        info = h.get("info", {})
        authors = info.get("authors", {}).get("author", [])
        if isinstance(authors, dict):
            authors = [authors]
        items.append({
            "title": info.get("title"),
            "authors": [a.get("text", "") for a in authors if isinstance(a, dict)][:6],
            "venue": info.get("venue"),
            "year": info.get("year"),
            "type": info.get("type"),
            "doi": info.get("doi"),
            "url": info.get("url"),
            "ee": info.get("ee"),
        })
    return {"ok": True, "items": items, "cost": "free",
            "ranking": "relevance", "timing_ms": dur_ms,
            "note": "CS-only, no abstracts, CC0"}


def hf_papers_search(query, max_results, timeout=15):
    """Hugging Face Papers search: hybrid semantic + keyword over arXiv-indexed
    AI/ML papers, public, no token required.

    Returns AI-curated summaries where available, plus linked models/datasets.
    Obtuse but high-signal for emergent AI research."""
    _throttle("hf_papers", 1.0)
    params = urllib.parse.urlencode({"q": query})
    url = "https://huggingface.co/api/papers/search?%s" % params
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    t0 = time.monotonic()
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    dur_ms = int((time.monotonic() - t0) * 1000)
    raw = data if isinstance(data, list) else data.get("papers", data.get("results", []))
    items = []
    for p in raw[:max_results]:
        if not isinstance(p, dict):
            continue
        items.append({
            "title": p.get("title"),
            "authors": [a.get("name", "") if isinstance(a, dict) else str(a)
                        for a in p.get("authors", [])[:6]],
            "published": p.get("publishedAt") or p.get("published_at"),
            "arxiv_id": p.get("id"),
            "url": "https://huggingface.co/papers/%s" % p.get("id") if p.get("id") else None,
            "summary": (p.get("summary") or p.get("abstract") or "")[:600],
            "upvotes": p.get("upvotes"),
        })
    return {"ok": True, "items": items, "cost": "free",
            "ranking": "relevance", "timing_ms": dur_ms,
            "note": "HF paper search, AI/ML focused"}


def exa_search(query, num_results):
    """Exa REST search. COSTS CREDITS - only call with explicit user opt-in."""
    import exa_audit  # local ledger: Exa exposes no usage endpoint
    t0 = time.perf_counter()
    url = "https://api.exa.ai/search"
    payload = json.dumps({
        "query": query,
        "type": "auto",
        "numResults": num_results,
    }).encode("utf-8")
    req = urllib.request.Request(url, data=payload, method="POST")
    req.add_header("Content-Type", "application/json")
    req.add_header("User-Agent", USER_AGENT)
    add_surrogate_to_request(req, "custom.exa", allowed_hosts=EXA_HOSTS)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(read_response_body(resp).decode("utf-8"))
    except Exception as e:
        exa_audit.log_call("/search", num_results,
                           (time.perf_counter() - t0) * 1000,
                           ok=False, error=e, query=query)
        raise
    exa_audit.log_call("/search", num_results,
                       (time.perf_counter() - t0) * 1000,
                       ok=True, query=query,
                       results_returned=len(data.get("results", [])),
                       cost_usd=(data.get("costDollars") or {}).get("total"))
    items = []
    for r in data.get("results", []):
        items.append({
            "title": r.get("title"),
            "url": r.get("url"),
            "publishedDate": r.get("publishedDate"),
            "score": r.get("score"),
        })
    return {"ok": True, "items": items, "cost": "exa-credits"}


ALPHAXIV_HOSTS = ("api.alphaxiv.org",)
_ARXIV_VER_RE = re.compile(r"v\d+$")


def _strip_arxiv_version(aid):
    return _ARXIV_VER_RE.sub("", aid or "")


def _alphaxiv_get(path, timeout, auth=False):
    """GET against api.alphaxiv.org. Search/metadata/similar-papers are
    public and must go WITHOUT the key (alphaXiv 403s keyed requests on
    public paths); auth=True attaches the vaulted key for library/private
    endpoints like /folders/v3."""
    url = "https://api.alphaxiv.org" + path
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    if auth:
        add_surrogate_to_request(req, "custom.alphaxiv",
                                 allowed_hosts=ALPHAXIV_HOSTS)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(read_response_body(resp).decode("utf-8"))


def _alphaxiv_item(r):
    aid = _strip_arxiv_version(r.get("universal_paper_id")
                               or r.get("canonical_id"))
    metrics = r.get("metrics") or {}
    pub = r.get("publication_date") or ""
    gh = r.get("github_url")
    return {
        "title": r.get("title"),
        "summary": (r.get("abstract") or "")[:600],
        "authors": r.get("authors") or [],
        "arxiv_id": aid or None,
        "doi": None,
        "url": "https://arxiv.org/abs/" + aid if aid else None,
        "pdf_url": "https://arxiv.org/pdf/" + aid if aid else None,
        "published": pub[:10] or None,
        "citations": None,  # votes are community upvotes, not citations;
        "source": "alphaxiv",  # kept separate in extras to avoid conflation
        "extras": {
            "paper_group_id": r.get("paper_group_id"),
            "votes": metrics.get("total_votes"),
            "public_votes": metrics.get("public_total_votes"),
            "topics": r.get("topics") or [],
            "github_url": gh,
        },
    }


def alphaxiv_search(query, max_results=10, timeout=10):
    """alphaXiv rich paper search: community-indexed arXiv with upvotes,
    topics, and linked GitHub repos. Public endpoint; key only unlocks
    library/private features."""
    path = "/v1/search/paper?q=%s" % urllib.parse.quote(query)
    data = _alphaxiv_get(path, timeout)
    items = [_alphaxiv_item(r)
             for r in (data if isinstance(data, list) else [])[:max_results]]
    return {"ok": True, "items": items, "cost": "free"}


def alphaxiv_lookup(aid, timeout=10):
    """alphaXiv metadata + comments + similar papers for one arXiv ID."""
    data = _alphaxiv_get("/papers/v3/legacy/%s"
                         % urllib.parse.quote(aid, safe=""), timeout)
    paper = data.get("paper") or {}
    pv = paper.get("paper_version") or {}
    pg = paper.get("paper_group") or {}
    group_id = pg.get("id")
    aid_norm = _strip_arxiv_version(pv.get("universal_paper_id") or aid)
    authors = paper.get("authors_v2") or paper.get("authors") or []
    if authors and isinstance(authors[0], dict):
        authors = [a.get("name") for a in authors if a.get("name")]
    pub = pv.get("publication_date") or ""
    item = {
        "title": pv.get("title"),
        "summary": (pv.get("abstract") or "")[:600],
        "authors": authors,
        "arxiv_id": aid_norm or None,
        "doi": None,
        "url": "https://arxiv.org/abs/" + aid_norm if aid_norm else None,
        "pdf_url": "https://arxiv.org/pdf/" + aid_norm if aid_norm else None,
        "published": pub[:10] or None,
        "citations": None,
        "source": "alphaxiv",
        "extras": {"paper_group_id": group_id,
                   "comments": len(data.get("comments") or [])},
    }
    similar = []
    if aid_norm:
        # NB: this endpoint takes the arXiv ID, not the paper-group UUID.
        try:
            sdata = _alphaxiv_get("/papers/v3/%s/similar-papers"
                                  % urllib.parse.quote(aid_norm, safe=""),
                                  timeout)
            for s in (sdata if isinstance(sdata, list) else [])[:8]:
                similar.append({
                    "title": s.get("title"),
                    "arxiv_id": _strip_arxiv_version(
                        s.get("universal_paper_id")
                        or s.get("canonical_id")),
                    "authors": s.get("authors") or [],
                })
        except Exception:
            pass
    return {"ok": True, "items": [item], "similar": similar, "cost": "free"}


def tldr_extractive(abstract, title=None, max_chars=320):
    """Extractive TLDR dupe (S2's tldr is an abstractive model; this is the
    free local stand-in): scores sentences by title-word overlap, position,
    and length; returns the top 2 in original order."""
    import re as _re
    if not abstract:
        return None
    text = " ".join(abstract.split())
    sents = _re.split(r"(?<=[.!?])\s+", text)
    sents = [s.strip() for s in sents if len(s.strip()) > 25]
    if not sents:
        return text[:max_chars]
    if len(sents) == 1:
        return sents[0][:max_chars]
    title_words = set(_re.findall(r"[a-z]{4,}", (title or "").lower()))
    scored = []
    for i, s in enumerate(sents):
        words = set(_re.findall(r"[a-z]{4,}", s.lower()))
        overlap = len(words & title_words)
        # position bonus (early sentences), length sweet spot ~80-200 chars
        score = overlap * 3 + max(0, 4 - i) * 0.7
        score += 1.0 if 60 <= len(s) <= 220 else 0.0
        scored.append((score, i, s))
    top = sorted(sorted(scored, reverse=True)[:2], key=lambda t: t[1])
    out = " ".join(s for _, _, s in top)
    return out[:max_chars]


def influential_citations(doi, max_citers=30, top_n=10, timeout=12):
    """Dupe of S2's influentialCitationCount (their ML model, key-gated).
    Free 2-hop version: OpenCitations gives citing DOIs; OpenAlex gives each
    citer's own cited_by_count; rank citers by it. The most-cited citers are
    the 'influential' ones."""
    doi = doi.strip()
    if doi.lower().startswith("doi:"):
        doi = doi[4:]
    t0 = time.monotonic()
    # 1. citing DOIs from OpenCitations Index
    url = ("https://api.opencitations.net/index/v1/citations/%s"
           % urllib.parse.quote(doi, safe=""))
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            cites = json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        return {"ok": False, "error": str(e)[:80], "items": []}
    citing = []
    for c in cites[:max_citers]:
        d = (c.get("citing") or "").strip()
        if d and d not in citing:
            citing.append(d)
    if not citing:
        return {"ok": True, "items": [], "timing_ms": 0, "cost": "free"}
    # 2. one batched OpenAlex call for all citers' metrics. OpenAlex OR
    # syntax is single-field: doi:10.1|10.2 (repeating the field 400s).
    _throttle("openalex", 1.0)
    filt = "doi:" + "|".join(citing)
    params = urllib.parse.urlencode({
        "filter": filt,
        "select": "id,doi,title,publication_year,cited_by_count",
        "per-page": min(50, len(citing)),
    })
    req = urllib.request.Request("%s/works?%s" % (OPENALEX_BASE, params),
                                 headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        return {"ok": False, "error": str(e)[:80], "items": []}
    ranked = []
    for w in data.get("results", []):
        ranked.append({
            "doi": (w.get("doi") or "").replace("https://doi.org/", ""),
            "title": w.get("title"),
            "year": w.get("publication_year"),
            "cited_by_count": w.get("cited_by_count") or 0,
        })
    ranked.sort(key=lambda r: r["cited_by_count"], reverse=True)
    return {
        "ok": True,
        "items": ranked[:top_n],
        "citers_seen": len(citing),
        "timing_ms": int((time.monotonic() - t0) * 1000),
        "cost": "free",
        "note": "2-hop influence proxy: citers ranked by their own citations",
    }


def citation_velocity(doi, timeout=10):
    """Citations-per-year histogram from OpenCitations creation dates --
    the 'is this heating up' signal."""
    doi = doi.strip()
    if doi.lower().startswith("doi:"):
        doi = doi[4:]
    url = ("https://api.opencitations.net/index/v1/citations/%s"
           % urllib.parse.quote(doi, safe=""))
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            cites = json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        return {"ok": False, "error": str(e)[:80]}
    years = {}
    for c in cites:
        y = (c.get("creation") or "")[:4]
        if y.isdigit():
            years[y] = years.get(y, 0) + 1
    return {"ok": True, "per_year": dict(sorted(years.items())),
            "total": len(cites), "cost": "free"}


AUDIT_LOG_DEFAULT = os.path.expanduser("~/.cache/shingle/papers_audit.jsonl")
ARXIV_AUDIT_LOG = os.path.expanduser("~/.cache/shingle/arxiv_audit.jsonl")


def audit_classify_error(err):
    """Taxonomy for leg failures -- the point of the audit."""
    if not err:
        return None
    e = str(err).lower()
    if "429" in e:
        return "http_429"
    if "403" in e:
        return "http_403"
    if "503" in e:
        return "http_503"
    if "timeout" in e or "timed out" in e:
        return "timeout"
    if "bot" in e or "captcha" in e or "challenge" in e or "html" in e:
        return "bot_check"
    if ("connection" in e or "urlopen" in e or "gaierror" in e
            or "dns" in e or "refused" in e):
        return "connection"
    return "other"


def _pct(sorted_vals, p):
    if not sorted_vals:
        return None
    k = min(len(sorted_vals) - 1, max(0, int(p * len(sorted_vals))))
    return sorted_vals[k]


def audit_parse_window(s):
    s = (s or "24h").strip().lower()
    if s == "all":
        return None
    m = re.match(r"^(\d+)\s*(h|d|m)?$", s)
    if not m:
        return 24.0
    n = int(m.group(1))
    unit = m.group(2) or "h"
    return n * {"m": 1 / 60, "h": 1.0, "d": 24.0}[unit]


def _read_jsonl(path):
    rows = []
    try:
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    rows.append(json.loads(line))
                except Exception:
                    continue
    except FileNotFoundError:
        pass
    return rows


def audit_append_run(log_path, record):
    """Append one router run to the JSONL audit log. Never raises."""
    try:
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")
    except Exception:
        pass


def audit_report(log_path=AUDIT_LOG_DEFAULT, window="24h",
                 arxiv_log_path=ARXIV_AUDIT_LOG):
    """Analyze the router's JSONL audit log into a report dict.

    Per-leg: run counts, ok-rate, p50/p95/max latency, error taxonomy.
    Plus a fail-fast score and generated recommendations -- the part that
    makes this more than a stats dump."""
    window_hours = audit_parse_window(window)
    now = time.time()
    rows = [r for r in _read_jsonl(log_path)
            if window_hours is None
            or (now - _ts_to_epoch(r.get("ts"))) <= window_hours * 3600]

    legs = {}
    modes = {}
    elapsed = []
    budget_hits = 0
    budget_total = 0
    for r in rows:
        modes[r.get("mode", "?")] = modes.get(r.get("mode", "?"), 0) + 1
        if isinstance(r.get("elapsed_ms"), (int, float)):
            elapsed.append(r["elapsed_ms"])
        timeout_ms = (r.get("timeout") or 3.0) * 1000
        for leg in r.get("legs", []):
            name = leg.get("leg", "?")
            d = legs.setdefault(name, {"runs": 0, "ok": 0, "timings": [],
                                       "errors": {}, "err_samples": {}})
            d["runs"] += 1
            if leg.get("ok"):
                d["ok"] += 1
            t = leg.get("timing_ms")
            if isinstance(t, (int, float)):
                d["timings"].append(t)
                budget_total += 1
                if t <= timeout_ms:
                    budget_hits += 1
            cls = audit_classify_error(leg.get("error"))
            if cls:
                d["errors"][cls] = d["errors"].get(cls, 0) + 1
                if cls not in d["err_samples"]:
                    d["err_samples"][cls] = str(leg.get("error"))[:90]

    leg_report = {}
    for name, d in sorted(legs.items()):
        ts = sorted(d["timings"])
        leg_report[name] = {
            "runs": d["runs"],
            "ok_rate": round(d["ok"] / d["runs"], 3) if d["runs"] else 0,
            "p50_ms": _pct(ts, 0.50),
            "p95_ms": _pct(ts, 0.95),
            "max_ms": ts[-1] if ts else None,
            "errors": dict(sorted(d["errors"].items(),
                                 key=lambda kv: -kv[1])),
            "err_samples": d["err_samples"],
        }

    # arXiv raw attempt log (shared budget with arxiv-mcp): outcome mix.
    ax_rows = [r for r in _read_jsonl(arxiv_log_path)
               if window_hours is None
               or (now - _ts_to_epoch(r.get("ts"))) <= window_hours * 3600]
    outcomes = {}
    retry_after_seen = False
    for r in ax_rows:
        outcomes[r.get("outcome", "?")] = outcomes.get(r.get("outcome", "?"), 0) + 1
        if r.get("retry_after"):
            retry_after_seen = True

    recommendations = []
    for name, lr in leg_report.items():
        if lr["runs"] >= 3 and lr["ok_rate"] < 0.5:
            recommendations.append(
                "%s ok-rate %.0f%% over %d runs -- it degrades gracefully, "
                "but consider raising --timeout or dropping the leg"
                % (name, lr["ok_rate"] * 100, lr["runs"]))
        elif lr["ok_rate"] == 0 and lr["runs"] >= 1:
            top = next(iter(lr["errors"]), "?")
            recommendations.append(
                "%s has no successes yet in %d run(s) (top failure: %s) -- "
                "too early to judge, watch this leg"
                % (name, lr["runs"], top))
        e429 = lr["errors"].get("http_429", 0)
        if lr["runs"] >= 3 and e429 / lr["runs"] > 0.3:
            recommendations.append(
                "%s is rate-limiting this egress (429 on %.0f%% of runs) -- "
                "redundancy across legs is doing its job"
                % (name, e429 / lr["runs"] * 100))
    if not recommendations:
        recommendations.append("all legs healthy in this window")

    es = sorted(elapsed)
    return {
        "ok": True,
        "window": window,
        "runs": len(rows),
        "runs_in_arxiv_log": len(ax_rows),
        "modes": modes,
        "avg_elapsed_ms": int(sum(es) / len(es)) if es else None,
        "p95_elapsed_ms": _pct(es, 0.95),
        "fail_fast_score": (round(budget_hits / budget_total, 3)
                            if budget_total else None),
        "legs": leg_report,
        "arxiv_attempts": {"outcomes": outcomes,
                           "retry_after_seen": retry_after_seen},
        "recommendations": recommendations,
        "credits_spent": False,
    }


def _ts_to_epoch(ts):
    """Parse the ISO ts we write; unknown -> 0 (excluded from windows)."""
    if not ts:
        return 0
    try:
        from datetime import datetime, timezone
        dt = datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
        return dt.replace(tzinfo=timezone.utc).timestamp()
    except Exception:
        return 0


def opencitations_lookup(doi, timeout=10):
    """OpenCitations: free, keyless citation graph. No signup, no key;
    180 req/min per IP anonymous. Meta API gives bibliographic metadata,
    Index API gives incoming citations (who cites this) and outgoing
    references. DOI in, citation graph out."""
    doi = doi.strip()
    if doi.lower().startswith("doi:"):
        doi = doi[4:]
    t0 = time.monotonic()
    meta_url = ("https://api.opencitations.net/meta/v1/metadata/doi:%s"
                % urllib.parse.quote(doi, safe=""))
    req = urllib.request.Request(meta_url, headers={"User-Agent": USER_AGENT})
    title, omid = None, None
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            meta = json.loads(resp.read().decode("utf-8"))
        if meta:
            title = meta[0].get("title")
            ids = meta[0].get("id", "")
            m = re.search(r"omid:(br/\d+)", ids)
            omid = m.group(1) if m else None
    except Exception:
        pass
    citing, references = [], []
    cited_by_count, ref_count = None, None
    for op in ("citations", "references"):
        try:
            url = ("https://api.opencitations.net/index/v1/%s/%s"
                   % (op, urllib.parse.quote(doi, safe="")))
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            key = "citing" if op == "citations" else "cited"
            sample = [d.get(key) for d in data[:10] if d.get(key)]
            if op == "citations":
                citing = sample
            else:
                references = sample
            total = len(data)
        except Exception:
            total = None
        if op == "citations":
            cited_by_count = total
        else:
            ref_count = total
    return {
        "ok": True,
        "doi": doi,
        "title": title,
        "omid": omid,
        "cited_by_count": cited_by_count,
        "citing_dois_sample": citing,
        "references_count": ref_count,
        "reference_dois_sample": references,
        "cost": "free",
        "timing_ms": int((time.monotonic() - t0) * 1000),
    }


def safe_call(name, fn, *args, **kwargs):
    try:
        return fn(*args, **kwargs)
    except Exception as e:
        return {"ok": False, "error": str(e), "items": [], "cost": "free"}


def main():
    ap = argparse.ArgumentParser(description="Routed emergent enrichment (free first).")
    ap.add_argument("--query", required=False, default=None,
                    help="Research question or topic.")
    ap.add_argument("--audit", action="store_true",
                    help="Print the local Exa usage audit and exit.")
    ap.add_argument("--audit-window", default="all",
                    help="Audit window: 24h, 7d, 30d, all (default all).")
    ap.add_argument("--per-source", type=int, default=5, help="Max results per source (default 5).")
    ap.add_argument("--skip-github", action="store_true", help="Skip GitHub code search.")
    ap.add_argument("--skip-arxiv", action="store_true", help="Skip arXiv search.")
    ap.add_argument("--skip-openalex", action="store_true", help="Skip OpenAlex search.")
    ap.add_argument("--skip-s2", action="store_true",
                    help="Skip Semantic Scholar search.")
    ap.add_argument("--skip-dblp", action="store_true", help="Skip DBLP search.")
    ap.add_argument("--skip-hf", action="store_true",
                    help="Skip Hugging Face Papers search.")
    ap.add_argument("--exa-ok", action="store_true",
                    help="Allow the Exa call (costs credits). Requires explicit user approval.")
    ap.add_argument("--out", default=None, help="Optional path to write JSON result.")
    args = ap.parse_args()

    if args.audit:
        import exa_audit
        exa_audit.print_report(exa_audit.report(args.audit_window))
        return

    if not args.query:
        ap.error("--query is required (unless --audit)")

    per_source = max(1, min(20, args.per_source))
    notes = []
    sources = {}

    if args.skip_github:
        sources["github"] = None
        notes.append("github skipped by flag")
    else:
        sources["github"] = safe_call("github", github_code_search, args.query, per_source)

    if args.skip_arxiv:
        sources["arxiv"] = None
        notes.append("arxiv skipped by flag")
    else:
        sources["arxiv"] = safe_call("arxiv", arxiv_search, args.query, per_source)

    if args.skip_openalex:
        sources["openalex"] = None
        notes.append("openalex skipped by flag")
    else:
        sources["openalex"] = safe_call("openalex", openalex_search,
                                        args.query, per_source)

    if args.skip_s2:
        sources["semanticscholar"] = None
        notes.append("semanticscholar skipped by flag")
    else:
        sources["semanticscholar"] = safe_call("s2", s2_search,
                                               args.query, per_source)

    if args.skip_dblp:
        sources["dblp"] = None
        notes.append("dblp skipped by flag")
    else:
        sources["dblp"] = safe_call("dblp", dblp_search, args.query, per_source)

    if args.skip_hf:
        sources["hf_papers"] = None
        notes.append("hf_papers skipped by flag")
    else:
        sources["hf_papers"] = safe_call("hf", hf_papers_search,
                                         args.query, per_source)

    credits_spent = False
    if args.exa_ok:
        exa_res = safe_call("exa", exa_search, args.query, per_source)
        sources["exa"] = exa_res
        if exa_res.get("ok"):
            credits_spent = True
            notes.append("exa called with explicit user opt-in")
        else:
            notes.append("exa call failed: %s" % exa_res.get("error", "unknown"))
    else:
        sources["exa"] = None
        notes.append("exa skipped: no --exa-ok flag (credits preserved)")

    result = {
        "ok": True,
        "query": args.query,
        "sources": sources,
        "credits_spent": credits_spent,
        "notes": notes,
    }
    out = json.dumps(result, indent=2)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(out)
    print(out)


if __name__ == "__main__":
    main()
