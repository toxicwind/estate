#!/usr/bin/env python3
"""Push ~/workspace/skills to toxicwind/skills via the GitHub git-database API.

No git-protocol auth needed: blobs -> tree -> commit (parent = old main HEAD,
preserving the July catalog history) -> fast-forward ref update.
"""
import sys, json, base64, subprocess, urllib.request, time
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, '/opt/hatch/skills/skill-creator/bin')
from dynamic_credentials import add_surrogate_to_request, read_json_response

API = 'https://api.github.com'
REPO = 'toxicwind/skills'
ROOT = '/home/hatch/workspace/skills'
UA = 'toxicwind-archive-bot/1.0'

def api(method, path, payload=None, retries=3):
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
            return read_json_response(urllib.request.urlopen(req, timeout=120))
        except Exception as e:
            last = e
            time.sleep(2 * (i + 1))
    raise RuntimeError(f'{method} {path} failed: {last}')

def make_blob(item):
    mode, path = item
    with open(f'{ROOT}/{path}', 'rb') as f:
        content = base64.b64encode(f.read()).decode()
    r = api('POST', f'/repos/{REPO}/git/blobs',
            {'content': content, 'encoding': 'base64'})
    return (mode, path, r['sha'])

# staged files with modes from the index
out = subprocess.run(['git', 'ls-files', '-s'], cwd=ROOT, capture_output=True, text=True, check=True)
items = []
for line in out.stdout.splitlines():
    parts = line.split()
    items.append((parts[0], parts[3]))
print(f'{len(items)} files to upload as blobs', flush=True)

blobs = []
with ThreadPoolExecutor(max_workers=8) as ex:
    for i, res in enumerate(ex.map(make_blob, items)):
        blobs.append(res)
        if (i + 1) % 50 == 0:
            print(f'  {i+1}/{len(items)} blobs', flush=True)
print('all blobs created', flush=True)

tree = [{'path': p, 'mode': m, 'type': 'blob', 'sha': s} for (m, p, s) in blobs]
tr = api('POST', f'/repos/{REPO}/git/trees', {'tree': tree})
print('tree:', tr['sha'], flush=True)

ref = api('GET', f'/repos/{REPO}/git/refs/heads/main')
old_sha = ref['object']['sha']
print('old main:', old_sha, flush=True)

msg = ("skills: first-class repo — 58 workspace skills\n\n"
       "Replaces the July skill-catalog tree (preserved in history).\n"
       "- Shared portable venv layout, skill-setup harness, runner.sh convention\n"
       "- .env/.env.example contract: live keys local-only, examples redacted\n"
       "- Secrets sweep clean before commit (109 findings, all false positives)")
cm = api('POST', f'/repos/{REPO}/git/commits',
         {'message': msg, 'tree': tr['sha'], 'parents': [old_sha]})
print('commit:', cm['sha'], flush=True)

# ref move needs curl_cffi + explicit UA (bare urllib PATCH gets 403)
import curl_cffi.requests
sess = curl_cffi.requests.Session()
sess.headers['User-Agent'] = UA
# inject surrogate auth header the same way the helper does for api.github.com
class FakeReq:  # minimal shim to reuse add_surrogate_to_request
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
