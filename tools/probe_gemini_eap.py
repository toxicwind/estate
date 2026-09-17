#!/usr/bin/env python3
"""Probe Gemini API Tool Retrieval EAP enrollment for this project.

Re-runnable. Never prints the key. Usage: python3 probe_gemini_eap.py
Exit 0 with EAP_OK when the project accepts defer_loading; EAP_BLOCKED otherwise.
"""
import json, re, sys, urllib.request

KEY_PATHS = ("/home/toxic/.secrets", "/home/toxic/sovereign/.secrets")

def load_key():
    for p in KEY_PATHS:
        try:
            txt = open(p).read()
        except OSError:
            continue
        m = re.search(r"GOOGLE_API_KEY=(\S+)", txt)
        if m:
            return m.group(1)
    return None

def gen(key, payload, model="gemini-2.5-flash"):
    url = "https://generativelanguage.googleapis.com/v1beta/models/%s:generateContent" % model
    req = urllib.request.Request(url, data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json", "x-goog-api-key": key})
    try:
        r = urllib.request.urlopen(req, timeout=30)
        return ("OK", r.status, json.loads(r.read()))
    except Exception as e:
        body = getattr(e, "read", lambda: b"")()
        try:
            body = json.loads(body)
        except Exception:
            body = {"raw": str(body)[:200]}
        return ("ERR", getattr(e, "code", "?"), body)

def main():
    key = load_key()
    if not key:
        print("EAP_BLOCKED: no GOOGLE_API_KEY in", KEY_PATHS)
        return 1
    decl = {"name": "probe_alpha", "description": "EAP enrollment probe",
            "parameters": {"type": "OBJECT", "properties": {"q": {"type": "STRING"}},
                           "required": ["q"]}}
    results = {}
    for label, extra in (("deferLoading", {"deferLoading": True}),
                         ("defer_loading", {"defer_loading": True})):
        d = dict(decl); d.update(extra)
        payload = {"contents": [{"role": "user", "parts": [{"text": "Say hello"}]}],
                   "tools": [{"functionDeclarations": [d]}]}
        status, code, body = gen(key, payload)
        err = body.get("error", {}).get("message", "") if isinstance(body, dict) else ""
        results[label] = {"status": status, "http": code, "error": err[:160]}
    print(json.dumps(results, indent=2))
    ok = any(r["status"] == "OK" for r in results.values())
    blocked_429 = any(r["http"] == 429 for r in results.values())
    if ok:
        print("EAP_OK: project accepts deferred tool declarations")
        return 0
    if blocked_429:
        print("EAP_BLOCKED: prepay credits depleted — top up at https://ai.studio/projects")
        return 2
    print("EAP_BLOCKED: unexpected response shape")
    return 1

if __name__ == "__main__":
    sys.exit(main())
