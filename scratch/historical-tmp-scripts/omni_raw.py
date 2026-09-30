import json, time, urllib.request, urllib.error
ROUTER = 'http://127.0.0.1:25104/v1/chat/completions'
# Direct-ish: use routeCircuitChain-free explicit via hybrid_direct; read raw body on 503
for i in range(3):
    sid = 'omniraw%d' % (int(time.time()*10) % 100000 + i)
    body = json.dumps({'model': 'nvidia/nvidia/nemotron-3-nano-omni-30b-a3b-reasoning', 'messages': [{'role':'user','content':'Say OK'}],'max_tokens': 20, 'stream': False}).encode()
    req = urllib.request.Request(ROUTER, data=body, headers={'Content-Type':'application/json','X-Sovereign-Strategy':'hybrid','X-Session-Id': sid})
    t = time.time()
    try:
        r = urllib.request.urlopen(req, timeout=60)
        print('try%d: %s via=%s %.1fs' % (i, r.status, r.headers.get('X-Routed-Via'), time.time()-t), flush=True)
    except urllib.error.HTTPError as e:
        print('try%d: HTTP %s %.1fs body=%r' % (i, e.code, time.time()-t, e.read().decode()[:200]), flush=True)
    time.sleep(5)
