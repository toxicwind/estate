import json, time, urllib.request, urllib.error
body = json.dumps({'model':'kimi-k3-nim','messages':[{'role':'user','content':'Reply with exactly: HERD_E2E_OK'}],'max_tokens':64}).encode()
r = urllib.request.Request('http://127.0.0.1:25100/v1/chat/completions', data=body, headers={'Content-Type':'application/json'})
t=time.time()
try:
    with urllib.request.urlopen(r, timeout=400) as x:
        d=json.load(x); dt=time.time()-t
        ch=d['choices'][0]['message']
        print('STATUS', x.status, 'in %.1fs'%dt, flush=True)
        print('CONTENT:', ch.get('content'), flush=True)
except urllib.error.HTTPError as e:
    print('HTTP', e.code, 'in %.1fs'%(time.time()-t), flush=True); print(e.read().decode()[:500], flush=True)
except Exception as e:
    print('ERR in %.1fs'%(time.time()-t), repr(e)[:200], flush=True)
print('DONE', flush=True)
