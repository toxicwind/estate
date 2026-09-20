#!/usr/bin/env python3
"""Incremental push to toxicwind/gear via git-database API.
Uploads only blobs whose SHA is missing from the remote tree, then creates
the full tree, commits on remote main, and fast-forwards the ref."""
import sys, json, time, base64, subprocess
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, '/opt/hatch/skills/skill-creator/bin')
from dynamic_credentials import add_surrogate_to_request, read_json_response

API = 'https://api.github.com'
REPO = 'toxicwind/gear'
ROOT = '/home/hatch/workspace/skills'
UA = 'toxicwind-archive-bot/1.0'
MESSAGE = sys.argv[1] if len(sys.argv) > 1 else 'gear: update'

import urllib.request

def api(method, path, payload=None, retries=8):
    data = json.dumps(payload).encode() if payload is not None else None
    last = None
    for i in range(retries):
        req = urllib.request.Request(API + path, data=data, method=method)
        req.add_header('Accept', 'application/vnd.github+json')
        req.add_header('User-Agent', UA)
        if data:
            req.add_header('Content-Type', 'application/json')
        add_surrogate_to_request(req, 'custom.github', allowed_hosts=['api.github.com'])
        try:
            return read_json_response(urllib.request.urlopen(req, timeout=180))
        except Exception as e:
            last = e
            print(f'  retry {i+1}: {str(e)[:80]}', flush=True)
            time.sleep(5 * (i + 1))
    raise RuntimeError(f'{method} {path} failed: {last}')

ref = api('GET', f'/repos/{REPO}/git/refs/heads/main')
old_sha = ref['object']['sha']
print('old main:', old_sha, flush=True)
cm0 = api('GET', f'/repos/{REPO}/git/commits/{old_sha}')
old_tree = cm0['tree']['sha']
tr0 = api('GET', f'/repos/{REPO}/git/trees/{old_tree}?recursive=1')
remote_blobs = {t['sha'] for t in tr0['tree'] if t['type'] == 'blob'}
print(f'{len(remote_blobs)} blobs in remote tree', flush=True)

out = subprocess.run(['git', 'ls-files', '-s'], cwd=ROOT, capture_output=True, text=True, check=True)
entries = []
missing = {}
for line in out.stdout.splitlines():
    parts = line.split()
    mode, sha, path = parts[0], parts[1], parts[3]
    entries.append((mode, sha, path))
    if sha not in remote_blobs:
        missing[sha] = path
print(f'{len(entries)} total entries, {len(missing)} blobs to upload', flush=True)

def make_blob(item):
    sha, path = item
    with open(f'{ROOT}/{path}', 'rb') as f:
        content = base64.b64encode(f.read()).decode()
    r = api('POST', f'/repos/{REPO}/git/blobs', {'content': content, 'encoding': 'base64'})
    assert r['sha'] == sha, f'sha mismatch {path}'
    return sha

if missing:
    with ThreadPoolExecutor(max_workers=8) as ex:
        list(ex.map(make_blob, missing.items()))
    print('new blobs uploaded', flush=True)

tree = [{'path': p, 'mode': m, 'type': 'blob', 'sha': s} for (m, s, p) in entries]
tr = api('POST', f'/repos/{REPO}/git/trees', {'tree': tree})
print('tree:', tr['sha'], flush=True)
cm = api('POST', f'/repos/{REPO}/git/commits',
         {'message': MESSAGE, 'tree': tr['sha'], 'parents': [old_sha]})
print('commit:', cm['sha'], flush=True)

import curl_cffi.requests
sess = curl_cffi.requests.Session()
sess.headers['User-Agent'] = UA
class FakeReq:
    def __init__(self): self.headers = {}
    def add_header(self, k, v): self.headers[k] = v
    def add_unredirected_header(self, k, v): self.headers[k] = v
    @property
    def full_url(self): return API + f'/repos/{REPO}/git/refs/heads/main'
fr = FakeReq()
add_surrogate_to_request(fr, 'custom.github', allowed_hosts=['api.github.com'])
sess.headers.update(fr.headers)
r = sess.patch(API + f'/repos/{REPO}/git/refs/heads/main',
               json={'sha': cm['sha'], 'force': False}, timeout=60)
print('ref PATCH:', r.status_code, flush=True)
r.raise_for_status()
print('PUSHED', cm['sha'])
