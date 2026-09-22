#!/usr/bin/env python3
"""E2E: kimi-k3-nim through herd :25100 with identity check."""
import json, time, urllib.request, urllib.error
payload = {'model': 'kimi-k3-nim',
           'messages': [{'role': 'user', 'content': 'What model are you? Reply in one short sentence.'}],
           'max_tokens': 64, 'stream': False}
h = {'Content-Type': 'application/json'}
r = urllib.request.Request('http://127.0.0.1:25100/v1/chat/completions',
                           data=json.dumps(payload).encode(), headers=h, method='POST')
t = time.time()
try:
    with urllib.request.urlopen(r, timeout=500) as resp:
        d = json.loads(resp.read().decode())
    dt = time.time() - t
    ch = d['choices'][0]
    print('E2E 200 in %.1fs' % dt, flush=True)
    print('CONTENT:', (ch['message'].get('content') or '')[:300], flush=True)
    print('MODEL:', d.get('model'), flush=True)
except urllib.error.HTTPError as e:
    print('E2E HTTP %d in %.1fs %s' % (e.code, time.time()-t, e.read().decode()[:500]), flush=True)
except Exception as e:
    print('E2E ERR in %.1fs %r' % (time.time()-t, e), flush=True)
print('DONE', flush=True)
