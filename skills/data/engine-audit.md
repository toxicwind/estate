# Engine Audit — Sovereign Fork vs Upstream

Generated: 2026-09-15T01:19:18.220Z
Total differences: 72

## Summary

| Type | Count |
|------|-------|
| Only in engine (sovereign) | 33 |
| Only in vendor (upstream) | 2 |
| Modified | 37 |

## Sovereign Additions (only in engine)

- `packages/agent/tsconfig.tsbuildinfo`
- `packages/ai/src/auth/oauth-refresh-support.ts`
- `packages/ai/src/auth/storage-contract.ts`
- `packages/ai/src/auth/usage-cache-impl.ts`
- `packages/ai/src/auth/usage-metrics.ts`
- `packages/ai/src/registry/api-key-login.ts`
- `packages/ai/tsconfig.tsbuildinfo`
- `packages/browser-relay/dist`
- `packages/browser-relay/tsconfig.tsbuildinfo`
- `packages/catalog/test/nvidia-wire-compat.test.ts`
- `packages/catalog/tsconfig.tsbuildinfo`
- `packages/coding-agent/bench/.boot-run-1789427092547.json`
- `packages/coding-agent/bench/.boot-run-1789427112383.json`
- `packages/coding-agent/dist`
- `packages/coding-agent/src/export/html/tool-views.generated.js`
- `packages/coding-agent/tsconfig.tsbuildinfo`
- `packages/collab-web/dist`
- `packages/collab-web/KIMI_TRANSPORT.md`
- `packages/collab-web/src/transports`
- `packages/collab-web/test/transports`
- `packages/collab-web/tsconfig.tsbuildinfo`
- `packages/metaharness/tsconfig.tsbuildinfo`
- `packages/mnemopi/tsconfig.tsbuildinfo`
- `packages/natives/native/pi_natives.linux-x64-modern.node`
- `packages/omptype/tsconfig.tsbuildinfo`
- `packages/snapcompact/tsconfig.tsbuildinfo`
- `packages/stats/dist`
- `packages/stats/tsconfig.tsbuildinfo`
- `packages/tui/test/double-slash.test.ts`
- `packages/tui/tsconfig.tsbuildinfo`
- `packages/typescript-edit-benchmark/tsconfig.tsbuildinfo`
- `packages/utils/tsconfig.tsbuildinfo`
- `packages/wire/tsconfig.tsbuildinfo`

## Upstream Only (not in engine)

- `vendor/oh-my-pi/packages/coding-agent/src/config`
- `vendor/oh-my-pi/packages/coding-agent/test/config`

## Modified Files

