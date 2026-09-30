import json, time, urllib.request, urllib.error
N = int(__import__("sys").argv[1]) if len(__import__("sys").argv)>1 else 60
out = []
for i in range(N):
    body = json.dumps({"model":"free","messages":[{"role":"user","content":"Reply with exactly: PROBE-OK"}],"max_tokens":16}).encode()
    req = urllib.request.Request("http://127.0.0.1:25104/v1/chat/completions", data=body,
        headers={"Content-Type":"application/json","X-Session-Id":f"probe-{i%8}"})
    t=time.time(); code=None; via="-"; err="-"; em="-"
    try:
        r = urllib.request.urlopen(req, timeout=130)
        code=r.status; via=r.headers.get("X-Routed-Via","-")
        b=r.read(400); em=(b[:120] or b"").decode("utf8","replace")
    except urllib.error.HTTPError as e:
        code=e.code; via=e.headers.get("X-Routed-Via","-")
        try: err=json.loads(e.read(600)).get("error","-")
        except Exception: err="unparseable"
    except Exception as e:
        err=f"exc:{type(e).__name__}:{str(e)[:80]}"
    dt=time.time()-t
    out.append((i,code,via,round(dt,1),str(err)[:70],em[:40].replace("\n"," ")))
    print(f"{i}: {code} via={via} {dt:.1f}s err={str(err)[:70]}", flush=True)
    time.sleep(1.0)
import collections
codes=collections.Counter(o[1] for o in out)
print("SUMMARY codes:",dict(codes))
vias=collections.Counter(o[2] for o in out)
print("SUMMARY via:",dict(vias))
errs=collections.Counter(o[4] for o in out)
print("SUMMARY errs:",dict(errs))
json.dump(out, open("/tmp/probe_results.json","w"))
