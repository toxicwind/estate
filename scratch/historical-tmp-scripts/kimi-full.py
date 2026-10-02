#!/usr/bin/env python3
"""Single focused probe via sidecar :25163 with FULL response dump."""
import json, time, urllib.request, urllib.error
payload = {'model': 'moonshotai/kimi-k3',
           'messages': [{'role': 'user', 'content': 'What model are you? Answer in one English sentence.'}],
           'max_tokens': 128, 'stream': False}
h = {'Content-Type': 'application/json'}
r = urllib.request.Request('http://127.0.0.1:25163/v1/chat/completions',
                           data=json.dumps(payload).encode(), headers=h, method='POST')
t = time.time()
try:
    with urllib.request.urlopen(r, timeout=500) as resp:
        raw = resp.read().decode()
    dt = time.time() - t
    d = json.loads(raw)
    ch = d['choices'][0]
    msg = ch['message']
    print('200 in %.1fs' % dt, flush=True)
    print('MODEL:', d.get('model'), flush=True)
    print('FINISH:', ch.get('finish_reason'), flush=True)
    print('CONTENT:', repr(msg.get('content'))[:400], flush=True)
    print('REASONING:', repr(msg.get('reasoning_content'))[:400], flush=True)
    print('USAGE:', d.get('usage'), flush=True)
except urllib.error.HTTPError as e:
    print('HTTP %d in %.1fs %s' % (e.code, time.time()-t, e.read().decode()[:600]), flush=True)
except Exception as e:
    print('ERR in %.1fs %r' % (time.time()-t, e), flush=True)
print('DONE', flush=True)
