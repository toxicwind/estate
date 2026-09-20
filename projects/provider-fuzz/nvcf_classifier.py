#!/usr/bin/env python3
"""
nvcf_classifier.py — NVCF forensic classifier.

NVIDIA's hosted NIM is a facade over NVCF (control plane / invocation plane /
compute plane). A 404 "Function not found for account" is a CONTROL-PLANE
lookup failure — the request never reached a model. It's not auth, not
connectivity, not your key.

The function UUID in the 404 body is the fingerprint:
- SAME UUID across different accounts/forum threads → GLOBALLY_DEAD (decommissioned)
- UUID unique per account → ENTITLEMENT_GAP (needs "Public API Endpoints" permission)

Usage:
    from nvcf_classifier import classify_nvcf_404
    result = classify_nvcf_404(http_code, body, account_id=None)
"""
import json
import os
import re
import subprocess

REGISTRY_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'dead_uuids.json')

# UUID pattern in NVCF 404 bodies
UUID_RE = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", re.I)
# Account ID pattern: 'xxx-xxx' quoted in the detail string
ACCOUNT_RE = re.compile(r"for account '([^']+)'")


def load_registry():
    """Load the dead-UUID registry. Format: {uuid: {model, first_seen, sources[], verdict}}"""
    if os.path.exists(REGISTRY_PATH):
        with open(REGISTRY_PATH) as f:
            return json.load(f)
    return {}


def save_registry(reg):
    with open(REGISTRY_PATH, 'w') as f:
        json.dump(reg, f, indent=2)


def extract_uuid(body):
    """Extract the NVCF function UUID from a 404 body."""
    m = UUID_RE.search(body or '')
    return m.group(0).lower() if m else None


def extract_account(body):
    """Extract the account ID from a 404 body."""
    m = ACCOUNT_RE.search(body or '')
    return m.group(1) if m else None


def classify_nvcf_404(http_code, body, model_id=None, account_id=None):
    """
    Classify an NVCF error response.

    Returns dict with:
        - classification: GLOBALLY_DEAD | ENTITLEMENT_GAP | AUTH_FAILURE |
                          CAPACITY_STARVED | NOT_NVCf_404 | UNKNOWN
        - uuid: extracted function UUID (or None)
        - account: extracted account ID (or None)
        - explanation: operator-truth string
        - evidence: the raw body snippet
    """
    body = body or ''

    # Auth failures are not NVCF issues
    if http_code in (401, 403):
        return {
            'classification': 'AUTH_FAILURE',
            'uuid': None,
            'account': account_id,
            'explanation': f'HTTP {http_code}: key is bad or lacks scope. Not an NVCF issue.',
            'evidence': body[:200],
        }

    # 504: control plane accepted (NVCF-REQID issued) but no worker claimed
    # the request in the poll window. The function EXISTS; capacity is zero.
    # Discovered live 2026-09-20: moonshotai/kimi-k3 -> 504 + nvcf-status: errored.
    if http_code == 504:
        return {
            'classification': 'CAPACITY_STARVED',
            'uuid': None,
            'account': account_id,
            'explanation': (
                'HTTP 504: NVCF accepted the request but no worker picked it up '
                'in the poll window. Function exists; zero serving capacity '
                'right now. Not death, not auth — starvation.'),
            'evidence': body[:200],
        }

    # Not a 404 \→ not our classifier's domain
    if http_code != 404:
        return {
            'classification': 'NOT_NVCf_404',
            'uuid': None,
            'account': account_id,
            'explanation': f'HTTP {http_code}: not an NVCF 404. Use the general reframer.',
            'evidence': body[:200],
        }

    uuid = extract_uuid(body)
    acct = extract_account(body) or account_id

    if not uuid:
        return {
            'classification': 'UNKNOWN',
            'uuid': None,
            'account': acct,
            'explanation': 'HTTP 404 but no NVCF function UUID in body. Cannot classify.',
            'evidence': body[:200],
        }

    reg = load_registry()
    entry = reg.get(uuid)

    if entry:
        # UUID seen before — check if it appeared across accounts
        sources = entry.get('sources', [])
        accounts = set(s.get('account') for s in sources if s.get('account'))
        if acct:
            accounts.add(acct)
        if len(accounts) >= 2 or entry.get('verdict') == 'GLOBALLY_DEAD':
            return {
                'classification': 'GLOBALLY_DEAD',
                'uuid': uuid,
                'account': acct,
                'explanation': (
                    f'{model_id or "Model"}: GLOBALLY DECOMMISSIONED. '
                    f'Function UUID {uuid} seen across {len(accounts)} accounts. '
                    f'The catalog is a zombie — migrate to a live route.'
                ),
                'evidence': body[:200],
            }
        else:
            return {
                'classification': 'ENTITLEMENT_GAP',
                'uuid': uuid,
                'account': acct,
                'explanation': (
                    f'{model_id or "Model"}: function exists but not enabled for this account. '
                    f'Needs "Public API Endpoints" permission (manual, non-self-service). '
                    f'UUID {uuid} seen only on this account so far.'
                ),
                'evidence': body[:200],
            }
    else:
        # New UUID — record it, tentatively ENTITLEMENT_GAP (single account so far)
        reg[uuid] = {
            'model': model_id,
            'first_seen': __import__('datetime').datetime.utcnow().isoformat() + 'Z',
            'sources': [{'account': acct, 'note': 'auto-registered by classifier'}],
            'verdict': 'UNDER_OBSERVATION',
        }
        save_registry(reg)
        return {
            'classification': 'ENTITLEMENT_GAP',
            'uuid': uuid,
            'account': acct,
            'explanation': (
                f'{model_id or "Model"}: NEW UUID {uuid} registered. '
                f'Tentatively ENTITLEMENT_GAP (single account). '
                f'If this UUID appears on another account, reclassify to GLOBALLY_DEAD.'
            ),
            'evidence': body[:200],
        }


