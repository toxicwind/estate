"""lens/profiles.py — Canonical lens registry for NvidiaLensSwarm.

This module was a stub ("# profiles") on main, which made the whole repo
unimportable: lens/__init__.py and launcher.py both import from it. This is
the real implementation.

Two profile flavors exist in this repo and they are NOT the same thing:
- lens/profile.py :: LensProfile — agent-oriented (system prompt, tools,
  temperature per role: researcher/coder/analyst/orchestrator).
- swarm/transport_profiles.py :: TransportProfile — transport-oriented
  (concurrency/batch/TPS presets: architectural/cognitive/bleeding),
  ported from the Drive maximal monolith.

This module bridges them: the five canonical lenses below reuse the
agent-oriented system prompts from lens/profile.py, override the dead
llama-3.1 default models with fail-fast-verified live NIM ids (2026-09-14
audit), and build dependency-aware SwarmDAGs via build_swarm_from_lens().
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from lens.profile import (
    LensProfile,
    RESEARCHER_LENS,
    CODER_LENS,
    ANALYST_LENS,
    ORCHESTRATOR_LENS,
)
from swarm.nvidia_swarm_core import SwarmDAG, AgentNode

# --- Model constants: fail-fast verified 2026-09-14 ------------------------------
# Old defaults (llama-3.1-405b/70b-instruct) are 404-gated / delisted. Do not use.
MODEL_PRIMARY = "openai/gpt-oss-20b"                  # alive-fast general chat
MODEL_FAST = "z-ai/glm-5.3-flash"                     # alive-fast alternate
MODEL_MOE = "nvidia/nemotron-3-ultra-550b-a55b"        # cold-start (~41s TTFT); opt-in only
MODEL_ANALYSIS = "openai/gpt-oss-20b"

MAX_OUTPUT_TOKENS = 4096
CONTEXT_WINDOW = 131072
STREAM = False
TIMEOUT_SECONDS = 5.0  # fail-fast: >3-5s is useless in production

# --- Canonical lens dicts (what lens/__init__.py imports) -------------------------

def _lens_dict(profile: LensProfile, *, model: str, temperature: float,
               role: str) -> Dict[str, Any]:
    return {
        "name": profile.name,
        "role": role,
        "agent_type": profile.agent_type,
        "model": model,
        "temperature": temperature,
        "max_tokens": profile.max_tokens,
        "system_prompt": profile.system_prompt,
        "tools": profile.tools,
        "grammar": profile.grammar,
        "max_concurrent": 4,
        "timeout_seconds": TIMEOUT_SECONDS,
    }


RESEARCH_LENS: Dict[str, Any] = _lens_dict(
    RESEARCHER_LENS, model=MODEL_PRIMARY, temperature=0.2, role="research")
CODE_LENS: Dict[str, Any] = _lens_dict(
    CODER_LENS, model=MODEL_PRIMARY, temperature=0.3, role="code")
ANALYSIS_LENS: Dict[str, Any] = _lens_dict(
    ANALYST_LENS, model=MODEL_ANALYSIS, temperature=0.2, role="analysis")
ORCHESTRATOR_LENS: Dict[str, Any] = _lens_dict(
    ORCHESTRATOR_LENS, model=MODEL_PRIMARY, temperature=0.4, role="orchestrator")
PROOF_LENS: Dict[str, Any] = _lens_dict(
    CODER_LENS, model=MODEL_FAST, temperature=0.1, role="proof")
PROOF_LENS["name"] = "nvidia_prover"
PROOF_LENS["system_prompt"] = (
    "You are a proof/verification agent. Given a claim, a plan, or code, "
    "attack it: find counterexamples, check edge cases, verify each step. "
    "Be adversarial but precise. Low temperature, high rigor. When using "
    "tools, respond with JSON: {\"tool\": \"TOOL_NAME\", \"params\": {...}}"
)

ALL_LENS_PROFILES: Dict[str, Dict[str, Any]] = {
    "research": RESEARCH_LENS,
    "code": CODE_LENS,
    "analysis": ANALYSIS_LENS,
    "orchestrator": ORCHESTRATOR_LENS,
    "proof": PROOF_LENS,
}

# Accept both naming schemes (launcher uses short names; profile.py uses -er/-or).
_LENS_ALIASES = {
    "researcher": "research",
    "coder": "code",
    "analyst": "analysis",
}


def resolve_lens(name: str) -> Dict[str, Any]:
    key = _LENS_ALIASES.get(name.lower(), name.lower())
    if key not in ALL_LENS_PROFILES:
        raise KeyError(
            f"unknown lens {name!r}; choose from {sorted(ALL_LENS_PROFILES)}")
    return ALL_LENS_PROFILES[key]


def build_swarm_from_lens(lens_names: List[str],
                          transport: Optional[Any] = None) -> SwarmDAG:
    """Build a dependency-aware SwarmDAG from lens names.

    Orchestrator (if requested) fans in on every other lens so it synthesizes
    their outputs; all other lenses run in parallel in layer 0.
    """
    dag = SwarmDAG(name="lens_swarm")
    resolved = [resolve_lens(n) for n in (lens_names or ["research"])]
    orch = [l for l in resolved if l["role"] == "orchestrator"]
    workers = [l for l in resolved if l["role"] != "orchestrator"]

    for lens in workers:
        dag.add_node(AgentNode(
            agent_id=f"lens_{lens['role']}",
            name=lens["name"],
            system_prompt=lens["system_prompt"],
            tools=lens["tools"],
            model=lens["model"],
            temperature=lens["temperature"],
            max_tokens=lens["max_tokens"],
        ))
    for lens in orch:
        dag.add_node(AgentNode(
            agent_id=f"lens_{lens['role']}",
            name=lens["name"],
            system_prompt=lens["system_prompt"],
            tools=lens["tools"],
            model=lens["model"],
            temperature=lens["temperature"],
            max_tokens=lens["max_tokens"],
            dependencies={f"lens_{w['role']}" for w in workers},
        ))
    return dag
