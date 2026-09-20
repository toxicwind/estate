#!/usr/bin/env python3
"""nim_probes.py — live-probe the 6 WTF.md build priorities, paper-informed.

PAPERS VERDICT (2026-09-20, hunted before probing):
1. Async contract CONFIRMED as NVIDIA's general contract (NOT three.ws-specific):
   - nvidia/nvcf official docs v0.6.0 (updated 3 days ago):
     "Cloud Functions adds invocation headers such as nvcf-reqid and nvcf-status
      when a request is accepted by the invocation service."
     "Set the NVCF-POLL-SECONDS header to a longer value... to rule out client
      polling issues." / "504: No worker picked up the request within the polling
      timeout window."
   - POST /v2/nvcf/pexec/functions/{functionId} + GET /v2/nvcf/pexec/status/{requestId}
     (scope: invoke_function).
   - nvidia/garak NVCF generator docs: "NVCF functions work by sending a request
     to an invocation endpoint, and then polling a status endpoint until the
     response is received. The cloud function is described using a UUID."
   - backblaze-labs/genblaze (3 days ago): "Cosmos and Edify Video return async
     (202 Accepted + NVCF-REQID header) and the provider polls NVCF for
     completion. Some fast models return inline synchronous responses."
2. Three-endpoint split CONFIRMED (nirholas/three.ws docs/nvidia-models.md,
   genblaze README, litellm docs):
   - integrate.api.nvidia.com/v1 — OpenAI-compatible chat/embeddings (the liar: catalog
     lists models the key cannot invoke).
   - ai.api.nvidia.com/v1/genai/... — model-specific generation, async (202+poll) or sync.
   - api.nvcf.nvidia.com/v2/nvcf — Cloud Functions mgmt + pexec status.
   Honest entitlement surface = GET /v2/nvcf/functions (needs list_functions scope).
3. Function UUIDs CONFIRMED — functions addressed by UUID (garak target_name=UUID);
   versions via /versions; per-function deployment status via /deployments.
4. NVCF-AI-Resource: NO official spec found anywhere. Only prior art =
   lucky-mandator/gocode-router example.config.yaml (204 days old), which passes it
   as a GENERIC custom header to integrate.api.nvidia.com/v1 — the Go code has
   zero NVCF-specific header logic (WTF.md correction verified). Expectation: the
   header is ignored upstream. Probe is cheap; run it, expect no-op.
5. 401 AND 403 = auth CONFIRMED (official docs: "401 or 403: verify the
   Authorization header is set to a valid API key with invocation permissions").
   Already in nvcf_classifier.py; this script verifies live with a bad-key probe.

Usage on yote: python3 nim_probes.py [--only N]   (N = 1..6)
"""
import json
import os
import re
import subprocess
import sys
import time
import urllib.request
import urllib.error

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from nvcf_classifier import classify_nvcf_404, extract_uuid

SECRETS = '/home/toxic/.secrets'
INTEGRATE = 'https://integrate.api.nvidia.com/v1'
NVCF = 'https://api.nvcf.nvidia.com'

RESULTS = {}


def _key(name):
    """Read a key from .secrets. Never prints the value."""
    with open(SECRETS) as f:
        for line in f:
            line = line.strip()
            if line.startswith('export ' + name + '='):
                val = line.split('=', 1)[1]
                if len(val) >= 2 and val[0] == val[-1] and val[0] in '"\'':
                    val = val[1:-1]
                return val
    return None


def _req(url, key, method='GET', payload=None, headers=None, timeout=60):
    req = urllib.request.Request(url, method=method,
                                 data=json.dumps(payload).encode() if payload else None)
    if key: req.add_header('Authorization', 'Bearer ' + key)
    req.add_header('Content-Type', 'application/json')
    for k, v in (headers or {}).items():
        req.add_header(k, v)
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, dict(resp.headers), resp.read().decode('utf-8', errors='replace'), int((time.time() - t0) * 1000)
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), e.read().decode('utf-8', errors='replace'), int((time.time() - t0) * 1000)
    except Exception as e:
        return -1, {}, 'EXC: %s: %s' % (type(e).__name__, str(e)[:200]), int((time.time() - t0) * 1000)


