#!/usr/bin/env python3
"""Phase 2: assemble candidates, dedupe, secrets-sweep, merge into ~/workspace/skills, build index.
Writes merge-report.json. Does NOT commit (commit happens after review of report).
"""
import os, re, json, hashlib, shutil, sys

STAGE = os.path.expanduser("~/workspace/merge-staging")
GEAR = os.path.expanduser("~/workspace/skills")
OUT = os.path.join(STAGE, "merge-report.json")

def skill_dirs():
    """Yield (source_tag, skill_name, dir_path)."""
    cands = []
    # july
    jd = os.path.join(STAGE, "july")
    for n in ["droidforge", "sdk-auditor", "stemforge"]:
        p = os.path.join(jd, n)
        if os.path.isdir(p):
            cands.append(("july", n, p))
    apx = os.path.join(jd, "apx", "apx")
    if os.path.isdir(apx):
        cands.append(("july", "apx", apx))
    # recon
    rd = os.path.join(STAGE, "recon")
    if os.path.isdir(rd):
        for n in sorted(os.listdir(rd)):
            p = os.path.join(rd, n)
            if os.path.isdir(p) and os.path.exists(os.path.join(p, "SKILL.md")):
                cands.append(("recon", n, p))
    # crisis
    cd = os.path.join(STAGE, "crisis")
    if os.path.isdir(cd):
        for n in sorted(os.listdir(cd)):
            p = os.path.join(cd, n)
            if os.path.isdir(p) and os.path.exists(os.path.join(p, "SKILL.md")):
                cands.append(("crisis", n, p))
    # tarballs — resolve the single top-level extracted dir
    def top(sub):
        d = os.path.join(STAGE, "tar", sub)
        kids = [k for k in os.listdir(d) if os.path.isdir(os.path.join(d, k))]
        return os.path.join(d, kids[0]) if kids else None
    ks = top("kimi-skills")
    if ks:
        for n in ["kimi-help-center", "kimi-widget"]:
            p = os.path.join(ks, n)
            if os.path.isdir(p):
                cands.append(("kimi-skills", n, p))
    mb = top("moonbox-skills-deploy")
    if mb:
        for n in ["envd-monitor", "grpc-probe", "portal-client", "s6-supervisor", "websocket-bridge"]:
            p = os.path.join(mb, n)
            if os.path.isdir(p):
                cands.append(("moonbox", n, p))
    cf = top("claude-forge")
    if cf:
        sd = os.path.join(cf, "skills")
        if os.path.isdir(sd):
            for n in sorted(os.listdir(sd)):
                p = os.path.join(sd, n)
                if os.path.isdir(p) and os.path.exists(os.path.join(p, "SKILL.md")):
                    cands.append(("claude-forge", n, p))
    kit = top("kimi-internal-toolkit")
    if kit:
        # flattened files — handled separately
        pass
    nsl = top("nvidia-swarm-lens")
    if nsl:
        sd = os.path.join(nsl, "skills")
        if os.path.isdir(sd):
            for n in sorted(os.listdir(sd)):
                p = os.path.join(sd, n)
                if os.path.isdir(p) and os.path.exists(os.path.join(p, "SKILL.md")):
                    cands.append(("nvidia-swarm-lens", n, p))
                elif os.path.isfile(p) and p.lower().endswith("skill.md"):
                    cands.append(("nvidia-swarm-lens", n.replace(".md", "").replace("-SKILL", ""), None, p))
    ast = top("agentic-sandbox-toolkit")
    if ast and os.path.exists(os.path.join(ast, "SKILL.md")):
        cands.append(("agentic-sandbox-toolkit", "agentic-sandbox-toolkit", ast))
    return cands

def norm_hash(path):
    with open(path, "rb") as f:
        data = f.read()
    # normalize: strip trailing whitespace per line, unify newlines
    lines = data.replace(b"\r\n", b"\n").split(b"\n")
    norm = b"\n".join(l.rstrip() for l in lines).strip()
    return hashlib.sha256(norm).hexdigest()

SECRET_RES = [
    (r"-----BEGIN (RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----", "private-key"),
    (r"\bghp_[A-Za-z0-9]{20,}", "github-pat"),
    (r"\bgho_[A-Za-z0-9]{20,}", "github-oauth"),
    (r"github_pat_[A-Za-z0-9_]{10,}", "github-fine-pat"),
    (r"\bAKIA[0-9A-Z]{16}\b", "aws-key"),
    (r"\bsk-ant-[A-Za-z0-9_-]{10,}", "anthropic-key"),
    (r"\bnvapi-[A-Za-z0-9_-]{10,}", "nvapi-key"),
    (r"\bxox[baprs]-[A-Za-z0-9-]{10,}", "slack-token"),
    (r"\bsk-[A-Za-z0-9]{20,}\b", "openai-like-key"),
]
SECRET_RES = [(re.compile(p), n) for p, n in SECRET_RES]

