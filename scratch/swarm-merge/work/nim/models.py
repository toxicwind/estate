"""nim/models.py — Curated NIM model table.

Source of truth: live 82-model audit 2026-09-14 (fail-fast 5s ladder, no retries):
  55 dead-404-gated | 10 alive-fast | 9 timeout-fast | 3 unavailable-503
  3 error-other | 2 streaming-noheaders

The catalog is nondeterministic and mutates (models delist without notice:
deepseek-v4-pro vanished mid-audit; 82 -> 81 models in ~10 min). Re-verify
with NimClient.models() before scripting new ids. GET /v1/models/{id} == 200
proves listing only, NOT inference entitlement — only a real completion does.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

# --- General chat default: verified alive-fast 2026-09-14 -----------------------
DEFAULT_MODEL = "openai/gpt-oss-20b"

FAST_CHAT_MODELS: List[str] = [
    "openai/gpt-oss-20b",      # alive-fast, general chat — default
    "z-ai/glm-5.3-flash",      # alive-fast, general chat — alternate
]

VISION_MODEL = "meta/llama-3.2-11b-vision-instruct"   # alive-fast
GUARD_MODEL = "nvidia/nemotron-3.5-content-safety"    # alive-fast

# --- Cold-start: real TTFT observed 2026-09-14 ----------------------------------
# kimi-k3 ~43s TTFT (20s probe "failure" was underpowered, not infra failure).
# ultra-550b ~41s TTFT in earlier runs, alive-fast in the 82-model pass.
# These need explicit opt-in (allow_cold_start=True) or they violate fail-fast.
COLD_START_MODELS: Dict[str, Dict[str, Any]] = {
    "moonshotai/kimi-k3": {
        "ttft_s": 43, "timeout_s": 90,
        "note": "43s TTFT observed 2026-09-14; reasoning_effort defaults to max (weak signal).",
    },
    "nvidia/nemotron-3-ultra-550b-a55b": {
        "ttft_s": 41, "timeout_s": 90,
        "note": "alive-fast in 82-model pass but 41s TTFT seen earlier; nondeterministic.",
    },
}

# --- Deprecated / end-of-life ----------------------------------------------------
DEPRECATED_MODELS: Dict[str, str] = {
    # serves `deprecation: 2026-10-03T09:00:00Z` header; 503'd in latest pass
    "nvidia/nemotron-3-super-120b-a12b": "2026-10-03T09:00:00Z",
}
EOL_MODELS = {
    # HTTP 410, end-of-life 2026-08-25; later delisted from catalog entirely
    "nvidia/nemotron-3-nano-30b-a3b",
}

# --- Dead for hosted chat: 404-gated for this account/key ------------------------
# Full LEGACY class (21/21) + EMBEDDING (7/7) + REWARD (1/1) gated in the audit.
# The repo's old default meta/llama-3.1-405b-instruct is not even listed anymore.
DEAD_404_MODELS = {
    "meta/llama-3.1-405b-instruct",   # old swarm default — delisted, do not use
    "meta/llama-3.1-70b-instruct",    # old swarm alternate — gated
    "nvidia/llama-3.1-nemotron-70b-instruct",  # gated
    "nvidia/nemotron-3-nano-30b-a3b",          # 410 EOL (also in EOL_MODELS)
}

# --- Transiently unhealthy (2026-09-14 pass) --------------------------------------
UNHEALTHY_503 = {
    "nvidia/nemotron-3-super-120b-a12b",                 # overloaded / deprecation drain
    "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning",     # ResourceExhausted
}
TIMEOUT_FAST = {
    "moonshotai/kimi-k3",
    "mistralai/mistral-nemotron",   # 500 once, then timeout — nondeterministic
}

# --- Task -> model routing for swarm agents ---------------------------------------
TASK_MODEL_ROUTING: Dict[str, str] = {
    "research": DEFAULT_MODEL,
    "code": DEFAULT_MODEL,
    "analysis": DEFAULT_MODEL,
    "orchestrator": DEFAULT_MODEL,
    "proof": "z-ai/glm-5.3-flash",
    "vision": VISION_MODEL,
    "guard": GUARD_MODEL,
    "reasoning-cold": "moonshotai/kimi-k3",  # needs allow_cold_start=True
}

_MODEL_INDEX: Dict[str, Dict[str, Any]] = {}


def _build_index() -> Dict[str, Dict[str, Any]]:
    idx: Dict[str, Dict[str, Any]] = {}
    for m in FAST_CHAT_MODELS:
        idx[m] = {"id": m, "status": "alive-fast", "cold_start": False, "task": "chat"}
    idx[VISION_MODEL] = {"id": VISION_MODEL, "status": "alive-fast", "cold_start": False, "task": "vision"}
    idx[GUARD_MODEL] = {"id": GUARD_MODEL, "status": "alive-fast", "cold_start": False, "task": "guard"}
    for m, spec in COLD_START_MODELS.items():
        idx[m] = {"id": m, "status": "cold-start", "cold_start": True,
                  "timeout_s": spec["timeout_s"], "task": "reasoning",
                  "note": spec["note"]}
    for m, eol in DEPRECATED_MODELS.items():
        idx[m] = {"id": m, "status": "deprecated", "cold_start": False,
                  "deprecation": eol, "note": "serves deprecation header; 503 in latest pass"}
    for m in EOL_MODELS:
        idx[m] = {"id": m, "status": "eol-410", "cold_start": False}
    for m in DEAD_404_MODELS:
        idx.setdefault(m, {"id": m, "status": "dead-404-gated", "cold_start": False})
    for m in UNHEALTHY_503:
        idx.setdefault(m, {"id": m, "status": "unavailable-503", "cold_start": False})
    return idx


def get_model_spec(model_id: str) -> Optional[Dict[str, Any]]:
    """Return the curated spec for a model id, or None if unlisted."""
    global _MODEL_INDEX
    if not _MODEL_INDEX:
        _MODEL_INDEX = _build_index()
    return _MODEL_INDEX.get(model_id)


def is_live(model_id: str) -> bool:
    """True only for models verified answering completions 2026-09-14."""
    spec = get_model_spec(model_id)
    return bool(spec and spec["status"] in ("alive-fast", "cold-start"))
