#!/usr/bin/env python3
"""
allowlist.py — Durable allowlist of models VERIFIED live by real probes.

This is the source of truth for herd routing — NOT any provider's catalog.
A model is only here if probe_truth.py returned LIVE with a real completion.

Usage:
    from allowlist import check, record, list_live
    check('nim', 'moonshotai/kimi-k2.6')  → None (not allowlisted) or entry
    record('openrouter', 'nvidia/nemotron-3-super-120b-a12b:free', latency_ms=489)
"""
import json
import os
from datetime import datetime, timezone

ALLOWLIST_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'allowlist.json')


def _now():
    return datetime.now(timezone.utc).isoformat()


def load():
    if os.path.exists(ALLOWLIST_PATH):
        with open(ALLOWLIST_PATH) as f:
            return json.load(f)
    return {"models": [], "updated": _now()}


def save(data):
    data["updated"] = _now()
    with open(ALLOWLIST_PATH, 'w') as f:
        json.dump(data, f, indent=2)


def record(provider, model_id, latency_ms=None, notes=None):
    """Record a model as verified-live. Called after probe_truth returns LIVE."""
    data = load()
    # Remove existing entry for same provider+model
    data["models"] = [m for m in data["models"]
                      if not (m["provider"] == provider and m["model"] == model_id)]
    data["models"].append({
        "provider": provider,
        "model": model_id,
        "last_verified": _now(),
        "latency_ms": latency_ms,
        "notes": notes or "",
        "verification": "probe_truth.py LIVE (real completion)",
    })
    save(data)
    return True


def revoke(provider, model_id, reason=""):
    """Remove a model that stopped verifying."""
    data = load()
    before = len(data["models"])
    data["models"] = [m for m in data["models"]
                      if not (m["provider"] == provider and m["model"] == model_id)]
    if len(data["models"]) < before:
        # Log the revocation
        data.setdefault("revocations", []).append({
            "provider": provider,
            "model": model_id,
            "revoked_at": _now(),
            "reason": reason,
        })
        save(data)
        return True
    return False


def check(provider, model_id, max_age_hours=24):
    """
    Check if a model is allowlisted and freshly verified.
    Returns the entry, or None if not listed or stale.
    """
    data = load()
    for m in data["models"]:
        if m["provider"] == provider and m["model"] == model_id:
            verified = datetime.fromisoformat(m["last_verified"])
            age_h = (datetime.now(timezone.utc) - verified).total_seconds() / 3600
            if age_h <= max_age_hours:
                return m
            return None  # stale
    return None


def list_live(provider=None):
    """List all allowlisted models, optionally filtered by provider."""
    data = load()
    models = data["models"]
    if provider:
        models = [m for m in models if m["provider"] == provider]
    return sorted(models, key=lambda m: (m["provider"], m["model"]))


def seed_from_probe_results(results):
    """Bulk-seed from probe_truth results. `results` = list of probe() dicts."""
    count = 0
    for r in results:
        if r.get("verdict") == "LIVE":
            record(r["provider"], r["model"], r.get("latency_ms"),
                   r.get("reframed", "")[:100])
            count += 1
    return count


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print(json.dumps(load(), indent=2))
    elif sys.argv[1] == "check":
        r = check(sys.argv[2], sys.argv[3])
        print(json.dumps(r, indent=2) if r else "NOT-ALLOWLISTED")
    elif sys.argv[1] == "list":
        prov = sys.argv[2] if len(sys.argv) > 2 else None
        for m in list_live(prov):
            print(f"{m['provider']:12} {m['model']:50} {m['latency_ms']}ms {m['last_verified'][:16]}")