def probe1_function_list(key):
    """#1: NVCF function-list = honest entitlement surface."""
    print('=== PROBE 1: NVCF /functions (entitlement ground truth) ===')
    http, hdrs, body, ms = _req(NVCF + '/v2/nvcf/functions', key)
    out = {'http': http, 'latency_ms': ms}
    if http == 200:
        try:
            data = json.loads(body)
            fns = data.get('functions', data if isinstance(data, list) else [])
            out['count'] = len(fns)
            out['functions'] = [
                {'id': f.get('id'), 'name': f.get('name'),
                 'status': f.get('status'), 'version': (f.get('versions') or [{}])[0].get('versionId') if f.get('versions') else None}
                for f in fns[:50]
            ]
            print('function count: %d' % len(fns))
            for f in out['functions'][:20]:
                print('  %s | %s | %s' % (f['id'], f['name'], f['status']))
        except Exception as e:
            out['parse_error'] = str(e)[:200]
            print('parse error: %s' % out['parse_error'])
    elif http in (401, 403):
        out['verdict'] = 'AUTH_OR_SCOPE'
        out['note'] = 'key lacks list_functions scope or is bad — cannot read entitlement surface'
        print('HTTP %d: key cannot list functions (scope/auth). body: %s' % (http, body[:200]))
    else:
        out['note'] = body[:300]
        print('HTTP %d: %s' % (http, body[:300]))
    RESULTS['probe1'] = out
    return out


def probe2_kimi_k3_async(key):
    """#2 HEADLINE: kimi-k3 with proper async handling. Dead, or alive-behind-async?"""
    print('=== PROBE 2: kimi-k3 async re-probe (HEADLINE) ===')
    payload = {
        'model': 'moonshotai/kimi-k3',
        'messages': [{'role': 'user', 'content': 'Reply with exactly: KIMI-K3-LIVE'}],
        'max_tokens': 20,
    }
    headers = {'NVCF-POLL-SECONDS': '30'}
    http, hdrs, body, ms = _req(INTEGRATE + '/chat/completions', key,
                                method='POST', payload=payload, headers=headers, timeout=45)
    out = {'http': http, 'latency_ms': ms}
    print('initial: HTTP %d in %dms' % (http, ms))
    # normalize header case
    lhdrs = {k.lower(): v for k, v in hdrs.items()}
    reqid = lhdrs.get('nvcf-reqid') or lhdrs.get('nvcf-request-id')

    if http == 200:
        out['verdict'] = 'ALIVE_INLINE'
        try:
            d = json.loads(body)
            out['content'] = d['choices'][0]['message']['content'][:120]
        except Exception:
            out['content'] = body[:120]
        print('VERDICT: ALIVE (inline 200). content: %s' % out['content'])
    elif http == 202 and reqid:
        out['reqid'] = reqid
        print('202 accepted, reqid=%s — polling status...' % reqid)
        status_url = NVCF + '/v2/nvcf/pexec/status/' + reqid
        for i in range(30):
            time.sleep(3)
            sht, sh, sb, sms = _req(status_url, key, timeout=20)
            print('  poll %d: HTTP %d (%dms)' % (i + 1, sht, sms))
            if sht == 200:
                out['verdict'] = 'ALIVE_BEHIND_ASYNC'
                out['polls'] = i + 1
                try:
                    d = json.loads(sb)
                    out['content'] = json.dumps(d)[:200]
                except Exception:
                    out['content'] = sb[:200]
                print('VERDICT: ALIVE-BEHIND-ASYNC after %d polls' % (i + 1))
                break
            elif sht not in (200, 202):
                out['verdict'] = 'POLL_FAILED_%d' % sht
                out['poll_body'] = sb[:200]
                print('VERDICT: poll failed HTTP %d: %s' % (sht, sb[:200]))
                break
        else:
            out['verdict'] = 'ASYNC_TIMEOUT_90S'
            print('VERDICT: still pending after 90s of polling — capacity starvation or dead worker pool')
    elif http == 504:
        out['verdict'] = 'NO_WORKER_504'
        print('VERDICT: 504 — no worker picked up the request in the 30s poll window (capacity, not death)')
    elif http == 404:
        c = classify_nvcf_404(http, body, model_id='moonshotai/kimi-k3')
        out['verdict'] = 'DEAD_' + c['classification']
        out['uuid'] = c['uuid']
        print('VERDICT: DEAD (%s), uuid=%s' % (c['classification'], c['uuid']))
    elif http in (401, 403):
        out['verdict'] = 'AUTH_FAILURE'
        print('VERDICT: AUTH failure HTTP %d' % http)
    else:
        out['verdict'] = 'UNKNOWN_%d' % http
        out['body'] = body[:300]
        print('VERDICT: unknown HTTP %d: %s' % (http, body[:300]))
    RESULTS['probe2'] = out
    return out


