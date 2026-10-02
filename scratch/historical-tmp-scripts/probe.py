import requests, json, time
t=time.time()
r=requests.post("http://127.0.0.1:25104/v1/chat/completions", json={"model":"sovereign/free","messages":[{"role":"user","content":"Reply with exactly: PROBE_OK"}],"max_tokens":16}, timeout=90)
print(r.status_code, round(time.time()-t,1))
print(r.text[:400])