def register_dead_uuid(uuid, model_id, source_note, account=None):
    """Manually register a known-dead UUID (e.g., from forum threads)."""
    reg = load_registry()
    uuid = uuid.lower()
    entry = reg.get(uuid, {
        'model': model_id,
        'first_seen': __import__('datetime').datetime.utcnow().isoformat() + 'Z',
        'sources': [],
        'verdict': 'GLOBALLY_DEAD',
    })
    entry['sources'].append({'account': account, 'note': source_note})
    # If 2+ distinct accounts, confirm GLOBALLY_DEAD
    accounts = set(s.get('account') for s in entry['sources'] if s.get('account'))
    if len(accounts) >= 2:
        entry['verdict'] = 'GLOBALLY_DEAD'
    reg[uuid] = entry
    save_registry(reg)
    return entry




# ---------------------------------------------------------------------------
# NemoClaw borrow (verbatim, 2026-09-20): canonical NVCF 404 classifier twin.
# Source: NVIDIA-NemoClaw src/lib/inference/nvcf-model-access.ts (Apache-2.0).
# The JS regex and the POSIX shell ERE express the SAME condition so host and
# sandbox probes cannot drift. Papers note: NVIDIA's own docs describe the
# underlying 404 ("Function not found for account") as the control-plane lookup
# failure when a model is in the public catalog but not deployed for the key.
# ---------------------------------------------------------------------------
NVCF_404_JS_RE = r"Function[ \t]+'[^']+':[ \t]*Not found for account"
NVCF_FUNCTION_NOT_FOUND_SHELL_ERE = "Function[[:blank:]]+'[^']+':[[:blank:]]*Not found for account"
NVCF_FUNCTION_NOT_FOUND_SHELL_MATCH_ARGS = "-qiE"
NVCF_FUNCTION_NOT_FOUND_MARKER = "nemoclaw-probe:nvcf-function-not-found"


def nvcf_function_not_found_message(model):
    """User-facing message (NemoClaw wording, verbatim logic)."""
    return (
        "Model '%s' not found \u2014 it is in the NVIDIA Build catalog but is not deployed "
        "for your account. Pick a different model, or check the model card on "
        "https://build.nvidia.com to see if it requires org-level access." % model
    )


def classify_shell_ere(body):
    """Classify with the REAL shell ERE (grep -qiE) — bash-side parity.

    Returns {'match': bool, 'marker': str|None}. Only the marker crosses trust
    boundaries, never the body (NemoClaw #6195 pattern).
    """
    body = body or ''
    try:
        p = subprocess.run(
            ['grep'] + NVCF_FUNCTION_NOT_FOUND_SHELL_MATCH_ARGS.split()
            + ['-e', NVCF_FUNCTION_NOT_FOUND_SHELL_ERE],
            input=body.encode(), capture_output=True, timeout=10)
        match = (p.returncode == 0)
    except Exception:
        # grep unavailable: fall back to the JS twin (same condition)
        match = bool(re.search(NVCF_404_JS_RE, body, re.I))
    return {'match': match,
            'marker': NVCF_FUNCTION_NOT_FOUND_MARKER if match else None}


# ---------------------------------------------------------------------------
# Ghost-ID guard (WTF.md priority #4): pin dead UUIDs so catalog refreshes
# can't resurrect them. Call BEFORE any route insertion.
# ---------------------------------------------------------------------------
def guard_uuid(uuid):
    """Check a function UUID against the dead registry before route insertion.

    Returns {'blocked': bool, 'reason': str, 'record': dict|None}.
    Blocks any UUID whose verdict is not CLEARED/UNDER_OBSERVATION.
    """
    uuid = (uuid or '').lower()
    reg = load_registry()
    rec = reg.get(uuid)
    if not rec:
        return {'blocked': False, 'reason': 'uuid not in registry — proceed', 'record': None}
    verdict = rec.get('verdict', '')
    if verdict in ('CLEARED', 'UNDER_OBSERVATION'):
        return {'blocked': False, 'reason': 'verdict=%s — allowed' % verdict, 'record': rec}
    return {'blocked': True,
            'reason': 'GHOST-ID BLOCKED: %s verdict=%s (model=%s, sources=%d). Refusing route insertion.' % (
                uuid, verdict, rec.get('model'), len(rec.get('sources', []))),
            'record': rec}


def guard_model_route(model_id, uuid=None):
    """Route-insertion guard: pass the model's function UUID (or extract from a probe body)."""
    if not uuid:
        return {'blocked': False, 'reason': 'no uuid supplied — probe the model first, then guard', 'record': None}
    return guard_uuid(uuid)


if __name__ == '__main__':
    import sys
    # CLI: nvcf_classifier.py <http_code> <body_file> [model_id]
    code = int(sys.argv[1])
    with open(sys.argv[2]) as f:
        body = f.read()
    model = sys.argv[3] if len(sys.argv) > 3 else None
    print(json.dumps(classify_nvcf_404(code, body, model), indent=2))
