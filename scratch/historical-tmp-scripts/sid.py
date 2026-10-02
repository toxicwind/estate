"""Extract NGC identity role/scope fields server-side. Key never printed."""
import re, json, urllib.request, urllib.error

sec = open("/home/toxic/.secrets").read()
KEY = re.search(r'^export NVIDIA_API_KEY=(.+)$', sec, re.M).group(1).strip().strip('"').strip("'")

def get(url):
    r = urllib.request.Request(url, headers={"Authorization": "Bearer " + KEY})
    try:
        return json.load(urllib.request.urlopen(r, timeout=30))
    except urllib.error.HTTPError as e:
        return {"http_error": e.code}

u = get("https://api.ngc.nvidia.com/v2/users/me")
user = u.get("user", u)
print("USER id/name/verified:", user.get("id"), user.get("name"), user.get("isVerified"))
for k, v in user.items():
    kl = k.lower()
    if any(w in kl for w in ("role", "scope", "permission", "entitle")):
        print("USER FIELD", k, "=", json.dumps(v)[:400])

o = get("https://api.ngc.nvidia.com/v2/orgs")
for g in o.get("organizations", []):
    print("ORG:", g.get("id"), g.get("displayName"), g.get("type"))
    for k, v in g.items():
        kl = k.lower()
        if any(w in kl for w in ("role", "scope", "permission", "entitle", "nvcf")):
            print("ORG FIELD", k, "=", json.dumps(v)[:500])
    print("productEnablements:", [(p.get("type"), p.get("productName")) for p in g.get("productEnablements", [])])
