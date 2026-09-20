"""nim/client.py — Shared NIM API layer for NvidiaLensSwarm.

ALL model calls in the merged swarm route through here (or AsyncNimClient).

Design rules (from Chris):
- Fail-fast: default total timeout 5s. Anything longer than 3-5s is useless
  in production. No retries — the catalog is nondeterministic; retrying a
  gated model just burns latency.
- Model-aware cold start: known-slow models (kimi-k3 ~43s TTFT, ultra-550b)
  raise ColdStartModelError unless the caller explicitly opts in with
  allow_cold_start=True (then budget extends to the model's timeout_s).
- Dead models (404-gated legacy, 410 EOL) fail BEFORE any network call with
  DeadModelError naming a live alternative. Don't probe corpses.
- Auth is layered: (1) Secure Vault via dynamic credential surrogate when
  available (sandbox), (2) NVIDIA_API_KEY env, (3) clean NimAuthError that
  says exactly how to fix it. The raw key is never logged, printed, or stored.
- Full private diagnostics on the result object; exceptions are sanitized
  (no response bodies, no account ids).

Sync client is stdlib-only (urllib). Async client needs aiohttp (already a
repo dependency).
"""
from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.request
from typing import Any, AsyncIterator, Dict, List, Optional

from .models import (
    DEFAULT_MODEL,
    COLD_START_MODELS,
    DEPRECATED_MODELS,
    EOL_MODELS,
    DEAD_404_MODELS,
    get_model_spec,
)

BASE_URL = "https://integrate.api.nvidia.com/v1"
HOSTS = ["integrate.api.nvidia.com"]
CREDENTIAL_NAME = "custom.nvidia"

FAIL_FAST_TIMEOUT = 5.0    # total seconds; Chris's production ceiling
COLD_START_TIMEOUT = 90.0  # only with explicit allow_cold_start=True


class NimError(RuntimeError):
    """Base for all NIM-layer errors."""


class NimAuthError(NimError):
    """No usable credential. Not a model failure — fix config."""


class NimHTTPError(NimError):
    def __init__(self, status: int, message: str):
        super().__init__(f"http_{status}: {message}")
        self.status = status


class NimTimeoutError(NimError):
    """Fail-fast timeout hit. Pre-classify: latency vs cold-start vs gate."""


class ColdStartModelError(NimError):
    """Model is known-slow; caller must opt in explicitly."""


class DeadModelError(NimError):
    """Model is 404-gated / EOL / delisted. Not worth a network call."""


def _check_model(model: str, allow_cold_start: bool) -> float:
    """Pre-flight model policy. Returns the timeout budget in seconds."""
    if model in EOL_MODELS or model in DEAD_404_MODELS:
        live = DEFAULT_MODEL
        raise DeadModelError(
            f"{model} is dead for hosted chat (404-gated / 410 EOL / delisted). "
            f"Use a live model such as {live}."
        )
    if model in DEPRECATED_MODELS:
        raise DeadModelError(
            f"{model} is deprecated (EOL {DEPRECATED_MODELS[model]}); "
            f"latest pass returned 503. Use {DEFAULT_MODEL}."
        )
    spec = COLD_START_MODELS.get(model)
    if spec:
        if not allow_cold_start:
            raise ColdStartModelError(
                f"{model} cold-starts (~{spec['ttft_s']}s TTFT observed); "
                f"violates the {FAIL_FAST_TIMEOUT}s fail-fast ceiling. "
                f"Pass allow_cold_start=True (budget {spec['timeout_s']}s) "
                f"or use {DEFAULT_MODEL}."
            )
        return float(spec["timeout_s"])
    return FAIL_FAST_TIMEOUT


def _surrogate_or_env_request(url: str, payload: Optional[dict]) -> urllib.request.Request:
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(
        url, data=data,
        headers={"Content-Type": "application/json"},
        method="POST" if data else "GET",
    )
    # 1. Secure Vault surrogate (sandbox). Raw key never readable.
    try:
        sys.path.insert(0, "/opt/hatch/skills/skill-creator/bin")
        from dynamic_credentials import (  # type: ignore
            DynamicCredentialError, add_surrogate_to_request,
        )
        try:
            add_surrogate_to_request(req, CREDENTIAL_NAME, allowed_hosts=HOSTS)
            return req
        except DynamicCredentialError:
            pass
    except ImportError:
        pass
    # 2. Env fallback (portable; e.g. awrawr-pc, CI with secrets).
    key = os.environ.get("NVIDIA_API_KEY", "")
    if key:
        req.add_header("Authorization", "Bearer " + key)
        return req
    # 3. Clean, actionable failure — never silently switch to mock.
    raise NimAuthError(
        "no_nvidia_credential: store an NVIDIA API key (build.nvidia.com, "
        f"starts with nvapi-) in the Secure Vault as {CREDENTIAL_NAME}, "
        "or set NVIDIA_API_KEY in the environment, then retry."
    )


