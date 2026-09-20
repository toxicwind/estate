#!/usr/bin/env python3
"""launcher.py — Main entry point for NVIDIA Swarm Lens (maximal-merge).

Safe-by-default CLI:
- Auth: explicit failure when no NVIDIA credential is available. Mock
  transport is ONLY for --mock / tests / demos — never a silent fallback.
- Subsystems (ZMQ, proxy, MCP, git, unshare, envd) are opt-in via flags.
- Fail-fast: 5s transport timeouts, bounded concurrency (8).

For the lean maximal runner see swarm_maximal.py. For direct model calls
see nim/ (the shared NIM API layer — all model calls route through it).
"""
from __future__ import annotations
import asyncio, json, os, sys, time
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent / ".env")  # optional; absent on clean checkouts
except ImportError:
    pass
sys.path.insert(0, str(Path(__file__).parent))

from swarm.nvidia_swarm_core import NvidiaSwarm, SwarmDAG
from swarm.nvidia_swarm_agent import NvidiaAgent
from swarm.nvidia_swarm_transport import NvidiaNIMClient
from lens.profiles import ALL_LENS_PROFILES, build_swarm_from_lens

# Optional subsystems are imported lazily so a minimal install still runs.
_OPTIONAL = {}


def _optional(name: str, module: str, attr: str):
    if name not in _OPTIONAL:
        try:
            mod = __import__(module, fromlist=[attr])
            _OPTIONAL[name] = getattr(mod, attr)
        except Exception as exc:  # missing dep / no runtime — opt-in only
            _OPTIONAL[name] = exc
    val = _OPTIONAL[name]
    if isinstance(val, Exception):
        raise RuntimeError(f"optional subsystem {name!r} unavailable: {val}")
    return val


class LauncherAuthError(RuntimeError):
    """No NVIDIA credential and --mock not given. Fix config, don't fake it."""


class MockTransport:
    """Explicit test double. Only used with --mock."""

    async def chat_completion(self, **kwargs) -> Dict[str, Any]:
        model = kwargs.get("model", "mock")
        messages = kwargs.get("messages", [])
        await asyncio.sleep(0.05)
        last = messages[-1]["content"] if messages else ""
        return {"content": f"[MOCK {model}] Processed: {last[:80]}...",
                "tool_calls": [], "_ttft_ms": 12.0, "_tps": 4200.0,
                "_latency_ms": 50.0, "transport": "mock"}

    async def stream_completion(self, **kwargs):
        yield {"type": "token", "content": "Mock", "accumulated": "Mock"}
        yield {"type": "token", "content": " response", "accumulated": "Mock response"}
        yield {"type": "done", "accumulated": "Mock response complete.",
               "latency_ms": 50.0}

    async def close(self): pass


