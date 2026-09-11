#!/usr/bin/env python3
"""
repo-audit — Maximal GitHub Repository Visibility Auditor

Uses gh API to fetch repos, pandas + pyarrow for analysis, and
naming-pattern scoring to recommend which repos should stay private
based on sensitive keywords, topics, and descriptions.

Features:
  - Multi-user / multi-repo support
  - Naming pattern scoring (private indicators weighted)
  - Topic-based anomaly detection
  - Description + language analysis
  - Parquet + CSV + JSON export via pyarrow
  - Agentic completion prompt generation
  - Bun version detection via gh API
"""

import subprocess
import json
import re
import sys
import time
from typing import List, Dict
from dataclasses import dataclass, field


import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import argparse


# ============================================================================
# Constants
# ============================================================================

PRIVATE_INDICATORS: Dict[str, int] = {
    # High-weight: clearly sensitive
    "private": 10, "secret": 10, "credential": 10, "password": 10,
    "token": 10, "key": 8, "keys": 8, "keyserver": 8,
    # Medium-weight: likely internal
    "internal": 7, "infra": 7, "infrastructure": 7,
    "config": 6, "configuration": 6, "secrets": 9,
    "deploy": 5, "deployer": 5, "pipeline": 5,
    "cicd": 5, "workflow": 5, "runner": 5,
    "backend": 4, "server": 4, "api-key": 8, "apikey": 8,
    # Lower-weight: could be either
    "db": 3, "database": 3, "cache": 3, "redis": 3,
    "monitor": 2, "monitoring": 2, "metrics": 2,
    "logs": 2, "logger": 2, "debug": 2,
    "env": 2, "environment": 2, "dotenv": 2,
    "ssl": 3, "tls": 3, "cert": 3, "certificate": 3,
    "ssh": 3, "gpg": 3, "encryption": 4,
    "auth": 4, "authentication": 4, "oauth": 4,
    "saml": 5, "ldap": 5, "iam": 4,
    "backup": 3, "archive": 3, "snapshot": 3,
}

PUBLIC_INDICATORS: Dict[str, int] = {
    # High-weight: clearly public
    "public": 10, "open": 8, "opensource": 10, "oss": 10,
    "library": 7, "sdk": 7, "demo": 7,
    "example": 7, "tutorial": 7, "docs": 7, "website": 7,
    "blog": 6, "template": 7, "boilerplate": 7,
    "skill": 6, "skills": 6, "plugin": 6, "extension": 5,
    # Medium-weight
    "tool": 4, "tools": 4, "cli": 4, "ui": 3, "frontend": 4,
    "react": 3, "vue": 3, "svelte": 3, "next": 3,
    "package": 4, "module": 4, "library": 7,
    "config": 3, "setup": 3, "starter": 5, "seed": 4,
}

SENSITIVE_TOPICS: List[str] = [
    "security", "infrastructure", "internal", "private",
    "secrets", "credentials", "authentication", "iam",
    "ci-cd", "deployment", "monitoring", "observability",
    "backup", "disaster-recovery", "network", "firewall",
    "vpn", "ssh", "encryption", "ssl", "tls",
    "database", "db", "redis", "kafka", "rabbitmq",
    "kubernetes", "docker", "container", "orchestration",
    "terraform", "ansible", "puppet", "chef",
]

SENSITIVE_LANGUAGES: List[str] = [
    "bash", "shell", "powershell", "dockerfile", "terraform",
    "hcl", "yaml", "toml", "ini", "env",
    "c", "cpp", "rust", "go", "asm",
]


@dataclass
class RepoAnalysis:
    name: str
    full_name: str
    private: bool
    visibility: str
    fork: bool
    stargazers: int
    language: str
    description: str
    topics: List[str]
    private_score: float = 0.0
    public_score: float = 0.0
    recommendation: str = "NEUTRAL"
    reasons: List[str] = field(default_factory=list)
    bun_version: str | None = None
    has_ci: bool = False
    has_readme: bool = False


