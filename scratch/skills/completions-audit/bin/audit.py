#!/usr/bin/env python3
"""audit.py — completions-audit harness.

Per-completion audit of an OpenAI-compatible /v1/chat/completions endpoint
(NVIDIA hosted NIM: https://integrate.api.nvidia.com/v1) with:

  - MICROSECOND-resolution latency landmarks via time.perf_counter_ns()
    (request_start -> first_byte/TTFB -> end, plus per-chunk ns in stream mode)
  - response integrity verification: HTTP status, response shape/schema checks,
    token usage accounting, finish_reason validation
  - timeout + error trace capture with a fail-fast dead-model taxonomy
    (404/410/503 twice -> model marked dead, remaining runs skipped)

Borrowed, not invented:
  - TykTechnologies/ai-studio proxy/stream_timing.go: nanosecond landmarks for
    request-start / first-chunk (TTFT); TPOT computed from completion token
    count after the stream drains.
  - nvidia-nim-loader/bin/nim.py: vault surrogate auth
    (add_surrogate_to_request, custom.nvidia). The raw key never leaves storage.
  - /home/toxic/model-audit-20260914.md (fleet): fail-fast dead-model taxonomy,
    no retry-spin on dead ids.
  - maximal-bench JSON (fleet): per-model status/errors/lastErr error taxonomy.
  - nvidia-nim-loader/bin/bench.py: SSE streaming measurement approach.
  - HFT doctrine (code-race SKILL.md): per-attempt ceilings, fail fast,
    latency is a correctness criterion.

Usage:
  audit.py [--models id,id,...] [--n 12] [--stream] [--max-tokens 64]
           [--timeout 60] [--prompt "..."] [--system "..."]
           [--temperature 0.2] [--out audit.jsonl]
           [--base https://integrate.api.nvidia.com/v1]

Output: one JSONL record per completion (--out file, default stdout-adjacent
<audit>.jsonl), then a summary JSON on stdout.
"""
from __future__ import annotations

import argparse
import datetime
import json
import statistics
import sys
import time
import traceback
import urllib.error
import urllib.request

sys.path.insert(0, "/opt/hatch/skills/skill-creator/bin")
from dynamic_credentials import (
    DynamicCredentialError,
    add_surrogate_to_request,
)

BASE = "https://integrate.api.nvidia.com/v1"
CRED = "custom.nvidia"
HOSTS = ["integrate.api.nvidia.com"]

DEAD_STATUSES = {"http_404", "http_410", "http_503"}
VALID_FINISH_REASONS = {"stop", "length", "tool_calls", "content_filter",
                        "function_call", None}


def now_iso() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def check(name: str, ok: bool, detail: str = "") -> dict:
    return {"name": name, "ok": bool(ok), "detail": str(detail)}


def verify_schema(data: dict, streaming: bool) -> list:
    """Shape/schema checks on a chat-completions body (or merged SSE body)."""
    checks: list = []
    checks.append(check("json_parse_ok", isinstance(data, dict)))
    if not isinstance(data, dict):
        return checks
    top = {"id", "object", "created", "model", "choices"}
    missing = sorted(top - set(data.keys()))
    checks.append(check("top_level_keys", not missing,
                        f"missing={missing}" if missing else ""))
    choices = data.get("choices")
    checks.append(check("choices_nonempty",
                        isinstance(choices, list) and len(choices) > 0,
                        f"choices={type(choices).__name__}"))
    fr = None
    if isinstance(choices, list) and choices:
        c0 = choices[0] if isinstance(choices[0], dict) else {}
        msg = c0.get("message") or {}
        delta = c0.get("delta") or {}
        content = msg.get("content") or msg.get("reasoning_content") or \
            delta.get("content") or delta.get("reasoning_content")
        checks.append(check("content_present",
                            isinstance(content, str) and len(content) > 0,
                            f"len={len(content) if isinstance(content, str) else 'n/a'}"))
        fr = c0.get("finish_reason")
        checks.append(check("finish_reason_valid", fr in VALID_FINISH_REASONS,
                            f"finish_reason={fr!r}"))
    usage = data.get("usage")
    if usage is None:
        checks.append(check("usage_present", False,
                            "no usage block" + (" (stream mode)" if streaming else "")))
    else:
        checks.append(check("usage_present", True))
        pt, ct, tt = usage.get("prompt_tokens"), usage.get("completion_tokens"), \
            usage.get("total_tokens")
        checks.append(check("usage_fields_numeric",
                            all(isinstance(v, int) for v in (pt, ct, tt)),
                            f"prompt={pt} completion={ct} total={tt}"))
        if all(isinstance(v, int) for v in (pt, ct, tt)):
            checks.append(check("usage_consistent", pt + ct == tt,
                                f"{pt}+{ct}={pt + ct} vs total={tt}"))
    return checks


