#!/usr/bin/env python3
"""Provider fuzzer: real completions, adequate tokens, no trust in listings.
Usage: fuzz.py <provider> <keyname> <base_url> <model> [model...]
Output: JSONL to stdout with {provider, model, http, content_preview, latency_ms, verdict}
"""
import json, sys, time, urllib.request, urllib.error, os

def get_key(keyname):
    # Read from /home/toxic/.secrets without printing
    val = None
    with open('/home/toxic/.secrets') as f:
        for line in f:
            line = line.strip()
            if line.startswith(f'export {keyname}='):
                val = line.split('=', 1)[1]
                # strip quotes if present
                if len(val) >= 2 and val[0] == val[-1] and val[0] in '"\'':
                    val = val[1:-1]
    return val

def probe(provider, key, base_url, model, max_tokens=100, timeout=60):
    url = base_url.rstrip('/') + '/chat/completions'
    payload = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": "Reply with exactly: FUZZ-LIVE"}],
        "max_tokens": max_tokens,
    }).encode()
    req = urllib.request.Request(url, data=payload, method='POST')
    req.add_header('Content-Type', 'application/json')
    req.add_header('Authorization', f'Bearer {key}')
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode('utf-8', errors='replace')
            http = resp.status
    except urllib.error.HTTPError as e:
        http = e.code
        body = e.read().decode('utf-8', errors='replace')[:500]
    except Exception as e:
        http = -1
        body = f'EXC: {type(e).__name__}: {str(e)[:200]}'
    latency_ms = int((time.time() - t0) * 1000)

    content = None
    finish = None
    err_msg = None
    if http == 200:
        try:
            d = json.loads(body)
            ch = d.get('choices', [{}])[0]
            finish = ch.get('finish_reason')
            msg = ch.get('message', {})
            content = msg.get('content')
            if not content and msg.get('reasoning'):
                content = '[reasoning-only]: ' + str(msg.get('reasoning'))[:100]
        except Exception:
            content = '[unparseable 200]'
    else:
        try:
            d = json.loads(body)
            err_msg = str(d.get('error', {}).get('message', d.get('error', '')))[:200]
        except Exception:
            err_msg = body[:200]

    # Verdict
    if http == 200 and content and 'FUZZ-LIVE' in str(content):
        verdict = 'LIVE'
    elif http == 200 and content:
        verdict = 'LIVE-WEAK'  # 200 with content but not our marker
    elif http == 200:
        verdict = 'EMPTY-200'
    elif http in (401, 403):
        verdict = 'AUTH-FAIL'
    elif http == 402:
        verdict = 'NO-CREDITS'
    elif http == 404:
        verdict = 'NOT-FOUND'
    elif http == 429:
        verdict = 'RATE-LIMIT'
    else:
        verdict = f'HTTP-{http}'

    return {
        'provider': provider,
        'model': model,
        'http': http,
        'finish': finish,
        'content_preview': str(content)[:120] if content else None,
        'error': err_msg,
        'latency_ms': latency_ms,
        'verdict': verdict,
    }

def main():
    provider = sys.argv[1]
    keyname = sys.argv[2]
    base_url = sys.argv[3]
    models = sys.argv[4:]
    key = get_key(keyname)
    if not key:
        print(json.dumps({'error': f'key {keyname} not found'}))
        sys.exit(1)
    for m in models:
        r = probe(provider, key, base_url, m)
        print(json.dumps(r), flush=True)

if __name__ == '__main__':
    main()
