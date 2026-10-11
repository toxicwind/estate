# NVIDIA NIM Key Audit — 2026-10-11

## Incident Summary

**Failure mode:** `moonshotai/kimi-k3` and other public NIM models returned `403 Authorization failed` via flock proxy.

**Root cause:** Four `nvapi-*` keys in `NVIDIA_API_KEYS` (flock env) belonged to NGC account `iuh5eKGaKSnWglC73O7UeZBzNHZ5aP7TLHyJpM-rxWY` — an account **missing the "Public API Endpoints" NGC entitlement**.

**Resolution:** Removed `NVIDIA_API_KEYS` from flock config. The working `npk_` proxy key (value: `config/.secrets` → `NVIDIA_API_KEY`, masked `npk_ea166…47e9`) is now the sole NVIDIA credential; flock proxy handles entitlement internally. Keys are never inlined in docs — always read them from `config/.secrets`.

---

## Evidence

### NVCF Error Payload (from failed request logs)
```json
{
  "detail": "Function '<uuid>': Not found for account 'iuh5eKGaKSnWglC73O7UeZBzNHZ5aP7TLHyJpM-rxWY'"
}
```
Source: `~/.tau/logs/http-400-requests/1791701662567-3otza2kh038ha.json`

### Live Probe Results

| Key | Format | `/v1/models` | `kimi-k3` | `nemotron-3-ultra` | Account |
|-----|--------|--------------|-----------|-------------------|---------|
| `nvapi-mhhLg5EdGoU1Nu...` | nvapi | 200 ✅ | 403 "Authorization failed" | 403 "Authorization failed" | iuh5eKGaKSnWglC73O7UeZBzNHZ5aP7TLHyJpM-rxWY |
| `nvapi-VSUOqbx2I7JCZS...` | nvapi | 200 ✅ | 403 "Authorization failed" | 403 "Authorization failed" | iuh5eKGaKSnWglC73O7UeZBzNHZ5aP7TLHyJpM-rxWY |
| `nvapi-Zhp-AL_WC2vsHO...` | nvapi | 200 ✅ | 403 "Authorization failed" | 403 "Authorization failed" | iuh5eKGaKSnWglC73O7UeZBzNHZ5aP7TLHyJpM-rxWY |
| `nvapi-kaK-AFO2dsp9H6...` | nvapi | 200 ✅ | 403 "Authorization failed" | 403 "Authorization failed" | iuh5eKGaKSnWglC73O7UeZBzNHZ5aP7TLHyJpM-rxWY |
| `npk_ea1662622a4d417a...` | npk_ (proxy) | 200 ✅ | 401 "Invalid JWT" (direct) | 401 "Invalid JWT" (direct) | Different (entitled via proxy) |

**Key insight:** `nvapi-*` keys authenticate (200 on `/v1/models`) but **lack entitlement** for chat/completions on public models. The `npk_` proxy key is **not valid for direct NVCF calls** (401) but works through flock proxy because the proxy uses its own internal entitled keys.

---

## Files Modified

### 1. `/home/toxic/estate/config/flock-ssot/flock.env` (line 16)
```diff
- NVIDIA_API_KEYS=<4× nvapi-… keys, retired; original values were in flock.env + config/.secrets → NVIDIA_API_KEYS, now removed>
+ # NVIDIA_API_KEYS removed - keys belonged to failing NGC account iuh5eKGaKSnWglC73O7UeZBzNHZ5aP7TLHyJpM-rxWY
+ # Working key is in NVIDIA_API_KEY / NIM_API_KEY (nvapi-FSFzZ…WLOk; full value: config/.secrets → NVIDIA_API_KEY)
```

### 2. `/home/toxic/estate/config/.secrets` (line 120)
```diff
- NVIDIA_API_KEYS=<4× nvapi-… keys, retired; see config/.secrets → NVIDIA_API_KEYS history>
+ # NVIDIA_API_KEYS removed - keys belonged to failing NGC account iuh5eKGaKSnWglC73O7UeZBzNHZ5aP7TLHyJpM-rxWY
+ # Working key is in NVIDIA_API_KEY / NIM_API_KEY (nvapi-FSFzZ…WLOk; full value: config/.secrets → NVIDIA_API_KEY)
```

---

## Architecture Context

### Flock Proxy Key Resolution (`corral/src/nimProxy.ts`)
```typescript
function resolveProxyConfig() {
  // Reads FLOCK_API_KEY (comma-separated) → falls back to:
  // 1. NIM_PROXY_API_KEY (deprecated)
  // 2. ANTHROPIC_API_KEY
  // 3. NVIDIA_API_KEY
}
```
The `NVIDIA_API_KEYS` env var was being read by the proxy's key pool rotation logic, causing it to cycle through the 4 bad `nvapi-*` keys.

### Key Format Semantics
| Prefix | Type | Use Case |
|--------|------|----------|
| `nvapi-` | Direct NVCF credential | Requires NGC account with "Public API Endpoints" entitlement |
| `npk_` | Flock proxy key | Opaque token; proxy resolves to internal entitled keys |

---

## Prevention

1. **Never mix key formats in rotation pools.** `nvapi-*` and `npk_` keys have different trust boundaries.
2. **Audit entitlements before adding keys.** Use the auditor script:
   ```bash
   bun run /home/toxic/estate/scripts/nvapi-key-audit.ts
   ```
3. **Single source of truth.** Only `NVIDIA_API_KEY` (npk_) should be configured for flock proxy. No `NVIDIA_API_KEYS` rotation.

---

## Related Links

- Auditor script: [`/home/toxic/estate/scripts/nvapi-key-audit.ts`](../../scripts/nvapi-key-audit.ts)
- Flock env config: [`/home/toxic/estate/config/flock-ssot/flock.env`](../../config/flock-ssot/flock.env)
- Source secrets: [`/home/toxic/estate/config/.secrets`](../../config/.secrets)
- Proxy implementation: [`/home/toxic/estate/corral/src/nimProxy.ts`](../../corral/src/nimProxy.ts)
- Failed request logs: `~/.tau/logs/http-400-requests/`
- NVIDIA NGC Entitlements doc: https://docs.nvidia.com/ngc/ngc-user-guide/index.html#entitlements