def _normalize_chat_response(data: dict, latency_ms: float) -> Dict[str, Any]:
    """Normalize an OpenAI-compatible chat response into the swarm result shape."""
    choice = (data.get("choices") or [{}])[0]
    msg = choice.get("message", {}) or {}
    content = msg.get("content") or msg.get("reasoning_content") or ""
    return {
        "content": content,
        "tool_calls": msg.get("tool_calls") or [],
        "finish_reason": choice.get("finish_reason"),
        "model": data.get("model"),
        "usage": data.get("usage") or {},
        "latency_ms": latency_ms,
        "raw": data,  # full private diagnostics; sanitize before publishing
    }


class NimClient:
    """Sync NIM client (stdlib only). Preferred default for agents."""

    def __init__(self, base_url: str = BASE_URL, timeout: float = FAIL_FAST_TIMEOUT):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    # -- raw calls ---------------------------------------------------------
    def _call(self, url: str, payload: Optional[dict], timeout: float) -> dict:
        req = _surrogate_or_env_request(url, payload)
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                body = resp.read()
                return {"ok": True, "data": json.loads(body)}
        except urllib.error.HTTPError as exc:
            # Sanitized: status + short reason only, never the body.
            return {"ok": False, "error": f"http_{exc.code}",
                    "detail": f"HTTP {exc.code} {exc.reason}"}
        except TimeoutError:
            return {"ok": False, "error": "timeout",
                    "detail": f"no response within {timeout}s (fail-fast)"}
        except Exception as exc:  # e.g. URLError
            return {"ok": False, "error": "request_failed",
                    "detail": str(exc)[:200]}

    # -- public API ----------------------------------------------------------
    def models(self) -> List[str]:
        """Live /v1/models ids. Public endpoint — needs no auth."""
        res = self._call(f"{self.base_url}/models", None, self.timeout)
        if not res["ok"]:
            raise NimError(f"models listing failed: {res['error']}")
        return [m.get("id") for m in res["data"].get("data", [])]

    def chat(self, messages: List[Dict[str, str]], model: str = DEFAULT_MODEL,
             allow_cold_start: bool = False, stream: bool = False,
             **kwargs: Any) -> Dict[str, Any]:
        """One chat completion. Raises typed NimError on any failure."""
        budget = _check_model(model, allow_cold_start)
        timeout = min(self.timeout, budget) if not allow_cold_start else budget
        payload = {"model": model, "messages": messages, "stream": stream}
        payload.update(kwargs)
        t0 = time.perf_counter()
        if stream:
            return self._chat_stream(payload, timeout, t0)
        res = self._call(f"{self.base_url}/chat/completions", payload, timeout)
        latency_ms = (time.perf_counter() - t0) * 1000
        if not res["ok"]:
            self._raise_for(res, model)
        return _normalize_chat_response(res["data"], latency_ms)

    def _chat_stream(self, payload: dict, timeout: float, t0: float) -> Dict[str, Any]:
        """SSE streaming: accumulate deltas, enforce stall timeout."""
        req = _surrogate_or_env_request(
            f"{self.base_url}/chat/completions", payload)
        chunks: List[str] = []
        tool_calls: List[dict] = []
        model = payload.get("model", "")
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                last_data = time.perf_counter()
                for raw in resp:
                    line = raw.decode("utf-8", "replace").strip()
                    if time.perf_counter() - last_data > timeout:
                        raise NimTimeoutError(
                            f"stream stall: no SSE data for {timeout}s")
                    if not line.startswith("data:"):
                        continue
                    last_data = time.perf_counter()
                    data = line[5:].strip()
                    if data == "[DONE]":
                        break
                    try:
                        obj = json.loads(data)
                    except json.JSONDecodeError:
                        continue
                    delta = (obj.get("choices") or [{}])[0].get("delta", {})
                    if delta.get("content"):
                        chunks.append(delta["content"])
                    if delta.get("tool_calls"):
                        tool_calls.extend(delta["tool_calls"])
        except TimeoutError:
            raise NimTimeoutError(
                f"stream connect/read exceeded {timeout}s (fail-fast)")
        latency_ms = (time.perf_counter() - t0) * 1000
        return {"content": "".join(chunks), "tool_calls": tool_calls,
                "finish_reason": "stop", "model": model, "usage": {},
                "latency_ms": latency_ms, "raw": {"streamed": True}}

    def ping(self) -> Dict[str, Any]:
        res = self._call(f"{self.base_url}/models", None, self.timeout)
        return {"ok": res["ok"], "error": res.get("error")}

    @staticmethod
    def _raise_for(res: dict, model: str) -> None:
        err, detail = res["error"], res.get("detail", "")
        if err == "timeout":
            raise NimTimeoutError(f"{model}: {detail}")
        if err.startswith("http_"):
            status = int(err.split("_")[1])
            if status == 404:
                raise DeadModelError(
                    f"{model}: 404 from NIM — gated for this account/key or "
                    f"delisted. Catalog is the unreliable narrator; only live "
                    f"probes tell the truth. Try {DEFAULT_MODEL}.")
            raise NimHTTPError(status, detail)
        raise NimError(f"{model}: {err}: {detail}")


