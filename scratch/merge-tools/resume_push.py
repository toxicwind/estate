#!/usr/bin/env python3
"""Resume the gear push: all 1292 blobs already exist on GitHub (content-
addressed, so local git index SHAs == remote blob SHAs). Rebuild the tree
from `git ls-files -s`, commit on remote main, move the ref."""
import sys, json, time, subprocess

sys.path.insert(0, '/opt/hatch/skills/skill-creator/bin')
from dynamic_credentials import add_surrogate_to_request, read_json_response

API = 'https://api.github.com'
REPO = 'toxicwind/gear'
ROOT = '/home/hatch/workspace/skills'
UA = 'toxicwind-archive-bot/1.0'

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

out = subprocess.run(['git', 'ls-files', '-s'], cwd=ROOT, capture_output=True, text=True, check=True)
tree = []
for line in out.stdout.splitlines():
    parts = line.split()
    tree.append({'path': parts[3], 'mode': parts[0], 'type': 'blob', 'sha': parts[1]})
print(f'{len(tree)} tree entries', flush=True)

tr = api('POST', f'/repos/{REPO}/git/trees', {'tree': tree})
print('tree:', tr['sha'], flush=True)

ref = api('GET', f'/repos/{REPO}/git/refs/heads/main')
old_sha = ref['object']['sha']
print('old main:', old_sha, flush=True)

msg = ("gear: consolidate all skill sources — 465 skills\n\n"
       "- Merged: July catalog (droidforge, sdk-auditor, stemforge, apx),\n"
       "  repo_kimi_team_recon (387 unique skills, content-deduped from 797 files),\n"
       "  moonbox-skills-deploy (5), nvidia-swarm-lens (3 browser variants),\n"
       "  agentic-sandbox-toolkit; kimi-widget/help-center upgraded to full-asset copies\n"
       "- Deduped: claude-forge 26, kimi-skills 2, crisis 4 (all content-dupes of recon set);\n"
       "  38 content-dupes skipped total\n"
       "- Adapted sovereign-skills lenses into 5 skills (lens-tectonic, lens-cryptographic, lens-osint, lens-stylometric, lens-orchestrator)\n"
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