def probe3_resource_header(key):
    """#3: NVCF-AI-Resource header — expect no-op (no spec, no router code honors it)."""
    print('=== PROBE 3: NVCF-AI-Resource header test ===')
    payload = {
        'model': 'moonshotai/kimi-k2.5',
        'messages': [{'role': 'user', 'content': 'Reply with exactly: HDR-TEST'}],
        'max_tokens': 20,
    }
    h_with, _, b_with, ms_with = _req(INTEGRATE + '/chat/completions', key, method='POST',
                                      payload=payload, headers={'NVCF-AI-Resource': 'moonshotai/kimi-k2.5'}, timeout=45)
    h_without, _, b_without, ms_without = _req(INTEGRATE + '/chat/completions', key, method='POST',
                                               payload=payload, timeout=45)
    out = {'with_header': {'http': h_with, 'ms': ms_with, 'body_head': b_with[:200]},
           'without_header': {'http': h_without, 'ms': ms_without, 'body_head': b_without[:200]}}
    print('with header:    HTTP %d (%dms): %s' % (h_with, ms_with, b_with[:150]))
    print('without header: HTTP %d (%dms): %s' % (h_without, ms_without, b_without[:150]))
    if h_with == h_without and extract_uuid(b_with) == extract_uuid(b_without):
        out['verdict'] = 'NO_OP'
        print('VERDICT: header is a NO-OP (same status, same function UUID either way)')
    else:
        out['verdict'] = 'DIFFERS'
        print('VERDICT: header CHANGES behavior — investigate')
    RESULTS['probe3'] = out
    return out


def probe4_ghost_guard():
    """#4: ghost-ID guard — registry check before route insertion. Test all 3 UUIDs."""
    print('=== PROBE 4: ghost-ID guard ===')
    from nvcf_classifier import load_registry, guard_uuid
    reg = load_registry()
    print('registry entries: %d' % len(reg))
    blocked = 0
    for uuid, rec in reg.items():
        g = guard_uuid(uuid)
        print('  %s (%s): guard=%s reason=%s' % (uuid, rec.get('verdict'), g['blocked'], g['reason'][:80]))
        if g['blocked']:
            blocked += 1
    # negative control: a fresh UUID must NOT be blocked
    neg = guard_uuid('aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee')
    print('  fresh-uuid negative control: blocked=%s' % neg['blocked'])
    out = {'registry_size': len(reg), 'blocked': blocked,
           'negative_control_pass': not neg['blocked'],
           'verdict': 'PASS' if blocked == len(reg) and not neg['blocked'] else 'FAIL'}
    print('VERDICT: %s (%d/%d blocked, negative control %s)' % (
        out['verdict'], blocked, len(reg), 'pass' if out['negative_control_pass'] else 'FAIL'))
    RESULTS['probe4'] = out
    return out


