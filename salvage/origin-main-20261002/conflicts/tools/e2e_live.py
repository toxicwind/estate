#!/usr/bin/env python3
"""Gemini EAP ↔ gatehouse MCP end-to-end, live, untruncated."""
import json, os, sys, ssl, time
import urllib.request, urllib.error
sys.path.insert(0, os.path.expanduser("~/sovereign"))
from tools.mcp_client import connect
from tools.payload_builder import build
from tools.toon import savings

GEMINI = "https://generativelanguage.googleapis.com/v1beta/interactions"
PROJ   = "gen-lang-client-0111199472"

def key():
    for l in open(os.path.expanduser("~/.secrets")):
        if l.startswith("GEMINI_EAP_KEY_0="):
            return l.split("=", 1)[1].strip().strip("\"'")
    raise SystemExit("no GEMINI_EAP_KEY_0")
K, CTX = key(), ssl.create_default_context()

def log(*a, **kw): print(*a, **kw, flush=True)

def gemini(body, timeout=120):
    r = urllib.request.Request(GEMINI, data=json.dumps(body).encode(), method="POST")
    r.add_header("x-goog-api-key", K)
    r.add_header("x-goog-user-project", PROJ)
    r.add_header("Content-Type", "application/json")
    t0 = time.monotonic()
    try:
        with urllib.request.urlopen(r, timeout=timeout, context=CTX) as resp:
            return resp.status, json.loads(resp.read()), (time.monotonic()-t0)*1000
    except urllib.error.HTTPError as e:
        raw = e.read().decode(errors="replace")
        try: doc = json.loads(raw)
        except Exception: doc = {"_raw": raw[:1000]}
        return e.code, doc, (time.monotonic()-t0)*1000

def run(query, max_turns=10):
    gh = connect()
    log(f"gatehouse: {len(gh.list_tools())} meta-tools, session={gh.sid}")
    body = build(query, session=gh)
    log(f"payload: {len(body['tools'])} tool entries")
    log("=" * 78)

    for turn in range(max_turns):
        code, doc, ms = gemini(body)
        if code != 200:
            log(f"turn {turn+1}: HTTP {code}\n{json.dumps(doc, indent=2)[:3000]}")
            return
        steps = doc.get("steps") or []
        log(f"\n─── turn {turn+1} ─── HTTP 200  {ms:.0f}ms  steps={[s.get('type') for s in steps]}")
        for s in steps:
            log(f"  [{s.get('type')}]")
            log(f"    {json.dumps(s, indent=2, ensure_ascii=False)}")

        fcs = [s for s in steps if s.get("type") == "function_call"]
        if not fcs:
            log("\n" + "=" * 78)
            log("FINAL ANSWER")
            log("=" * 78)
            for s in steps:
                if s.get("type") == "model_output":
                    for c in (s.get("content") or []):
                        if c.get("type") == "text": log(c["text"])
            return

        results = []
        for fc in fcs:
            name, args = fc.get("name"), fc.get("arguments") or {}
            log(f"\n  → gatehouse.call({name})")
            log(f"    args={json.dumps(args, indent=2)}")
            t0 = time.monotonic()
            rr = gh.call(name, args)
            call_ms = (time.monotonic()-t0)*1000
            content = ((rr.get("result") or {}).get("content")) or rr
            size = len(json.dumps(content, ensure_ascii=False))
            log(f"    ← {size}B in {call_ms:.0f}ms")
            sv = savings(content) if isinstance(content, (dict, list)) else None
            if sv:
                note = "TOON" if sv["toon_applied"] else "JSON"
                log(f"    {note}: {sv['saved_pct']:+}%  ({sv['json_bytes']}B→{sv['toon_bytes']}B)")
            log(f"    result: {json.dumps(content, indent=2, ensure_ascii=False)[:4000]}")
            results.append({"type": "function_result", "name": name,
                            "call_id": fc.get("id"), "result": content})
        body = {"model": "gemini-flash-tool-retrieval",
                "previous_interaction_id": doc.get("id"),
                "input": results, "tools": body["tools"]}

if __name__ == "__main__":
    q = " ".join(sys.argv[1:]) or (
        "Use retrieve_tools to find arXiv search tools. "
        "Then use arxiv:search_papers with date_from='2026-09-28' "
        "and sort_by='date' to find the newest cs.LG paper. "
        "Report the arXiv ID, title, and authors.")
    log(f"query: {q!r}")
    run(q)
