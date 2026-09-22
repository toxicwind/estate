import json, time, urllib.request, urllib.error
body = json.dumps({'model':'moonshotai/kimi-k3','messages':[{'role':'user','content':'Who are you? Answer in one sentence, naming your model and maker.'}],'max_tokens':512}).encode()
r = urllib.request.Request('http://127.0.0.1:25163/v1/chat/completions', data=body, headers={'Content-Type':'application/json'})
t=time.time()
try:
    with urllib.request.urlopen(r, timeout=400) as x:
        d=json.load(x); dt=time.time()-t
        ch=d['choices'][0]['message']
        print('STATUS', x.status, 'in %.1fs'%dt, flush=True)
        print('MODEL:', d.get('model'), flush=True)
        print('REASONING[:200]:', (ch.get('reasoning_content') or ch.get('reasoning') or '')[:200], flush=True)
        print('CONTENT:', ch.get('content'), flush=True)
except urllib.error.HTTPError as e:
    print('HTTP', e.code, 'in %.1fs'%(time.time()-t), flush=True); print(e.read().decode()[:600], flush=True)
except Exception as e:
    print('ERR in %.1fs'%(time.time()-t), repr(e)[:200], flush=True)
print('DONE', flush=True)
