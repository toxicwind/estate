import json, time, urllib.request, urllib.error
ROUTER = 'http://127.0.0.1:25104/v1/chat/completions'
prompt = 'A bat and ball cost 1.10 total. The bat costs 1.00 more than the ball. How much does the ball cost? Think step by step, then give the final number.'
body = json.dumps({'model': 'nvidia/nvidia/nemotron-3-nano-omni-30b-a3b-reasoning', 'messages': [{'role':'user','content': prompt}],'max_tokens': 500, 'stream': False}).encode()
req = urllib.request.Request(ROUTER, data=body, headers={'Content-Type':'application/json','X-Sovereign-Strategy':'hybrid','X-Session-Id': 'omniq%d' % (int(time.time())%100000)})
t = time.time()
try:
    r = urllib.request.urlopen(req, timeout=90)
    j = json.loads(r.read().decode())
    msg = j['choices'][0]['message']
    print('STATUS', r.status, 'via=', r.headers.get('X-Routed-Via'), 'time=%.1fs' % (time.time()-t))
    print('REASONING_LEN', len(msg.get('reasoning_content') or ''))
    print('REASONING_HEAD:', repr((msg.get('reasoning_content') or '')[:300]))
    print('CONTENT_TAIL:', repr((msg.get('content') or '')[-200:]))
    print('USAGE:', j.get('usage'))
except urllib.error.HTTPError as e:
    print('HTTP', e.code, e.read().decode()[:200])
