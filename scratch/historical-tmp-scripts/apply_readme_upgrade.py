#!/usr/bin/env python3
"""Apply the oracle-derived README hero + architecture-composition upgrade.

Edits /home/toxic/sovereign/README.md in place. Idempotent: skips steps
whose anchors are already in the target state.
"""
import re
import sys

P = "/home/toxic/sovereign/README.md"

NEW_HERO = (
    "> **Sovereign is the self-hosted operating environment where a working agent fleet lives**"
    " \u2014 one OpenAI-compatible inference front door, HMAC-signed fleet chat, a work market with"
    " stake-and-slash accountability, and a pitchfork-supervised service stack, all in one tree on"
    " the yote box. Communication, accountability, and supervision aren\u2019t three projects here;"
    " they\u2019re three layers of the same commitments: nothing silent, nothing unverifiable."
)

OLD_HERO_START = "> Chris's ops + workspace monorepo on the yote box"

COMPOSITION = """Three layers compose into one working system. Each one independently enforces the same commitments \u2014 every action attributable, every claim checkable, nothing running silent:

- **Communication \u2014 squawk.** HMAC-signed agent chat (websocket `:25147` + feed `:25135`, global sequence). The fleet's voice and the live operations log.
- **Accountability \u2014 oracle-market.** Work is triaged, bid on, cleared by Vickrey auction, executed, then verified and settled \u2014 with stake-and-slash collateral and the fused Oracle decision engine standing in for approval. Cheating is priced; decisions are checkable.
- **Governance \u2014 pitchfork + bridge + the knowledgebase.** A systemd-user-unit supervisor over the daemon stack, the live hatch\u2194yote exec bridge, and the fleet knowledgebase as required reading. The doctrine that keeps the box honest.

```mermaid
flowchart TB
    subgraph comm["Communication"]
        SQ[squawk<br/>signed fleet chat<br/>:25147 / :25135]
    end
    subgraph acct["Accountability"]
        OM[oracle-market<br/>bids \u00b7 Vickrey \u00b7 stake/slash<br/>Oracle decision engine]
    end
    subgraph gov["Governance"]
        PF[pitchfork<br/>systemd user unit]
        BR[bridge<br/>hatch\u2194yote exec :8379]
        KB[fleet-knowledgebase<br/>standing rules]
    end
    SQ <--> OM
    OM <--> PF
    SQ <--> PF
    BR -.-> PF
```

The inference path underneath:

"""

def main():
    with open(P, encoding="utf-8") as f:
        text = f.read()
    changed = []

    # 1. Hero swap
    if NEW_HERO.split("**Sovereign is")[1][:20] not in text:
        lines = text.split("\n")
        for i, ln in enumerate(lines):
            if ln.startswith(OLD_HERO_START):
                lines[i] = NEW_HERO
                changed.append("hero")
                break
        else:
            print("ANCHOR-MISS: hero", file=sys.stderr)
            sys.exit(1)
        text = "\n".join(lines)

    # 2. Composition insert after "## Architecture"
    if "Three layers compose into one working system" not in text:
        anchor = "## Architecture\n\n"
        if anchor not in text:
            print("ANCHOR-MISS: architecture", file=sys.stderr)
            sys.exit(1)
        text = text.replace(anchor, anchor + COMPOSITION, 1)
        changed.append("composition")

    # 3. De-duplicate mermaid node ids across diagrams (PF -> PF2, bridge -> bridge2
    #    in the 2nd/3rd diagrams so the new first diagram's ids don't collide)
    if "PF2[pitchfork<br/>systemd user unit]" not in text:
        # second diagram block only: replace within the inference-path diagram
        parts = text.split("```mermaid")
        # parts[2] is the inference-path diagram (parts[0] pre, parts[1] composition, parts[2] inference, parts[3] bridge)
        if len(parts) >= 4:
            parts[2] = parts[2].replace("PF[pitchfork<br/>systemd user unit]",
                                        "PF2[pitchfork<br/>systemd user unit]")
            parts[2] = parts[2].replace("PF -.-> HERD", "PF2 -.-> HERD")
            parts[2] = parts[2].replace("PF -.-> MG", "PF2 -.-> MG")
            parts[2] = parts[2].replace("PF -.-> KP", "PF2 -.-> KP")
            parts[3] = parts[3].replace('subgraph bridge["hatch \u2194 yote bridge"]',
                                        'subgraph bridge2["hatch \u2194 yote bridge"]')
            text = "```mermaid".join(parts)
            changed.append("mermaid-ids")
        else:
            print("ANCHOR-MISS: mermaid blocks", file=sys.stderr)
            sys.exit(1)

    # 4. "Both diagrams" -> "All diagrams"
    if "> Both diagrams render inline" in text:
        text = text.replace("> Both diagrams render inline", "> All diagrams render inline", 1)
        changed.append("tip")

    # 5. Last-verified bump
    if "*Last verified 2026-09-20" in text:
        text = text.replace("*Last verified 2026-09-20", "*Last verified 2026-09-21", 1)
        changed.append("verified-date")

    with open(P, "w", encoding="utf-8") as f:
        f.write(text)
    print("CHANGED: " + (",".join(changed) if changed else "nothing (already applied)"))

if __name__ == "__main__":
    main()
