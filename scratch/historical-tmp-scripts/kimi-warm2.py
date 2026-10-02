#!/usr/bin/env python3
"""Warm-latency check: is kimi-k3 warm after the first 131.7s call? Key never printed."""
import json, time, urllib.request, urllib.error

key = None
with open('/home/toxic/.secrets') as f:
    for line in f:
        line = line.strip()
        if line.startswith('export '):
            line = line[7:].strip()
        if line.startswith('NVIDIA_API_KEY='):
            key = line.split('=', 1)[1].strip().strip('"').strip("'")
assert key

payload = {
    'model': 'moonshotai/kimi-k3',
    'messages': [{'role': 'user', 'content': 'Reply with exactly: WARM_OK'}],
    'max_tokens': 32,
    'stream': False,
}
body = json.dumps(payload).encode()
h = {'Content-Type': 'application/json', 'Authorization': 'Bearer ' + key}
r = urllib.request.Request('https://integrate.api.nvidia.com/v1/chat/completions',
                           data=body, headers=h, method='POST')
t = time.time()
try:
    with urllib.request.urlopen(r, timeout=300) as resp:
        data = resp.read().decode()
    dt = time.time() - t
    d = json.loads(data)
    ch = d['choices'][0]
    msg = ch['message']
    print('STATUS 200 in %.1fs' % dt, flush=True)
    print('CONTENT:', (msg.get('content') or '')[:120], flush=True)
    print('REASONING[:120]:', (msg.get('reasoning_content') or '')[:120], flush=True)
    print('FINISH:', ch.get('finish_reason'), 'MODEL:', d.get('model'), flush=True)
    print('USAGE:', d.get('usage'), flush=True)
except urllib.error.HTTPError as e:
    print('HTTP', e.code, 'in %.1fs' % (time.time() - t), e.read().decode()[:300], flush=True)
except Exception as e:
    print('ERR in %.1fs' % (time.time() - t), repr(e)[:200], flush=True)
print('DONE', flush=True)
