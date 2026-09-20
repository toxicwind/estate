import sys, json, urllib.request, urllib.error
sys.path.insert(0, "/opt/hatch/skills/skill-creator/bin")
from dynamic_credentials import add_surrogate_to_request, read_response_body
ALLOWED_HOSTS = ["api.github.com"]
CRED = "custom.github"
def gh(method, path, body=None):
    req = urllib.request.Request("https://api.github.com"+path,
        data=json.dumps(body).encode() if body is not None else None, method=method)
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("User-Agent", "toxicwind-archive-bot/1.0")
    req.add_header("X-GitHub-Api-Version", "2022-11-28")
    add_surrogate_to_request(req, CRED, allowed_hosts=ALLOWED_HOSTS)
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            raw = read_response_body(resp)
            return resp.status, json.loads(raw.decode()) if raw else None
    except urllib.error.HTTPError as e:
        return e.code, None
