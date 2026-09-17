#!/usr/bin/env python3
"""Probe Gemini API Tool Retrieval EAP enrollment for this project.

Uses the EAP-enrolled key (GEMINI_API_KEY_2, project 654595778272, eap=1)
against the EAP model (models/gemini-flash-tool-retrieval).
Re-runnable. Never prints the key.
Exit 0 = EAP_OK, 2 = EAP_BLOCKED (billing), 1 = other failure.
"""
import json
import re
import sys
import urllib.request

SECRETS = "/home/toxic/.secrets"
EAP_MODEL = "gemini-flash-tool-retrieval"


def load_eap_key():
    txt = open(SECRETS).read()
    m = re.search(r"GEMINI_API_KEY_2=[\"']?([^\"'\s]+)", txt)
    return m.group(1) if m else None


def gen(key, payload, model=EAP_MODEL):
    url = "https://generativelanguage.googleapis.com/v1beta/models/%s:generateContent" % model
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json", "x-goog-api-key": key},
    )
    try:
        r = urllib.request.urlopen(req, timeout=60)
        return ("OK", r.status, json.loads(r.read()))
    except Exception as e:
        body = getattr(e, "read", lambda: b"")()
        try:
            body = json.loads(body)
        except Exception:
            body = {"raw": str(body)[:200]}
        return ("ERR", getattr(e, "code", "?"), body)


def main():
    key = load_eap_key()
    if not key:
        print("EAP_BLOCKED: no GEMINI_API_KEY_2 in", SECRETS)
        return 1
    decls = [
        {
            "name": "probe_alpha",
            "description": "EAP enrollment probe",
            "deferLoading": True,
            "parameters": {
                "type": "OBJECT",
                "properties": {"q": {"type": "STRING"}},
                "required": ["q"],
            },
        }
    ]
    payload = {
        "contents": [{"role": "user", "parts": [{"text": "Say hello"}]}],
        "tools": [{"functionDeclarations": decls}],
    }
    status, code, body = gen(key, payload)
    if status == "OK":
        text = ""
        try:
            text = body["candidates"][0]["content"]["parts"][0].get("text", "")
        except Exception:
            pass
        print(json.dumps({"model": EAP_MODEL, "http": code, "text_head": text[:120]}))
        print("EAP_OK: project accepts deferred tool declarations")
        return 0
    err = body.get("error", {}).get("message", "") if isinstance(body, dict) else ""
    print(json.dumps({"model": EAP_MODEL, "http": code, "error": err[:200]}))
    if code == 429:
        print("EAP_BLOCKED: prepay credits depleted — top up at https://ai.studio/projects")
        return 2
    print("EAP_BLOCKED: unexpected response")
    return 1


if __name__ == "__main__":
    sys.exit(main())