- vendor: `vendor/oh-my-pi/packages/agent/package.json` → engine: `packages/agent/package.json`
- vendor: `vendor/oh-my-pi/packages/agent/tsconfig.json` → engine: `packages/agent/tsconfig.json`
- vendor: `vendor/oh-my-pi/packages/ai/package.json` → engine: `packages/ai/package.json`
- vendor: `vendor/oh-my-pi/packages/ai/src/auth-storage.ts` → engine: `packages/ai/src/auth-storage.ts`
- vendor: `vendor/oh-my-pi/packages/ai/src/registry/cloudflare-ai-gateway.ts` → engine: `packages/ai/src/registry/cloudflare-ai-gateway.ts`
- vendor: `vendor/oh-my-pi/packages/ai/tsconfig.json` → engine: `packages/ai/tsconfig.json`
- vendor: `vendor/oh-my-pi/packages/browser-relay/tsconfig.json` → engine: `packages/browser-relay/tsconfig.json`
- vendor: `vendor/oh-my-pi/packages/catalog/package.json` → engine: `packages/catalog/package.json`
- vendor: `vendor/oh-my-pi/packages/catalog/src/compat/rules/auth/nvidia.kdl` → engine: `packages/catalog/src/compat/rules/auth/nvidia.kdl`
- vendor: `vendor/oh-my-pi/packages/catalog/src/compat/rules/providers/nvidia.kdl` → engine: `packages/catalog/src/compat/rules/providers/nvidia.kdl`
- vendor: `vendor/oh-my-pi/packages/catalog/src/compat/rules.json` → engine: `packages/catalog/src/compat/rules.json`
- vendor: `vendor/oh-my-pi/packages/catalog/src/provider-models/descriptors.ts` → engine: `packages/catalog/src/provider-models/descriptors.ts`
- vendor: `vendor/oh-my-pi/packages/catalog/tsconfig.json` → engine: `packages/catalog/tsconfig.json`
- vendor: `vendor/oh-my-pi/packages/coding-agent/package.json` → engine: `packages/coding-agent/package.json`
- vendor: `vendor/oh-my-pi/packages/coding-agent/tsconfig.json` → engine: `packages/coding-agent/tsconfig.json`
- vendor: `vendor/oh-my-pi/packages/collab-web/package.json` → engine: `packages/collab-web/package.json`
- vendor: `vendor/oh-my-pi/packages/collab-web/src/lib/client.ts` → engine: `packages/collab-web/src/lib/client.ts`
- vendor: `vendor/oh-my-pi/packages/collab-web/tsconfig.json` → engine: `packages/collab-web/tsconfig.json`
- vendor: `vendor/oh-my-pi/packages/metaharness/package.json` → engine: `packages/metaharness/package.json`
- vendor: `vendor/oh-my-pi/packages/metaharness/tsconfig.json` → engine: `packages/metaharness/tsconfig.json`
- vendor: `vendor/oh-my-pi/packages/mnemopi/package.json` → engine: `packages/mnemopi/package.json`
- vendor: `vendor/oh-my-pi/packages/mnemopi/tsconfig.json` → engine: `packages/mnemopi/tsconfig.json`
- vendor: `vendor/oh-my-pi/packages/omptype/tsconfig.json` → engine: `packages/omptype/tsconfig.json`
- vendor: `vendor/oh-my-pi/packages/snapcompact/package.json` → engine: `packages/snapcompact/package.json`
- vendor: `vendor/oh-my-pi/packages/snapcompact/tsconfig.json` → engine: `packages/snapcompact/tsconfig.json`
- vendor: `vendor/oh-my-pi/packages/stats/package.json` → engine: `packages/stats/package.json`
- vendor: `vendor/oh-my-pi/packages/stats/tsconfig.json` → engine: `packages/stats/tsconfig.json`
- vendor: `vendor/oh-my-pi/packages/tui/package.json` → engine: `packages/tui/package.json`
- vendor: `vendor/oh-my-pi/packages/tui/src/autocomplete.ts` → engine: `packages/tui/src/autocomplete.ts`
- vendor: `vendor/oh-my-pi/packages/tui/src/tui.ts` → engine: `packages/tui/src/tui.ts`
- vendor: `vendor/oh-my-pi/packages/tui/src/utils.ts` → engine: `packages/tui/src/utils.ts`
- vendor: `vendor/oh-my-pi/packages/tui/tsconfig.json` → engine: `packages/tui/tsconfig.json`
- vendor: `vendor/oh-my-pi/packages/typescript-edit-benchmark/package.json` → engine: `packages/typescript-edit-benchmark/package.json`
- vendor: `vendor/oh-my-pi/packages/typescript-edit-benchmark/tsconfig.json` → engine: `packages/typescript-edit-benchmark/tsconfig.json`
- vendor: `vendor/oh-my-pi/packages/utils/package.json` → engine: `packages/utils/package.json`
- vendor: `vendor/oh-my-pi/packages/utils/tsconfig.json` → engine: `packages/utils/tsconfig.json`
- vendor: `vendor/oh-my-pi/packages/wire/tsconfig.json` → engine: `packages/wire/tsconfig.json`
