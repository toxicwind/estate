import json, subprocess, select, time
exec(open("/tmp/act2.py").read().split("# create tab")[0])
TP="data:text/html,<h1>hi</h1>"
for phase,calls in [
  ("L1",[("get_health",{}),("get_config",{}),("get_metrics",{}),("get_sessions",{}),("initialize_browserless",{})]),
  ("L2",[("get_content",{"url":TP}),("take_screenshot",{"url":TP}),("execute_function",{"url":TP,"code":"() => 1"})]),
  ("L3",[("generate_pdf",{"url":TP}),("unblock",{"url":TP}),("export_page",{"url":TP}),("run_performance_audit",{"url":TP})]),
  ("L4",[("execute_browserql",{"query":"{ status }"}),("download_files",{"url":TP}),("create_websocket_connection",{})]),
]:
    t0=time.time(); g=call(calls,timeout=50)
    print(f"== {phase} ({time.time()-t0:.1f}s) ==")
    for i,(n,a) in enumerate(calls, start=10):
        d=g.get(i,{})
        if "error" in d: print("FAIL",n,"-",json.dumps(d["error"])[:130])
        else:
            r=d["result"]; txt=r["content"][0]["text"] if r.get("content") else json.dumps(r)[:80]
            print(("PASS " if not r.get("isError") else "FAIL ")+n+" - "+txt[:110].replace("\n"," "))
