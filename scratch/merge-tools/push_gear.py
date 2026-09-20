#!/usr/bin/env python3
"""Push ~/workspace/skills to toxicwind/gear via the GitHub git-database API.
Adapted from push_skills_api.py (REPO=toxicwind/gear). Builds the full tree
from the local git index, commits on top of remote main, fast-forwards the ref.
"""
import sys, json, base64, subprocess, time
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, '/opt/hatch/skills/skill-creator/bin')
from dynamic_credentials import add_surrogate_to_request, read_json_response

API = 'https://api.github.com'
REPO = 'toxicwind/gear'
ROOT = '/home/hatch/workspace/skills'
UA = 'toxicwind-archive-bot/1.0'

import urllib.request

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
        if (i + 1) % 200 == 0:
            print(f'  {i+1}/{len(items)} blobs', flush=True)
print('all blobs created', flush=True)

tree = [{'path': p, 'mode': m, 'type': 'blob', 'sha': s} for (m, p, s) in blobs]
tr = api('POST', f'/repos/{REPO}/git/trees', {'tree': tree})
print('tree:', tr['sha'], flush=True)

ref = api('GET', f'/repos/{REPO}/git/refs/heads/main')
old_sha = ref['object']['sha']
print('old main:', old_sha, flush=True)

msg = ("gear: consolidate all skill sources — 460 skills\n\n"
       "- Merged: July catalog (droidforge, sdk-auditor, stemforge, apx),\n"
       "  repo_kimi_team_recon (387 unique skills, content-deduped from 797 files),\n"
       "  moonbox-skills-deploy (5), nvidia-swarm-lens (3 browser variants),\n"
       "  agentic-sandbox-toolkit; kimi-widget/help-center upgraded to full-asset copies\n"
       "- Deduped: claude-forge 26, kimi-skills 2, crisis 4 (all content-dupes of recon set);\n"
       "  38 content-dupes skipped total\n"
       "- Added SKILL_INDEX.md (categorized + alphabetical)\n"
       "- Secrets sweep: 2 flags, both verified documentation examples (fake key patterns)")
cm = api('POST', f'/repos/{REPO}/git/commits',
         {'message': msg, 'tree': tr['sha'], 'parents': [old_sha]})
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
