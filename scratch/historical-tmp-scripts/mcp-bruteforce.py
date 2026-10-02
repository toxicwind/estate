#!/usr/bin/env python3
"""Bruteforce every browserless-mcp tool via real MCP stdio. Read responses, then kill (server doesn't exit on stdin EOF)."""
import json, subprocess, select, time, sys

MCP_SH = "/home/toxic/sovereign/projects/mesh/browserless/mcp.sh"
TEST_PAGE = "data:text/html,<html><body><h1 id='h'>hello</h1><input id='i' value=''><button id='b' onclick=\"document.getElementById('h').textContent='clicked'\">go</button></body></html>"
results = []

def run_calls(calls, per_call_timeout=25):
    """calls: list of (name, args). Returns list of (name, ok, summary)."""
    lines = [
        json.dumps({"jsonrpc":"2.0","id":1,"method":"initialize",
                    "params":{"protocolVersion":"2024-11-05","capabilities":{}, "clientInfo":{"name":"brute","version":"1"}}}),
        json.dumps({"jsonrpc":"2.0","method":"notifications/initialized"}),
    ]
    ids = {}
    for i,(name,args) in enumerate(calls, start=10):
        ids[i] = name
        lines.append(json.dumps({"jsonrpc":"2.0","id":i,"method":"tools/call",
                                 "params":{"name":name,"arguments":args}}))
    p = subprocess.Popen([MCP_SH], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE, text=True)
    p.stdin.write("\n".join(lines)+"\n"); p.stdin.flush()
    got = {}
    deadline = time.time() + per_call_timeout * max(1,len(calls))
    buf = ""
    while time.time() < deadline and len(got) < len(calls):
        r,_,_ = select.select([p.stdout], [], [], 1.0)
        if r:
            chunk = p.stdout.readline()
            if not chunk: break
            try: d = json.loads(chunk)
            except: continue
            if d.get("id",0) >= 10:
                got[d["id"]] = d
        elif p.poll() is not None:
            break
    try: p.kill()
    except: pass
    out = []
    for i,(name,args) in enumerate(calls, start=10):
        d = got.get(i)
        if d is None:
            out.append((name, False, "NO_RESPONSE (timeout/hang)"))
        elif "error" in d:
            out.append((name, False, "RPC_ERROR: "+json.dumps(d["error"])[:150]))
        else:
            r = d.get("result",{})
            content = r.get("content",[])
            txt = content[0].get("text","") if content else json.dumps(r)[:200]
            is_err = r.get("isError", False)
            out.append((name, not is_err, txt[:200].replace("\n"," ")))
    return out

def show(res):
    for (n,ok,txt) in res:
        print(("PASS " if ok else "FAIL ") + n + " - " + txt[:110])
        results.append((n,ok,txt))

print("== PHASE 1: persistent_status / tabs ==")
r = run_calls([("persistent_status",{}),("persistent_tabs",{})]); show(r)

print("== PHASE 2: new tab + navigate + read ==")
r = run_calls([("persistent_new_tab",{"url":TEST_PAGE})]); show(r)
tab = None
for (n,ok,txt) in r:
    if n=="persistent_new_tab" and ok:
        try:
            d = json.loads(txt); tab = d.get("tabId") or d.get("id")
        except: pass
print("TAB:", tab)
if tab:
    r = run_calls([
        ("persistent_navigate",{"tab":tab,"url":TEST_PAGE}),
        ("persistent_text",{"tab":tab}),
        ("persistent_evaluate",{"tab":tab,"function":"document.getElementById('h').textContent"}),
    ]); show(r)
    print("== PHASE 3: click/fill/screenshot ==")
    r = run_calls([
        ("persistent_click",{"tab":tab,"selector":"#b"}),
        ("persistent_evaluate",{"tab":tab,"function":"document.getElementById('h').textContent"}),
        ("persistent_fill",{"tab":tab,"selector":"#i","text":"bruteforce"}),
        ("persistent_evaluate",{"tab":tab,"function":"document.getElementById('i').value"}),
        ("persistent_screenshot",{"tab":tab}),
    ]); show(r)
    print("== PHASE 4: activate/tabs/close + failure injection ==")
    r = run_calls([
        ("persistent_activate_tab",{"tab":tab}),
        ("persistent_tabs",{}),
        ("persistent_navigate",{"tab":"no-such-tab","url":TEST_PAGE}),
        ("persistent_click",{"tab":tab,"selector":"#does-not-exist"}),
        ("persistent_close_tab",{"tab":tab}),
        ("persistent_close_tab",{"tab":tab}),
    ]); show(r)
else:
    print("SKIP phases 2-4: no tab")

print("== PHASE 5: legacy HTTP tools ==")
r = run_calls([
    ("get_health",{}),
    ("get_config",{}),
    ("get_metrics",{}),
    ("get_sessions",{}),
    ("initialize_browserless",{}),
    ("get_content",{"url":TEST_PAGE}),
    ("take_screenshot",{"url":TEST_PAGE}),
], per_call_timeout=30); show(r)
r = run_calls([
    ("execute_function",{"url":TEST_PAGE,"function":"() => document.title"}),
    ("generate_pdf",{"url":TEST_PAGE}),
    ("unblock",{"url":TEST_PAGE}),
    ("export_page",{"url":TEST_PAGE}),
    ("run_performance_audit",{"url":TEST_PAGE}),
    ("execute_browserql",{"query":"{ status }"}),
    ("download_files",{"url":TEST_PAGE}),
    ("create_websocket_connection",{}),
], per_call_timeout=40); show(r)

print("== SUMMARY ==")
npass = sum(1 for x in results if x[1]); nfail = sum(1 for x in results if not x[1])
print(f"PASS {npass} FAIL {nfail} TOTAL {len(results)}")
for (n,ok,txt) in results:
    if not ok: print("FAILED:",n,"-",txt[:140])
