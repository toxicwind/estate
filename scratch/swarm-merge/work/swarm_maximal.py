"""swarm_maximal.py — Maximal single-entry wiring for NvidiaLensSwarm.

The old file was a stub ("# swarm"). This is the real maximal composition:
transport preset (architectural/cognitive/bleeding) + canonical lens DAG
(research/code/analysis/orchestrator/proof) + the unified nim/ API layer,
all fail-fast and model-aware.

Two execution styles:
- Async DAG via the repo's NvidiaSwarm engine (NvidiaNIMClient transport).
- Direct single-call via nim.NimClient (stdlib, surrogate auth).

Examples:
    python swarm_maximal.py --task "summarize this repo" --lenses research,code
    python swarm_maximal.py --ping            # NIM reachability + live models
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

sys.path.insert(0, str(Path(__file__).parent))

from nim import NimClient, NimError, DEFAULT_MODEL, FAIL_FAST_TIMEOUT
from nim.models import TASK_MODEL_ROUTING
from swarm.nvidia_swarm_core import NvidiaSwarm, SwarmDAG
from swarm.nvidia_swarm_transport import NvidiaNIMClient
from swarm.transport_profiles import get_transport_profile
from lens.profiles import build_swarm_from_lens, ALL_LENS_PROFILES


class MaximalSwarm:
    """Fail-fast swarm: preset transport + lens DAG, one call to run."""

    def __init__(self, profile: str = "architectural",
                 api_key: Optional[str] = None):
        self.preset = get_transport_profile(profile)
        self.transport = NvidiaNIMClient(api_key=api_key)
        self.swarm = NvidiaSwarm(
            transport=self.transport,
            max_concurrent=self.preset.concurrency,
            batch_size=self.preset.batch_size,
        )

    async def run(self, task: str,
                  lenses: List[str] = ("research", "code"),
                  context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        unknown = [l for l in lenses if l not in ALL_LENS_PROFILES]
        if unknown:
            raise KeyError(f"unknown lenses {unknown}; "
                           f"choose from {sorted(ALL_LENS_PROFILES)}")
        dag = build_swarm_from_lens(list(lenses))
        messages = [{"role": "user", "content": task}]
        return await self.swarm.run_dag(dag, messages, context or {})

    async def close(self) -> None:
        await self.transport.close()


async def _amain(args: argparse.Namespace) -> int:
    if args.ping:
        client = NimClient(timeout=FAIL_FAST_TIMEOUT)
        try:
            print(json.dumps(client.ping(), indent=2))
            models = client.models()
            print(f"live catalog: {len(models)} models")
            print("default:", DEFAULT_MODEL)
            return 0
        except NimError as exc:
            print(json.dumps({"ok": False, "error": str(exc)}))
            return 1
    if args.lenses_list:
        print(json.dumps(
            {k: {"model": v["model"], "role": v["role"]}
             for k, v in ALL_LENS_PROFILES.items()}, indent=2))
        return 0
    swarm = MaximalSwarm(profile=args.profile)
    try:
        result = await swarm.run(args.task, lenses=args.lenses.split(","))
    except (NimError, KeyError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}))
        return 1
    finally:
        await swarm.close()
    print(json.dumps(result, indent=2, default=str))
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Maximal NvidiaLensSwarm runner")
    ap.add_argument("--task", default="Analyze this repo and suggest next steps.",
                    help="Task prompt for the swarm")
    ap.add_argument("--lenses", default="research,code",
                    help="Comma-separated lens names")
    ap.add_argument("--profile", default="architectural",
                    choices=["architectural", "cognitive", "bleeding"],
                    help="Transport tuning preset")
    ap.add_argument("--ping", action="store_true", help="NIM reachability check")
    ap.add_argument("--lenses-list", action="store_true", help="List lens profiles")
    args = ap.parse_args()
    return asyncio.run(_amain(args))


if __name__ == "__main__":
    raise SystemExit(main())
