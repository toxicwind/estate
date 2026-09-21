#!/usr/bin/env python3
"""nvcf-access-probe.py — read-only enumeration of NVIDIA API surfaces for our
build.nvidia.com key (NVCF-DIG, 2026-09-21).

Reads NVIDIA_API_KEY from /home/toxic/.secrets (or env). The key is NEVER
printed, logged, or written to any report. Email addresses are redacted from
the saved JSON report.

Surfaces covered:
  integrate.api.nvidia.com  OpenAI-compatible front door (/v1/models, /v1/chat/completions)
  api.nvcf.nvidia.com       NVCF control plane (functions list, assets, per-function authz)
  ai.api.nvidia.com         genai async gateway
  api.ngc.nvidia.com        NGC identity / org / registry catalog

Usage:
  python3 bin/nvcf-access-probe.py [--report /tmp/nvcf-access.json]
                                   [--inference-models a/b,c/d]  # 1-token entitlement probes
                                   [--no-inference]
"""
import argparse, json, os, re, sys, time, urllib.request, urllib.error

SECRETS_PATH = os.environ.get("NIM_KIMI_SECRETS", "/home/toxic/.secrets")
EMAIL_RE = re.compile(r'"[\w.+-]+@[\w-]+\.[\w.]+"')

def load_key():
    v = os.environ.get("NVIDIA_API_KEY")
    if v:
        return v
    try:
        with open(SECRETS_PATH) as f:
            for line in f:
                line = line.strip()
                if line.startswith("export "):
                    line = line[7:].strip()
                if line.startswith("NVIDIA_API_KEY="):
                    return line.split("=", 1)[1].strip().strip('"').strip("'")
    except Exception as e:
        print("secrets read failed: %s" % type(e).__name__, file=sys.stderr)
    return None

KEY = load_key()
if not KEY:
    print("FATAL: no NVIDIA_API_KEY", file=sys.stderr)
    sys.exit(1)

def call(method, url, auth=True, extra_headers=None, body=None, timeout=25,
         max_body=2000000):
    headers = {"User-Agent": "nvcf-access-probe/1.0", "Accept": "application/json"}
    if auth:
        headers["Authorization"] = "Bearer " + KEY
    if extra_headers:
        headers.update(extra_headers)
    if body is not None:
        headers["Content-Type"] = "application/json"
    t0 = time.time()
    rec = {"method": method, "url": url,
           "auth": "bearer" if auth else ("custom" if extra_headers else "none")}
    try:
        req = urllib.request.Request(url, data=body, headers=headers, method=method)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            rec["status"] = resp.status
            rec["body"] = resp.read(max_body).decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        try:
            rec["body"] = e.read(20000).decode("utf-8", "replace")
        except Exception:
            rec["body"] = ""
        rec["status"] = e.code
    except Exception as e:
        rec["status"] = "ERR"
        rec["body"] = type(e).__name__
    rec["ms"] = int((time.time() - t0) * 1000)
    return rec

PROBES = [
    # (name, method, url, auth, extra_headers)
    ("int-models", "GET", "https://integrate.api.nvidia.com/v1/models", True, None),
    ("int-models-noauth", "GET", "https://integrate.api.nvidia.com/v1/models", False, None),
    ("int-model-detail", "GET", "https://integrate.api.nvidia.com/v1/models/moonshotai/kimi-k3", True, None),
    ("int-usage", "GET", "https://integrate.api.nvidia.com/v1/usage", True, None),
    ("int-billing", "GET", "https://integrate.api.nvidia.com/v1/billing", True, None),
    ("nvcf-functions", "GET", "https://api.nvcf.nvidia.com/v2/nvcf/functions", True, None),
    ("nvcf-functions-noauth", "GET", "https://api.nvcf.nvidia.com/v2/nvcf/functions", False, None),
    ("nvcf-assets", "GET", "https://api.nvcf.nvidia.com/v2/nvcf/assets", True, None),
    ("nvcf-authz-bare", "GET", "https://api.nvcf.nvidia.com/v2/nvcf/authorizations", True, None),
    ("nvcf-deployments", "GET", "https://api.nvcf.nvidia.com/v2/nvcf/deployments", True, None),
    ("genai-root", "GET", "https://ai.api.nvidia.com/v1/genai", True, None),
    ("genai-kimi3", "GET", "https://ai.api.nvidia.com/v1/genai/moonshotai/kimi-k3", True, None),
    ("ngc-users-me", "GET", "https://api.ngc.nvidia.com/v2/users/me", True, None),
    ("ngc-orgs", "GET", "https://api.ngc.nvidia.com/v2/orgs", True, None),
    ("ngc-org-noauth", "GET", "https://api.ngc.nvidia.com/v2/org", False, None),
    ("ngc-models", "GET", "https://api.ngc.nvidia.com/v2/models", True, None),
]

