# Sovereign bug-bounty openers (headed Playwright)

Headed browser helpers to open **real $$ bounty programs** for the agent PATH-wrapper hang pack.

## Programs

| Script | Program | $$ surface |
|--------|---------|------------|
| `open-xai.mjs` | [HackerOne X / xAI](https://hackerone.com/x) | X/xAI/Grok security bounties |
| `open-github.mjs` | [HackerOne GitHub](https://hackerone.com/github) + [bounty.github.com](https://bounty.github.com/) | Criticals advertised **$30k+** |
| `open-google.mjs` | [Google Bug Hunters VRP](https://bughunters.google.com/) | Google VRP rewards ($$ tiers) |
| `run-all.mjs` | All three | One headed window, many tabs |

Evidence pack to attach: `~/projects/agent-path-wrapper-bug/`

## Run

```bash
cd ~/sovereign/tools/bugbounty
export DISPLAY=:0
# optional: attach CDP instead of launch
# export BB_CDP_URL=http://127.0.0.1:9222

node open-xai.mjs
node open-github.mjs
node open-google.mjs
# or
node run-all.mjs

# screenshot-only then exit:
BB_CLOSE=1 node run-all.mjs
```

Artifacts: `~/sovereign/tools/bugbounty/artifacts/{xai,github,google}/`

## $$ framing (read program policy before submit)

These are **paid** programs. Your finding must still **match scope**:

| Program | Best $$ angle for this issue |
|---------|------------------------------|
| **X / xAI** | Grok/API/web **security** impact (auth, data leak, prompt injection with impact) — pure local hang may be out-of-scope; frame **remote agent impact** if any |
| **GitHub** | In-scope **github.com** / Copilot cloud security only — local IDE hang usually **no bounty** unless cloud agent boundary |
| **Google** | Antigravity/Gemini **cloud** security if in VRP rules — local desktop hang often **no payout** |

Scripts open the portals; **you** map impact to in-scope assets for cash.

## Helpers

- `lib/helpers.mjs` — Firefox-first launch, CDP attach, screenshots, manifests
