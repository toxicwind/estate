#!/usr/bin/env python3
"""Build SKILL_INDEX.md: categorized, navigable index of all gear skills."""
import os, re

GEAR = os.path.expanduser("~/workspace/skills")

CATS = [
    ("OSINT / Recon", ["osint", "recon", "footprint", "subdomain", "threat intel", "attribution", "dox", "surveillance"]),
    ("Security", ["secur", "vuln", "audit", "pentest", "malware", "forensic", "exploit", "red team", "blue team", "soc", "siem"]),
    ("Code & Dev", ["code", "debug", "refactor", "review", "git", "ci", "build", "test", "deprecat", "sdk", "api dev", "cli"]),
    ("LLM / AI Eval", ["llm", "eval", "prompt", "benchmark", "model", "rag", "agent", "harness"]),
    ("Browser / Web", ["browser", "scrap", "crawl", "web", "playwright", "selenium", "cloudflare"]),
    ("Infra / DevOps", ["infra", "k8s", "docker", "deploy", "monitor", "sre", "network", "dns", "proxy", "server", "supervisor"]),
    ("Data", ["data", "sql", "etl", "pandas", "parquet", "dashboard", "analy"]),
    ("Research / Academic", ["research", "paper", "academic", "arxiv", "citat", "phd", "thesis"]),
    ("Media / Creative", ["image", "video", "audio", "design", "copywrit", "brand", "music", "podcast", "art"]),
    ("Docs / Writing", ["writ", "doc", "blog", "readme", "content", "copy", "translat", "editorial"]),
    ("Kimi / Widget", ["kimi", "widget"]),
]

def meta(d):
    p = os.path.join(GEAR, d, "SKILL.md")
    name, desc = d, ""
    try:
        t = open(p, encoding="utf-8", errors="replace").read(4000)
        m = re.search(r"^description:\s*(.+)$", t, re.M)
        if m:
            desc = m.group(1).strip().strip('"')
        else:
            ls = [l.strip() for l in t.splitlines()]
            for i, l in enumerate(ls):
                if l.startswith("#"):
                    for l2 in ls[i+1:]:
                        if l2 and not l2.startswith("#") and not l2.startswith("---") and not l2.startswith("```"):
                            desc = l2
                            break
                    break
        m2 = re.search(r"^name:\s*(.+)$", t, re.M)
        if m2:
            name = m2.group(1).strip().strip('"')
    except Exception:
        pass
    return name, desc[:150]

skills = []
for d in sorted(os.listdir(GEAR)):
    if d.startswith(".") or not os.path.isdir(os.path.join(GEAR, d)):
        continue
    if not os.path.exists(os.path.join(GEAR, d, "SKILL.md")):
        continue
    n, ds = meta(d)
    skills.append((d, n, ds))

def categorize(d, n, ds):
    hay = f"{d} {n} {ds}".lower()
    for cat, kws in CATS:
        if any(k in hay for k in kws):
            return cat
    return "Misc / Other"

buckets = {}
for d, n, ds in skills:
    buckets.setdefault(categorize(d, n, ds), []).append((d, n, ds))

out = ["# Skill Index", "", f"{len(skills)} skills. One dir per skill, `SKILL.md` at each root.", "",
       "## Categories", ""]
for cat, _ in CATS + [("Misc / Other", [])]:
    items = buckets.get(cat, [])
    if not items:
        continue
    out.append(f"### {cat} ({len(items)})")
    for d, n, ds in sorted(items):
        label = n if n != d else d
        out.append(f"- `{d}` — {ds}" if ds else f"- `{d}`")
    out.append("")
out += ["## Alphabetical", ""]
for d, n, ds in sorted(skills):
    out.append(f"- `{d}` — {ds}" if ds else f"- `{d}`")
open(os.path.join(GEAR, "SKILL_INDEX.md"), "w").write("\n".join(out) + "\n")
print(f"index: {len(skills)} skills, {len(buckets)} categories")
for c in sorted(buckets): print(f"  {c}: {len(buckets[c])}")