# ============================================================================
# gh API Integration
# ============================================================================

def run_gh(args: List[str], timeout: int = 30) -> str:
    """Execute gh CLI with execFile-style args (no shell)."""
    cmd = ["gh"] + args
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, check=True, timeout=timeout
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] gh api failed: {e.stderr.strip()}", file=sys.stderr)
        return ""
    except subprocess.TimeoutExpired:
        print(f"[ERROR] gh api timed out after {timeout}s", file=sys.stderr)
        return ""


def fetch_repos_for_user(username: str) -> List[Dict]:
    """Fetch all repositories for a single user/org via gh API (paginated)."""
    import subprocess
    cmd = f"gh api users/{username}/repos --paginate | jq -s 'map(.[] | {{name, full_name, private, visibility, fork, stargazers_count, language, description, topics, html_url, pushed_at, created_at}})'"
    proc = subprocess.run(
        ["bash", "-c", cmd],
        capture_output=True, text=True, timeout=60
    )
    if proc.returncode != 0:
        print(f"[ERROR] gh api failed: {proc.stderr.strip()}", file=sys.stderr)
        return []
    try:
        return json.loads(proc.stdout.strip())
    except json.JSONDecodeError:
        return []


def fetch_repo_detail(owner: str, repo: str) -> Dict:
    """Fetch detailed repo info including topics and bun version."""
    out = run_gh(["api", f"repos/{owner}/{repo}", "--jq", json.dumps({
        "name": ".name", "private": ".private", "visibility": ".visibility",
        "fork": ".fork", "stargazers_count": ".stargazers_count",
        "language": ".language", "description": ".description",
        "topics": ".topics", "html_url": ".html_url"
    }), "--include-topics"])
    if out:
        try:
            return json.loads(out)
        except json.JSONDecodeError:
            pass
    return {}


def detect_bun_version(owner: str, repo: str) -> str | None:
    """Detect bun version by checking package.json or bunfig.toml."""
    for path in ["package.json", "bunfig.toml", ".tool-versions"]:
        out = run_gh(["api", f"repos/{owner}/{repo}/contents/{path}", "--jq", ".content"])
        if out:
            try:
                import base64
                decoded = base64.b64decode(out).decode("utf-8")
                if path == "package.json":
                    data = json.loads(decoded)
                    if "bun" in data.get("packageManager", ""):
                        return data["packageManager"].split("@")[-1]
                    if "engines" in data and "bun" in data["engines"]:
                        return data["engines"]["bun"]
                elif path == "bunfig.toml":
                    for line in decoded.split("\n"):
                        if "version" in line:
                            match = re.search(r'"([^"]+)"', line)
                            if match:
                                return match.group(1)
            except Exception:
                pass
    return None


# ============================================================================
# Naming Pattern Analysis
# ============================================================================

def analyze_name_pattern(name: str, description: str, topics: List[str]) -> tuple:
    """Score a repo based on naming patterns, description, and topics."""
    name_lower = name.lower()
    desc_lower = (description or "").lower()
    topics_lower = [t.lower() for t in topics]
    combined = f"{name_lower} {desc_lower} {' '.join(topics_lower)}"

    private_score = 0.0
    public_score = 0.0
    reasons: List[str] = []

    # Check private indicators
    for term, weight in PRIVATE_INDICATORS.items():
        if re.search(r'\b' + re.escape(term) + r'\w*', combined):
            private_score += weight
            reasons.append(f"contains '{term}' (weight {weight})")

    # Check public indicators
    for term, weight in PUBLIC_INDICATORS.items():
        if re.search(r'\b' + re.escape(term) + r'\w*', combined):
            public_score += weight
            reasons.append(f"contains '{term}' (weight {weight})")

    # Topic-based scoring
    for topic in topics_lower:
        if topic in SENSITIVE_TOPICS:
            private_score += 5
            reasons.append(f"topic '{topic}' is sensitive")
        if topic in ["open-source", "opensource", "public"]:
            public_score += 8
            reasons.append(f"topic '{topic}' suggests public")

    # Language-based hints
    # (included in combined text check above)

    # Determine recommendation
    recommendation = "NEUTRAL"
    if private_score > public_score and private_score >= 8:
        recommendation = "PRIVATE"
    elif public_score > private_score and public_score >= 8:
        recommendation = "PUBLIC"
    elif private_score > public_score and private_score >= 4:
        recommendation = "CONSIDER_PRIVATE"
    elif public_score > private_score and public_score >= 4:
        recommendation = "CONSIDER_PUBLIC"

    # Override: forks are almost always public
    # (handled in caller)

    return private_score, public_score, recommendation, reasons