def merge_sse_chunks(chunks: list) -> dict:
    """Rebuild a chat-completions-shaped body from parsed SSE data chunks."""
    merged: dict = {"object": "chat.completion.chunk", "choices": [],
                    "usage": None}
    content_parts: list = []
    finish_reason = None
    mid = None
    for ch in chunks:
        mid = mid or ch.get("id")
        if ch.get("model"):
            merged["model"] = ch["model"]
        if ch.get("created"):
            merged["created"] = ch["created"]
        if isinstance(ch.get("usage"), dict):
            merged["usage"] = ch["usage"]
        for c in ch.get("choices", []):
            if isinstance(c, dict):
                if c.get("finish_reason") and finish_reason is None:
                    finish_reason = c["finish_reason"]
                delta = c.get("delta", {}) or {}
                t = delta.get("content") or delta.get("reasoning_content") or ""
                if t:
                    content_parts.append(t)
    merged["id"] = mid
    merged["choices"] = [{"index": 0,
                          "message": {"role": "assistant",
                                      "content": "".join(content_parts)},
                          "finish_reason": finish_reason}]
    if finish_reason:
        merged["object"] = "chat.completion"
    return merged


def build_request(payload: dict) -> urllib.request.Request:
    req = urllib.request.Request(
        f"{BASE}/chat/completions",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json",
                 "Accept": "text/event-stream"},
        method="POST",
    )
    add_surrogate_to_request(req, CRED, allowed_hosts=HOSTS)
    return req


def run_streaming(payload: dict, timeout: float) -> dict:
    """One streaming completion. Landmarks in perf_counter_ns (Tyk pattern)."""
    t0 = time.perf_counter_ns()
    req = build_request(payload)
    rec: dict = {"ts": {"request_start_ns": t0}, "chunk_ns": []}
    chunks: list = []
    first_byte_ns = None
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            rec["http_status"] = resp.status
            if not 200 <= resp.status < 300:
                raise urllib.error.HTTPError(
                    req.full_url, resp.status, "bad status", resp.headers, None)
            n_chunks = 0
            while True:
                raw = resp.readline()
                t = time.perf_counter_ns()
                if not raw:
                    break
                line = raw.decode("utf-8", "replace").strip()
                if not line.startswith("data:"):
                    continue
                body = line[5:].strip()
                if body == "[DONE]":
                    rec["ts"]["done_ns"] = t
                    break
                try:
                    ch = json.loads(body)
                except json.JSONDecodeError:
                    continue
                n_chunks += 1
                if first_byte_ns is None:
                    first_byte_ns = t
                    rec["ts"]["first_byte_ns"] = t
                rec["chunk_ns"].append(t)
                chunks.append(ch)
                if n_chunks > 2000:
                    break
            rec["n_sse_chunks"] = n_chunks
            rec["ts"]["end_ns"] = time.perf_counter_ns()
            if first_byte_ns is None:
                rec["error"] = {"type": "no_chunks",
                                "detail": "stream ended with zero data chunks"}
                rec["ok"] = False
                return rec
            merged = merge_sse_chunks(chunks)
            rec["integrity"] = {"schema_ok": None, "checks": [],
                                "usage": merged.get("usage")}
            rec["integrity"]["checks"] = verify_schema(merged, streaming=True)
            rec["integrity"]["schema_ok"] = all(
                c["ok"] for c in rec["integrity"]["checks"])
            rec["finish_reason"] = merged["choices"][0]["finish_reason"]
            rec["text"] = merged["choices"][0]["message"]["content"][:200]
            ct = (merged.get("usage") or {}).get("completion_tokens")
            span = rec["ts"]["end_ns"] - first_byte_ns
            rec["latency_ns"] = {
                "ttfb": first_byte_ns - t0,
                "e2e": rec["ts"]["end_ns"] - t0,
                "tpot_avg": span / ct if ct else None,
                "tpot_basis": "completion_tokens" if ct
                              else f"n_chunks={n_chunks}",
            }
            rec["ok"] = rec["integrity"]["schema_ok"]
            return rec
    except (urllib.error.HTTPError, TimeoutError) as exc:  # noqa: BLE001
        return error_rec(rec, exc)
    except Exception as exc:  # noqa: BLE001
        return error_rec(rec, exc)


