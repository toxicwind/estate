import asyncio, inspect, os, ssl, sys
sys.path.insert(0, "/home/hatch/workspace/skills/.venv/lib/python3.12/site-packages")
import websockets

WS_URL = "wss://github-mcp-host.tailc9ac71.ts.net/squawk-ws"
PROXY = os.environ.get("https_proxy")
TOKEN = open(os.path.expanduser("~/hooks/state/squawk-ws.token")).read().strip()
SSL_CTX = ssl._create_unverified_context()

def base_kw():
    return dict(proxy=PROXY, ssl=SSL_CTX, open_timeout=20)

async def attempt(name, **kw):
    k = base_kw(); k.update(kw)
    params = inspect.signature(websockets.connect).parameters
    if "additional_headers" in params:
        k["additional_headers"] = {"Authorization": "Bearer " + TOKEN}
    else:
        k["extra_headers"] = {"Authorization": "Bearer " + TOKEN}
    try:
        async with websockets.connect(WS_URL, **k) as ws:
            print(f"{name}: CONNECTED")
            await ws.close()
    except Exception as e:
        print(f"{name}: {type(e).__name__}: {str(e)[:80]}")

async def main():
    await attempt("auth+deflate(default)")
    await attempt("auth+compression=None", compression=None)
    await attempt("auth+curl-UA", user_agent_header="curl/8.5.0")

asyncio.run(main())
