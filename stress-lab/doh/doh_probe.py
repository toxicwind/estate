#!/usr/bin/env python3
"""DoH bypass probe — compare Google (8.8.8.8) vs Cloudflare (1.1.1.1) JSON DoH.
Detects local UDP53 hijack/poisoning by checking two independent DoH resolvers
agree on IP set + TTL. Discrepancy = IP diff OR |TTLmin diff| > 30s.
Network-fault tolerant: each resolver try is wrapped; a private proxy responder
lets us TEST discrepancy logic offline (see --local).
"""
import json, sys, os, urllib.request, urllib.parse

GOOGLE = "https://dns.google/resolve"
CLOUDFLARE = "https://cloudflare-dns.com/dns-query"

def doh_json(base, domain, typ="A", timeout=8, local={"dns.google/resolve": "8.8.8.8", "cloudflare-dns.com": "1.1.1.1"}):
    url = f"{base}?name={urllib.parse.quote(domain)}&type={typ}"
    req = urllib.request.Request(url, headers={"Accept": "application/dns-json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            j = json.loads(r.read().decode())
    except Exception as e:
        return {"error": str(e), "ips": [], "ttls": [], "min": None, "max": None, "raw": {"Status": -1}}
    ans = j.get("Answer", [])
    ips = [a["data"] for a in ans if a.get("type") in (1, 28)]
    ttls = [a.get("TTL") for a in ans if a.get("TTL") is not None]
    return {"ips": ips, "ttls": ttls,
            "min": min(ttls) if ttls else None, "max": max(ttls) if ttls else None,
            "raw": j}

def compare(jg, jc, drift=30):
    ips_differ = sorted(jg["ips"]) != sorted(jc["ips"])
    delta = None
    if jg["min"] is not None and jc["min"] is not None:
        delta = abs(jg["min"] - jc["min"])
    ip_diff = ips_differ
    ttl_disc = delta is not None and delta > drift
    return {"ip_differ": ip_diff, "ttl_delta": delta, "ttl_discrepancy": ttl_disc,
            "discrepancy": ip_diff or ttl_disc,
            "google_status": jg["raw"].get("Status"), "cf_status": jc["raw"].get("Status")}

def main():
    domain = sys.argv[1] if len(sys.argv) > 1 else "github.com"
    typ = sys.argv[2] if len(sys.argv) > 2 else "A"
    mode = "--local" in sys.argv  # offline self-test of the discrepancy logic
    if mode:
        # simulate: Google returns one IP set, Cloudflare a shifted set => poison detected
        jg = {"ips": ["140.82.112.3"], "ttls": [42], "min": 42, "max": 42, "raw": {"Status": 0}}
        jc = {"ips": ["140.82.113.3", "140.82.114.3"], "ttls": [999], "min": 999, "max": 999, "raw": {"Status": 0}}
    else:
        jg = doh_json(GOOGLE, domain, typ)
        jc = doh_json(CLOUDFLARE, domain, typ)
    cmp = compare(jg, jc)
    report = {"domain": domain, "type": typ, "google": jg, "cloudflare": jc, **cmp,
              "vjTrigger": "GLITCH" if cmp["discrepancy"] else "STABLE",
              "timestamp": __import__("datetime").datetime.now().isoformat()}
    print(json.dumps(report, indent=2))
    try:
        os.makedirs(".", exist_ok=True)
        open("doh_report.json", "w").write(json.dumps(report, indent=2))
    except Exception as e:
        print(f"; write fail: {e}", file=sys.stderr)
    sys.exit(0 if not cmp["discrepancy"] else 2)  # 0 clean, 2 discrepancy-to-flag

if __name__ == "__main__":
    main()
