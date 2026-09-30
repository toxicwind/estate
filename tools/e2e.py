#!/usr/bin/env python3
"""End-to-end: Gemini EAP ↔ gatehouse MCP, with TOON on results."""
import json, os, sys, ssl, time
import urllib.request, urllib.error
sys.path.insert(0, os.path.expanduser("~/sovereign"))

from tools.mcp_client import connect
from tools.payload_builder import build as build_payload
from tools.toon import savings, encode as toon_encode

GEMINI = "https://generativelanguage.googleapis.com/v1beta/interactions"
PROJ = "gen-lang-client-0111199472"

def key():
    for l in open(os.path.expanduser("~/.secrets")):
        if l.startswith("GEMINI_EAP_KEY_0="):
            return l.split("=",1)[1].strip().strip("'\"")
    raise SystemExit("no key")
K = key()
CTX = ssl.create_default_context()

def gemini(body: dict, timeout: int = 90) -> tuple[int, dict, float]:
    r = urllib.request.Request(GEMINI, data=json.dumps(body).encode(), method="POST")
    r.add_header("x-goog-api-key", K)
    r.add_header("x-goog-user-project", PROJ)
    r.add_header("Content-Type", "application/json")
    t0 = time.monotonic()
    try:
        with urllib.request.urlopen(r, timeout=timeout, context=CTX) as resp:
            return resp.status, json.loads(resp.read()), (time.monotonic()-t0)*1000
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")
        try: doc = json.loads(body)
        except Exception: doc = {"_raw": body[:500]}
        return e.code, doc, (time.monotonic()-t0)*1000

def run(query: str, max_turns: int = 8) -> dict:
    """Loop until Gemini stops emitting function_calls."""
    gh = connect()
    tools = gh.list_tools()
    print(f"  gatehouse: {len(tools)} meta-tools, session={gh.sid}")

    body = build_payload(query, session=gh)
    print(f"  payload: {len(body['tools'])} tool entries")
    transcript = []

    for turn in range(max_turns):
        code, doc, ms = gemini(body)
        if code != 200:
            err = (doc.get("error") or {}).get("message") or doc.get("_raw","")[:200]
            print(f"  turn {turn+1}: HTTP {code}  {err}")
            return {"error": err, "transcript": transcript}

        steps = doc.get("steps") or []
        step_types = [s.get("type") for s in steps]
        print(f"  turn {turn+1}: HTTP 200  {ms:.0f}ms  steps={step_types}")
        transcript.append({"turn": turn+1, "steps": steps})

        fcs = [s for s in steps if s.get("type") == "function_call"]
        if not fcs:
            # final answer
            text = ""
            for s in reversed(steps):
                if s.get("type") == "model_output":
                    c = s.get("content") or []
                    if isinstance(c, list) and c:
                        text = c[0].get("text","")
                        break
            return {"final": text, "transcript": transcript, "session": gh.sid}

        # Execute each function call against gatehouse
        function_results = []
        for fc in fcs:
            name = fc.get("name")
            args = fc.get("arguments") or {}
            print(f"    → call {name}({json.dumps(args)[:120]})")
            r = gh.call(name, args)
            result = (r.get("result") or {})
            content = result.get("content") or result
            # measure TOON savings on the result payload
            sv = savings(content) if isinstance(content, (dict, list)) else None
            if sv:
                print(f"      TOON would save {sv['saved_pct']}% "
                      f"({sv['json_bytes']}B→{sv['toon_bytes']}B)")
            function_results.append({
                "type": "function_result",
                "name": name,
                "call_id": fc.get("id"),
                "result": content,
            })

        body = {
            "model": "gemini-flash-tool-retrieval",
            "previous_interaction_id": doc.get("id"),
            "input": function_results,
            "tools": body["tools"],
        }

    return {"error":"max turns reached","transcript":transcript}

if __name__ == "__main__":
    q = " ".join(sys.argv[1:]) or (
        "Use retrieve_tools to find a tool that searches arXiv papers, "
        "then use it to search for the paper 2506.12345."
    )
    print(f"query: {q!r}")
    out = run(q)
    if "final" in out:
        print()
        print("─" * 60)
        print(out["final"])
        print("─" * 60)
