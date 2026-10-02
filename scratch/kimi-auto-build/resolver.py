#!/usr/bin/env python3
"""kimi-auto resolver — scheduled Kimi model auditor/selector.

Runs on a timer (systemd user timer). Each run:

  1. MODELS-AWARE:  GET <herd>/v1/models, filter to Kimi-family ids.
  2. SECRETS-AWARE: record which credential NAMES are present in the
     environment (never values) — MOONSHOT_API_KEY, KIMI_API_KEY,
     OPENROUTER_API_KEY, NVIDIA_API_KEY.
  3. BENCHMARK-DRIVEN: probe every Kimi candidate with a minimal chat
     completion; measure latency and success.
  4. Select the best (successful, then fastest) and atomically write
     the state file consumed by shim.py and the Tau extension.

Never prints, logs, or stores secret values — only names/presence.
"""

import argparse
import datetime
import http.client
import json
import os
import re
import sys
import tempfile
import time
from urllib.parse import urlparse

DEFAULT_HERD = "http://127.0.0.1:25100"
DEFAULT_STATE = os.path.expanduser("~/.local/share/kimi-auto/state.json")
DEFAULT_LOG = os.path.expanduser("~/.local/share/kimi-auto/resolver.log")

KIMI_RE = re.compile(r"kimi|moonshot", re.IGNORECASE)

# Credential NAMES the selector is aware of. Presence only — values are
# never read, printed, or stored.
SECRET_NAMES = [
    "MOONSHOT_API_KEY",
    "KIMI_API_KEY",
    "OPENROUTER_API_KEY",
    "NVIDIA_API_KEY",
]

PROBE_TIMEOUT = 60


def log(msg, log_path):
    line = f"{datetime.datetime.now().isoformat(timespec='seconds')} {msg}"
    print(line, flush=True)
    try:
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        with open(log_path, "a", encoding="utf-8") as fh:
            fh.write(line + "\n")
    except Exception:
        pass


def herd_request(herd_url, method, path, body=None, timeout=30):
    u = urlparse(herd_url)
    conn = http.client.HTTPConnection(u.hostname, u.port or 80, timeout=timeout)
    headers = {}
    data = None
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    conn.request(method, path, body=data, headers=headers)
    resp = conn.getresponse()
    payload = resp.read()
    conn.close()
    return resp.status, payload


def list_models(herd_url):
    status, payload = herd_request(herd_url, "GET", "/v1/models", timeout=15)
    if status != 200:
        raise RuntimeError(f"/v1/models -> HTTP {status}")
    data = json.loads(payload.decode("utf-8"))
    return [m["id"] for m in data.get("data", []) if m.get("id")]


def probe_model(herd_url, model_id):
    """Minimal chat probe. Returns (ok, latency_ms, note)."""
    body = {
        "model": model_id,
        "messages": [{"role": "user", "content": "ping"}],
        "max_tokens": 5,
    }
    start = time.monotonic()
    try:
        status, payload = herd_request(
            herd_url, "POST", "/v1/chat/completions", body, timeout=PROBE_TIMEOUT
        )
        latency_ms = int((time.monotonic() - start) * 1000)
        if status != 200:
            return False, latency_ms, f"http_{status}"
        data = json.loads(payload.decode("utf-8"))
        if data.get("choices"):
            return True, latency_ms, "ok"
        return False, latency_ms, "no_choices"
    except Exception as exc:
        latency_ms = int((time.monotonic() - start) * 1000)
        return False, latency_ms, f"error:{type(exc).__name__}"


def write_state_atomic(state_path, state):
    os.makedirs(os.path.dirname(state_path), exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(state_path), prefix=".state-")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(state, fh, indent=2)
            fh.write("\n")
        os.replace(tmp, state_path)
    finally:
        try:
            os.unlink(tmp)
        except OSError:
            pass


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--herd", default=os.environ.get("KIMI_AUTO_HERD", DEFAULT_HERD))
    ap.add_argument("--state", default=os.environ.get("KIMI_AUTO_STATE", DEFAULT_STATE))
    ap.add_argument("--log", default=os.environ.get("KIMI_AUTO_LOG", DEFAULT_LOG))
    ap.add_argument("--dry-run", action="store_true", help="probe and report, do not write state")
    args = ap.parse_args()

    secrets_present = [n for n in SECRET_NAMES if n in os.environ and os.environ[n]]
    secrets_missing = [n for n in SECRET_NAMES if n not in secrets_present]
    log(f"secrets present: {secrets_present or ['(none)']}; missing: {secrets_missing}", args.log)

    try:
        model_ids = list_models(args.herd)
    except Exception as exc:
        log(f"FATAL: cannot list herd models: {exc}", args.log)
        return 2

    kimi_ids = [m for m in model_ids if KIMI_RE.search(m)]
    log(f"herd models: {len(model_ids)} total, Kimi candidates: {kimi_ids or ['(none)']}", args.log)

    results = []
    for mid in kimi_ids:
        ok, latency_ms, note = probe_model(args.herd, mid)
        results.append({"id": mid, "ok": ok, "latency_ms": latency_ms, "note": note})
        log(f"probe {mid}: ok={ok} latency={latency_ms}ms note={note}", args.log)

    viable = sorted(
        [r for r in results if r["ok"]], key=lambda r: r["latency_ms"]
    )
    now = datetime.datetime.now(datetime.timezone.utc).astimezone().isoformat(timespec="seconds")

    if not viable:
        log("no viable Kimi candidate; state left unchanged", args.log)
        # Still record the failed audit for observability, but keep last good model.
        prev_model = None
        try:
            with open(args.state, encoding="utf-8") as fh:
                prev_model = json.load(fh).get("model")
        except Exception:
            pass
        state = {
            "model": prev_model or "kimi-k3",
            "updated_at": now,
            "resolver": "kimi-auto-resolver/1.0",
            "healthy": False,
            "reason": "no Kimi candidate passed probe; keeping last known",
            "secrets_present": secrets_present,
            "secrets_missing": secrets_missing,
            "candidates": results,
        }
    else:
        best = viable[0]
        reason_bits = [f"{best['id']} fastest healthy probe ({best['latency_ms']}ms)"]
        if len(viable) > 1:
            alts = ", ".join(f"{r['id']} ({r['latency_ms']}ms)" for r in viable[1:])
            reason_bits.append(f"alternates: {alts}")
        state = {
            "model": best["id"],
            "updated_at": now,
            "resolver": "kimi-auto-resolver/1.0",
            "healthy": True,
            "reason": "; ".join(reason_bits),
            "secrets_present": secrets_present,
            "secrets_missing": secrets_missing,
            "candidates": results,
        }

    if args.dry_run:
        print(json.dumps(state, indent=2))
        return 0

    write_state_atomic(args.state, state)
    log(f"selected: {state['model']} (healthy={state['healthy']}) -> {args.state}", args.log)
    return 0


if __name__ == "__main__":
    sys.exit(main())
