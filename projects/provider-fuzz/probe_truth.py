#!/usr/bin/env python3
"""
probe_truth.py — Probe-before-build library.

Advertised capability ≠ actual availability. The catalog is marketing.
The runtime is truth. PROBE BEFORE YOU BUILD.

Usage:
    from probe_truth import probe
    result = probe('nim', 'moonshotai/kimi-k2.6')
    # → {'verdict': 'LYING', 'http': 404, 'latency_ms': 109,
    #    'classification': 'GLOBALLY_DEAD', 'evidence': {...}}

For NIM: 1-token chat/completions probe + UUID extraction via nvcf_classifier.
For OpenRouter: check endpoint list first (zero endpoints = short-circuit DEAD), then probe.
"""
import json
import os
import sys
import time
import urllib.request
import urllib.error

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from nvcf_classifier import classify_nvcf_404
from reframer import reframe


def _get_key(keyname):
    """Read key from /home/toxic/.secrets without printing."""
    with open('/home/toxic/.secrets') as f:
        for line in f:
            line = line.strip()
            if line.startswith(f'export {keyname}='):
                val = line.split('=', 1)[1]
                if len(val) >= 2 and val[0] == val[-1] and val[0] in '"\'':
                    val = val[1:-1]
                return val
    return None


# Provider configs: (base_url, keyname)
PROVIDERS = {
    'nim': ('https://integrate.api.nvidia.com/v1', 'NVIDIA_API_KEY'),
    'openrouter': ('https://openrouter.ai/api/v1', 'OPENROUTER_API_KEY_1'),
    'moonshot': ('https://api.moonshot.ai/v1', 'MOONSHOT_API_KEY'),
    'mistral': ('https://api.mistral.ai/v1', 'MISTRAL_API_KEY'),
    'pollinations': ('https://gen.pollinations.ai/v1', None),  # anonymous
}


def _raw_probe(base_url, key, model, max_tokens=100, timeout=60):
    """Raw HTTP probe. Returns (http_code, body, latency_ms)."""
    url = base_url.rstrip('/') + '/chat/completions'
    payload = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": "Reply with exactly: PROBE-LIVE"}],
        "max_tokens": max_tokens,
    }).encode()
    req = urllib.request.Request(url, data=payload, method='POST')
    req.add_header('Content-Type', 'application/json')
    if key:
        req.add_header('Authorization', f'Bearer {key}')
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode('utf-8', errors='replace')
            http = resp.status
    except urllib.error.HTTPError as e:
        http = e.code
        body = e.read().decode('utf-8', errors='replace')
    except Exception as e:
        http = -1
        body = f'EXC: {type(e).__name__}: {str(e)[:200]}'
    return http, body, int((time.time() - t0) * 1000)


def _openrouter_endpoints(key, model):
    """Check OpenRouter's endpoint list for a model. Zero endpoints = retired."""
    url = f'https://openrouter.ai/api/v1/models/{model}/endpoints'
    req = urllib.request.Request(url)
    req.add_header('Authorization', f'Bearer {key}')
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            d = json.loads(resp.read().decode())
            eps = d.get('data', {}).get('endpoints', [])
            return len(eps), [e.get('provider_name') for e in eps[:5]]
    except Exception as e:
        return None, [f'endpoint-check-failed: {type(e).__name__}']


def probe(provider, model_id, max_tokens=100, timeout=60):
    """
    Probe a (provider, model) for truth.

    Returns:
        verdict: LIVE | DEAD | LYING
        classification: (for NIM 404s) GLOBALLY_DEAD | ENTITLEMENT_GAP | AUTH_FAILURE
        reframed: operator-truth string
        Plus http, latency_ms, evidence.
    """
    if provider not in PROVIDERS:
        return {'verdict': 'DEAD', 'error': f'unknown provider: {provider}'}

    base_url, keyname = PROVIDERS[provider]
    key = _get_key(keyname) if keyname else None
    if keyname and not key:
        return {'verdict': 'DEAD', 'error': f'key {keyname} not found'}

    result = {
        'provider': provider,
        'model': model_id,
        'verdict': 'UNKNOWN',
        'http': None,
        'latency_ms': None,
        'classification': None,
        'reframed': None,
        'evidence': {},
    }

    # OpenRouter: check endpoint list FIRST (zero endpoints = short-circuit DEAD)
    if provider == 'openrouter':
        n_eps, ep_names = _openrouter_endpoints(key, model_id)
        result['evidence']['endpoint_count'] = n_eps
        result['evidence']['endpoint_providers'] = ep_names
        if n_eps == 0:
            result['verdict'] = 'DEAD'
            result['reframed'] = (
                f'{model_id}: RETIRED. OpenRouter lists it but serves ZERO endpoints. '
                f'The catalog entry is a corpse. Do not route here.'
            )
            return result

    # The actual probe — 1-token minimum, 100 default (reasoning models need room)
    http, body, latency = _raw_probe(base_url, key, model_id, max_tokens, timeout)
    result['http'] = http
    result['latency_ms'] = latency

    # Parse for content
    content = None
    finish = None
    if http == 200:
        try:
            d = json.loads(body)
            ch = d.get('choices', [{}])[0]
            finish = ch.get('finish_reason')
            msg = ch.get('message', {})
            content = msg.get('content')
            result['evidence']['finish_reason'] = finish
            result['evidence']['has_reasoning'] = bool(msg.get('reasoning'))
        except Exception:
            pass

    # NIM 404 → NVCF classifier
    if provider == 'nim' and http == 404:
        cls = classify_nvcf_404(http, body, model_id)
        result['classification'] = cls['classification']
        result['evidence']['nvcf_uuid'] = cls['uuid']
        result['evidence']['nvcf_account'] = cls['account']
        # A 404 with a UUID is LYING (listed but not invocable), not merely DEAD
        result['verdict'] = 'LYING'
        result['reframed'] = cls['explanation']
        return result

    # Verdict logic
    if http == 200 and content and 'PROBE-LIVE' in content:
        result['verdict'] = 'LIVE'
        result['reframed'] = f'{model_id}: LIVE on {provider} ({latency}ms). Verified by real completion.'
    elif http == 200 and content:
        result['verdict'] = 'LIVE'
        result['reframed'] = f'{model_id}: LIVE on {provider} ({latency}ms, weak marker).'
    elif http == 200:
        result['verdict'] = 'LYING'
        result['reframed'] = reframe(provider, http, body, model_id)
    elif http in (401, 403):
        result['verdict'] = 'DEAD'
        result['reframed'] = reframe(provider, http, body, model_id)
    elif http == 402:
        result['verdict'] = 'DEAD'
        result['reframed'] = reframe(provider, http, body, model_id)
    elif http == 404:
        result['verdict'] = 'LYING'  # Listed somewhere but not invocable
        result['reframed'] = reframe(provider, http, body, model_id)
    elif http == 410:
        result['verdict'] = 'DEAD'
        result['reframed'] = reframe(provider, http, body, model_id)
    elif http == 504:
        cls = classify_nvcf_404(http, body, model_id)
        result['classification'] = cls['classification']
        result['verdict'] = 'LYING'  # listed/invoked, but zero workers behind it
        result['reframed'] = cls['explanation']
    elif http == 429:
        result['verdict'] = 'DEAD'
        result['reframed'] = reframe(provider, http, body, model_id)
    elif http == -1:
        result['verdict'] = 'LYING' if 'Timeout' in body else 'DEAD'
        result['reframed'] = f'{model_id}: {"HANGS (timeout)" if "Timeout" in body else "unreachable"} on {provider}.'
    else:
        result['verdict'] = 'DEAD'
        result['reframed'] = reframe(provider, http, body, model_id)

    result['evidence']['body_snippet'] = body[:300]
    return result




