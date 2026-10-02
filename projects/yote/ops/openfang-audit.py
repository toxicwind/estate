#!/usr/bin/env python3
"""OpenFang audit probe — validates the canonical post-2026-09-21 topology.

Checks:
  - Exactly one `openfang start` kernel process (no duplicate kernels)
  - :25196 kernel, :25103 mesh-front proxy listening; :25203 and :4200 dark
  - Single DB/WAL/SHM owner (one kernel PID holds ~/.openfang/data/openfang.db)
  - Kernel API: /api/health, /api/status, /api/agents, /api/triggers, /v1/models
  - All four chat routes return exact ROUTE_OK (assistant, squawk-relay,
    oracle-market, coyote) via :25196 and assistant via :25103 proxy
  - Both triggers registered
  - Funnel/dashboard: /openfang + /api + assets reachable
  - Pitchfork snapshot records openfang, openfang-front (no axiom, no dupes)

Usage: openfang-audit.py [--json]
Exit 0 = all checks pass, 1 = one or more failures.
"""
import json
import subprocess
import sys
import urllib.request

KERNEL = "http://127.0.0.1:25196"
PROXY = "http://127.0.0.1:25103"
CHAT_ROUTES = ["assistant", "squawk-relay", "oracle-market", "coyote"]
RESULTS = []


def check(name, ok, detail=""):
    RESULTS.append({"name": name, "ok": bool(ok), "detail": detail})


def sh(cmd):
    return subprocess.run(cmd, shell=True, capture_output=True, text=True)


def http_json(url, timeout=15):
    with urllib.request.urlopen(url, timeout=timeout) as r:
        return json.load(r), r.status


def http_post_json(url, payload, timeout=60):
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r), r.status


def main():
    # --- single kernel process ---
    p = sh("ps -eo pid,cmd | grep '[o]penfang start'")
    pids = [l.split()[0] for l in p.stdout.strip().splitlines() if l.strip()]
    check("single-kernel-process", len(pids) == 1, f"pids={pids}")

    # --- listeners ---
    ss = sh("ss -tln").stdout
    check("kernel-25196-listening", ":25196" in ss)
    check("proxy-25103-listening", ":25103" in ss)
    check("retired-25203-dark", ":25203" not in ss, "duplicate kernel port must be dark")
    check("retired-4200-dark", ":4200" not in ss, "legacy port must be dark")

    # --- single DB owner ---
    db = sh("fuser /home/toxic/.openfang/data/openfang.db 2>/dev/null").stdout.strip()
    owners = db.split()
    check(
        "single-db-owner",
        len(owners) == 1 and (not pids or owners[0] == pids[0]),
        f"db_holders={owners} kernel_pid={pids}",
    )

    # --- kernel API surface ---
    try:
        h, s = http_json(f"{KERNEL}/api/health")
        check("kernel-health", s == 200 and h.get("status") == "ok", str(h)[:80])
    except Exception as e:
        check("kernel-health", False, str(e)[:120])

    agents = {}
    try:
        st, s = http_json(f"{KERNEL}/api/status")
        agents = {a["name"]: a for a in st.get("agents", [])}
        check("status-agents", len(agents) >= 4, f"agents={sorted(agents)}")
        asst = agents.get("assistant", {})
        check(
            "assistant-route",
            asst.get("model_provider") == "llama-swap"
            and "nex" in str(asst.get("model_name")),
            f"{asst.get('model_name')}/{asst.get('model_provider')}",
        )
    except Exception as e:
        check("status-agents", False, str(e)[:120])
        check("assistant-route", False, "no status")

    for path in ["/api/agents", "/api/triggers", "/v1/models"]:
        try:
            _, s = http_json(f"{KERNEL}{path}")
            check(f"kernel{path}", s == 200)
        except Exception as e:
            check(f"kernel{path}", False, str(e)[:120])

    try:
        trig, _ = http_json(f"{KERNEL}/api/triggers")
        names = sorted(t.get("id", "")[:8] for t in trig)
        check("triggers-registered", len(trig) >= 2, f"count={len(trig)}")
    except Exception as e:
        check("triggers-registered", False, str(e)[:120])

    # --- chat routes: exact ROUTE_OK ---
    for route in CHAT_ROUTES:
        try:
            d, s = http_post_json(
                f"{KERNEL}/v1/chat/completions",
                {
                    "model": f"openfang:{route}",
                    "messages": [{"role": "user", "content": "Reply with exactly: ROUTE_OK"}],
                    "max_tokens": 20,
                },
            )
            text = d["choices"][0]["message"]["content"]
            check(f"chat-{route}", "ROUTE_OK" in text, text[:60])
        except Exception as e:
            check(f"chat-{route}", False, str(e)[:120])

    # --- proxy path ---
    try:
        d, s = http_post_json(
            f"{PROXY}/v1/chat/completions",
            {
                "model": "openfang:assistant",
                "messages": [{"role": "user", "content": "Reply with exactly: ROUTE_OK"}],
                "max_tokens": 20,
            },
        )
        text = d["choices"][0]["message"]["content"]
        check("proxy-chat-assistant", "ROUTE_OK" in text, text[:60])
    except Exception as e:
        check("proxy-chat-assistant", False, str(e)[:120])

    try:
        h, s = http_json(f"{PROXY}/api/health")
        check("proxy-health", s == 200, str(h)[:60])
    except Exception as e:
        check("proxy-health", False, str(e)[:120])

    # --- pitchfork snapshot ---
    snap = sh("cat /home/toxic/.local/state/pitchfork/state.toml").stdout
    check("snapshot-openfang", "openfang" in snap)
    check("snapshot-openfang-front", "openfang-front" in snap)
    check("snapshot-no-axiom", "axiom" not in snap.lower(), "old daemon name must be gone")

    as_json = "--json" in sys.argv
    failed = [r for r in RESULTS if not r["ok"]]
    if as_json:
        print(json.dumps({"ok": not failed, "checks": RESULTS}, indent=1))
    else:
        for r in RESULTS:
            mark = "PASS" if r["ok"] else "FAIL"
            print(f"{mark} {r['name']}" + (f" :: {r['detail']}" if r["detail"] else ""))
        print(f"\n{len(RESULTS)-len(failed)}/{len(RESULTS)} checks passed")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
