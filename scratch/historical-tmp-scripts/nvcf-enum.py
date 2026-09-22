#!/usr/bin/env python3
"""NVCF plane enumeration: find the kimi-k3 function, its versions, our entitlement.
Key read from /home/toxic/.secrets, NEVER printed."""
import json, urllib.request, urllib.error

key = None
with open('/home/toxic/.secrets') as f:
    for line in f:
        line = line.strip()
        if line.startswith('export '):
            line = line[7:].strip()
        if line.startswith('NVIDIA_API_KEY='):
            key = line.split('=', 1)[1].strip().strip('"').strip("'")
assert key, 'no NVIDIA_API_KEY'

BASE = 'https://api.nvcf.nvidia.com/v2/nvcf'

def get(path, timeout=60):
    h = {'Authorization': 'Bearer ' + key, 'Accept': 'application/json'}
    r = urllib.request.Request(BASE + path, headers=h, method='GET')
    try:
        with urllib.request.urlopen(r, timeout=timeout) as resp:
            return (resp.status, json.loads(resp.read().decode()))
    except urllib.error.HTTPError as e:
        return (e.code, {'_err': e.read().decode()[:300]})
    except Exception as e:
        return ('ERR', {'_err': repr(e)[:200]})

print('=== functions (our key entitlement list) ===', flush=True)
s, data = get('/functions')
print('status:', s, flush=True)
fns = data.get('functions', []) if isinstance(data, dict) else []
print('count:', len(fns), flush=True)
kimi = []
for f in fns:
    name = f.get('name', '')
    fid = f.get('id', '')
    if 'kimi' in name.lower() or 'k3' in name.lower():
        kimi.append(f)
        print('KIMI FN:', name, '| id:', fid, '| status:', f.get('status'),
              '| ownedByDifferentAccount:', f.get('ownedByDifferentAccount'), flush=True)
if not kimi:
    print('no kimi-named function; first 15 names:', flush=True)
    for f in fns[:15]:
        print('  -', f.get('name'), '|', f.get('id'), '|', f.get('status'), flush=True)

for f in kimi:
    fid = f['id']
    print('\n=== versions for', f.get('name'), '===', flush=True)
    s2, vers = get('/functions/%s/versions' % fid)
    print('status:', s2, flush=True)
    vs = vers.get('versions', []) if isinstance(vers, dict) else vers
    if isinstance(vs, list):
        for v in vs:
            print('  ver:', v.get('id') or v.get('versionId'),
                  '| name:', v.get('name'),
                  '| status:', v.get('status'), flush=True)
    else:
        print('  raw:', str(vers)[:400], flush=True)
print('DONE', flush=True)
