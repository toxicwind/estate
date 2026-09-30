# nim-proxy-audit-20260915

![status](https://img.shields.io/badge/status-consolidated-lightgrey)
![audit](https://img.shields.io/badge/audit-2026--09--15-blue)

> **Consolidated.** This repo was merged into [toxicwind/nvidia-nim](https://github.com/toxicwind/nvidia-nim) (2026-09-17) with full history preserved — the report now lives at [`audit-proxy-20260915/REPORT.md`](https://github.com/toxicwind/nvidia-nim/tree/main/audit-proxy-20260915) there. New NIM work goes there. This repo is kept as a read-only pointer.

## What this was

A forensic audit of the **nim-proxy** daemon on awrawr-pc (`:8000`), run 2026-09-15 ~03:45 UTC after the proxy was reported as "never completed".

## Verdict (from [REPORT.md](./REPORT.md), preserved verbatim)

**The proxy was COMPLETE and HEALTHY.** The "never completed" was not the proxy — it was two downstream integrations that never shipped:

| # | Finding | State |
|---|---------|-------|
| 1 | `/v1/models` with the client key → **HTTP 200, 81 models** — full client→proxy→NVIDIA path live | ✅ verified working |
| 2 | Herd integration: 3 plans produced, Chris never picked → **no execution** (decision blocker — his call) | ⏳ blocked on Chris |
| 3 | super-ralph "nim-proxy as claude" consumer never wired | ⏳ separate lane |
| 4 | The "key never supplied" premise was **stale** — `NIM_PROXY_API_KEY` (`npk_…`) exists in `/home/toxic/.secrets` and SHA-256-matches the proxy's configured client key | ✅ corrected by this audit |

Also verified: Docker→native binary migration finished, 4× `nvapi-…` upstream keys at 40 rpm each (160 rpm aggregate), config and secrets files at `0600`.

> [!NOTE]
> Key values are never reproduced here or in the report — only hashes and prefixes. The report's security note stands: `/home/toxic/.nim-proxy-data/config.json` holds live upstream keys in plaintext by the proxy's design.

## Contents

- [`REPORT.md`](./REPORT.md) — the full forensic audit: what was verified working, ranked reasons for the stall, security note, timeline, and what was executed. Preserved verbatim.