# ============================================================================
# Analysis Engine
# ============================================================================

def analyze_repos(repos: List[Dict], include_bun: bool = False) -> List[RepoAnalysis]:
    """Analyze all repos and return structured analysis."""
    results = []

    for repo in repos:
        name = repo.get("name", "unknown")
        full_name = repo.get("full_name", name)
        owner, _, repo_name = full_name.partition("/")

        # Get detailed info including topics
        detail = fetch_repo_detail(owner, repo_name) if include_bun else repo
        topics = detail.get("topics", repo.get("topics", []))
        description = repo.get("description", "")

        # Analyze naming patterns
        private_score, public_score, recommendation, reasons = analyze_name_pattern(
            name, description, topics
        )

        # Fork override
        if repo.get("fork"):
            public_score += 10
            recommendation = "PUBLIC"
            reasons.append("fork (should be public)")

        # Bun version detection
        bun_version = None
        if include_bun:
            bun_version = detect_bun_version(owner, repo_name)

        # Check CI indicators
        has_ci = any(t in topics_lower for t in ["github-actions", "ci", "cicd", "github"]) if (topics_lower := [t.lower() for t in topics]) else False

        analysis = RepoAnalysis(
            name=name,
            full_name=full_name,
            private=repo.get("private", True),
            visibility=repo.get("visibility", "unknown"),
            fork=repo.get("fork", False),
            stargazers=repo.get("stargazers_count", 0),
            language=repo.get("language", "unknown"),
            description=description,
            topics=topics,
            private_score=private_score,
            public_score=public_score,
            recommendation=recommendation,
            reasons=reasons,
            bun_version=bun_version,
            has_ci=has_ci,
        )
        results.append(analysis)

    return results


# ============================================================================
# DataFrame Conversion & Export
# ============================================================================

def to_dataframe(analyses: List[RepoAnalysis]) -> pd.DataFrame:
    """Convert analysis results to pandas DataFrame."""
    rows = []
    for a in analyses:
        rows.append({
            "name": a.name,
            "full_name": a.full_name,
            "private": a.private,
            "visibility": a.visibility,
            "fork": a.fork,
            "stargazers": a.stargazers,
            "language": a.language,
            "description": a.description,
            "topics": ", ".join(a.topics),
            "private_score": round(a.private_score, 2),
            "public_score": round(a.public_score, 2),
            "recommendation": a.recommendation,
            "reasons": "; ".join(a.reasons),
            "bun_version": a.bun_version or "",
            "has_ci": a.has_ci,
        })
    df = pd.DataFrame(rows)
    if not df.empty:
        df = df.sort_values("private_score", ascending=False)
    return df


def export_parquet(df: pd.DataFrame, path: str) -> None:
    """Export DataFrame to Parquet using pyarrow."""
    table = pa.Table.from_pandas(df)
    pq.write_table(table, path)
    print("[EXPORT] Parquet written to " + path + " (" + str(len(df)) + " rows)")


def export_csv(df: pd.DataFrame, path: str) -> None:
    """Export DataFrame to CSV."""
    df.to_csv(path, index=False)
    print("[EXPORT] CSV written to " + path + " (" + str(len(df)) + " rows)")


