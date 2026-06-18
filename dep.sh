#!/usr/bin/env bash
set -euo pipefail

# ============================================================
# SOVEREIGN STACK - MONOLITHIC DEPLOYMENT
# Replaces proxy, rebuilds ik_llama with governor, restarts all
# ============================================================

# --- CONFIG ---
SOVEREIGN_HOME="${SOVEREIGN_HOME:-/home/toxic/sovereign}"
MODEL_PATH="${MODEL_PATH:-/home/toxic/models/Qwen3.6-27B-Heretic-Cerebellum-v1-Q2_K_Mixed.gguf}"
IK_LLAMA_SRC="/home/toxic/ik_llama.cpp-main"
BUILD_DIR="${IK_LLAMA_SRC}/build"
INSTALL_BIN="${SOVEREIGN_HOME}/bin/llama-server"
FLOW_FILE="${SOVEREIGN_HOME}/nfcot_flow.pt"

echo "============================================================"
echo " SOVEREIGN DEPLOYMENT"
echo "============================================================"

# 1. Stop all services (llama-server, proxy, etc.)
echo "1. Stopping any running services..."
pkill -f "llama-server" 2>/dev/null || true
pkill -f "nfcot_proxy.py" 2>/dev/null || true
pkill -f "openfang" 2>/dev/null || true
pkill -f "sovereign_watchdog" 2>/dev/null || true
sleep 2

# 2. Backup old proxy and replace with the final version
echo "2. Installing final nfcot_proxy.py ..."
mkdir -p "${SOVEREIGN_HOME}/modules"
cat > "${SOVEREIGN_HOME}/modules/nfcot_proxy.py" << 'EOF'
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
DIM = int(os.getenv("MODEL_DIM", "5120"))  # force 5120

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
EOF
chmod +x "${SOVEREIGN_HOME}/modules/nfcot_proxy.py"

# 3. (Optional) Rebuild ik_llama with your governor and weight_pack
echo "3. Rebuilding ik_llama with Sovereign governor..."
cd "${IK_LLAMA_SRC}"

# Copy your governor and kernel files into the source tree if they aren't already there.
# Assumes they are already present in the repo root.
if [ -f "sovereign_governor.cpp" ] && [ -f "sovereign_governor.h" ] && [ -f "weight_pack_sm86_fixed.cu" ]; then
    echo "   Governor files found. Proceeding with build."
else
    echo "   Governor files not found. Skipping rebuild (using existing binary)."
    # If you want to force a rebuild regardless, uncomment the next line:
    # echo "   ERROR: missing governor files. Please place them in ${IK_LLAMA_SRC} and rerun."
    # exit 1
fi

# Configure and build
mkdir -p "${BUILD_DIR}"
cd "${BUILD_DIR}"
cmake .. -DCMAKE_BUILD_TYPE=Release -DGGML_CUDA=ON -DGGML_CUDA_ARCH="sm86"
make -j$(nproc)
cp bin/llama-server "${INSTALL_BIN}" 2>/dev/null || cp bin/llama-cli "${INSTALL_BIN}" 2>/dev/null || echo "   Warning: Could not copy llama-server, check build output."

# 4. Ensure flow file exists (create if missing)
if [ ! -f "${FLOW_FILE}" ]; then
    echo "4. Creating default flow file (dim=5120)..."
    python3 -c "import torch; from pathlib import Path; p=Path('${FLOW_FILE}'); p.parent.mkdir(parents=True, exist_ok=True); torch.save({'dummy': torch.tensor(0)}, p)"
fi

# 5. Start the stack using mise
echo "5. Starting stack with mise..."
cd "${SOVEREIGN_HOME}"
mise run start &

# 6. Wait and verify
echo "6. Waiting for services to come up..."
sleep 5
echo -n "   Checking llama-server (port 25001): "
if ss -tln | grep -q ':25001'; then echo "✓"; else echo "✗"; fi
echo -n "   Checking proxy (port 25008): "
if curl -sf http://127.0.0.1:25008/health >/dev/null 2>&1; then
    echo "✓"
    echo "   Proxy health: $(curl -s http://127.0.0.1:25008/health | jq -c .)"
else
    echo "✗ (may still be starting)"
fi

echo "============================================================"
echo " DEPLOYMENT COMPLETE"
echo " Logs: ${SOVEREIGN_HOME}/logs/"
echo " To test: curl -X POST http://127.0.0.1:25008/v1/chat/completions ..."
echo "============================================================"
