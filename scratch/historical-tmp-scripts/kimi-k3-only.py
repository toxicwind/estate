#!/usr/bin/env python3
"""Kimi K3 NIM completion — hot-load-aware (300s), identity-checked. Key never printed."""
import json, time, urllib.request, urllib.error

key = None
with open('/home/toxic/.secrets') as f:
    for line in f:
        line = line.strip()
        if line.startswith('export '):
            line = line[7:].strip()
        if line.startswith('NVIDIA_API_KEY='):
            key = line.split('=', 1)[1].strip().strip('"').strip("'")
assert key, 'no NVIDIA_API_KEY'

def post(payload, timeout):
    body = json.dumps(payload).encode()
    h = {'Content-Type': 'application/json', 'Authorization': 'Bearer ' + key}
    r = urllib.request.Request('https://integrate.api.nvidia.com/v1/chat/completions',
                               data=body, headers=h, method='POST')
    t = time.time()
    try:
        with urllib.request.urlopen(r, timeout=timeout) as resp:
            return (resp.status, time.time() - t, dict(resp.headers), resp.read().decode())
    except urllib.error.HTTPError as e:
        try:
            eb = e.read().decode()[:800]
        except Exception:
            eb = ''
        return (e.code, time.time() - t, dict(e.headers), eb)
    except Exception as e:
        return ('ERR', time.time() - t, {}, repr(e)[:300])

payload = {
    'model': 'moonshotai/kimi-k3',
    'messages': [{'role': 'user',
                  'content': 'What model are you? Reply with your exact model name and vendor, one short line.'}],
    'max_tokens': 64,
    'stream': False,
}
print('POST kimi-k3 ...', flush=True)
s, dt, hd, body = post(payload, 300)
print('STATUS:', s, 'in %.1fs' % dt, flush=True)
print('BODY[:800]:', body[:800], flush=True)
if s == 202:
    rid = hd.get('NVCF-REQID') or hd.get('nvcf-reqid')
    print('ASYNC 202 reqid=', rid, flush=True)
    if rid:
        for i in range(28):
            time.sleep(10)
            h2 = {'Authorization': 'Bearer ' + key}
            rq = urllib.request.Request('https://api.nvcf.nvidia.com/v2/nvcf/queues/' + rid,
                                        headers=h2, method='GET')
            try:
                with urllib.request.urlopen(rq, timeout=60) as rp:
                    b2 = rp.read().decode()
                print('poll %d -> 200: %s' % (i, b2[:500]), flush=True)
                break
            except urllib.error.HTTPError as e2:
                if e2.code == 202:
                    print('poll %d -> 202 still queued' % i, flush=True)
                    continue
                print('poll %d -> %d: %s' % (i, e2.code, e2.read().decode()[:200]), flush=True)
                break
            except Exception as e2:
                print('poll %d ERR %s' % (i, repr(e2)[:150]), flush=True)
                break
if s == 200:
    try:
        d = json.loads(body)
        print('CONTENT:', d['choices'][0]['message']['content'][:300], flush=True)
        print('MODEL_FIELD:', d.get('model'), flush=True)
    except Exception as e:
        print('parse fail:', e, flush=True)
print('DONE', flush=True)
