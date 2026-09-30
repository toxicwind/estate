#!/usr/bin/env python3
"""Back-to-back latency: does kimi-k3 stay warm between immediate calls?"""
import json, time, urllib.request, urllib.error
key = open('/home/toxic/.secrets').read()
key = [l.split('=',1)[1].strip().strip('"').strip("'") for l in key.splitlines() if l.startswith('export NVIDIA_API_KEY=')][0]
def call(tag):
    payload = {'model': 'moonshotai/kimi-k3',
               'messages': [{'role': 'user', 'content': 'Reply with exactly: %s' % tag}],
               'max_tokens': 16, 'stream': False}
    h = {'Content-Type': 'application/json', 'Authorization': 'Bearer ' + key}
    r = urllib.request.Request('https://integrate.api.nvidia.com/v1/chat/completions',
                               data=json.dumps(payload).encode(), headers=h, method='POST')
    t = time.time()
    try:
        with urllib.request.urlopen(r, timeout=400) as resp:
            d = json.loads(resp.read().decode())
        dt = time.time() - t
        print('%s: 200 in %.1fs content=%r model=%s' % (tag, dt, d['choices'][0]['message'].get('content'), d.get('model')), flush=True)
    except urllib.error.HTTPError as e:
        print('%s: HTTP %d in %.1fs %s' % (tag, e.code, time.time()-t, e.read().decode()[:200]), flush=True)
    except Exception as e:
        print('%s: ERR in %.1fs %r' % (tag, time.time()-t, e), flush=True)
for i in (1, 2):
    call('PING%d' % i)
print('DONE', flush=True)
