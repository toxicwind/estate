#!/usr/bin/env python3
"""doorbell: client for the estate MCP bridge. Standard library only. Never prints secrets."""
import argparse, hashlib, json, os, re, sys, time, urllib.error, urllib.parse, urllib.request
from pathlib import Path

BASE = os.environ.get("DOORBELL_BASE", "http://127.0.0.1:25202").rstrip("/")
PUBLIC = os.environ.get("DOORBELL_PUBLIC", "https://estate.tailc9ac71.ts.net").rstrip("/")
CACHE = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache")) / "doorbell"
CONF = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "doorbell"
MCP_PATHS = [os.environ["DOORBELL_MCP_PATH"]] if os.environ.get("DOORBELL_MCP_PATH") else ["/doorbell-mcp", "/mcp"]
LOOPBACK = re.compile(r"^https?://(127\.0\.0\.1|localhost|\[::1\])(:|/|$)")
DESTRUCTIVE = re.compile(r"(delete|remove|write|edit|exec|run|process|kill|push|send|create|update|trash|drop|reset|move|share)", re.I)
SECRET = re.compile(r"(tok_[A-Za-z0-9]{8,}|npk_[A-Za-z0-9]{8,}|sk-[A-Za-z0-9_-]{12,}|gh[pousr]_[A-Za-z0-9]{20,}|AIza[0-9A-Za-z_-]{30,}|Bearer\s+\S+)")
SESSION: dict = {}

class Err(Exception): pass
def die(msg): raise Err(msg)
def redact(s): return SECRET.sub("<redacted>", str(s))
def fp(v): return f"{v[:4]}…#{hashlib.sha256(v.encode()).hexdigest()[:6]}"

