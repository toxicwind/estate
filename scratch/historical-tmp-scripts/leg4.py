import json, subprocess, select, time
exec(open("/tmp/leg2.py").read().split("TP=")[0])
TP="data:text/html,<h1>hi</h1>"
init=("initialize_browserless",{"token":"","host":"127.0.0.1","port":25130})
print("== with explicit host/port ==")
calls=[init,("get_health",{}),("get_config",{}),("get_metrics",{}),("get_sessions",{})]
g=call(calls,timeout=60); show(g,calls)
