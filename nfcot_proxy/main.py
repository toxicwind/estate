#!/usr/bin/env python3
"""NF-CoT Proxy — inline bootstrap stub. Replace with full version."""
import os, json, asyncio
import httpx
from fastapi import FastAPI, Request, Response
from fastapi.responses import StreamingResponse
import uvicorn

UPSTREAM      = os.environ.get("MODEL_URL",           "http://127.0.0.1:25001")
PORT          = int(os.environ.get("NFCOT_PORT",      "25008"))
TRIGGER_TOKEN = os.environ.get("TRIGGER_TOKEN",       "<|im_start|>think")
FORCE_TRIGGER = os.environ.get("FORCE_TRIGGER",       "false").lower() == "true"
SHADOW_LATENT = os.environ.get("ENABLE_SHADOW_LATENT","0") == "1"

app    = FastAPI(title="NF-CoT Proxy", version="0.2.0-stub")
client = httpx.AsyncClient(base_url=UPSTREAM, timeout=300.0)

@app.get("/health")
async def health():
    return {"status":"ok","upstream":UPSTREAM,"force_trigger":FORCE_TRIGGER}

@app.get("/metrics")
async def metrics():
    return Response("nfcot_up 1\n", media_type="text/plain")

def _inject(payload):
    msgs = payload.get("messages", [])
    sys  = [m for m in msgs if m["role"] == "system"]
    if sys:  sys[0]["content"] = TRIGGER_TOKEN + "\n" + sys[0]["content"]
    else:    msgs.insert(0, {"role":"system","content":TRIGGER_TOKEN})
    payload["messages"] = msgs
    return payload

@app.api_route("/v1/{path:path}", methods=["GET","POST","PUT","DELETE","OPTIONS"])
async def proxy(path: str, request: Request):
    body = await request.body()
    is_c = path in ("chat/completions","completions")
    if is_c and FORCE_TRIGGER and body:
        try:
            p = json.loads(body)
            body = json.dumps(_inject(p)).encode()
        except: pass
    hdrs = {k:v for k,v in request.headers.items() if k.lower() not in ("host","content-length")}
    r = await client.request(request.method, f"/{path}", headers=hdrs, content=body)
    return Response(content=r.content, status_code=r.status_code,
                    media_type=r.headers.get("content-type","application/json"))

if __name__ == "__main__":
    print(f"[nfcot] :{PORT} → {UPSTREAM}  force={FORCE_TRIGGER}  shadow={SHADOW_LATENT}")
    uvicorn.run(app, host="0.0.0.0", port=PORT, log_level="warning")
