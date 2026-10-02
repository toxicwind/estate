"""nim/ — Unified NVIDIA NIM API layer for NvidiaLensSwarm.

OpenAI-compatible client for https://integrate.api.nvidia.com/v1 with:
- fail-fast timeouts (5s default, Chris's rule: >3-5s is useless in production)
- model-aware cold-start handling (kimi-k3 ~43s TTFT, ultra-550b slow)
- layered auth: Secure Vault surrogate (sandbox) -> NVIDIA_API_KEY env -> clean error
- curated model table from the 2026-09-14 82-model live audit

Sovereign seam: this client speaks plain OpenAI-compatible /v1/chat/completions,
so it can be registered as a herd upstream (herd = inference router, :25100/v1)
without changes. See SOVEREIGN.md.
"""
from .models import (
    DEFAULT_MODEL,
    FAST_CHAT_MODELS,
    VISION_MODEL,
    GUARD_MODEL,
    COLD_START_MODELS,
    DEPRECATED_MODELS,
    EOL_MODELS,
    DEAD_404_MODELS,
    TASK_MODEL_ROUTING,
    get_model_spec,
    is_live,
)
from .client import (
    NimClient,
    AsyncNimClient,
    NimError,
    NimAuthError,
    NimHTTPError,
    NimTimeoutError,
    ColdStartModelError,
    DeadModelError,
    FAIL_FAST_TIMEOUT,
    COLD_START_TIMEOUT,
)

__all__ = [
    "DEFAULT_MODEL", "FAST_CHAT_MODELS", "VISION_MODEL", "GUARD_MODEL",
    "COLD_START_MODELS", "DEPRECATED_MODELS", "EOL_MODELS", "DEAD_404_MODELS",
    "TASK_MODEL_ROUTING", "get_model_spec", "is_live",
    "NimClient", "AsyncNimClient",
    "NimError", "NimAuthError", "NimHTTPError", "NimTimeoutError",
    "ColdStartModelError", "DeadModelError",
    "FAIL_FAST_TIMEOUT", "COLD_START_TIMEOUT",
]