def export_json(df: pd.DataFrame, path: str) -> None:
    """Export DataFrame to JSON."""
    df.to_json(path, orient="records", indent=2)
    print("[EXPORT] JSON written to " + path + " (" + str(len(df)) + " rows)")


# ============================================================================
# Report Generation
# ============================================================================

def print_report(df: pd.DataFrame) -> None:
    """Print comprehensive audit report."""
    if df.empty:
        print("No repositories found.")
        return

    total = len(df)
    public_count = len(df[~df["private"]])
    private_count = len(df[df["private"]])
    forks = len(df[df["fork"]])

    print(f"\n{'=' * 70}")
    print(f"  MAXIMAL REPO VISIBILITY AUDIT")
    print(f"{'=' * 70}")
    print(f"  Total repos: {total} | Public: {public_count} | Private: {private_count} | Forks: {forks}")
    print(f"{'=' * 70}")

    # Recommendations
    to_private = df[(df["recommendation"] == "PRIVATE") & (~df["private"])]
    to_public = df[(df["recommendation"] == "PUBLIC") & (df["private"])]
    consider_private = df[(df["recommendation"] == "CONSIDER_PRIVATE")]
    consider_public = df[(df["recommendation"] == "CONSIDER_PUBLIC")]

    if len(to_private) > 0:
        print(f"\n🔒 MAKE PRIVATE ({len(to_private)} repos):")
        for _, row in to_private.iterrows():
            print(f"   {row['full_name']} — {row['reasons']}")
            print(f"     gh api --method PATCH repos/{row['full_name']} -f private=true")

    if len(to_public) > 0:
        print(f"\n🌐 MAKE PUBLIC ({len(to_public)} repos):")
        for _, row in to_public.iterrows():
            print(f"   {row['full_name']} — {row['reasons']}")
            print(f"     gh api --method PATCH repos/{row['full_name']} -f private=false")

    if len(consider_private) > 0:
        print(f"\n⚠️  CONSIDER PRIVATE ({len(consider_private)} repos):")
        for _, row in consider_private.iterrows():
            print(f"   {row['full_name']} — score: private={row['private_score']}, public={row['public_score']}")

    if len(consider_public) > 0:
        print(f"\n⚠️  CONSIDER PUBLIC ({len(consider_public)} repos):")
        for _, row in consider_public.iterrows():
            print(f"   {row['full_name']} — score: private={row['private_score']}, public={row['public_score']}")

    # Topic heatmap
    topic_counts = {}
    for topics_str in df["topics"]:
        if pd.notna(topics_str) and topics_str:
            for t in topics_str.split(", "):
                t = t.strip()
                if t in SENSITIVE_TOPICS:
                    topic_counts[t] = topic_counts.get(t, 0) + 1

    if topic_counts:
        print(f"\n🔍 SENSITIVE TOPIC HEATMAP:")
        for topic, count in sorted(topic_counts.items(), key=lambda x: -x[1]):
            bar = "█" * min(count, 20)
            print(f"   {topic:25s} {count:3d} {bar}")

    # Bun detection summary
    bun_repos = df[df["bun_version"].notna() & (df["bun_version"] != "")]
    if len(bun_repos) > 0:
        print(f"\n🔥 BUN-ENABLED REPOS ({len(bun_repos)}):")
        for _, row in bun_repos.iterrows():
            print(f"   {row['full_name']} — bun {row['bun_version']}")

    print(f"\n{'=' * 70}")
    print(f"  Audit complete.")
    print(f"{'=' * 70}\n")


