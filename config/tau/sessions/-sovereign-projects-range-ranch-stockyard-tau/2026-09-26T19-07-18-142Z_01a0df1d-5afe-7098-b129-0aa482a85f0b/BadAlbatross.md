{
  "result": "readme-maximal audit complete — NEEDS UPDATE",
  "report": "/tmp/readme-maximal-report.md#02e3 (235 anchored lines, verified dry-run on /tmp/ranch-verify-full3.md)",
  "target": "/home/toxic/sovereign/projects/range/ranch/README.md#8fc6 — 77 lines, untouched",
  "skill": "/home/toxic/.tau/agent/managed-skills/readme-maximal/SKILL.md#e4ca — 9-section maximal doctrine",
  "ground_truth": {
    "25100": "verified 25100/25193/25127/25111 vs mcp_config.json:2,552,554 and docs/ARCHITECTURE.md",
    "25127": "55 hits → 3 actionable (chute:91, wrangler mcp_config.json:2, dist:118) — 0 in ranch README (missing)",
    "ffs_map": "104488 files, barn/wrangler 2225, barn/chute 14, no LICENSE at root",
    "ffs_grep_barn_shep": "3 hits — all MERGE-DECISIONS.md:3,4,6 historical (0 in ranch README)",
    "ffs_grep_shep": "30 hits → 5 actionable filtered (tau ports.env:44, tau README:43, etc) — 0 in ranch README",
    "ast_grep_shep": "0 matches — structural clean",
    "wrangler": "38 hits — 1 in ranch README:58 correct barn/wrangler path"
  },
  "verdict": "NEEDS UPDATE — 12 claims: 6 FAIL (badges, mermaid, config, dev, license, aesthetics) + 5 PARTIAL (hero, bullets, quickstart, architecture, ports) + 1 PASS (links)",
  "missing_10": [
    "badges for-the-badge row",
    "mermaid flowchart (replace ASCII 9:db..34:cd)",
    "Why ranch bullets",
    "quickstart polish + port table",
    "## Architecture consolidation + 25127 port table",
    "## Config table",
    "## Development ffs/hashline/bun pointers",
    "## License & Security (MIT + 127.0.0.1 binding)",
    "25127 in ranch README",
    "table header fix 38:d9"
  ],
  "patches_A_F": "6 hashline patches with [path#HASH] anchors in report — all verified sequentially on disposable copy /tmp/ranch-verify-full3.md: 8fc6→a134(A)→3631(B mermaid)→7e5a(C Why)→2123(D Architecture)→0dcd(E Quickstart)→380a(F Config/Dev/License) all rc=0, final 123 lines. Anchors drift: D 36:40..45:9a→42:40..51:10 after C; E 63:cd..77:8d→80:cd..94:dc after D; F INS.POST 77:8d→93:2c after E — documented in report Notes. Do not apply — main will hashline patch + push",
  "constraints": "only ffs read/map/grep/glob + ast-grep run + hashline read/patch + bun -e length<2000 filter; no head/sed/grep fallbacks"
}