class AsyncNimClient:
    """Async NIM client (aiohttp). Env auth only — the credential surrogate
    is urllib-Request based, so async paths need NVIDIA_API_KEY set."""

    def __init__(self, base_url: str = BASE_URL, timeout: float = FAIL_FAST_TIMEOUT,
                 api_key: Optional[str] = None):
        import aiohttp  # deferred: only needed for async use
        self._aiohttp = aiohttp
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        key = api_key or os.environ.get("NVIDIA_API_KEY", "")
        if not key:
            raise NimAuthError(
                "no_nvidia_credential: AsyncNimClient needs NVIDIA_API_KEY in "
                "the environment (the Secure Vault surrogate is sync-only); "
                "use NimClient for surrogate auth.")
        self._headers = {"Content-Type": "application/json",
                         "Authorization": "Bearer " + key}

    async def chat(self, messages: List[Dict[str, str]], model: str = DEFAULT_MODEL,
                   allow_cold_start: bool = False, **kwargs: Any) -> Dict[str, Any]:
        budget = _check_model(model, allow_cold_start)
        timeout = min(self.timeout, budget) if not allow_cold_start else budget
        payload = {"model": model, "messages": messages, "stream": False}
        payload.update(kwargs)
        t0 = time.perf_counter()
        aio_timeout = self._aiohttp.ClientTimeout(total=timeout, connect=3)
        try:
            async with self._aiohttp.ClientSession(timeout=aio_timeout) as s:
                async with s.post(f"{self.base_url}/chat/completions",
                                  headers=self._headers, json=payload) as r:
                    if r.status != 200:
                        raise NimHTTPError(r.status, f"HTTP {r.status}")
                    data = await r.json()
        except TimeoutError:
            raise NimTimeoutError(f"{model}: no response within {timeout}s (fail-fast)")
        latency_ms = (time.perf_counter() - t0) * 1000
        if isinstance(data, dict) and data.get("error"):
            raise NimHTTPError(400, str(data["error"])[:200])
        return _normalize_chat_response(data, latency_ms)

    async def chat_stream(self, messages: List[Dict[str, str]],
                          model: str = DEFAULT_MODEL,
                          allow_cold_start: bool = False,
                          **kwargs: Any) -> AsyncIterator[str]:
        """Yield content deltas as they arrive (SSE). Stall-guarded."""
        budget = _check_model(model, allow_cold_start)
        timeout = min(self.timeout, budget) if not allow_cold_start else budget
        payload = {"model": model, "messages": messages, "stream": True}
        payload.update(kwargs)
        aio_timeout = self._aiohttp.ClientTimeout(total=timeout, connect=3,
                                                  sock_read=timeout)
        async with self._aiohttp.ClientSession(timeout=aio_timeout) as s:
            async with s.post(f"{self.base_url}/chat/completions",
                              headers=self._headers, json=payload) as r:
                if r.status != 200:
                    raise NimHTTPError(r.status, f"HTTP {r.status}")
                async for raw in r.content:
                    line = raw.decode("utf-8", "replace").strip()
                    if not line.startswith("data:"):
                        continue
                    data = line[5:].strip()
                    if data == "[DONE]":
                        break
                    try:
                        obj = json.loads(data)
                    except json.JSONDecodeError:
                        continue
                    delta = (obj.get("choices") or [{}])[0].get("delta", {})
                    if delta.get("content"):
                        yield delta["content"]
