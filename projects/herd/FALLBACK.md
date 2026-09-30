# Herd (llama-swap) Edge-Case Fallback

**Status:** Active as of 2026-09-30. Blessed binary sha256:
`e1d70dd074bf6c1218ce45be5e2cf9ebb609cf7439d279989d2429c2f08e2e4e`
Immutable copy: `/home/toxic/sovereign/projects/herd/llama-swap.20260930-052800`

## If llama-swap fails to start or dies

Herd serves on `:25100`. The sovereign router (`:25104`) depends on it via
`LLM_BASE_URL` (default `http://127.0.0.1:25100/v1`).

### Immediate fallback (no restart needed)

Set the env override to bypass herd and hit providers directly:

```bash
# On yote, for the router process environment:
export LLM_BASE_URL="https://openrouter.ai/api/v1"
# or
export LLAMA_SWAP_V1="https://openrouter.ai/api/v1"
```

The router reads `LLM_BASE_URL` first, then `LLAMA_SWAP_V1`, then defaults to
herd `:25100`. Setting either env var reroutes around a dead herd instantly.
Restart the router (`sovereign/router`) to pick up the change.

### Restore the binary (warden path)

Do NOT roll back to a stale backup. The warden (`bin/estate-reconcile`)
follows **fallback, not rollback**:

- `estate-reconcile check` — read-only drift report (exit 1 on drift)
- `estate-reconcile --apply` — atomically restores from the immutable copy
  (tmp file + rename; never reverts to an older version)

If the immutable copy itself is corrupt, rebuild from source:
`toxicwind/sovereign-swap` @ `7fc25280816fa7f98764ac46d1435d55ac9dc3c3`
(or newer upstream — prefer cutting edge per Chris).

### Verify after recovery

```bash
curl -sf http://127.0.0.1:25100/health        # expect: OK
curl -sf http://127.0.0.1:25100/v1/models     # expect: model list JSON
/home/toxic/sovereign/bin/estate-reconcile check  # expect: exit 0
```

## Why fallback, not rollback (Chris 2026-09-30)

"A fallback is not a rollback." Rolling back to the Sep 21 binary would
discard the Sep 29 rebuild (three iterations: 23MB → 36MB → 37.5MB, the
current one verified serving). The warden reports STALE (manifest needs
refresh) when live sha != manifest but live is healthy — it never reverts
files. Build forward.
