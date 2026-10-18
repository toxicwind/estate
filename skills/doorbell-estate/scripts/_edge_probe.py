#!/usr/bin/env python3
"""Scratch loopback OAuth-compat matrix probe for doorbell-oauth-edge (:25217).
Standard library only. DELETE after running."""
import json, urllib.parse, urllib.request, urllib.error

BASE = "http://127.0.0.1:25217"
REDIRECT = "https://claude.ai/api/mcp/auth_callback"


def http(method, path, headers=None, body=None):
    url = BASE + path
    data = None
    if body is not None:
        if isinstance(body, (dict, list)):
            data = json.dumps(body).encode()
            headers = dict(headers or {})
            headers["Content-Type"] = "application/json"
        else:
            data = body.encode() if isinstance(body, str) else body
    req = urllib.request.Request(url, data=data, headers=headers or {}, method=method)
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return r.status, dict(r.headers), r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), e.read().decode("utf-8", "replace")
    except Exception as e:
        return 0, {}, f"{type(e).__name__}: {e}"


def show(n, label, st, hd, txt):
    prefix = txt[:220].replace("\n", "\\n")
    print(f"[{n}] {label} → HTTP {st} | {prefix}")
    if st >= 400:
        print(f"      headers: WWW-Authenticate={hd.get('www-authenticate')!r}")


# 1: POST /doorbell-mcp tools/list NO auth → 401 + WWW-Authenticate + error JSON
st, hd, txt = http("POST", "/doorbell-mcp", {"Accept": "application/json, text/event-stream"},
                   {"jsonrpc": "2.0", "id": 1, "method": "tools/list"})
show(1, "POST /doorbell-mcp tools/list NO auth", st, hd, txt)

# 2: DCR → 201 + client_id + client_secret
st, hd, txt = http("POST", "/api/oauth/register",
                   {"Content-Type": "application/json"},
                   {"client_name": "kite-test", "redirect_uris": [REDIRECT]})
show(2, "POST /api/oauth/register DCR", st, hd, txt)
try:
    d = json.loads(txt); CID = d["client_id"]; SEC = d["client_secret"]
except Exception:
    CID = SEC = None
    print("      (could not parse client creds)")

# 3: client_credentials token → 200 + tok_<hex>.<hmac>
if CID:
    st, hd, txt = http("POST", "/api/oauth/token",
                       {"Content-Type": "application/x-www-form-urlencoded"},
                       urllib.parse.urlencode({"grant_type": "client_credentials", "client_id": CID, "client_secret": SEC}))
    show(3, "POST /api/oauth/token client_credentials", st, hd, txt)
    try:
        TOK = json.loads(txt)["access_token"]
    except Exception:
        TOK = None
        print("      (could not parse access_token)")
else:
    TOK = None

# 4: MCP tools/list with Bearer → 200 + tools array
if TOK:
    st, hd, txt = http("POST", "/doorbell-mcp",
                       {"Authorization": f"Bearer {TOK}", "Accept": "application/json, text/event-stream"},
                       {"jsonrpc": "2.0", "id": 2, "method": "tools/list"})
    show(4, "POST /doorbell-mcp tools/list Bearer tok", st, hd, txt)

# 5: client_credentials bad secret → 401 invalid_client
if CID:
    st, hd, txt = http("POST", "/api/oauth/token",
                       {"Content-Type": "application/x-www-form-urlencoded"},
                       urllib.parse.urlencode({"grant_type": "client_credentials", "client_id": CID, "client_secret": "deadbeefbadsecret"}))
    show(5, "POST /api/oauth/token client_credentials BAD secret", st, hd, txt)

# 6: GET /.well-known/oauth-protected-resource → 200 discovery doc
st, hd, txt = http("GET", "/.well-known/oauth-protected-resource")
show(6, "GET /.well-known/oauth-protected-resource", st, hd, txt)

# 7: GET /authorize → 302 Location ?code=
if CID:
    st, hd, txt = http("GET", f"/authorize?client_id={CID}&redirect_uri={urllib.parse.quote(REDIRECT, safe='')}")
    show(7, "GET /authorize ?client_id=&redirect_uri=", st, hd, txt)
    try:
        loc = hd.get("location") or hd.get("Location") or ""
        CODE = urllib.parse.parse_qs(urllib.parse.urlparse(loc).query).get("code", [None])[0]
    except Exception:
        CODE = None
        print("      (could not parse code from Location)")
else:
    CODE = None

# 8: authorization_code token → 200 token
if CID and CODE:
    st, hd, txt = http("POST", "/api/oauth/token",
                       {"Content-Type": "application/x-www-form-urlencoded"},
                       urllib.parse.urlencode({"grant_type": "authorization_code", "code": CODE, "redirect_uri": REDIRECT, "client_id": CID}))
    show(8, "POST /api/oauth/token authorization_code", st, hd, txt)
    try:
        TOK2 = json.loads(txt)["access_token"]
    except Exception:
        TOK2 = None
        print("      (could not parse auth-code access_token)")
else:
    TOK2 = None

# 9: MCP tools/list Bearer token-from-8 → 200
if TOK2:
    st, hd, txt = http("POST", "/doorbell-mcp",
                       {"Authorization": f"Bearer {TOK2}", "Accept": "application/json, text/event-stream"},
                       {"jsonrpc": "2.0", "id": 3, "method": "tools/list"})
    show(9, "POST /doorbell-mcp tools/list Bearer auth-code tok", st, hd, txt)

print("DONE")