def run_single(payload: dict, timeout: float) -> dict:
    """One non-streaming completion."""
    t0 = time.perf_counter_ns()
    req = build_request(payload)
    rec: dict = {"ts": {"request_start_ns": t0}}
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            rec["http_status"] = resp.status
            if not 200 <= resp.status < 300:
                raise urllib.error.HTTPError(
                    req.full_url, resp.status, "bad status", resp.headers, None)
            body = resp.read()
            t1 = time.perf_counter_ns()
            rec["ts"]["first_byte_ns"] = t1  # non-stream: first byte == end
            rec["ts"]["end_ns"] = t1
            data = json.loads(body.decode("utf-8"))
            rec["latency_ns"] = {"ttfb": t1 - t0, "e2e": t1 - t0}
            checks = verify_schema(data, streaming=False)
            rec["integrity"] = {"schema_ok": all(c["ok"] for c in checks),
                                "checks": checks,
                                "usage": data.get("usage")}
            ch0 = (data.get("choices") or [{}])[0]
            rec["finish_reason"] = ch0.get("finish_reason")
            msg = ch0.get("message", {}) or {}
            rec["text"] = (msg.get("content") or
                           msg.get("reasoning_content") or "")[:200]
            rec["ok"] = rec["integrity"]["schema_ok"]
            return rec
    except (urllib.error.HTTPError, TimeoutError) as exc:  # noqa: BLE001
        return error_rec(rec, exc)
    except Exception as exc:  # noqa: BLE001
        return error_rec(rec, exc)


def error_rec(rec: dict, exc: BaseException) -> dict:
    rec["ts"]["end_ns"] = time.perf_counter_ns()
    code = getattr(exc, "code", None)
    if isinstance(exc, urllib.error.HTTPError):
        err_type = f"http_{code}"
        try:
            detail = exc.read().decode("utf-8", "replace")[:400]
        except Exception:
            detail = str(exc)[:400]
    elif isinstance(exc, TimeoutError):
        err_type, detail = "timeout", str(exc)[:400]
    else:
        err_type, detail = type(exc).__name__, str(exc)[:400]
    rec["http_status"] = code if isinstance(code, int) else None
    rec["ok"] = False
    rec["error"] = {"type": err_type, "detail": detail,
                    "trace": traceback.format_exc(limit=3)[-1200:]}
    return rec


