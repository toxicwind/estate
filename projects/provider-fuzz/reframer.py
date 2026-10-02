#!/usr/bin/env python3
"""
reframer.py — Translate provider lies into operator truth.

Providers emit opaque errors ("Function not found for account", empty 200s,
"success:false" inside HTTP 200). This layer reframes them into actionable
truth, the way NVIDIA's own NemoClaw has isNvcfFunctionNotFoundForAccount()
because the raw body is "opaque to the user".
"""
import json


def reframe(provider, http_code, body, model_id=None):
    """
    Translate a provider error into operator truth.
    Returns a human-actionable string. Never parrots the provider's lie.
    """
    body = (body or '')[:500]
    mid = model_id or 'model'

    # Try to extract provider's error message for context
    prov_msg = ''
    try:
        d = json.loads(body)
        err = d.get('error', {})
        if isinstance(err, dict):
            prov_msg = err.get('message', '')[:150]
        elif isinstance(err, str):
            prov_msg = err[:150]
    except Exception:
        pass

    # --- HTTP 200 with no content (the empty lie) ---
    if http_code == 200:
        return (
            f'{mid}: EMPTY-200 on {provider}. The provider returned HTTP 200 '
            f'with no usable content. This is either a reasoning model starved '
            f'of tokens (retry with max_tokens>=100) or a dead endpoint wearing '
            f'a 200 mask. Do not trust the 200.'
        )

    # --- 401/403 ---
    if http_code in (401, 403):
        if 'pollinations' in provider.lower() or 'api key is required' in prov_msg.lower():
            return (
                f'{mid}: KEY-REQUIRED on {provider}. Anonymous access revoked for '
                f'this model. Get a key or drop the route.'
            )
        return (
            f'{mid}: AUTH-FAIL on {provider} (HTTP {http_code}). Key is bad, '
            f'expired, or lacks scope. Not a model problem — fix the credential.'
        )

    # --- 402 ---
    if http_code == 402:
        return (
            f'{mid}: NO-CREDITS on {provider}. The account is out of money. '
            f'Top up or use a free-tier route. The model itself may be fine.'
        )

    # --- 404 ---
    if http_code == 404:
        if provider == 'nim':
            # NVCF 404s are handled by nvcf_classifier; this is the fallback
            return (
                f'{mid}: NOT-INVOCABLE on NIM. The catalog lists it but the '
                f'control plane has no live function. See nvcf_classifier for '
                f'UUID-level forensics (GLOBALLY_DEAD vs ENTITLEMENT_GAP).'
            )
        return (
            f'{mid}: NOT-FOUND on {provider} (HTTP 404). The ID is wrong, '
            f'retired, or never existed. Check the provider\'s current catalog — '
            f'not a cached copy.'
        )

    # --- 410 ---
    if http_code == 410:
        return (
            f'{mid}: GONE on {provider} (HTTP 410). Decommissioned. The catalog '
            f'entry is a zombie. Remove the route, do not retry.'
        )

    # --- 429 ---
    if http_code == 429:
        if 'insufficient balance' in prov_msg.lower() or 'suspended' in prov_msg.lower():
            return (
                f'{mid}: ACCOUNT-SUSPENDED on {provider}. Valid key, zero balance. '
                f'Recharge the account. This is the highest-priority fix if it\'s '
                f'your Kimi route.'
            )
        return (
            f'{mid}: RATE-LIMITED on {provider} (HTTP 429). Not dead — back off '
            f'and retry. If persistent, the tier is too small for the load.'
        )

    # --- Pollinations-style body-lie ---
    if '"success":false' in body and http_code == 200:
        return (
            f'{mid}: BODY-LIE on {provider}. HTTP 200 with "success:false" inside. '
            f'The provider lies at the HTTP layer. Always parse the body. '
            f'Message: {prov_msg}'
        )

    # --- Fallback ---
    return (
        f'{mid}: HTTP {http_code} on {provider}. '
        f'Provider says: "{prov_msg}". Don\'t trust it — probe again or move on.'
    )


if __name__ == '__main__':
    import sys
    print(reframe(sys.argv[1], int(sys.argv[2]), open(sys.argv[3]).read() if len(sys.argv) > 3 else '', sys.argv[4] if len(sys.argv) > 4 else None))
