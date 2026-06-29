cat > /home/toxic/sovereign/modules/nfcot_proxy.py << 'ENDOFSCRIPT'
#!/usr/bin/env python3
"""
NF-CoT Proxy — Final Production Version
"""
import os
import sys
import uuid
import time
import logging
import hashlib
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional
import requests
import torch
import torch.nn as nn
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
import uvicorn

MODEL_URL = os.getenv("MODEL_URL", "http://127.0.0.1:25001")
PROXY_PORT = int(os.getenv("PROXY_PORT", "25008"))
FLOW_PATH = Path(os.getenv("FLOW_PATH", "/home/toxic/sovereign/nfcot_flow.pt")).resolve()
TRIGGER_TOKEN = "<think>"
FORCE_TRIGGER = os.getenv("FORCE_TRIGGER", "").lower() in ("1", "true", "yes")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

logging.basicConfig(level=getattr(logging, LOG_LEVEL, logging.INFO), format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("nfcot_proxy")

@dataclass
class Receipt:
    act_hash: str
    latent: float
    shadow_latent: float
    timestamp: float = 0.0
    flow_enabled: bool = True
    model_dim: int = 0
    trigger_used: str = ""
    injection_success: bool = False

class CouplingLayer(nn.Module):
    def __init__(self, dim: int, hidden_dim: int = 512):
        super().__init__()
        self.dim = dim
        self.register_buffer('mask', torch.arange(dim) % 2 == 0)
        self.net = nn.Sequential(nn.Linear(dim // 2, hidden_dim), nn.ReLU(), nn.Linear(hidden_dim, dim // 2))

    def forward(self, x: torch.Tensor, reverse: bool = False):
        if x.dim() == 1:
            x = x.unsqueeze(0)
        mask = self.mask.to(x.device)
        x1, x2 = x[:, mask], x[:, ~mask]
        s = self.net(x1)
        y2 = x2 + s if not reverse else x2 - s
        y = torch.zeros_like(x)
        y[:, mask], y[:, ~mask] = x1, y2
        return y.squeeze(0) if x.dim() == 1 else y

class TARFlow(nn.Module):
    def __init__(self, dim: int, num_layers: int = 4, hidden_dim: int = 512):
        super().__init__()
        self.dim = dim
        self.layers = nn.ModuleList([CouplingLayer(dim, hidden_dim) for _ in range(num_layers)])

    def forward(self, x: torch.Tensor, reverse: bool = False):
        y = x
        for layer in (self.layers if not reverse else reversed(self.layers)):
            y = layer(y, reverse=reverse)
        return y, torch.tensor(0.0)

flow = None
dim = 5120
flow_enabled = False
model_id = "unknown"

def load_flow():
    global flow, flow_enabled
    flow = TARFlow(dim=dim)
    if FLOW_PATH.exists():
        try:
            state = torch.load(FLOW_PATH, map_location="cpu", weights_only=True)
            flow.load_state_dict(state, strict=False)
            flow_enabled = True
            log.info(f"✓ Loaded flow (dim={dim})")
        except Exception as e:
            log.warning(f"Flow load failed: {e}")
    else:
        torch.save(flow.state_dict(), FLOW_PATH)
        flow_enabled = True
        log.info("✓ Initialized new flow")

app = FastAPI(title="NF-CoT Proxy (Sovereign)")

@app.on_event("startup")
def startup():
    global model_id
    try:
        r = requests.get(f"{MODEL_URL}/v1/models", timeout=3)
        if r.ok:
            model_id = r.json()["data"][0]["id"]
    except Exception:
        pass
    load_flow()

def get_embedding(text: str) -> Optional[List[float]]:
    try:
        r = requests.post(f"{MODEL_URL}/embedding", json={"content": text}, timeout=10)
        emb = r.json().get("embedding", [])
        if emb and isinstance(emb[0], list):
            emb = emb[-1]
        return emb
    except Exception:
        return None

def compute_latent(emb: List[float]) -> float:
    if len(emb) > dim:
        emb = emb[:dim]
    elif len(emb) < dim:
        emb += [0.0] * (dim - len(emb))
    with torch.no_grad():
        y, _ = flow(torch.tensor(emb, dtype=torch.float32))
        return float(y.mean().item())

@app.post("/v1/chat/completions")
async def chat_completions(request: Request):
    req = await request.json()
    messages = req.get("messages", [])
    max_tokens = req.get("max_tokens", 2048)
    temperature = req.get("temperature", 0.7)

    if FORCE_TRIGGER:
        messages.insert(0, {
            "role": "system",
            "content": "You are in deep reasoning mode. Begin your response with <think> and think carefully before answering."
        })

    payload = {
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "stop": [TRIGGER_TOKEN],
        "chat_template_kwargs": {"enable_thinking": True}
    }

    try:
        r = requests.post(f"{MODEL_URL}/v1/chat/completions", json=payload, timeout=180)
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        raise HTTPException(502, f"Upstream error: {e}")

    text = data["choices"][0]["message"]["content"]

    latent_value = 0.0
    shadow_latent = 0.0
    injected = False
    trigger_used = ""

    if flow_enabled:
        try:
            full_context = " ".join([m.get("content", "") for m in messages]) + text
            emb = get_embedding(full_context[:2000])
            if emb:
                shadow_latent = compute_latent(emb)
        except Exception:
            pass

    if TRIGGER_TOKEN in text:
        trigger_used = TRIGGER_TOKEN
        before, after = text.split(TRIGGER_TOKEN, 1)
        try:
            context = " ".join([m.get("content", "") for m in messages]) + before + TRIGGER_TOKEN
            emb = get_embedding(context)
            if emb:
                latent_value = compute_latent(emb)
                injected = True
        except Exception as e:
            log.error(f"Latent error: {e}")

        if injected:
            inject_block = f"\n<|latent_state|>{latent_value:.6f}</|latent_state|>\n"
            resume_messages = messages + [{"role": "assistant", "content": before + TRIGGER_TOKEN + inject_block}]
            try:
                resume = requests.post(f"{MODEL_URL}/v1/chat/completions", json={
                    "messages": resume_messages,
                    "max_tokens": max(1, max_tokens - len(text)//3),
                    "temperature": temperature,
                    "chat_template_kwargs": {"enable_thinking": True}
                }, timeout=120)
                if resume.ok:
                    text = before + TRIGGER_TOKEN + inject_block + resume.json()["choices"][0]["message"]["content"]
            except Exception:
                text = before + TRIGGER_TOKEN + inject_block + after

    receipt = Receipt(
        act_hash=hashlib.sha256(f"{time.time()}{latent_value}{model_id}".encode()).hexdigest()[:16],
        latent=latent_value if injected else 0.0,
        shadow_latent=shadow_latent,
        timestamp=time.time(),
        flow_enabled=flow_enabled,
        model_dim=dim,
        trigger_used=trigger_used,
        injection_success=injected
    )

    return JSONResponse({
        "id": f"chatcmpl-{uuid.uuid4().hex[:8]}",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": model_id,
        "choices": [{"index": 0, "message": {"role": "assistant", "content": text}, "finish_reason": "stop"}],
        "usage": data.get("usage", {}),
        "sovereign_receipt": asdict(receipt)
    })

@app.get("/health")
async def health():
    return {
        "status": "ok",
        "flow_enabled": flow_enabled,
        "dim": dim,
        "model_id": model_id,
        "trigger_token": TRIGGER_TOKEN
    }

@app.get("/v1/models")
async def list_models():
    try:
        resp = requests.get(f"{MODEL_URL}/v1/models", timeout=3)
        if resp.ok:
            return JSONResponse(content=resp.json())
    except Exception:
        pass

    return JSONResponse(content={
        "object": "list",
        "data": [{"id": model_id, "flow_enabled": flow_enabled, "dim": dim}]
    })

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=PROXY_PORT, log_level="info")
ENDOFSCRIPT

chmod +x /home/toxic/sovereign/modules/nfcot_proxy.py
pkill -f nfcot_proxy.py