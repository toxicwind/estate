import json, subprocess, select, time, re
exec(open("/tmp/leg2.py").read().split("TP=")[0])
TP="data:text/html,<h1>hi</h1>"
init=("initialize_browserless",{"token":tok})
print("== LEGACY BATCH 1 (init + health/config/metrics/sessions) ==")
calls=[init,("get_health",{}),("get_config",{}),("get_metrics",{}),("get_sessions",{})]
g=call(calls,timeout=60); show(g,calls)
print("== LEGACY BATCH 2 (init + content/screenshot/function) ==")
calls=[init,("get_content",{"url":TP}),("take_screenshot",{"url":TP}),("execute_function",{"url":TP,"code":"() => document.title"})]
g=call(calls,timeout=90); show(g,calls)