def generate_agentic_prompts(df: pd.DataFrame) -> List[str]:
    """Generate completion prompts for agentic mode."""
    prompts = []
    to_private = df[(df["recommendation"] == "PRIVATE") & (~df["private"])]
    to_public = df[(df["recommendation"] == "PUBLIC") & (df["private"])]

    for _, row in to_private.iterrows():
        prompts.append(
            f"Make repo {row['full_name']} private via: "
            f"gh api --method PATCH repos/{row['full_name']} -f private=true"
        )

    for _, row in to_public.iterrows():
        prompts.append(
            f"Make repo {row['full_name']} public via: "
            f"gh api --method PATCH repos/{row['full_name']} -f private=false"
        )

    return prompts


# ============================================================================
# Main
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        prog="repo-audit",
        description="Maximal GitHub Repository Visibility Auditor",
        epilog="Examples:\n"
               "  python repo_audit.py --user toxicwind\n"
               "  python repo_audit.py --users toxicwind,sovereign --parquet out.parquet\n"
               "  python repo_audit.py --repos toxicwind/pi,toxicwind/tau --bun --json\n",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--user", default="", help="GitHub username/org")
    parser.add_argument("--users", default="", help="Comma-separated users")
    parser.add_argument("--repos", default="", help="Comma-separated owner/repo pairs")
    parser.add_argument("--format", choices=["table", "csv", "json", "parquet"], default="table")
    parser.add_argument("--parquet", default="repo-audit.parquet", help="Parquet output path")
    parser.add_argument("--csv", default="repo-audit.csv", help="CSV output path")
    parser.add_argument("--json", default="repo-audit.json", help="JSON output path")
    parser.add_argument("--bun", action="store_true", help="Detect bun versions")
    parser.add_argument("--all", action="store_true", help="Include all analysis details")
    parser.add_argument("--stream", action="store_true", help="Enable streaming output")
    args = parser.parse_args()

    # Collect users and repos
    users = [u.strip() for u in args.users.split(",") if u.strip()] if args.users else []
    if args.user:
        users.append(args.user)
    if not users:
        users = ["toxicwind"]  # default

    repo_specs = [r.strip() for r in args.repos.split(",") if r.strip()] if args.repos else []

    # Fetch all repos
    all_repos = []
    if repo_specs:
        for spec in repo_specs:
            parts = spec.split("/")
            if len(parts) == 2:
                detail = fetch_repo_detail(parts[0], parts[1])
                if detail:
                    all_repos.append(detail)
    else:
        for user in users:
            print("[FETCH] Fetching repos for " + user + "...")
            repos = fetch_repos_for_user(user)
            all_repos.extend(repos)
            print(f"[FETCH] {len(repos)} repos from {user}")

    if not all_repos:
        print("[ERROR] No repositories found.", file=sys.stderr)
        sys.exit(1)

    print(f"[FETCH] Total repos: {len(all_repos)}")

    # Analyze
    print("[ANALYZE] Running naming pattern scoring...")
    t0 = time.perf_counter()
    analyses = analyze_repos(all_repos, include_bun=args.bun)
    elapsed = (time.perf_counter() - t0) * 1000
    print("[ANALYZE] Done in " + str(round(elapsed, 1)) + "ms")

    # Convert to DataFrame
    df = to_dataframe(analyses)

    # Print report
    print_report(df)

    # Export
    output_format = args.format
    if output_format == "parquet":
        export_parquet(df, args.parquet)
    elif output_format == "csv":
        export_csv(df, args.csv)
    elif output_format == "json":
        export_json(df, args.json)

    # Also export to parquet if --parquet specified
    if args.parquet and output_format != "parquet":
        export_parquet(df, args.parquet)
    if args.csv and output_format != "csv":
        export_csv(df, args.csv)
    if args.json and output_format != "json":
        export_json(df, args.json)

    # Agentic prompts
    prompts = generate_agentic_prompts(df)
    if prompts:
        print(f"\n🤖 AGENTIC PROMPTS ({len(prompts)}):")
        for p in prompts[:5]:
            print(f"   {p}")
        if len(prompts) > 5:
            print(f"   ... and {len(prompts) - 5} more")

    return df


if __name__ == "__main__":
    main()
