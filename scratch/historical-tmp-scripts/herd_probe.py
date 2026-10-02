import json, urllib.request, time
body = json.dumps({"model": "oracle-judge-a",
                   "messages": [{"role": "user", "content": "Reply with exactly: {\"posterior\": 0.5}"}],
                   "temperature": 0.2, "max_tokens": 60}).encode()
req = urllib.request.Request('http://127.0.0.1:25100/v1/chat/completions',
                             data=body,
                             headers={'Content-Type': 'application/json'},
                             method='POST')
t0 = time.time()
try:
    with urllib.request.urlopen(req, timeout=60) as r:
        print('STATUS', r.status)
        print('HEADERS', dict(r.headers))
        data = json.load(r)
    print('KEYS', list(data.keys()))
    print('MODEL', repr(data.get('model')))
    print('CHOICES0', json.dumps(data['choices'][0])[:300])
    print('USAGE', data.get('usage'))
except Exception as e:
    print('ERR', type(e).__name__, e, 'code=', getattr(e, 'code', None))
    try:
        print('ERRBODY', e.read()[:300])
    except Exception:
        pass
print('LAT', round(time.time() - t0, 2))
