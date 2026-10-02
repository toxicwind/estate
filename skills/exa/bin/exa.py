#!/usr/bin/env python3
"""Exa AI search CLI using the stored custom.exa credential.

Usage:
  exa.py search <query> [--n N] [--type auto|neural|keyword]
                         [--livecrawl always|fallback|never] [--chars N]
  exa.py contents <url>... [--chars N]
  exa.py find-similar <url> [--n N]
  exa.py answer <query>

Output: JSON on stdout. Every call is appended to
~/.cache/shingle/exa_calls.jsonl (endpoint, elapsed_ms, ok, cost_usd).

Auth: Secure Vault connector custom.exa. Only the hsurr:* surrogate is sent,
and only to api.exa.ai; authd substitutes the real key at egress time.
"""
import json
import os
import sys
import time
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dynamic_credentials as dc

ALLOWED = ["api.exa.ai"]
CRED = "custom.exa"
BASE = "https://api.exa.ai"
CALL_LOG = os.path.expanduser("~/.cache/shingle/exa_calls.jsonl")


def _log(endpoint, elapsed_ms, ok, cost_usd, query):
    try:
        os.makedirs(os.path.dirname(CALL_LOG), exist_ok=True)
        with open(CALL_LOG, "a") as f:
            f.write(json.dumps({
                "ts": time.time(), "endpoint": endpoint,
                "elapsed_ms": int(elapsed_ms), "ok": ok,
                "cost_usd": cost_usd, "query": str(query)[:120],
            }) + "\n")
    except OSError:
        pass


def _post(path, payload, timeout=60):
    url = BASE + path
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("Content-Type", "application/json")
    req.add_header("User-Agent", "muse-exa-skill/1.0")
    t0 = time.perf_counter()
    ok, cost = False, None
    try:
        dc.add_surrogate_to_request(req, CRED, allowed_hosts=ALLOWED)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            result = dc.read_json_response(resp)
        ok = True
        cost = (result.get("costDollars") or {}).get("total")
        return result
    finally:
        _log(path, (time.perf_counter() - t0) * 1000, ok, cost,
             json.dumps(payload)[:120])


def _take_flag(rest, name, default=None):
    if name in rest:
        i = rest.index(name)
        try:
            val = rest[i + 1]
        except IndexError:
            raise ValueError(f"{name} needs a value")
        return val, rest[:i] + rest[i + 2:]
    return default, rest


def _take_bool(rest, name):
    if name in rest:
        return True, [x for x in rest if x != name]
    return False, rest


def cmd_search(rest):
    n, rest = _take_flag(rest, "--n", "5")
    stype, rest = _take_flag(rest, "--type", "auto")
    livecrawl, rest = _take_flag(rest, "--livecrawl", "fallback")
    chars, rest = _take_flag(rest, "--chars", None)
    if not rest:
        raise ValueError("query required")
    payload = {"query": " ".join(rest), "numResults": int(n),
               "type": stype, "livecrawl": livecrawl}
    if chars:
        payload["contents"] = {"text": {"maxCharacters": int(chars)}}
    return _post("/search", payload)


def cmd_contents(rest):
    chars, rest = _take_flag(rest, "--chars", "8000")
    if not rest:
        raise ValueError("at least one url required")
    return _post("/contents", {"urls": rest,
                               "text": {"maxCharacters": int(chars)}})


def cmd_find_similar(rest):
    n, rest = _take_flag(rest, "--n", "5")
    if not rest:
        raise ValueError("url required")
    return _post("/findSimilar", {"url": rest[0], "numResults": int(n)})


def cmd_answer(rest):
    if not rest:
        raise ValueError("query required")
    return _post("/answer", {"query": " ".join(rest)})


def main(argv):
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__)
        return 0
    cmd, rest = argv[0], argv[1:]
    try:
        if cmd == "search":
            out = cmd_search(rest)
        elif cmd == "contents":
            out = cmd_contents(rest)
        elif cmd == "find-similar":
            out = cmd_find_similar(rest)
        elif cmd == "answer":
            out = cmd_answer(rest)
        else:
            raise ValueError(f"unknown command: {cmd}")
    except ValueError as e:
        print(json.dumps({"error": str(e)}))
        return 2
    except dc.DynamicCredentialError as e:
        print(json.dumps({"error": f"credential: {e}"}))
        return 3
    print(json.dumps(out, indent=1)[:20000])
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))