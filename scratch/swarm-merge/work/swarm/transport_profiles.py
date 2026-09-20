"""swarm/transport_profiles.py — Transport tuning presets.

Ported from the Drive maximal monolith (its "LensProfile" was transport-
oriented: concurrency/batch/TPS — a different animal from lens/profile.py's
agent-oriented LensProfile, hence the rename).

The Drive originals assumed a local Triton gRPC endpoint, 20s timeouts, and
concurrency up to 128. This merge targets hosted NIM with fail-fast rules,
so values are re-based: timeout 5s, bounded concurrency. The *shapes*
(three orthogonal presets) are preserved.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

FAIL_FAST_TIMEOUT = 5.0


@dataclass
class TransportProfile:
    name: str = "architectural"
    transport: str = "nim-http"   # hosted NIM; "triton-grpc" only for local Triton
    concurrency: int = 8
    batch_size: int = 4
    tps_target: int = 2500
    grammar_mode: str = "regex"   # "regex" (JSON) or "tag" (<tool_call>)
    kv_cache_optimized: bool = True
    persistent_conn: bool = True
    timeout_guard_sec: float = FAIL_FAST_TIMEOUT


TRANSPORT_PROFILES: Dict[str, TransportProfile] = {
    "architectural": TransportProfile(
        name="architectural",
        transport="nim-http",
        concurrency=8,
        batch_size=4,
        tps_target=2500,
        grammar_mode="regex",
        kv_cache_optimized=True,
        persistent_conn=True,
        timeout_guard_sec=FAIL_FAST_TIMEOUT,
    ),
    "cognitive": TransportProfile(
        name="cognitive",
        transport="nim-http",
        concurrency=4,
        batch_size=2,
        tps_target=1800,
        grammar_mode="tag",
        kv_cache_optimized=True,
        persistent_conn=True,
        timeout_guard_sec=FAIL_FAST_TIMEOUT,
    ),
    "bleeding": TransportProfile(
        name="bleeding",
        transport="nim-http",
        concurrency=16,
        batch_size=8,
        tps_target=3500,
        grammar_mode="regex",
        kv_cache_optimized=True,
        persistent_conn=True,
        timeout_guard_sec=FAIL_FAST_TIMEOUT,
    ),
}


def get_transport_profile(name: str = "architectural") -> TransportProfile:
    if name not in TRANSPORT_PROFILES:
        raise KeyError(f"unknown transport profile {name!r}; "
                       f"choose from {sorted(TRANSPORT_PROFILES)}")
    return TRANSPORT_PROFILES[name]
