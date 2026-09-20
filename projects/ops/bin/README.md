# projects/ops/bin

Permanent operations tooling. Per the permanence rule: the script is the
deliverable — one-off commands and chat-only results are not.

## hesitance-scan.sh

Estate hesitance-rot detector. Scans briefs, docs, cron bodies, and skill
docs for designed-in hesitance ("ask Chris", "awaiting approval",
"skip long builds", "do not investigate", ...), classifies each hit as
ROT / LEGITIMATE / QUOTE / ANTI, and exits nonzero when rot is found.

Usage:

```sh
hesitance-scan.sh [path ...]     # scan files/dirs (defaults pick box roots)
hesitance-scan.sh --fleet -n 30  # also scan recent fleet messages (squawk CLI)
hesitance-scan.sh --quiet        # summary suppressed; exit code only
```

Classifications:

- **ROT** — genuine hesitance baked into an instruction. Fix at the root:
  rewrite the offending brief template or doc, don't patch around it.
- **LEGITIMATE** — genuinely needs Chris: money, credentials, irreversible
  external sends, or "only Chris can do X" stated once, plainly.
- **QUOTE** — historical quote of the old bad brief (scar documentation in
  SOUL.md/IDENTITY.md), not a live instruction.
- **ANTI** — the line explicitly prohibits the pattern (negation), e.g.
  "I never ask Chris to do things". Anti-hesitance doctrine, not rot.

Never scanned: vendored code (`vendor/`, `vendors/`), `node_modules/`,
`site-packages/`, `archive/`, `_archive/` (superseded bodies are historical
evidence, not live instructions), `.git/`.
