#!/usr/bin/env python3
"""
Repo Audit Skill: Analyze GitHub repositories and recommend privacy settings.

Uses gh CLI to fetch repository data, then analyzes names, descriptions, and topics
to recommend which repositories should be private based on naming patterns.
Outputs recommendations as CSV or Parquet.
"""

import argparse
import json
import os
import subprocess
import sys
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False
    print("Warning: pandas not installed, will output CSV only", file=sys.stderr)

try:
    import pyarrow as pa
    import pyarrow.parquet as pq
    HAS_PYARROW = True
except ImportError:
    HAS_PYARROW = False
    print("Warning: pyarrow not installed, Parquet output disabled", file=sys.stderr)


def run_gh(args: List[str], timeout: int = 30) -> str:
    """Execute gh CLI with execFile-style args (no shell)."""
    cmd = ["gh"] + args
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False
    )
    if result.returncode != 0:
        raise subprocess.CalledProcessError(result.returncode, cmd, result.stdout, result.stderr)
    return result.stdout


def fetch_repos_for_user(username: str) -> List[Dict]:
    """Fetch all repositories for a single user/org via gh API (paginated)."""
    print(f"[FETCH] Fetching repos for {username}...")
    try:
        # Use gh api with paginate and slurp to get all repos as a single JSON array
        output = run_gh([
            "api",
            f"/users/{username}/repos",
            "--paginate",
            "--slurp"
        ])
        
        if not output.strip():
            print("[FETCH] No repos found")
            return []
        
        # Parse the JSON array
        repos = json.loads(output)
        print(f"[FETCH] Total repos fetched for {username}: {len(repos)}")
        return repos if isinstance(repos, list) else []
        
    except (subprocess.CalledProcessError, json.JSONDecodeError) as e:
        print(f"[FETCH] Error fetching repos for {username}: {e}", file=sys.stderr)
        return []


def fetch_repo_detail(owner: str, repo: str) -> Dict:
    """Fetch detailed repo info including topics and bun version."""
    try:
        # Get repo details
        repo_output = run_gh([
            "api",
            f"/repos/{owner}/{repo}"
        ])
        
        repo_data = json.loads(repo_output)
        
        # Get topics
        try:
            topics_output = run_gh([
                "api",
                f"/repos/{owner}/{repo}/topics",
                "-H", "Accept: application/json+git"
            ])
            topics_data = json.loads(topics_output)
            repo_data["topics"] = topics_data.get("names", []) if isinstance(topics_data, dict) else []
        except:
            repo_data["topics"] = []
            
        return repo_data
    except subprocess.CalledProcessError:
        return {}


def detect_bun_version(owner: str, repo: str) -> Optional[str]:
    """Detect bun version by checking package.json or bunfig.toml."""
    files_to_check = [
        ("package.json", ".bun.version"),
        ("bunfig.toml", "bun.version"),
        (".tool-versions", "bun")
    ]
    
    for filename, key in files_to_check:
        try:
            output = run_gh([
                "api",
                f"/repos/{owner}/{repo}/contents/{filename}"
            ])
            import base64
            content = base64.b64decode(output['content']).decode('utf-8')
            
            if filename.endswith('.json'):
                data = json.loads(content)
                if key in data:
                    return str(data[key])
            elif filename.endswith('.toml'):
                # Simple TOML parsing for bun.version
                for line in content.split('\n'):
                    if line.strip().startswith(key + '='):
                        return line.split('=', 1)[1].strip().strip('"')
            else:  # .tool-versions
                for line in content.split('\n'):
                    if line.startswith(key + ' '):
                        return line.split()[1]
        except (KeyError, subprocess.CalledProcessError):
            continue
    
    return None


# ============================================================================
# Scoring Constants
# ============================================================================

# Private indicators (higher score = more likely should be private)
PRIVATE_INDICATORS: Dict[str, int] = {
    "secret": 10,
    "token": 10,
    "key": 10,
    "credential": 10,
    "password": 10,
    "passwd": 10,
    "private": 8,
    "internal": 8,
    "confidential": 8,
    "proprietary": 8,
    "cert": 7,
    "certificate": 7,
    "ssh": 7,
    "gpg": 7,
    "pem": 6,
    "p12": 6,
    "pfx": 6,
    "config": 5,
    "settings": 5,
    "env": 5,
    ".env": 5,
    "dotenv": 5,
    "cred": 4,
    "auth": 4,
    "oauth": 4,
    "ssl": 3,
    "tls": 3
}

# Public indicators (higher score = more likely should be public)
PUBLIC_INDICATORS: Dict[str, int] = {
    "public": 5,
    "open": 4,
    "source": 4,
    "community": 3,
    "demo": 3,
    "example": 3,
    "template": 3,
    "tutorial": 3,
    "guide": 3,
    "docs": 3,
    "documentation": 3,
    "website": 2,
    "blog": 2,
    "portfolio": 2
}

