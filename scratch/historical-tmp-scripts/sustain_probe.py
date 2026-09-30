import json, time, urllib.request, urllib.error
ROUTER = 'http://127.0.0.1:25104/v1/chat/completions'
N = 60
res = []
for i in range(N):
    sid = 'sus%d' % (int(time.time()*10) % 1000000 + i)
    body = json.dumps({'model': 'free', 'messages': [{'role':'user','content':'Reply with exactly: OK'}],'max_tokens': 20, 'stream': False}).encode()
    req = urllib.request.Request(ROUTER, data=body, headers={'Content-Type':'application/json','X-Sovereign-Strategy':'hybrid','X-Session-Id': sid})
    t = time.time()
    try:
        r = urllib.request.urlopen(req, timeout=90)
        r.read()
        res.append((r.status, round(time.time()-t,1), r.headers.get('X-Routed-Via','?')))
    except urllib.error.HTTPError as e:
        res.append((e.code, round(time.time()-t,1), 'HTTPError'))
    except Exception as e:
        res.append(('ERR', round(time.time()-t,1), type(e).__name__))
    print('req %d: %s' % (i, res[-1]), flush=True)
ok = sum(1 for s,_,_ in res if s == 200)
e503 = sum(1 for s,_,_ in res if s == 503)
print('SUMMARY: %d/%d ok, %d x503' % (ok, N, e503))
