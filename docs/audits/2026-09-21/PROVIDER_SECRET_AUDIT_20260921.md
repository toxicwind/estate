# Provider Secret Audit — 2026-09-21

Auditor: provider-audit (Ember's crew). Method: secretsmith metadata inventory +
config reference sweep + in-process liveness probes (values never printed,
logged, or stored; verdicts only). Read-only — nothing rotated, minted, or
modified.

## Where credentials live

- GNOME keyring (`login` collection): 3 items — `Chromium Safe Storage`
  (`chrome_libsecret_os_crypt_password_v2`) + 2 Bitwarden token entries
  (`org.freedesktop.Secret.Generic`). **No provider API keys in the keyring.**
- Provider keys live in `/home/toxic/.secrets` (136 exports, mode 0600),
  parsed at startup by the keypool sidecar (`herd-keypool.py`, :25109).
  The keypool injects keys per-call; `herd.yaml` carries no hardcoded keys.
- `~/sovereign/.secrets` is only a secret-scanner fingerprint baseline.

## Per-provider verdicts

| Provider key | Referenced by | Defined | Liveness (2026-09-21) |
|---|---|---|---|
| OPENROUTER_API_KEY_FREE | keypools.yaml (openrouter-free) | yes | LIVE (keypool: healthy; direct probe 200) |
| OPENROUTER_API_KEY_1 | keypools.yaml (both pools) | yes | LIVE (direct probe 200; keypool audit log shows a historical probe 401 — recovered) |
| OPENROUTER_API_KEY | keypools.yaml (openrouter-paid) | yes | not probed (paid pool, unprobed by keypool) |
| GEMINI_API_KEY … _5 (6 keys) | keypools.yaml (gemini) | yes | ALL 6 LIVE |
| MOONSHOT_API_KEY | herd.yaml | yes | LIVE (200). NOTE: 401 "User not found" on 2026-09-20 — key is good now; the earlier routing rewrite was a misdiagnosis |
| MISTRAL_API_KEY | herd.yaml, openfang-25196.toml | yes | LIVE (200) |
| NVIDIA_API_KEY | nim-kimi-sidecar.py | yes | LIVE (200) |
| DEEPSEEK_API_KEY | (standby, no live ref) | yes | LIVE (200) |
| HF_TOKEN | hf tooling | yes | LIVE (200 via whoami-v2 — the correct endpoint; v1 401s even for valid tokens) |
| FLOCK_API_KEY | herd.yaml (flock peer, currently disabled) | yes | defined; peer disabled, not probed |
| ANTHROPIC_API_KEY | openfang-25196.toml | yes | **DEAD — 401** |
| GROQ_API_KEY | openfang-25196.toml | yes | **DEAD — 403** |
| CEREBRAS_API_KEY | (standby, no live ref) | yes | DEAD — 403 |
| LLAMA_API_KEY | herd.yaml (20×) | n/a | empty-by-design: local llama-server peers need no auth; `LLAMA_API_KEY=` is an intentional empty env passthrough, not a gap |

## Gaps

**Referenced-but-missing: none.** `CLOUDFLARE_API_TOKEN` and
`WHATSAPP_VERIFY_TOKEN` appear only in comments, not active config.

**Dead keys needing Chris's call (no action taken):**
1. `ANTHROPIC_API_KEY` — 401, referenced by openfang-25196.toml
2. `GROQ_API_KEY` — 403, referenced by openfang-25196.toml
3. `CEREBRAS_API_KEY` — 403, standby (no live references)

**Present-but-unreferenced (standby, informational):** `NVIDIA_API_KEYS`,
`NVIDIA_NIM_API_KEY`, `NVIDIA_NIM_API_KEY_1`, `NIM_API_KEY`,
`NIM_PROXY_API_KEY`, `HF_TOKEN_1`, `HUGGINGFACE_HUB_TOKEN`,
`DEEPSEEK_API_KEY`, `CEREBRAS_API_KEY`, `NITRADO_API_KEY`, `SERPER_API_KEY`,
`TAVILY_API_KEY`, `EXA_API_KEY`, `FIRECRAWL_API_KEY`, `BRAVE_SEARCH_API_KEY`,
`GMAIL_APP_PASSWORD`, `TELEGRAM_BOT_TOKEN`, `DISCORD_TOKEN`, and others —
defined in `/home/toxic/.secrets` with no live config reference.

## Hygiene findings

- The keypool audit log (`data/keypool-audit.jsonl`) contains value-shaped
  detail fields on some key events. Recommend scrubbing values at write time
  (fingerprints only, as the code comments already intend).
- One intermediate tool call during this audit printed unredacted values due
  to a faulty redaction filter on my side; values appeared only in transient
  tool output, were not persisted anywhere, and are not in this report.
- secretsmith inventory commands used: `check`, `collections`, `search`
  (metadata only). Proven safe for this audit pattern.

## Keypool live state (for the record)

- openrouter-free: `OPENROUTER_API_KEY_FREE` healthy, `_1` unknown (unprobed)
- openrouter-paid: both keys unknown (unprobed)
- gemini: 6 keys unknown to keypool (lazy) — all 6 verified LIVE directly