# Sensitive topics that increase privacy score
SENSITIVE_TOPICS: List[str] = [
    "security", "authentication", "authorization", "crypto", "encryption",
    "keys", "tokens", "secrets", "credentials", "private", "internal",
    "config", "settings", "infrastructure", "deploy", "devops"
]

# Sensitive languages
SENSITIVE_LANGUAGES: List[str] = [
    "Shell", "Bash", "PowerShell", "Dockerfile", "Makefile", "YAML", "TOML"
]


def analyze_name_pattern(name: str, description: str, topics: List[str]) -> Tuple[int, int, str, List[str]]:
    """Score a repo based on naming patterns, description, and topics."""
    name_lower = name.lower()
    desc_lower = (description or "").lower()
    topics_lower = [t.lower() for t in topics]
    
    private_score = 0
    public_score = 0
    reasons = []
    
    # Check name for indicators
    for indicator, weight in PRIVATE_INDICATORS.items():
        if indicator in name_lower:
            private_score += weight
            reasons.append(f"name contains '{indicator}' (+{weight})")
    
    # Check description for indicators
    for indicator, weight in PRIVATE_INDICATORS.items():
        if indicator in desc_lower:
            private_score += weight
            reasons.append(f"description contains '{indicator}' (+{weight})")
    
    # Check topics for indicators
    for topic in topics_lower:
        for indicator, weight in PRIVATE_INDICATORS.items():
            if indicator in topic:
                private_score += weight
                reasons.append(f"topic '{topic}' contains '{indicator}' (+{weight})")
                break
    
    # Check for public indicators
    for indicator, weight in PUBLIC_INDICATORS.items():
        if indicator in name_lower:
            public_score += weight
            reasons.append(f"name contains '{indicator}' (+{weight}) [public]")
        if indicator in desc_lower:
            public_score += weight
            reasons.append(f"description contains '{indicator}' (+{weight}) [public]")
    
    # Check sensitive topics
    for topic in topics_lower:
        if topic in SENSITIVE_TOPICS:
            private_score += 3
            reasons.append(f"sensitive topic '{topic}' (+3)")
    
    return private_score, public_score, "; ".join(reasons), reasons