def percentile(xs: list, p: float) -> float | None:
    if not xs:
        return None
    s = sorted(xs)
    k = (len(s) - 1) * p / 100
    f = int(k)
    c = min(f + 1, len(s) - 1)
    return s[f] + (s[c] - s[f]) * (k - f)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", default="openai/gpt-oss-20b")
    ap.add_argument("--n", type=int, default=12)
    ap.add_argument("--stream", action="store_true")
    ap.add_argument("--max-tokens", type=int, default=64)
    ap.add_argument("--timeout", type=float, default=60)
    ap.add_argument("--prompt", default="Reply with exactly: OK")
    ap.add_argument("--system", default="")
    ap.add_argument("--temperature", type=float, default=0.2)
    ap.add_argument("--out", default="")
    ap.add_argument("--sleep", type=float, default=1.0)
    args = ap.parse_args()

    models = [m.strip() for m in args.models.split(",") if m.strip()]
    try:
        build_request({"model": models[0], "messages": []})
    except DynamicCredentialError as exc:
        print(json.dumps({"ok": False, "error": "no_nvidia_credential",
                          "detail": str(exc)[:200]}))
        return 2

    out_path = args.out or f"audit-{now_iso()[:19].replace(':', '')}.jsonl"
    messages = []
    if args.system:
        messages.append({"role": "system", "content": args.system})
    messages.append({"role": "user", "content": args.prompt})

    dead: set = set()
    dead_hits: dict = {}
    records: list = []
    fh = open(out_path, "w")
    try:
        for model in models:
            payload = {"model": model, "messages": messages,
                       "temperature": args.temperature,
                       "max_tokens": args.max_tokens}
            if args.stream:
                payload["stream"] = True
                payload["stream_options"] = {"include_usage": True}
            for i in range(args.n):
                if model in dead:
                    break
                run = run_streaming if args.stream else run_single
                rec = run(payload, args.timeout)
                rec.update({"seq": len(records), "model": model,
                            "stream": args.stream, "wall_time": now_iso()})
                # fail-fast dead-model taxonomy (borrowed from model-audit)
                et = (rec.get("error") or {}).get("type", "")
                if et in DEAD_STATUSES:
                    dead_hits[model] = dead_hits.get(model, 0) + 1
                    if dead_hits[model] >= 2:
                        dead.add(model)
                        rec["model_marked_dead"] = True
                fh.write(json.dumps(rec) + "\n")
                fh.flush()
                records.append(rec)
                time.sleep(args.sleep)
    finally:
        fh.close()

    ok_recs = [r for r in records if r.get("ok")]
    e2e = [r["latency_ns"]["e2e"] for r in ok_recs if "latency_ns" in r]
    ttfb = [r["latency_ns"]["ttfb"] for r in ok_recs if "latency_ns" in r]
    summary = {
        "wall_time": now_iso(), "models": models, "stream": args.stream,
        "n_attempted": len(records), "n_ok": len(ok_recs),
        "n_failed": len(records) - len(ok_recs),
        "dead_models": sorted(dead),
        "error_taxonomy": {},
        "latency_ns": {
            "e2e_median": percentile(e2e, 50), "e2e_p95": percentile(e2e, 95),
            "ttfb_median": percentile(ttfb, 50), "ttfb_p95": percentile(ttfb, 95),
            "n_measured": len(e2e),
        },
        "latency_us": {
            k: (v / 1000 if v is not None else None)
            for k, v in {"e2e_median": percentile(e2e, 50),
                         "e2e_p95": percentile(e2e, 95),
                         "ttfb_median": percentile(ttfb, 50),
                         "ttfb_p95": percentile(ttfb, 95)}.items()},
        "integrity": {
            "all_passed": all(r.get("integrity", {}).get("schema_ok")
                              for r in ok_recs) if ok_recs else False,
            "failed_checks": [
                {"seq": r["seq"], "model": r["model"],
                 "failed": [c["name"] for c in
                            r.get("integrity", {}).get("checks", [])
                            if not c["ok"]]}
                for r in records
                if r.get("integrity") and not r["integrity"]["schema_ok"]],
        },
        "out": out_path,
    }
    for r in records:
        et = (r.get("error") or {}).get("type", "ok" if r.get("ok") else "?")
        summary["error_taxonomy"][et] = summary["error_taxonomy"].get(et, 0) + 1
    print(json.dumps(summary, indent=2))
    return 0 if records and ok_recs else 1


if __name__ == "__main__":
    sys.exit(main())