# ---------------------------------------------------------------------------
# NVCF function-list probe (WTF.md priority #1, 2026-09-20).
# GET /v2/nvcf/functions = the HONEST entitlement surface: exactly the
# functions this key's account can see, with per-function ACTIVE/INACTIVE.
# Scope note: requires the list_functions scope; a 401/403 here means the key
# lacks listing scope (or is bad) — NOT that the account has zero functions.
# This is account-associated ground truth, not a proof of invocation rights.
# ---------------------------------------------------------------------------
NVCF_BASE = 'https://api.nvcf.nvidia.com'


def probe_nvcf_functions(keyname='NVIDIA_API_KEY', timeout=60):
    """List the NVCF functions visible to this key's account.

    Returns dict: verdict, count, active_count, functions[{id,name,status}],
    kimi_hits (name matches), evidence. Never prints the key.
    """
    key = _get_key(keyname)
    if not key:
        return {'verdict': 'DEAD', 'error': 'key %s not found' % keyname}
    url = NVCF_BASE + '/v2/nvcf/functions'
    req = urllib.request.Request(url, method='GET')
    req.add_header('Authorization', 'Bearer ' + key)
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            http, body = resp.status, resp.read().decode('utf-8', errors='replace')
    except urllib.error.HTTPError as e:
        http, body = e.code, e.read().decode('utf-8', errors='replace')
    except Exception as e:
        return {'verdict': 'DEAD', 'http': -1,
                'reframed': 'NVCF /functions unreachable: %s: %s' % (type(e).__name__, str(e)[:120])}
    ms = int((time.time() - t0) * 1000)
    out = {'http': http, 'latency_ms': ms, 'count': 0, 'active_count': 0,
           'functions': [], 'kimi_hits': []}
    if http in (401, 403):
        out['verdict'] = 'AUTH_OR_SCOPE'
        out['reframed'] = ('NVCF /functions -> HTTP %d: key bad or lacks list_functions scope. '
                           'Cannot read the entitlement surface.' % http)
        return out
    if http != 200:
        out['verdict'] = 'DEAD'
        out['reframed'] = 'NVCF /functions -> HTTP %d: %s' % (http, body[:200])
        return out
    try:
        d = json.loads(body)
        fns = d.get('functions', d if isinstance(d, list) else [])
    except Exception as e:
        out['verdict'] = 'DEAD'
        out['reframed'] = 'NVCF /functions: unparsable body: %s' % str(e)[:120]
        return out
    for f in fns:
        rec = {'id': f.get('id'), 'name': f.get('name'), 'status': f.get('status')}
        out['functions'].append(rec)
        if f.get('status') == 'ACTIVE':
            out['active_count'] += 1
        nm = (f.get('name') or '').lower()
        if 'kimi' in nm or 'moonshot' in nm:
            out['kimi_hits'].append(rec)
    out['count'] = len(fns)
    out['verdict'] = 'LIVE'
    out['reframed'] = ('NVCF entitlement surface: %d functions (%d ACTIVE) visible to this key. '
                       '%d kimi-related.' % (out['count'], out['active_count'], len(out['kimi_hits'])))
    return out


if __name__ == '__main__':
    # CLI: probe_truth.py <provider> <model> [max_tokens]  OR  probe_truth.py nvcf-functions
    if len(sys.argv) > 1 and sys.argv[1] == 'nvcf-functions':
        print(json.dumps(probe_nvcf_functions(), indent=2))
        sys.exit(0)
    # CLI: probe_truth.py <provider> <model> [max_tokens]
    provider = sys.argv[1]
    model = sys.argv[2]
    mt = int(sys.argv[3]) if len(sys.argv) > 3 else 100
    print(json.dumps(probe(provider, model, mt), indent=2))
