"""Minimal GitHub API client for the herd CI-health task.

Auth via the skill-creator dynamic credential surrogate (custom.github).
GET/POST/PATCH via urllib; ref mutations (create/update/delete) via
curl_cffi with an explicit User-Agent (bare-urllib PATCH/POST on git refs
fails with RemoteDisconnected / 403 admin-rules per AGENTS.md lesson).
Never prints or persists raw credentials.
"""
import json
import sys
import urllib.request
import urllib.error

sys.path.insert(0, "/opt/hatch/skills/skill-creator/bin")
from dynamic_credentials import (
    add_surrogate_to_request,
    read_response_body,
    dynamic_credential_entry,
)

API = "https://api.github.com"
UA = "toxicwind-archive-bot/1.0"
REPO = "toxicwind/herd"


def _req(method, path, body=None):
    url = API + path
    data = None
    headers = {"User-Agent": UA, "Accept": "application/vnd.github+json"}
    if body is not None:
        data = json.dumps(body).encode()
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    add_surrogate_to_request(req, "custom.github", allowed_hosts=["api.github.com"])
    try:
        resp = urllib.request.urlopen(req, timeout=60)
    except urllib.error.HTTPError as e:
        detail = read_response_body(e).decode("utf-8", errors="replace")
        raise RuntimeError(f"{method} {path} -> HTTP {e.code}: {detail[:600]}")
    raw = read_response_body(resp)
    if not raw:
        return None
    return json.loads(raw.decode("utf-8"))


def get(path, params=None):
    url = API + path
    if params:
        url += "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(
        url, headers={"User-Agent": UA, "Accept": "application/vnd.github+json"}, method="GET"
    )
    add_surrogate_to_request(req, "custom.github", allowed_hosts=["api.github.com"])
    try:
        resp = urllib.request.urlopen(req, timeout=60)
    except urllib.error.HTTPError as e:
        detail = read_response_body(e).decode("utf-8", errors="replace")
        raise RuntimeError(f"GET {path} -> HTTP {e.code}: {detail[:600]}")
    return json.loads(read_response_body(resp).decode("utf-8"))


def _curl(method, path, body):
    """Ref mutations through curl_cffi with explicit User-Agent."""
    from curl_cffi import requests as creq

    entry = dynamic_credential_entry("custom.github")
    surrogate = str(entry["surrogate"]).strip()
    r = creq.request(
        method,
        API + path,
        headers={
            "User-Agent": UA,
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {surrogate}",
            "Content-Type": "application/json",
        },
        data=json.dumps(body),
        timeout=60,
    )
    if r.status_code >= 300:
        raise RuntimeError(f"{method} {path} -> HTTP {r.status_code}: {r.text[:600]}")
    return r.json() if r.text.strip() else None


def create_ref(ref, sha):
    return _curl("POST", f"/repos/{REPO}/git/refs", {"ref": ref, "sha": sha})


def update_ref(ref, sha, force=False):
    # ref like "heads/ci/workflow-health-monitor"
    return _curl("PATCH", f"/repos/{REPO}/git/refs/{ref}", {"sha": sha, "force": force})


def create_blob(content):
    return _req("POST", f"/repos/{REPO}/git/blobs", {"content": content, "encoding": "utf-8"})


def create_tree(base_tree, entries):
    return _req("POST", f"/repos/{REPO}/git/trees", {"base_tree": base_tree, "tree": entries})


def create_commit(message, tree_sha, parents):
    return _req(
        "POST",
        f"/repos/{REPO}/git/commits",
        {"message": message, "tree": tree_sha, "parents": parents},
    )