def probe5_shell_ere():
    """#5: NemoClaw shell-ERE twin, borrowed verbatim. Verify vs canonical bodies."""
    print('=== PROBE 5: shell-ERE twin ===')
    from nvcf_classifier import (NVCF_FUNCTION_NOT_FOUND_SHELL_ERE, NVCF_404_JS_RE, classify_shell_ere,
                                 NVCF_FUNCTION_NOT_FOUND_MARKER)
    print('ERE: %s' % NVCF_FUNCTION_NOT_FOUND_SHELL_ERE)
    print('marker: %s' % NVCF_FUNCTION_NOT_FOUND_MARKER)
    from nvcf_classifier import load_registry
    reg = load_registry()
    ok = 0
    for uuid in reg:
        body = '{"status":404,"title":"Not Found","detail":"Function \'%s\': Not found for account \'test-acct-1\'}' % uuid
        r = classify_shell_ere(body)
        js = bool(re.search(NVCF_404_JS_RE, body, re.I))
        print('  %s: shell=%s js-twin=%s marker=%s' % (uuid[:8], r['match'], js, r['marker']))
        if r['match'] and js and r['marker'] == NVCF_FUNCTION_NOT_FOUND_MARKER:
            ok += 1
    # negative: a 200 body must not match
    neg = classify_shell_ere('{"choices":[{"message":{"content":"hi"}}]}')
    print('  200-body negative control: match=%s' % neg['match'])
    out = {'matched': ok, 'total': len(reg), 'negative_control_pass': not neg['match'],
           'verdict': 'PASS' if ok == len(reg) and not neg['match'] else 'FAIL'}
    print('VERDICT: %s' % out['verdict'])
    RESULTS['probe5'] = out
    return out


def probe6_bad_key():
    """#6: bad-key probe — 401/403 must both classify AUTH_FAILURE."""
    print('=== PROBE 6: bad-key 403/401 -> AUTH mapping ===')
    live_model = "nvidia/llama-3.1-nemotron-70b-instruct"  # live as of 2026-09-20
    payload = {"model": live_model,
               "messages": [{"role": "user", "content": "hi"}], "max_tokens": 5}
    h403, _, b403, _ = _req(INTEGRATE + "/chat/completions", "nvapi-DEADBEEF-bad-key",
                            method="POST", payload=payload, timeout=30)
    h401, _, b401, _ = _req(INTEGRATE + "/chat/completions", None,
                            method="POST", payload=payload, timeout=30)
    c403 = classify_nvcf_404(h403, b403)["classification"]
    c401 = classify_nvcf_404(h401, b401)["classification"]
    ok = (h403 == 403 and c403 == "AUTH_FAILURE" and h401 == 401 and c401 == "AUTH_FAILURE")
    out = {"bad_key_http": h403, "bad_key_maps": c403,
           "no_key_http": h401, "no_key_maps": c401,
           "verdict": "PASS" if ok else "FAIL"}
    print("bad-key -> HTTP %d (%s); no-key -> HTTP %d (%s). VERDICT: %s" % (
        h403, c403, h401, c401, out["verdict"]))
    RESULTS['probe6'] = out
    return out


def main():
    only = sys.argv[sys.argv.index('--only') + 1] if '--only' in sys.argv else None
    key = _key('NVIDIA_API_KEY')
    if not key:
        print('FATAL: NVIDIA_API_KEY not found in .secrets')
        sys.exit(2)
    print('key present: yes (NVIDIA_API_KEY, len=%d)' % len(key))
    run = {
        '1': lambda: probe1_function_list(key),
        '2': lambda: probe2_kimi_k3_async(key),
        '3': lambda: probe3_resource_header(key),
        '4': probe4_ghost_guard,
        '5': probe5_shell_ere,
        '6': probe6_bad_key,
    }
    for n, fn in run.items():
        if only and n != only:
            continue
        try:
            fn()
        except Exception as e:
            RESULTS['probe' + n] = {'verdict': 'EXCEPTION', 'error': '%s: %s' % (type(e).__name__, str(e)[:200])}
            print('PROBE %s EXCEPTION: %s' % (n, str(e)[:200]))
        print()
    print('==== SUMMARY ====')
    for k, v in RESULTS.items():
        print('%s: %s' % (k, v.get('verdict', v.get('http'))))
    with open('/tmp/nim_probes_results.json', 'w') as f:
        json.dump(RESULTS, f, indent=2)
    print('(full results: /tmp/nim_probes_results.json)')


if __name__ == '__main__':
    main()