def analyze_repo(repo: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze a single repo and determine if it should be private."""
    name = repo["name"]
    description = repo.get("description", "")
    topics = repo.get("topics", [])
    
    # Get detailed info
    try:
        detail = fetch_repo_detail(repo["owner"]["login"], name)
        # Merge detail into repo
        for key, value in detail.items():
            if key not in repo:
                repo[key] = value
    except:
        pass
    
    # Check for bun version
    bun_version = detect_bun_version(
        repo["owner"]["login"], 
        name
    ) if detail else None
    
    # Analyze naming patterns
    private_score, public_score, reasons, reason_list = analyze_name_pattern(
        name, description, topics
    )
    
    # Determine recommendation
    if private_score > public_score and private_score >= 5:
        recommendation = "PRIVATE"
    elif public_score > private_score and public_score >= 5:
        recommendation = "PUBLIC"
    elif private_score > 0 or public_score > 0:
        recommendation = "CONSIDER_" + ("PRIVATE" if private_score > public_score else "PUBLIC")
    else:
        recommendation = "NEUTRAL"
    
    return {
        "name": repo["name"],
        "owner": repo["owner"]["login"],
        "visibility": repo["visibility"],  # public or private
        "html_url": repo["html_url"],
        "description": repo.get("description", ""),
        "topics": ", ".join(topics),
        "stars": repo["stargazers_count"],
        "fork": repo["fork"],
        "private": repo["private"],
        "bun_version": bun_version,
        "private_score": private_score,
        "public_score": public_score,
        "recommendation": recommendation,
        "reasons": reasons
    }


def load_env_map() -> Dict[str, Dict]:
    """Load environment mapping of projects to their locations."""
    env_map = {}
    
    # Check for local projects
    base_paths = [
        "/home/toxic/projects",
        "/home/toxic/sovereign",
        "/home/toxic/sovereign/src",
        "/home/toxic/sovereign/skills"
    ]
    
    for base_path in base_paths:
        if not os.path.exists(base_path):
            continue
            
        try:
            for item in os.listdir(base_path):
                item_path = os.path.join(base_path, item)
                if os.path.isdir(item_path) and os.path.exists(os.path.join(item_path, ".git")):
                    # Get git info
                    try:
                        # Get last commit date
                        date_output = subprocess.run(
                            ["git", "-C", item_path, "log", "-1", "--format=%ci"],
                            capture_output=True, text=True, check=True
                        )
                        last_push = date_output.stdout.strip() if date_output.returncode == 0 else "unknown"
                        
                        # Get remote origin URL
                        remote_output = subprocess.run(
                            ["git", "-C", item_path, "remote", "get-url", "origin"],
                            capture_output=True, text=True, check=False
                        )
                        remote_url = remote_output.stdout.strip() if remote_output.returncode == 0 else ""
                        
                        env_map[item] = {
                            "path": item_path,
                            "last_push": last_push,
                            "remote_url": remote_url,
                            "type": "local"
                        }
                    except:
                        env_map[item] = {
                            "path": item_path,
                            "last_push": "unknown",
                            "remote_url": "",
                            "type": "local"
                        }
        except (PermissionError, OSError):
            continue
    
    return env_map


def main():
    parser = argparse.ArgumentParser(
        description="Audit GitHub repositories and recommend privacy settings with local context"
    )
    parser.add_argument(
        "--user", "-u",
        default=os.environ.get("GH_USER", "toxicwind"),
        help="GitHub username or organization (default: toxicwind or GH_USER)"
    )
    parser.add_argument(
        "--users", "-U",
        help="Comma-separated list of GitHub users/orgs to audit"
    )
    parser.add_argument(
        "--repos", "-r",
        help="Comma-separated list of specific repos to audit (format: owner/repo)"
    )
    parser.add_argument(
        "--output", "-o",
        default="repo-audit",
        help="Output file basename (default: repo-audit)"
    )
    parser.add_argument(
        "--format", "-f",
        choices=["csv", "parquet", "json", "both"],
        default="both",
        help="Output format (default: both)"
    )
    parser.add_argument(
        "--threshold", "-t",
        type=int,
        default=0,
        help="Minimum stars to consider (default: 0)"
    )
    parser.add_argument(
        "--local-only",
        action="store_true",
        help="Only analyze repos that exist locally"
    )
    parser.add_argument(
        "--github-only",
        action="store_true",
        help="Only analyze repos that exist on GitHub (not local)"
    )
    parser.add_argument(
        "--show-env",
        action="store_true",
        help="Show environment mapping and exit"
    )
    
    args = parser.parse_args()
    
    # Show env map if requested
    if args.show_env:
        env_map = load_env_map()
        print("Environment Mapping:")
        for project, info in env_map.items():
            print(f"  {project}:")
            print(f"    Path: {info['path']}")
            print(f"    Last Push: {info['last_push']}")
            print(f"    Remote: {info['remote_url']}")
            print(f"    Type: {info['type']}")
        return
    
    # Determine what to audit
    target_users = []
    target_repos = []
    
    if args.users:
        target_users = [u.strip() for u in args.users.split(",")]
    elif args.repos:
        # Parse owner/repo format
        for repo_spec in args.repos.split(","):
            repo_spec = repo_spec.strip()
            if "/" in repo_spec:
                owner, repo = repo_spec.split("/", 1)
                target_repos.append((owner, repo))
            else:
                # Assume it's a repo under the default user
                target_repos.append((args.user, repo_spec))
    else:
        target_users = [args.user]
    
    # Fetch repos based on target
    all_repos = []
    
    if target_repos:
        # Fetch specific repos
        for owner, repo_name in target_repos:
            try:
                repo_data = fetch_repo_detail(owner, repo_name)
                if repo_data:
                    all_repos.append(repo_data)
            except Exception as e:
                print(f"[WARN] Could not fetch {owner}/{repo_name}: {e}", file=sys.stderr)
    else:
        # Fetch repos for users
        for user in target_users:
            try:
                repos = fetch_repos_for_user(user)
                all_repos.extend(repos)
            except Exception as e:
                print(f"[ERROR] Failed to fetch repos for {user}: {e}", file=sys.stderr)
                continue
    
    print(f"[INFO] Total repositories to analyze: {len(all_repos)}")
    
    # Filter by stars
    if args.threshold > 0:
        all_repos = [r for r in all_repos if r["stargazers_count"] >= args.threshold]
        print(f"[INFO] After star threshold (>={args.threshold}): {len(all_repos)} repos")
    
    # Load environment map for local context
    env_map = load_env_map()
    print(f"[INFO] Loaded environment map for {len(env_map)} local projects")
    
    # Analyze each repo
    print("[ANALYZING] Analyzing repositories...")
    results = []
    for i, repo in enumerate(all_repos, 1):
        if i % 10 == 0 or i == len(all_repos):
            print(f"  Progress: {i}/{len(all_repos)}")
        results.append(analyze_repo(repo))
    
    # Convert to DataFrame if pandas available
    if HAS_PANDAS:
        df = pd.DataFrame(results)
        # Reorder columns for readability
        cols = [
            "owner", "name", "visibility", "private", "bun_version",
            "private_score", "public_score", "recommendation", "reasons",
            "stars", "fork", "description", "topics", "html_url"
        ]
        # Only select columns that exist
        existing_cols = [col for col in cols if col in df.columns]
        df = df[existing_cols]
    else:
        df = None
    
    # Output
    basename = args.output
    if args.format in ["csv", "both"]:
        csv_path = f"{basename}.csv"
        if HAS_PANDAS:
            df.to_csv(csv_path, index=False)
        else:
            # Write CSV manually
            import csv
            if results:
                with open(csv_path, 'w', newline='') as f:
                    writer = csv.DictWriter(f, fieldnames=results[0].keys())
                    writer.writeheader()
                    writer.writerows(results)
        print(f"[EXPORT] CSV written to: {csv_path}")
    
    if args.format in ["parquet", "both"] and HAS_PYARROW and HAS_PANDAS:
        parquet_path = f"{basename}.parquet"
        df.to_parquet(parquet_path, index=False)
        print(f"[EXPORT] Parquet written to: {parquet_path}")
    elif args.format in ["parquet", "both"]:
        print("[EXPORT] Parquet output skipped (missing pandas or pyarrow)", file=sys.stderr)
    
    if args.format in ["json", "both"]:
        json_path = f"{basename}.json"
        if HAS_PANDAS:
            df.to_json(json_path, orient="records", indent=2)
        else:
            with open(json_path, 'w') as f:
                json.dump(results, f, indent=2)
        print(f"[EXPORT] JSON written to: {json_path}")
    
    # Print summary
    if HAS_PANDAS and len(df) > 0:
        private_count = df[df["recommendation"] == "PRIVATE"].shape[0]
        public_count = df[df["recommendation"] == "PUBLIC"].shape[0]
        consider_private = df[df["recommendation"] == "CONSIDER_PRIVATE"].shape[0]
        consider_public = df[df["recommendation"] == "CONSIDER_PUBLIC"].shape[0]
        neutral_count = df[df["recommendation"] == "NEUTRAL"].shape[0]
        
        print("\n" + "="*60)
        print("REPO AUDIT SUMMARY")
        print("="*60)
        print(f"Total repositories analyzed: {len(df)}")
        print(f"🔒 Recommend PRIVATE: {private_count}")
        print(f"🟢 Recommend PUBLIC: {public_count}")
        print(f"⚠️  Consider PRIVATE: {consider_private}")
        print(f"⚠️  Consider PUBLIC: {consider_public}")
        print(f"⚪ Neutral: {neutral_count}")
        
        if private_count > 0:
            print(f"\n🔒 TOP {min(10, private_count)} REPOS TO MAKE PRIVATE:")
            top_private = df[df["recommendation"] == "PRIVATE"].nlargest(10, "private_score")
            for _, row in top_private.iterrows():
                print(f"  {row['owner']}/{row['name']} (score: {row['private_score']}) - {row['reasons'][:80]}...")
        
        if consider_private > 0:
            print(f"\n⚠️  TOP {min(10, consider_private)} REPOS TO CONSIDER MAKING PRIVATE:")
            top_consider = df[df["recommendation"] == "CONSIDER_PRIVATE"].nlargest(10, "private_score")
            for _, row in top_consider.iterrows():
                print(f"  {row['owner']}/{row['name']} (score: {row['private_score']}) - {row['reasons'][:80]}...")
    else:
        # Manual summary
        private_count = sum(1 for r in results if r["recommendation"] == "PRIVATE")
        public_count = sum(1 for r in results if r["recommendation"] == "PUBLIC")
        consider_private = sum(1 for r in results if r["recommendation"] == "CONSIDER_PRIVATE")
        consider_public = sum(1 for r in results if r["recommendation"] == "CONSIDER_PUBLIC")
        neutral_count = sum(1 for r in results if r["recommendation"] == "NEUTRAL")
        
        print("\n" + "="*60)
        print("REPO AUDIT SUMMARY")
        print("="*60)
        print(f"Total repositories analyzed: {len(results)}")
        print(f"🔒 Recommend PRIVATE: {private_count}")
        print(f"🟢 Recommend PUBLIC: {public_count}")
        print(f"⚠️  Consider PRIVATE: {consider_private}")
        print(f"⚠️  Consider PUBLIC: {consider_public}")
        print(f"⚪ Neutral: {neutral_count}")
        
        if private_count > 0:
            print(f"\n🔒 TOP {min(10, private_count)} REPOS TO MAKE PRIVATE:")
            sorted_results = sorted(
                [r for r in results if r["recommendation"] == "PRIVATE"],
                key=lambda x: x["private_score"],
                reverse=True
            )
            for repo in sorted_results[:10]:
                print(f"  {repo['owner']}/{repo['name']} (score: {repo['private_score']}) - {repo['reasons'][:80]}...")


if __name__ == "__main__":
    main()