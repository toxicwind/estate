"""nvidia_swarm_transport.py — Triton gRPC + HTTP persistent pool."""
from __future__ import annotations
import asyncio, json, time, os
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
import logging

logger = logging.getLogger("nvidia_swarm.transport")

try:
    import grpc
    from grpc import aio as grpc_aio
    GRPC_AVAILABLE = True
except ImportError:
    GRPC_AVAILABLE = False

try:
    import aiohttp
    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False

@dataclass
class PersistentConnectionPool:
    base_url: str = "https://integrate.api.nvidia.com"
    api_key: str = field(default_factory=lambda: os.getenv("NVIDIA_API_KEY", ""))
    max_connections: int = 8  # fail-fast: bounded concurrency, no 50-wide storms
    _session: Optional[Any] = field(default=None, repr=False)
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock)

    async def get_session(self) -> Any:
        async with self._lock:
            if self._session is None or self._session.closed:
                import aiohttp
                self._connector = aiohttp.TCPConnector(limit=self.max_connections, limit_per_host=self.max_connections,
                    enable_cleanup_closed=True, force_close=False, ttl_dns_cache=300, use_dns_cache=True)
                self._session = aiohttp.ClientSession(connector=self._connector, timeout=aiohttp.ClientTimeout(total=5, connect=3),  # fail-fast: >3-5s is useless
                    headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json", "Accept": "application/json", "Accept-Encoding": "gzip, deflate"})
            return self._session

    async def close(self):
        async with self._lock:
            if self._session and not self._session.closed:
                await self._session.close()
                self._session = None

    async def post(self, endpoint: str, payload: Dict[str, Any]) -> tuple:
        session = await self.get_session()
        url = f"{self.base_url}{endpoint}"
        t0 = time.perf_counter()
        async with session.post(url, json=payload) as resp:
            body = await resp.text()
            latency = (time.perf_counter() - t0) * 1000
            headers = dict(resp.headers)
            try:
                data = json.loads(body) if body else {}
            except json.JSONDecodeError:
                data = {"raw": body}
            data["_ttft_ms"] = float(headers.get("x-ttft-ms", 0.0))
            data["_tps"] = float(headers.get("x-tokens-per-sec", 0.0))
            data["_latency_ms"] = latency
            return resp.status, data, headers

@dataclass
class TritonTransport:
    triton_url: str = "localhost:8001"
    model_name: str = "openai/gpt-oss-20b"  # old default was a dead legacy id
    model_version: str = "1"
    _stub: Optional[Any] = field(default=None, repr=False)
    _channel: Optional[Any] = field(default=None, repr=False)

    async def connect(self):
        if not GRPC_AVAILABLE:
            raise RuntimeError("grpcio required")
        import grpc
        from tritonclient.grpc import service_pb2, service_pb2_grpc
        self._channel = grpc_aio.insecure_channel(self.triton_url)
        self._stub = service_pb2_grpc.GRPCInferenceServiceStub(self._channel)
        await self._stub.ServerReady(service_pb2.ServerReadyRequest())
        logger.info(f"Triton gRPC connected to {self.triton_url}")

    async def infer(self, prompt: str, max_tokens: int = 4096, temperature: float = 0.3, top_p: float = 0.9) -> Dict[str, Any]:
        if not self._stub:
            await self.connect()
        from tritonclient.grpc import service_pb2
        inputs = [
            service_pb2.ModelInferRequest().InferInputTensor(name="prompt", datatype="BYTES", shape=[1,1], contents=service_pb2.InferTensorContents(byte_contents=[prompt.encode()])),
            service_pb2.ModelInferRequest().InferInputTensor(name="max_tokens", datatype="INT32", shape=[1,1], contents=service_pb2.InferTensorContents(int_contents=[max_tokens])),
            service_pb2.ModelInferRequest().InferInputTensor(name="temperature", datatype="FP32", shape=[1,1], contents=service_pb2.InferTensorContents(fp32_contents=[temperature])),
        ]
        request = service_pb2.ModelInferRequest(model_name=self.model_name, model_version=self.model_version, inputs=inputs)
        t0 = time.perf_counter()
        response = await self._stub.ModelInfer(request)
        latency = (time.perf_counter() - t0) * 1000
        raw_output = response.outputs[0].contents.byte_contents[0].decode()
        return {"content": raw_output, "tool_calls": [], "_ttft_ms": 0.0, "_tps": 0.0, "_latency_ms": latency, "transport": "triton_grpc"}

    async def close(self):
        if self._channel:
            await self._channel.close()

@dataclass
class NvidiaNIMClient:
    api_key: str = field(default_factory=lambda: os.getenv("NVIDIA_API_KEY", ""))
    base_url: str = "https://integrate.api.nvidia.com"
    model: str = "openai/gpt-oss-20b"  # alive-fast 2026-09-14; old default delisted
    enable_streaming: bool = True
    enable_triton: bool = False
    triton_url: str = "localhost:8001"
    _http_pool: Optional[PersistentConnectionPool] = field(default=None, repr=False)
    _triton: Optional[TritonTransport] = field(default=None, repr=False)
    _metrics: List[Dict[str, Any]] = field(default_factory=list)

    def __post_init__(self):
        self._http_pool = PersistentConnectionPool(base_url=self.base_url, api_key=self.api_key)
        if self.enable_triton and GRPC_AVAILABLE:
            self._triton = TritonTransport(triton_url=self.triton_url, model_name=self.model)

    async def chat_completion(self, model: Optional[str] = None, messages: Optional[List[Dict[str, str]]] = None,
                              tools: Optional[List[Dict[str, Any]]] = None, temperature: float = 0.3, max_tokens: int = 4096,
                              stream: Optional[bool] = None, extra_body: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        stream = stream if stream is not None else self.enable_streaming
        model = model or self.model
        messages = messages or []
        if self._triton and self.enable_triton:
            prompt = self._messages_to_prompt(messages)
            return await self._triton.infer(prompt=prompt, max_tokens=max_tokens, temperature=temperature)
        payload = {"model": model, "messages": messages, "temperature": temperature, "max_tokens": max_tokens, "stream": stream}
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"
        if extra_body:
            payload.update(extra_body)
        status, data, headers = await self._http_pool.post("/v1/chat/completions", payload)
        if status != 200:
            raise RuntimeError(f"NIM error {status}: {data}")
        choice = data.get("choices", [{}])[0]
        message = choice.get("message", {})
        result = {"content": message.get("content", ""), "tool_calls": message.get("tool_calls", []),
                  "finish_reason": choice.get("finish_reason", ""), "model": data.get("model", model),
                  "usage": data.get("usage", {}), "_ttft_ms": data.get("_ttft_ms", 0.0), "_tps": data.get("_tps", 0.0),
                  "_latency_ms": data.get("_latency_ms", 0.0), "transport": "http_rest"}
        self._metrics.append({"model": model, "latency_ms": result["_latency_ms"], "ttft_ms": result["_ttft_ms"], "tps": result["_tps"],
                              "tokens_in": result["usage"].get("prompt_tokens", 0), "tokens_out": result["usage"].get("completion_tokens", 0)})
        return result

    async def stream_completion(self, model: Optional[str] = None, messages: Optional[List[Dict[str, str]]] = None,
                                temperature: float = 0.3, max_tokens: int = 4096):
        model = model or self.model
        messages = messages or []
        payload = {"model": model, "messages": messages, "temperature": temperature, "max_tokens": max_tokens, "stream": True}
        session = await self._http_pool.get_session()
        url = f"{self.base_url}/v1/chat/completions"
        t0 = time.perf_counter()
        async with session.post(url, json=payload) as resp:
            if resp.status != 200:
                body = await resp.text()
                raise RuntimeError(f"Stream error {resp.status}: {body}")
            buffer = ""
            async for line in resp.content:
                line = line.decode("utf-8").strip()
                if line.startswith("data: "):
                    data_str = line[6:]
                    if data_str == "[DONE]":
                        break
                    try:
                        chunk = json.loads(data_str)
                        delta = chunk.get("choices", [{}])[0].get("delta", {})
                        content = delta.get("content", "")
                        if content:
                            buffer += content
                            yield {"type": "token", "content": content, "accumulated": buffer}
                    except json.JSONDecodeError:
                        continue
            latency = (time.perf_counter() - t0) * 1000
            yield {"type": "done", "accumulated": buffer, "latency_ms": latency}

    def _messages_to_prompt(self, messages: List[Dict[str, str]]) -> str:
        parts = []
        for msg in messages:
            role, content = msg.get("role", "user"), msg.get("content", "")
            if role == "system":
                parts.append(f"System: {content}")
            elif role == "user":
                parts.append(f"User: {content}")
            elif role == "assistant":
                parts.append(f"Assistant: {content}")
        return "\n\n".join(parts)

    async def close(self):
        if self._http_pool:
            await self._http_pool.close()
        if self._triton:
            await self._triton.close()

    def get_metrics(self) -> List[Dict[str, Any]]:
        return self._metrics.copy()

    def get_aggregate_metrics(self) -> Dict[str, float]:
        if not self._metrics:
            return {}
        return {"avg_latency_ms": sum(m["latency_ms"] for m in self._metrics)/len(self._metrics),
                "avg_ttft_ms": sum(m["ttft_ms"] for m in self._metrics)/len(self._metrics),
                "avg_tps": sum(m["tps"] for m in self._metrics)/len(self._metrics),
                "total_requests": len(self._metrics), "total_tokens_in": sum(m["tokens_in"] for m in self._metrics),
                "total_tokens_out": sum(m["tokens_out"] for m in self._metrics)}
