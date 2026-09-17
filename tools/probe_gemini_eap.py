#!/usr/bin/env python3
"""Probe Gemini API Tool Retrieval EAP enrollment for this project.

Uses the EAP-enrolled key (GEMINI_API_KEY_2, project 654595778272, eap=1)
against the EAP model (gemini-flash-tool-retrieval) on the Interactions API
(POST /v1beta/interactions) — generateContent does NOT support tool retrieval.
Re-runnable. Never prints the key.
Exit 0 = EAP_OK, 2 = EAP_BLOCKED (billing), 1 = other failure.
"""
import json
import re
import sys
import urllib.request

SECRETS = "/home/toxic/.secrets"
EAP_MODEL = "gemini-flash-tool-retrieval"
INTERACTIONS_URL = "https://generativelanguage.googleapis.com/v1beta/interactions"


def load_eap_key():
    txt = open(SECRETS).read()
    m = re.search(r"GEMINI_API_KEY_2=[\"']?([^\"'\s]+)", txt)
    return m.group(1) if m else None


def interactions(key, payload):
    req = urllib.request.Request(
        INTERACTIONS_URL,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json", "x-goog-api-key": key},
    )
    try:
        r = urllib.request.urlopen(req, timeout=90)
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
    payload = {
        "model": EAP_MODEL,
        "input": "Convert 100 USD to EUR.",
        "tools": [
            {"type": "tool_search"},
            {
                "type": "function",
                "name": "convert_currency",
                "description": "Convert currency amount.",
                "defer_loading": True,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "amount": {"type": "number"},
                        "to": {"type": "string"},
                    },
                    "required": ["amount", "to"],
                },
            },
        ],
    }
    status, code, body = interactions(key, payload)
    if status == "OK":
        step_types = [s.get("type") for s in body.get("steps", [])]
        print(json.dumps({
            "model": EAP_MODEL,
            "http": code,
            "interaction_id": body.get("id"),
            "status": body.get("status"),
            "step_types": step_types,
        }))
        print("EAP_OK: interactions endpoint accepts tool_search + defer_loading")
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
