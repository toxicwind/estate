#!/usr/bin/env python3
"""
NF-CoT Proxy — Final Production Version (dim=5120, fallback)
"""
import os, sys, uuid, time, logging, hashlib, requests, torch, torch.nn as nn
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import List, Optional
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
import uvicorn

MODEL_URL = os.getenv("MODEL_URL", "http://127.0.0.1:25001")
PROXY_PORT = int(os.getenv("PROXY_PORT", "25008"))
FLOW_PATH = Path(os.getenv("FLOW_PATH", "/home/toxic/sovereign/nfcot_flow.pt")).resolve()
TRIGGER_TOKEN = "<think>"
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
DIM = int(os.getenv("MODEL_DIM", "5120"))

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
        self.net = nn.Sequential(nn.Linear(dim//2, hidden_dim), nn.ReLU(), nn.Linear(hidden_dim, dim//2))
    def forward(self, x, reverse=False):
        if x.dim() == 1: x = x.unsqueeze(0)
        mask = self.mask.to(x.device)
        x1, x2 = x[:, mask], x[:, ~mask]
        s = self.net(x1)
        y2 = x2 + s if not reverse else x2 - s
        y = torch.zeros_like(x)
        y[:, mask], y[:, ~mask] = x1, y2
        return y.squeeze(0)

class TARFlow(nn.Module):
    def __init__(self, dim: int, num_layers=4, hidden_dim=512):
        super().__init__()
        self.layers = nn.ModuleList([CouplingLayer(dim, hidden_dim) for _ in range(num_layers)])
    def forward(self, x, reverse=False):
        y = x
        for layer in (self.layers if not reverse else reversed(self.layers)):
            y = layer(y, reverse=reverse)
        return y, torch.tensor(0.0)

app = FastAPI(title="NF-CoT Proxy (Sovereign)")
flow = None
flow_enabled = False
model_id = "unknown"

def load_flow():
    global flow, flow_enabled
    flow = TARFlow(dim=DIM)
    if FLOW_PATH.exists():
        try:
            state = torch.load(FLOW_PATH, map_location="cpu", weights_only=True)
            flow.load_state_dict(state, strict=False)
            flow_enabled = True
            log.info(f"✓ Loaded flow (dim={DIM})")
        except Exception as e:
            log.warning(f"Flow load failed: {e}")
    else:
        torch.save(flow.state_dict(), FLOW_PATH)
        flow_enabled = True
        log.info("✓ Initialized new flow")

@app.on_event("startup")
def startup():
    global model_id
    try:
        r = requests.get(f"{MODEL_URL}/v1/models", timeout=3)
        if r.ok:
            model_id = r.json()["data"][0].get("id", "unknown")
    except Exception:
        pass
    load_flow()

def get_embedding(text: str) -> Optional[List[float]]:
    try:
        r = requests.post(f"{MODEL_URL}/embedding", json={"content": text[:2000]}, timeout=10)
        emb = r.json().get("embedding", [])
        if emb and isinstance(emb[0], list): emb = emb[-1]
        return emb
    except Exception:
        return None

def compute_latent(emb: List[float]) -> float:
    if len(emb) > DIM: emb = emb[:DIM]
    elif len(emb) < DIM: emb += [0.0]*(DIM - len(emb))
    with torch.no_grad():
        y, _ = flow(torch.tensor(emb, dtype=torch.float32))
        return float(y.mean().item())

@app.post("/v1/chat/completions")
async def chat_completions(request: Request):
    req = await request.json()
    messages = req.get("messages", [])
    max_tokens = req.get("max_tokens", 2048)
    temperature = req.get("temperature", 0.7)

    payload = {
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "chat_template_kwargs": {"enable_thinking": True}
    }
    try:
        r = requests.post(f"{MODEL_URL}/v1/chat/completions", json=payload, timeout=180)
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        raise HTTPException(502, f"Upstream error: {e}")

    text = data["choices"][0]["message"]["content"]
    if not text:
        log.warning("Upstream returned empty content.")
        return JSONResponse({
            "id": f"chatcmpl-{uuid.uuid4().hex[:8]}",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": model_id,
            "choices": [{"index":0, "message":{"role":"assistant","content":""}, "finish_reason":"stop"}],
            "usage": data.get("usage", {}),
            "sovereign_receipt": {"flow_enabled": flow_enabled, "injection_success": False}
        })

    latent_val = 0.0; shadow_val = 0.0; injected = False; trigger_used = ""
    if flow_enabled and TRIGGER_TOKEN in text:
        trigger_used = TRIGGER_TOKEN
        before, after = text.split(TRIGGER_TOKEN, 1)
        try:
            context = " ".join([m.get("content","") for m in messages]) + before + TRIGGER_TOKEN
            emb = get_embedding(context)
            if emb:
                latent_val = compute_latent(emb)
                injected = True
        except Exception as e:
            log.error(f"Latent error: {e}")

        if injected:
            inject_block = f"\n<|latent_state|>{latent_val:.6f}</|latent_state|>\n"
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
            except Exception as e:
                log.warning(f"Resume failed: {e}")
                text = before + TRIGGER_TOKEN + inject_block + after

    receipt = Receipt(
        act_hash=hashlib.sha256(f"{time.time()}{latent_val}{model_id}".encode()).hexdigest()[:16],
        latent=latent_val if injected else 0.0,
        shadow_latent=shadow_val,
        timestamp=time.time(),
        flow_enabled=flow_enabled,
        model_dim=DIM,
        trigger_used=trigger_used,
        injection_success=injected
    )
    return JSONResponse({
        "id": f"chatcmpl-{uuid.uuid4().hex[:8]}",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": model_id,
        "choices": [{"index":0, "message":{"role":"assistant","content":text}, "finish_reason":"stop"}],
        "usage": data.get("usage", {}),
        "sovereign_receipt": asdict(receipt)
    })

@app.get("/health")
async def health():
    return {"status":"ok","flow_enabled":flow_enabled,"dim":DIM,"model_id":model_id,"trigger_token":TRIGGER_TOKEN}

@app.get("/v1/models")
async def list_models():
    try:
        r = requests.get(f"{MODEL_URL}/v1/models", timeout=3)
        if r.ok: return JSONResponse(content=r.json())
    except: pass
    return JSONResponse(content={"object":"list","data":[{"id":model_id,"flow_enabled":flow_enabled,"dim":DIM}]})

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=PROXY_PORT, log_level=LOG_LEVEL.lower())
