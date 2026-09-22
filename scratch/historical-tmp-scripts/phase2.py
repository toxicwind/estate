import json, subprocess, select, time
exec(open("/tmp/phase1.py").read().split("TP=")[0].replace("for phase","XXX for phase"))
TP="data:text/html,<html><body><h1 id=h>hello</h1><input id=i value=><button id=b onclick=\"document.getElementById(CHARhCHAR).textContent=CHARclickedCHAR\">go</button></body></html>".replace("CHAR","\"")
# get a fresh tab
res=run_calls([("persistent_new_tab",{"url":"data:text/html,<h1>x</h1>"})],timeout=30)
tab=None
for (n,ok,txt) in res:
    print(("PASS " if ok else "FAIL ")+n+" - "+txt[:80])
    if ok:
        import re
        m=re.search(r"New tab (\d+)",txt); tab=int(m.group(1)) if m else None
print("TAB:",tab)
if tab is not None:
    for phase,calls in [
      ("P3",[("persistent_navigate",{"tab":tab,"url":TP}),
             ("persistent_text",{"tab":tab}),
             ("persistent_evaluate",{"tab":tab,"function":"document.getElementById(\"h\").textContent"})]),
      ("P4",[("persistent_click",{"tab":tab,"selector":"#b"}),
             ("persistent_evaluate",{"tab":tab,"function":"document.getElementById(\"h\").textContent"}),
             ("persistent_fill",{"tab":tab,"selector":"#i","text":"bruteforce"}),
             ("persistent_evaluate",{"tab":tab,"function":"document.getElementById(\"i\").value"}),
             ("persistent_screenshot",{"tab":tab})]),
      ("P5",[("persistent_activate_tab",{"tab":tab}),
             ("persistent_navigate",{"tab":999,"url":"data:text/html,x"}),
             ("persistent_click",{"tab":tab,"selector":"#does-not-exist"}),
             ("persistent_evaluate",{"tab":tab}),
             ("persistent_close_tab",{"tab":tab}),
             ("persistent_close_tab",{"tab":tab})]),
    ]:
        t0=time.time(); res=run_calls(calls,timeout=45)
        print(f"== {phase} ({time.time()-t0:.1f}s) ==")
        for (n,ok,txt) in res: print(("PASS " if ok else "FAIL ")+n+" - "+txt[:100])