def secure_write(p: Path, data: str):
    p.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(p, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w") as f: f.write(data)

def http(method, url, headers=None, body=None, timeout=20):
    req = urllib.request.Request(url, data=body, headers=headers or {}, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, {k.lower(): v for k, v in r.headers.items()}, r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, {k.lower(): v for k, v in e.headers.items()}, e.read().decode("utf-8", "replace")
    except Exception as e:
        return 0, {}, f"{type(e).__name__}: {e}"

def get_client(create=False):
    cid, sec = os.environ.get("DOORBELL_CLIENT_ID"), os.environ.get("DOORBELL_CLIENT_SECRET")
    if cid: return {"client_id": cid, "client_secret": sec or ""}
    f = CONF / "client.json"
    if f.exists(): return json.loads(f.read_text())
    if not create: return None
    if not LOOPBACK.match(BASE): die("refusing dynamic client registration against a non-loopback base")
    body = {"client_name": "doorbell-skill", "redirect_uris": ["http://127.0.0.1/cb"], "grant_types": ["client_credentials"], "token_endpoint_auth_method": "client_secret_post"}
    st, _, txt = http("POST", BASE + "/api/oauth/register", {"Content-Type": "application/json"}, json.dumps(body).encode())
    if st not in (200, 201): die(f"registration failed: HTTP {st} {redact(txt)[:200]}")
    d = json.loads(txt); c = {"client_id": d["client_id"], "client_secret": d.get("client_secret", "")}
    secure_write(f, json.dumps(c)); return c

def token_paths():
    paths = []
    st, _, txt = http("GET", BASE + "/.well-known/oauth-authorization-server")
    if st == 200:
        try: paths.append(urllib.parse.urlparse(json.loads(txt)["token_endpoint"]).path)
        except Exception: pass
    for p in ("/api/oauth/token", "/token"):
        if p not in paths: paths.append(p)
    return paths

def get_token(force=False):
    tf = CACHE / "token.json"
    if not force and tf.exists():
        try:
            t = json.loads(tf.read_text())
            if t["base"] == BASE and t["exp"] > time.time() + 60: return t["access_token"]
        except Exception: pass
    def attempt(client):
        form = {"grant_type": "client_credentials"}
        if client: form.update(client_id=client["client_id"], client_secret=client["client_secret"])
        data = urllib.parse.urlencode(form).encode()
        for p in token_paths():
            st, _, txt = http("POST", BASE + p, {"Content-Type": "application/x-www-form-urlencoded"}, data)
            if st == 200:
                try: d = json.loads(txt); return d["access_token"], int(d.get("expires_in", 3600))
                except Exception: continue
        return None
    r = attempt(get_client()) or attempt(get_client(create=True))
    if not r: die("could not obtain a token (bridge down or token path changed; run: ss -ltnp | rg 25202)")
    tok, ttl = r
    secure_write(tf, json.dumps({"base": BASE, "access_token": tok, "exp": time.time() + ttl}))
    return tok

def parse(txt, rid):
    txt = txt.strip(); msgs = []
    if txt[:1] in "{[":
        try: j = json.loads(txt); msgs = j if isinstance(j, list) else [j]
        except Exception: pass
    if not msgs:
        for line in txt.splitlines():
            if line.startswith("data:"):
                try: msgs.append(json.loads(line[5:].strip()))
                except Exception: pass
    for m in msgs:
        if m.get("id") == rid or len(msgs) == 1:
            if "error" in m: die(f"MCP error: {redact(json.dumps(m['error']))[:400]}")
            return m.get("result")
    die(f"unparseable MCP response: {redact(txt)[:300]}")

def rpc(token, method, params=None, rid=1, notify=False):
    body = {"jsonrpc": "2.0", "method": method}
    if params is not None: body["params"] = params
    if not notify: body["id"] = rid
    h = {"Authorization": f"Bearer {token}", "Content-Type": "application/json", "Accept": "application/json, text/event-stream"}
    if SESSION.get("id"): h["Mcp-Session-Id"] = SESSION["id"]
    last = None
    for p in ([SESSION["path"]] if SESSION.get("path") else MCP_PATHS):
        st, hd, txt = http("POST", BASE + p, h, json.dumps(body).encode(), timeout=60)
        if st in (404, 405): last = (st, p); continue
        SESSION["path"] = p
        if hd.get("mcp-session-id"): SESSION["id"] = hd["mcp-session-id"]
        if notify: return None
        if st == 401: die("401 from MCP: token rejected (run: doorbell.py status)")
        if st not in (200, 202): die(f"HTTP {st} from {p}: {redact(txt)[:300]}")
        return parse(txt, rid)
    die(f"no MCP endpoint answered (tried {MCP_PATHS}); last={last}")

def handshake(token):
    if SESSION.get("ready"): return
    try:
        rpc(token, "initialize", {"protocolVersion": "2025-06-18", "capabilities": {}, "clientInfo": {"name": "doorbell-skill", "version": "1"}}, rid=0)
        rpc(token, "notifications/initialized", notify=True)
    except Err: pass  # some bridges accept tools/list without initialize
    SESSION["ready"] = True

def list_tools(token):
    handshake(token)
    return (rpc(token, "tools/list", {}, rid=2) or {}).get("tools", [])

def cmd_status(a):
    print(f"base={BASE}")
    st, _, _ = http("GET", BASE + "/.well-known/oauth-authorization-server"); print(f"discovery: HTTP {st}")
    t0 = time.time(); tok = get_token(force=a.refresh); print(f"token: ok {fp(tok)} ({int((time.time() - t0) * 1000)}ms)")
    tools = list_tools(tok); print(f"mcp: ok path={SESSION.get('path')} session={'yes' if SESSION.get('id') else 'no'} tools={len(tools)}")

def cmd_tools(a):
    for t in list_tools(get_token()):
        req = ",".join((t.get("inputSchema") or {}).get("required", [])) or "-"
        print(f"{t['name']:32} req=[{req}]  {(t.get('description') or '').strip().splitlines()[0][:90] if t.get('description') else ''}")

def cmd_call(a):
    if DESTRUCTIVE.search(a.tool) and not a.yes:
        die(f"'{a.tool}' looks state-changing; re-run with --yes after the user has approved it")
    try: args = json.loads(a.args)
    except Exception: die("args must be a JSON object, e.g. '{\"path\":\"/tmp/x\"}'")
    tok = get_token(); handshake(tok)
    res = rpc(tok, "tools/call", {"name": a.tool, "arguments": args}, rid=3) or {}
    for c in res.get("content", []):
        print(redact(c.get("text") if c.get("type") == "text" else json.dumps(c)))
    if res.get("isError"): sys.exit(2)

def cmd_exposure(a):
    print(f"public={PUBLIC}")
    st, _, _ = http("POST", PUBLIC + "/doorbell-mcp", {"Content-Type": "application/json", "Accept": "application/json, text/event-stream"}, json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/list"}).encode())
    print(f"[{'PASS' if st in (401, 403, 404) else 'FAIL'}] unauthenticated tools/list on public MCP → HTTP {st} (want 401/403/404)")
    body = {"client_name": "exposure-probe", "redirect_uris": ["https://claude.ai/api/mcp/auth_callback"], "grant_types": ["authorization_code"], "response_types": ["code"], "token_endpoint_auth_method": "client_secret_post"}
    st, _, _ = http("POST", PUBLIC + "/api/oauth/register", {"Content-Type": "application/json"}, json.dumps(body).encode())
    note = {404: "not proxied: safe, but the claude.ai connector cannot register", 201: "OPEN registration reachable from the internet: gate /authorize behind human approval first"}.get(st, "")
    print(f"[INFO] public DCR → HTTP {st} {note}")

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--yes", action="store_true", help="assume approval for state-changing calls")
    common.add_argument("--refresh", action="store_true", help="force token refresh")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("status", parents=[common]).set_defaults(f=cmd_status)
    sub.add_parser("tools", parents=[common]).set_defaults(f=cmd_tools)
    c = sub.add_parser("call", parents=[common]); c.add_argument("tool"); c.add_argument("args", nargs="?", default="{}"); c.set_defaults(f=cmd_call)
    sub.add_parser("exposure", parents=[common]).set_defaults(f=cmd_exposure)
    a = ap.parse_args()
    try: a.f(a)
    except Err as e: print(f"doorbell: {redact(e)}", file=sys.stderr); sys.exit(1)

if __name__ == "__main__": main()
