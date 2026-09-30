import json, time, urllib.request, urllib.error
ROUTER = 'http://127.0.0.1:25104/v1/chat/completions'
prompt = 'A bat and ball cost 1.10 total. The bat costs 1.00 more than the ball. How much does the ball cost? Think step by step.'
body = json.dumps({'model': 'nvidia/nvidia/nemotron-3-nano-omni-30b-a3b-reasoning', 'messages': [{'role':'user','content': prompt}],'max_tokens': 400, 'stream': False}).encode()
req = urllib.request.Request(ROUTER, data=body, headers={'Content-Type':'application/json','X-Sovereign-Strategy':'hybrid','X-Session-Id': 'omni%d' % (int(time.time())%100000)})
t = time.time()
try:
    r = urllib.request.urlopen(req, timeout=60)
    j = json.loads(r.read().decode())
    dt = time.time()-t
    msg = j['choices'][0]['message']
    print('STATUS', r.status, 'via=', r.headers.get('X-Routed-Via'), 'time=%.1fs' % dt)
    print('REASONING:', repr((msg.get('reasoning_content') or '')[:400]))
    print('CONTENT:', repr((msg.get('content') or '')[:400]))
except urllib.error.HTTPError as e:
    print('HTTP', e.code, '%.1fs' % (time.time()-t), e.read().decode()[:200])
except Exception as e:
    print('ERR', type(e).__name__, e)