def summarize(results):
    """Enrich a few key probes with parsed verdicts (no key material)."""
    by_name = {r["name"]: r for r in results}
    r = by_name.get("nvcf-functions")
    if r and r["status"] == 200:
        try:
            fns = json.loads(r["body"])["functions"]
            owned = sum(1 for f in fns if f.get("ownedByDifferentAccount"))
            st = {}
            for f in fns:
                st[f.get("status")] = st.get(f.get("status"), 0) + 1
            r["verdict"] = {"total": len(fns), "ownedByDifferentAccount": owned,
                            "statuses": st}
        except Exception:
            r["verdict"] = {"parse": "failed (body truncated?)"}
    r = by_name.get("int-models")
    if r and r["status"] == 200:
        try:
            ms = json.loads(r["body"])["data"]
            r["verdict"] = {"count": len(ms), "ids": [m["id"] for m in ms]}
        except Exception:
            r["verdict"] = {"parse": "failed"}
    r = by_name.get("ngc-users-me")
    if r and r["status"] == 200:
        try:
            u = json.loads(EMAIL_RE.sub('"[redacted]"', r["body"]))["user"]
            roles = u.get("roles", [])
            r["verdict"] = {"name": u.get("name"), "id": u.get("id"),
                            "verified": u.get("verified"),
                            "orgRoles": [x.get("orgRoles") for x in roles]}
        except Exception:
            r["verdict"] = {"parse": "failed"}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--report", default="/tmp/nvcf-access.json")
    ap.add_argument("--inference-models", default="moonshotai/kimi-k2.6,nvidia/llama-3.1-nemotron-70b-instruct",
                    help="comma-separated model ids for 1-token entitlement probes")
    ap.add_argument("--no-inference", action="store_true")
    a = ap.parse_args()

    results = []
    for name, method, url, auth, xh in PROBES:
        rec = call(method, url, auth=auth, extra_headers=xh)
        rec["name"] = name
        results.append(rec)
        print("%-22s %s %s -> %s (%dms)" % (name, method, url, rec["status"], rec["ms"]),
              flush=True)

    # per-function detail + authz for the first kimi-tagged function (read-only)
    by_name = {r["name"]: r for r in results}
    fr = by_name.get("nvcf-functions")
    if fr and fr["status"] == 200:
        try:
            fns = json.loads(fr["body"])["functions"]
            kimi = [f for f in fns
                    if "kimi" in json.dumps(f.get("tags") or []).lower()
                    or "kimi" in (f.get("name") or "").lower()]
            if kimi:
                fid = kimi[0]["id"]
                d = call("GET", "https://api.nvcf.nvidia.com/v2/nvcf/functions/" + fid)
                d["name"] = "nvcf-function-detail"
                results.append(d)
                print("%-22s GET %s -> %s (%dms)" %
                      (d["name"], d["url"], d["status"], d["ms"]), flush=True)
                z = call("GET", "https://api.nvcf.nvidia.com/v2/nvcf/authorizations/functions/" + fid)
                z["name"] = "nvcf-function-authz"
                results.append(z)
                print("%-22s GET %s -> %s (%dms)" %
                      (z["name"], z["url"], z["status"], z["ms"]), flush=True)
        except Exception as e:
            print("function deep-dive skipped: %s" % type(e).__name__)

    if not a.no_inference:
        for model in [m.strip() for m in a.inference_models.split(",") if m.strip()]:
            payload = json.dumps({"model": model, "messages": [{"role": "user",
                "content": "hi"}], "max_tokens": 1}).encode()
            rec = call("POST", "https://integrate.api.nvidia.com/v1/chat/completions",
                       body=payload, timeout=60)
            rec["name"] = "infer:" + model
            results.append(rec)
            print("%-22s POST chat/completions -> %s (%dms) body=%.120s" %
                  (rec["name"], rec["status"], rec["ms"], rec["body"]), flush=True)

    summarize(results)
    redacted = EMAIL_RE.sub('"[redacted]"', json.dumps(results))
    with open(a.report, "w") as f:
        f.write(redacted)
    print("report: %s (%d probes)" % (a.report, len(results)))

if __name__ == "__main__":
    main()