class SwarmLauncher:
    def __init__(self, use_mock: bool = False, api_key: Optional[str] = None,
                 enable_zmq: bool = False, enable_proxy: bool = False,
                 enable_mcp: bool = False, enable_git: bool = False,
                 enable_unshare: bool = False, enable_envd: bool = False):
        self.use_mock = use_mock
        self.api_key = api_key or os.getenv("NVIDIA_API_KEY", "")
        self.pat = os.getenv("GITHUB_TOKEN", "")
        self.flags = {"zmq": enable_zmq, "proxy": enable_proxy, "mcp": enable_mcp,
                      "git": enable_git, "unshare": enable_unshare, "envd": enable_envd}
        self.swarm: Optional[NvidiaSwarm] = None
        self.transport: Optional[Any] = None
        self.zmq = self.proxy = self.mcp = None
        self.git = self.unshare = self.envd = None
        self._metrics_log: List[Dict[str, Any]] = []

    async def init(self):
        if self.use_mock:
            print("[LAUNCHER] MOCK transport (explicit --mock)")
            self.transport = MockTransport()
        elif not self.api_key:
            raise LauncherAuthError(
                "no_nvidia_credential: set NVIDIA_API_KEY (or use the nim/ "
                "Secure Vault surrogate) — or pass --mock for an explicit "
                "test double. Refusing to silently fake a live run.")
        else:
            print("[LAUNCHER] LIVE NVIDIA NIM transport")
            self.transport = NvidiaNIMClient(api_key=self.api_key)
        self.swarm = NvidiaSwarm(transport=self.transport, max_concurrent=8,
                                 batch_size=4)
        f = self.flags
        if f["zmq"]:
            ZMQEngine = _optional("zmq", "swarm.nvidia_swarm_zmq", "ZMQEngine")
            self.zmq = ZMQEngine()
            print("[LAUNCHER] ZMQ engine connected")
        if f["proxy"]:
            ProxyStack = _optional("proxy", "swarm.nvidia_swarm_proxy", "ProxyStack")
            self.proxy = ProxyStack()
            print(f"[LAUNCHER] Proxy stack: {self.proxy.deploy()}")
        if f["mcp"]:
            MCPManager = _optional("mcp", "swarm.nvidia_swarm_mcp", "MCPManager")
            self.mcp = MCPManager()
            print("[LAUNCHER] MCP manager ready")
        if f["git"]:
            GitPushHelper = _optional("git", "swarm.nvidia_swarm_git", "GitPushHelper")
            self.git = GitPushHelper(pat=self.pat)
            print("[LAUNCHER] Git helper ready")
        if f["unshare"]:
            UnshareRoot = _optional("unshare", "swarm.nvidia_swarm_unshare", "UnshareRoot")
            self.unshare = UnshareRoot()
        if f["envd"]:
            EnvdMimicry = _optional("envd", "swarm.nvidia_swarm_envd", "EnvdMimicry")
            self.envd = EnvdMimicry()
            print(f"[LAUNCHER] Envd health: {self.envd.health()}")

    async def run_task(self, task: str, lens_names: List[str] = None,
                       context: Optional[Dict[str, Any]] = None,
                       stream: bool = False) -> Dict[str, Any]:
        lens_names = lens_names or ["research", "code", "analysis", "orchestrator"]
        context = context or {}
        context["user_task"] = task
        context["timestamp"] = time.strftime("%Y-%m-%dT%H:%M:%SZ")
        dag = build_swarm_from_lens(lens_names)
        messages = [{"role": "user", "content": task}]
        print(f"[LAUNCHER] Task: {task[:100]}...")
        print(f"[LAUNCHER] Lenses: {lens_names}")
        print(f"[LAUNCHER] DAG layers: {len(dag.topological_sort())}")
        if stream and not self.use_mock:
            print("[LAUNCHER] Streaming via orchestrator lens...")
            orch = ALL_LENS_PROFILES.get("orchestrator")
            if orch:
                async for chunk in self.transport.stream_completion(messages=messages):
                    if chunk.get("type") == "token":
                        print(chunk.get("content", ""), end="", flush=True)
                    elif chunk.get("type") == "done":
                        print(f"\n[LAUNCHER] Stream done ({chunk.get('latency_ms', 0):.0f}ms)")
                        return {"streamed": True, "final": chunk.get("accumulated")}
        result = await self.swarm.run_dag(dag, messages, context)
        agg = self.swarm.get_aggregate_metrics()
        self._metrics_log.append({"task": task[:200], "lenses": lens_names,
            "total_latency_ms": result["total_latency_ms"], "aggregate": agg})
        print(f"[LAUNCHER] DAG done in {result['total_latency_ms']:.1f}ms")
        return result

    async def close(self):
        if self.transport:
            await self.transport.close()
        if self.zmq:
            self.zmq.close()
        if self.proxy:
            self.proxy.teardown()

    def save_metrics(self, path: str = "swarm_metrics.json"):
        with open(path, "w") as f:
            json.dump(self._metrics_log, f, indent=2, default=str)
        print(f"[LAUNCHER] Metrics saved to {path}")


async def main():
    import argparse
    parser = argparse.ArgumentParser(description="NVIDIA Swarm Lens Launcher")
    parser.add_argument("--mock", action="store_true",
                        help="Use explicit mock transport (tests/demos only)")
    parser.add_argument("--task", type=str, default="", help="Task to run")
    parser.add_argument("--lenses", type=str, default="research,code,analysis,orchestrator",
                        help="Comma-separated lens names")
    parser.add_argument("--stream", action="store_true", help="Enable streaming")
    parser.add_argument("--zmq", action="store_true", help="Enable ZMQ subsystem")
    parser.add_argument("--proxy", action="store_true", help="Enable proxy subsystem")
    parser.add_argument("--mcp", action="store_true", help="Enable MCP subsystem")
    parser.add_argument("--git", action="store_true", help="Enable git helper")
    parser.add_argument("--envd", action="store_true", help="Enable envd mimicry")
    args = parser.parse_args()
    launcher = SwarmLauncher(
        use_mock=args.mock, enable_zmq=args.zmq, enable_proxy=args.proxy,
        enable_mcp=args.mcp, enable_git=args.git, enable_envd=args.envd)
    await launcher.init()
    try:
        if args.task:
            result = await launcher.run_task(
                args.task, lens_names=args.lenses.split(","), stream=args.stream)
            print(json.dumps(result, indent=2, default=str))
        else:
            result = await launcher.run_task(
                "Analyze the current codebase structure and suggest optimizations "
                "for NVIDIA NIM inference throughput.",
                lens_names=["research", "code", "analysis"])
            print("\n=== RESULT ===")
            for aid, res in result.get("results", {}).items():
                print(f"\n--- {aid} ---")
                print(res.get("content", "")[:500])
    finally:
        launcher.save_metrics()
        await launcher.close()


if __name__ == "__main__":
    asyncio.run(main())
