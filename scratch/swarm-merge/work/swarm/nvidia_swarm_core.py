"""nvidia_swarm_core.py — Async DAG execution engine for NVIDIA NIM Swarm."""
from __future__ import annotations
import asyncio, json, time, uuid, logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple, Coroutine
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger("nvidia_swarm.core")

@dataclass
class AgentNode:
    agent_id: str
    name: str
    system_prompt: str
    tools: List[Dict[str, Any]] = field(default_factory=list)
    model: str = "openai/gpt-oss-20b"  # fail-fast verified 2026-09-14; old llama-3.1-405b default is dead
    temperature: float = 0.3
    max_tokens: int = 4096
    dependencies: Set[str] = field(default_factory=set)
    handoff_targets: List[str] = field(default_factory=list)
    _result: Optional[Dict[str, Any]] = field(default=None, repr=False)
    _status: str = field(default="pending", repr=False)
    _latency_ms: float = field(default=0.0, repr=False)
    _ttft_ms: float = field(default=0.0, repr=False)
    _tps: float = field(default=0.0, repr=False)

    def to_dict(self) -> Dict[str, Any]:
        return {"agent_id": self.agent_id, "name": self.name, "model": self.model,
                "dependencies": list(self.dependencies), "handoff_targets": self.handoff_targets,
                "status": self._status, "latency_ms": self._latency_ms,
                "ttft_ms": self._ttft_ms, "tps": self._tps}

class SwarmDAG:
    def __init__(self, name: str = "swarm_dag"):
        self.name = name
        self.nodes: Dict[str, AgentNode] = {}
        self.edges: Dict[str, Set[str]] = {}
        self._lock = asyncio.Lock()

    def add_node(self, node: AgentNode) -> "SwarmDAG":
        self.nodes[node.agent_id] = node
        if node.agent_id not in self.edges:
            self.edges[node.agent_id] = set()
        for dep in node.dependencies:
            if dep not in self.edges:
                self.edges[dep] = set()
            self.edges[dep].add(node.agent_id)
        return self

    def topological_sort(self) -> List[List[str]]:
        in_degree = {aid: len(n.dependencies) for aid, n in self.nodes.items()}
        layers: List[List[str]] = []
        remaining = set(self.nodes.keys())
        while remaining:
            layer = [aid for aid in remaining if in_degree[aid] == 0]
            if not layer:
                raise ValueError("Cycle detected in SwarmDAG")
            layers.append(layer)
            for aid in layer:
                remaining.remove(aid)
                for downstream in self.edges.get(aid, set()):
                    in_degree[downstream] -= 1
        return layers

class NvidiaSwarm:
    def __init__(self, transport: Any, max_concurrent: int = 50, batch_size: int = 8, enable_batching: bool = True):
        self.transport = transport
        self.max_concurrent = max_concurrent
        self.batch_size = batch_size
        self.enable_batching = enable_batching
        self._semaphore = asyncio.Semaphore(max_concurrent)
        self._executor = ThreadPoolExecutor(max_workers=max_concurrent)
        self._metrics: List[Dict[str, Any]] = []

    async def run_dag(self, dag: SwarmDAG, initial_messages: List[Dict[str, str]], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        context = context or {}
        completed: Set[str] = set()
        all_results: Dict[str, Any] = {}
        start_time = time.perf_counter()
        layers = dag.topological_sort()
        logger.info(f"DAG '{dag.name}': {len(dag.nodes)} nodes, {len(layers)} layers")
        for layer_idx, layer in enumerate(layers):
            layer_start = time.perf_counter()
            tasks = [self._execute_node(dag.nodes[aid], self._build_messages(dag.nodes[aid], initial_messages, all_results, context), context) for aid in layer]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for aid, res in zip(layer, results):
                if isinstance(res, Exception):
                    dag.nodes[aid]._status = "error"
                    logger.error(f"Node {aid} failed: {res}")
                    all_results[aid] = {"error": str(res)}
                else:
                    dag.nodes[aid]._status = "completed"
                    dag.nodes[aid]._result = res
                    all_results[aid] = res
                    completed.add(aid)
            logger.info(f"Layer {layer_idx} done in {(time.perf_counter()-layer_start)*1000:.1f}ms")
        return {"dag_name": dag.name, "total_latency_ms": (time.perf_counter()-start_time)*1000,
                "layers_executed": len(layers), "nodes_completed": len(completed),
                "results": all_results, "node_metrics": {aid: n.to_dict() for aid, n in dag.nodes.items()}}

    async def _execute_node(self, node: AgentNode, messages: List[Dict[str, str]], context: Dict[str, Any]) -> Dict[str, Any]:
        async with self._semaphore:
            t0 = time.perf_counter()
            response = await self.transport.chat_completion(model=node.model, messages=messages, tools=node.tools or None,
                temperature=node.temperature, max_tokens=node.max_tokens)
            latency = (time.perf_counter() - t0) * 1000
            node._latency_ms = latency
            node._ttft_ms = response.get("_ttft_ms", 0.0)
            node._tps = response.get("_tps", 0.0)
            self._metrics.append({"agent_id": node.agent_id, "latency_ms": latency, "ttft_ms": node._ttft_ms, "tps": node._tps})
            return {"agent_id": node.agent_id, "content": response.get("content", ""), "tool_calls": response.get("tool_calls", []),
                    "model": node.model, "latency_ms": latency}

    def _build_messages(self, node: AgentNode, initial: List[Dict[str, str]], upstream: Dict[str, Any], context: Dict[str, Any]) -> List[Dict[str, str]]:
        msgs = [{"role": "system", "content": node.system_prompt}]
        msgs.extend(initial)
        for dep in node.dependencies:
            if dep in upstream and "content" in upstream[dep]:
                msgs.append({"role": "user", "content": f"[Output from {dep}]: {upstream[dep]['content']}"})
        if context:
            msgs.append({"role": "user", "content": f"[Context]: {json.dumps(context, default=str)}"})
        return msgs

    def get_metrics(self) -> List[Dict[str, Any]]:
        return self._metrics.copy()

    def get_aggregate_metrics(self) -> Dict[str, float]:
        if not self._metrics:
            return {}
        latencies = [m["latency_ms"] for m in self._metrics]
        ttfts = [m["ttft_ms"] for m in self._metrics if m["ttft_ms"] > 0]
        tps_vals = [m["tps"] for m in self._metrics if m["tps"] > 0]
        return {"avg_latency_ms": sum(latencies)/len(latencies), "max_latency_ms": max(latencies), "min_latency_ms": min(latencies),
                "avg_ttft_ms": sum(ttfts)/len(ttfts) if ttfts else 0.0, "avg_tps": sum(tps_vals)/len(tps_vals) if tps_vals else 0.0,
                "total_invocations": len(self._metrics)}
