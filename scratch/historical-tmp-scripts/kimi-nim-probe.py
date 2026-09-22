#!/usr/bin/env python3
"""Kimi K3 NIM probe — correct model ID, hot-load-aware, identity-checked.
Read-only key use: NVIDIA_API_KEY read from /home/toxic/.secrets, NEVER printed."""
import json, time, urllib.request, urllib.error

key = None
with open('/home/toxic/.secrets') as f:
    for line in f:
        line = line.strip()
        if line.startswith('export '):
            line = line[7:].strip()
        if line.startswith('NVIDIA_API_KEY='):
            key = line.split('=', 1)[1].strip().strip('"').strip("'")
assert key, 'no NVIDIA_API_KEY in .secrets'
print('key: SET(%d chars)' % len(key), flush=True)

def req(method, url, payload=None, timeout=180):
    body = json.dumps(payload).encode() if payload is not None else None
    h = {'Content-Type': 'application/json', 'Authorization': 'Bearer ' + key}
    r = urllib.request.Request(url, data=body, headers=h, method=method)
    t = time.time()
    try:
        with urllib.request.urlopen(r, timeout=timeout) as resp:
            data = resp.read().decode()
        return (resp.status, time.time() - t, dict(resp.headers), data)
    except urllib.error.HTTPError as e:
        try:
            eb = e.read().decode()[:600]
        except Exception:
            eb = ''
        return (e.code, time.time() - t, dict(e.headers), eb)
    except Exception as e:
        return ('ERR', time.time() - t, {}, repr(e)[:200])

print('\n=== 1. GET /v1/models (is kimi-k3 listed?) ===', flush=True)
s, dt, hd, body = req('GET', 'https://integrate.api.nvidia.com/v1/models', timeout=60)
print(' -> %s in %.1fs' % (s, dt), flush=True)
if s == 200:
    ms = json.loads(body)['data']
    k3 = [m for m in ms if 'kimi' in m['id'].lower()]
    print(' total models:', len(ms), flush=True)
    for m in k3:
        print('  KIMI:', m['id'], flush=True)
else:
    print(' body:', body[:300], flush=True)

print('\n=== 2. NVCF function entitlement (read-only) ===', flush=True)
s, dt, hd, body = req('GET', 'https://api.nvcf.nvidia.com/v2/nvcf/functions', timeout=60)
print(' -> %s in %.1fs body[:300]=%r' % (s, dt, body[:300]), flush=True)

print('\n=== 3. repro: kimi-k2-instruct (round-2 410 source?) ===', flush=True)
s, dt, hd, body = req('POST', 'https://integrate.api.nvidia.com/v1/chat/completions',
    {'model': 'moonshotai/kimi-k2-instruct',
     'messages': [{'role': 'user', 'content': 'Reply with exactly: K2_OK'}],
     'max_tokens': 16, 'stream': False}, timeout=60)
print(' -> %s in %.1fs body[:300]=%r' % (s, dt, body[:300]), flush=True)

print('\n=== 4. kimi-k3 completion, hot-load-aware (180s), identity check ===', flush=True)
payload = {
    'model': 'moonshotai/kimi-k3',
    'messages': [{'role': 'user',
                  'content': 'What model are you? Reply with your exact model name and vendor, one short line.'}],
    'max_tokens': 64,
    'stream': False,
    # NOTE: top_p deliberately omitted — NVIDIA pins it per-model (0.95 for K3);
    # injecting the OpenAI default 1.0 gets a 400 validation error.
}
s, dt, hd, body = req('POST', 'https://integrate.api.nvidia.com/v1/chat/completions', payload, timeout=180)
print(' -> %s in %.1fs' % (s, dt), flush=True)
print(' body[:600]=%r' % body[:600], flush=True)
if s == 202:
    rid = hd.get('NVCF-REQID') or hd.get('nvcf-reqid') or hd.get('Nvcf-Reqid')
    print(' ASYNC 202, reqid=', rid, flush=True)
    if rid:
        for i in range(18):
            time.sleep(10)
            s2, dt2, hd2, b2 = req('GET',
                'https://api.nvcf.nvidia.com/v2/nvcf/queues/' + rid, timeout=60)
            print(' poll %d -> %s in %.1fs body[:200]=%r' % (i, s2, dt2, b2[:200]), flush=True)
            if s2 == 200:
                print(' FINAL:', b2[:600], flush=True)
                break
if s == 200:
    try:
        d = json.loads(body)
        msg = d['choices'][0]['message']['content']
        print(' CONTENT:', msg[:200], flush=True)
        print(' MODEL_FIELD:', d.get('model'), flush=True)
    except Exception as e:
        print(' parse fail:', e, flush=True)
print('DONE', flush=True)