def sweep_dir(d):
    hits = []
    for root, _, files in os.walk(d):
        if ".git" in root:
            continue
        for fn in files:
            fp = os.path.join(root, fn)
            try:
                with open(fp, "rb") as f:
                    data = f.read()
                # skip obvious binaries
                if b"\x00" in data[:8000]:
                    continue
                text = data.decode("utf-8", errors="replace")
            except Exception:
                continue
            for rx, name in SECRET_RES:
                for m in rx.finditer(text):
                    # allow .env.example / docs mentioning patterns generically
                    if "example" in fp.lower() or "README" in fp or "SKILL.md" in fp:
                        # still flag real-looking long tokens, skip obvious placeholders
                        val = m.group(0)
                        if any(ph in val for ph in ["xxx", "XXX", "your", "YOUR", "example", "placeholder", "***"]):
                            continue
                    hits.append({"file": os.path.relpath(fp, d), "type": name,
                                 "sample": m.group(0)[:24] + "..."})
    return hits

def skill_desc(skill_path):
    sm = os.path.join(skill_path, "SKILL.md")
    name, desc = os.path.basename(skill_path), ""
    try:
        with open(sm, encoding="utf-8", errors="replace") as f:
            text = f.read(4000)
        m = re.search(r"^description:\s*(.+)$", text, re.M)
        if m:
            desc = m.group(1).strip().strip('"')[:140]
        else:
            # first non-empty line after first heading
            lines = [l.strip() for l in text.splitlines()]
            for i, l in enumerate(lines):
                if l.startswith("#"):
                    for l2 in lines[i+1:]:
                        if l2 and not l2.startswith("#") and not l2.startswith("---"):
                            desc = l2[:140]
                            break
                    break
        m2 = re.search(r"^name:\s*(.+)$", text, re.M)
        if m2:
            name = m2.group(1).strip().strip('"')
    except Exception:
        pass
    return name, desc

def main():
    cands = skill_dirs()
    print(f"{len(cands)} candidate skill dirs", flush=True)
    existing = {d for d in os.listdir(GEAR) if os.path.isdir(os.path.join(GEAR, d))}
    # content hash of existing gear SKILL.mds
    exist_hash = {}
    for d in existing:
        sm = os.path.join(GEAR, d, "SKILL.md")
        if os.path.exists(sm):
            exist_hash[norm_hash(sm)] = d

    seen_hash = dict(exist_hash)  # hash -> dir name that claimed it
    report = {"merged": [], "skipped_dupe": [], "skipped_secret": [], "renamed": []}
    merged_meta = []  # (final_name, src, desc)

    for src, name, dpath, *rest in cands:
        sm = rest[0] if rest else os.path.join(dpath, "SKILL.md")
        if dpath is None:  # single-file skill (nvidia-swarm-lens odd names)
            print(f"  SKIP (single file, no dir): {src}/{name}", flush=True)
            report["skipped_dupe"].append({"name": name, "src": src, "reason": "single-file, needs dir struct"})
            continue
        if not os.path.exists(sm):
            report["skipped_dupe"].append({"name": name, "src": src, "reason": "no SKILL.md"})
            continue
        h = norm_hash(sm)
        if h in seen_hash:
            report["skipped_dupe"].append({"name": name, "src": src,
                                           "reason": f"content-dupe of {seen_hash[h]}"})
            continue
        final = name
        if final in existing:
            # same name, different content — keep both, suffix the newcomer
            final = f"{name}-{src}"
            report["renamed"].append({"from": name, "to": final, "src": src})
        hits = sweep_dir(dpath)
        real_hits = [x for x in hits]  # report all; block only on high-confidence
        if real_hits:
            print(f"  SECRET HITS in {src}/{name}: {real_hits}", flush=True)
            report["skipped_secret"].append({"name": name, "src": src, "hits": real_hits})
            continue
        dest = os.path.join(GEAR, final)
        shutil.copytree(dpath, dest)
        seen_hash[h] = final
        existing.add(final)
        _, desc = skill_desc(dest)
        merged_meta.append((final, src, desc))
        report["merged"].append({"name": final, "src": src, "from": dpath})

    # kimi-internal-toolkit flattened files: compare to kimi-skills
    kit = None
    kd = os.path.join(STAGE, "tar", "kimi-internal-toolkit")
    if os.path.isdir(kd):
        kids = os.listdir(kd)
        if kids:
            kit = os.path.join(kd, kids[0], "audit", "skills")
    if kit and os.path.isdir(kit):
        for fn in os.listdir(kit):
            fp = os.path.join(kit, fn)
            if not os.path.isfile(fp):
                continue
            h = norm_hash(fp)
            base = fn.replace("_app_.agents_skills_", "").replace("_SKILL.md", "").replace("_", "-")
            if h in seen_hash:
                report["skipped_dupe"].append({"name": fn, "src": "kimi-internal-toolkit",
                                               "reason": f"content-dupe of {seen_hash[h]}"})
            else:
                print(f"  NOTE: kimi-internal-toolkit/{fn} unique content (maps to {base})", flush=True)
                report["merged"].append({"name": fn, "src": "kimi-internal-toolkit",
                                         "reason": "unique flattened skill file - needs manual dir struct"})

    json.dump(report, open(OUT, "w"), indent=1)
    json.dump(merged_meta, open(os.path.join(STAGE, "merged_meta.json"), "w"), indent=1)
    print(f"merged={len(report['merged'])} dupe={len(report['skipped_dupe'])} "
          f"secret={len(report['skipped_secret'])} renamed={len(report['renamed'])}", flush=True)
    print("REPORT:", OUT, flush=True)

if __name__ == "__main__":
    main()
