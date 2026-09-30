#!/usr/bin/env python3
"""Exhaustive genuine-Kimi provider probe. Run on yote.
Read-only: reads keys from /home/toxic/.secrets, NEVER prints key values.
Tests each provider for a real Kimi completion; reports honest upstream status."""
import json, os, sys, time, urllib.request, urllib.error

# Load secrets without printing
secrets = {}
try:
    with open('/home/toxic/.secrets') as f:
        for line in f:
            line = line.strip()
            if line.startswith('export '):
                line = line[7:].strip()
            if line and not line.startswith('#') and '=' in line:
                k, v = line.split('=', 1)
                secrets[k.strip()] = v.strip().strip('"').strip("'")
except Exception as e:
    print('WARN: could not read .secrets:', e)

def mask_present(name):
    v = secrets.get(name, '')
    return 'SET(%d chars)' % len(v) if v and 'password' not in v.lower() else ('MISSING' if not v else 'SET')

print('=== key presence (values never printed) ===')
for k in ['MOONSHOT_API_KEY', 'OPENROUTER_API_KEY', 'OPENROUTER_API_KEY_1',
          'OPENROUTER_API_KEY_FREE', 'HF_TOKEN', 'NVIDIA_API_KEY']:
    print(' ', k, mask_present(k))

def post(url, headers, payload, timeout=60):
    body = json.dumps(payload).encode()
    req = urllib.request.Request(url, data=body, headers=headers)
    t = time.time()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            d = json.load(r)
        dt = time.time() - t
        msg = d.get('choices', [{}])[0].get('message', {}).get('content', '')
        return ('200', dt, (msg or '')[:80], None)
    except urllib.error.HTTPError as e:
        try:
            err = e.read().decode()[:200]
        except Exception:
            err = ''
        return (str(e.code), time.time() - t, '', err)
    except Exception as e:
        return ('ERR', time.time() - t, '', str(e)[:120])

P = {"messages": [{"role": "user", "content": "Reply with exactly: KIMI_OK"}], "max_tokens": 32}

print('\n=== 1. Moonshot direct (platform API) ===')
mk = secrets.get('MOONSHOT_API_KEY', '')
if mk:
    for mid in ['kimi-k2.6', 'kimi-k3']:
        code, dt, content, err = post('https://api.moonshot.ai/v1/chat/completions',
            {'Content-Type': 'application/json', 'Authorization': 'Bearer ' + mk},
            dict(P, model=mid), timeout=90)
        print(' moonshot/%s -> %s in %.1fs content=%r err=%r' % (mid, code, dt, content, (err or '')[:100]))
else:
    print(' SKIP: no MOONSHOT_API_KEY')

print('\n=== 2. OpenRouter (free + paid pools) ===')
for keyname in ['OPENROUTER_API_KEY_FREE', 'OPENROUTER_API_KEY_1', 'OPENROUTER_API_KEY']:
    k = secrets.get(keyname, '')
    if not k:
        print(' SKIP:', keyname, 'missing'); continue
    for mid in ['moonshotai/kimi-k3:free', 'moonshotai/kimi-k2.6:free']:
        code, dt, content, err = post('https://openrouter.ai/api/v1/chat/completions',
            {'Content-Type': 'application/json', 'Authorization': 'Bearer ' + k,
             'HTTP-Referer': 'https://sovereign.local', 'X-Title': 'kimi-probe'},
            dict(P, model=mid), timeout=90)
        print(' OR[%s] %s -> %s in %.1fs content=%r err=%r' % (keyname, mid, code, dt, content, (err or '')[:100]))

print('\n=== 3. HuggingFace Inference Providers ===')
hf = secrets.get('HF_TOKEN', '') or secrets.get('HUGGING_FACE_HUB_TOKEN', '')
if hf:
    for mid in ['moonshotai/Kimi-K3', 'moonshotai/Kimi-K2-Instruct']:
        code, dt, content, err = post('https://router.huggingface.co/v1/chat/completions',
            {'Content-Type': 'application/json', 'Authorization': 'Bearer ' + hf},
            dict(P, model=mid), timeout=120)
        print(' hf/%s -> %s in %.1fs content=%r err=%r' % (mid, code, dt, content, (err or '')[:100]))
else:
    print(' SKIP: no HF token')

print('\n=== 4. NVIDIA NIM ===')
nv = secrets.get('NVIDIA_API_KEY', '')
if nv:
    code, dt, content, err = post('https://integrate.api.nvidia.com/v1/chat/completions',
        {'Content-Type': 'application/json', 'Authorization': 'Bearer ' + nv},
        dict(P, model='moonshotai/kimi-k2-instruct'), timeout=90)
    print(' nim/kimi-k2-instruct -> %s in %.1fs content=%r err=%r' % (code, dt, content, (err or '')[:100]))
else:
    print(' SKIP: no NVIDIA_API_KEY')

print('\n=== 5. Pollinations (no key) ===')
code, dt, content, err = post('https://text.pollinations.ai/openai',
    {'Content-Type': 'application/json'},
    dict(P, model='kimi-k2'), timeout=120)
print(' pollinations/kimi-k2 -> %s in %.1fs content=%r err=%r' % (code, dt, content, (err or '')[:100]))

print('\n=== 6. herd Kimi aliases (end-to-end via :25100) ===')
for alias in ['kimi', 'kimi-k2', 'kimi-code', 'kimi-auto']:
    code, dt, content, err = post('http://127.0.0.1:25100/v1/chat/completions',
        {'Content-Type': 'application/json'},
        dict(P, model=alias), timeout=300)
    print(' herd/%s -> %s in %.1fs content=%r err=%r' % (alias, code, dt, content, (err or '')[:100]))

print('\n=== 7. standalone kimi-auto shim :25153 ===')
code, dt, content, err = post('http://127.0.0.1:25153/v1/chat/completions',
    {'Content-Type': 'application/json'},
    dict(P, model='kimi-auto'), timeout=300)
print(' shim25153/kimi-auto -> %s in %.1fs content=%r err=%r' % (code, dt, content, (err or '')[:100]))
print('DONE')
