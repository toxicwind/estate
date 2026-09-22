import json, sys, time, urllib.request, urllib.error
ROUTER = 'http://127.0.0.1:25104/v1/chat/completions'
def probe(spec, timeout=40):
    sid = 'mp%d' % (int(time.time()*10) % 100000)
    body = json.dumps({'model': spec, 'messages': [{'role':'user','content':'Reply with exactly: PROBE_OK'}],'max_tokens': 60, 'stream': False}).encode()
    req = urllib.request.Request(ROUTER, data=body, headers={'Content-Type':'application/json','X-Sovereign-Strategy':'hybrid','X-Session-Id': sid})
    t = time.time()
    try:
        r = urllib.request.urlopen(req, timeout=timeout)
        j = json.loads(r.read().decode())
        dt = time.time()-t
        txt = (j['choices'][0]['message'].get('content') or '')[:60]
        via = r.headers.get('X-Routed-Via', '?')
        print('%s -> %s via=%s %.1fs text=%r' % (spec, r.status, via, dt, txt), flush=True)
    except urllib.error.HTTPError as e:
        dt = time.time()-t
        eb = e.read().decode()[:200].replace(chr(10),' ')
        print('%s -> HTTP %s %.1fs body=%r' % (spec, e.code, dt, eb), flush=True)
    except Exception as e:
        print('%s -> ERR %s %s' % (spec, type(e).__name__, e), flush=True)
for spec in sys.argv[1:]:
    probe(spec)
