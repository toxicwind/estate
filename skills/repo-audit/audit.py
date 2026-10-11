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
from typing import List, Dict, Any, Optional

try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False
    print("Warning: pandas not installed, will output CSV only", file=sys.stderr)

try:
    import pyarrow
    HAS_PYARROW = True
except ImportError:
    HAS_PYARROW = False
    print("Warning: pyarrow not installed, Parquet output disabled", file=sys.stderr)


def run_gh_api(args: List[str]) -> str:
    """Run gh api command and return stdout."""
    # gh api uses - flag for parameters
    cmd = ["gh", "api"] + args
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        check=False  # Don't raise exception, handle manually
    )
    if result.returncode != 0:
        print(f"Error running gh api: {result.stderr}", file=sys.stderr)
        # Try without jq if that's the issue
        if "-H" in args or "--header" in args or "-q" in args or "--jq" in args:
            # Remove the jq/header args and retry
            filtered_args = []
            skip_next = False
            for i, arg in enumerate(args):
                if skip_next:
                    skip_next = False
                    continue
                if arg in ["-H", "--header", "-q", "--jq"]:
                    skip_next = True
                    continue
                if arg.startswith("-H") or arg.startswith("--header") or arg.startswith("-q") or arg.startswith("--jq"):
                    continue
                filtered_args.append(arg)
            if filtered_args != args:
                print("Retrying without jq/header parameters...", file=sys.stderr)
                result = subprocess.run(
                    ["gh", "api"] + filtered_args,
                    capture_output=True,
                    text=True,
                    check=False
                )
                if result.returncode == 0:
                    return result.stdout
        raise subprocess.CalledProcessError(result.returncode, cmd, result.stdout, result.stderr)
    return result.stdout


def fetch_repos(user: str, per_page: int = 100) -> List[Dict[str, Any]]:
    """Fetch all repositories for a user/org using gh api with pagination."""
    repos = []
    page = 1
    while True:
        print(f"Fetching page {page}...", end="", flush=True)
        # Build args for gh api
        args = [
            f"/users/{user}/repos",
            f"-H", f"X-GitHub-Per-Page: {per_page}",
            f"-H", f"Page: {page}"
        ]
        try:
            output = run_gh_api(args + ["-q", ".[]"])
        except subprocess.CalledProcessError as e:
            print(f" failed: {e}", file=sys.stderr)
            break
        
        if not output.strip():
            print(" done")
            break
            
        page_data = [json.loads(line) for line in output.strip().split("\n") if line]
        if not page_data:
            print(" done")
            break
        repos.extend(page_data)
        print(f" got {len(page_data)} repos (total: {len(repos)})")
        if len(page_data) < per_page:
            break
        page += 1
    return repos


def fetch_repo_topics(owner: str, repo: str) -> List[str]:
    """Fetch topics for a repository."""
    try:
        output = run_gh_api([
            f"/repos/{owner}/{repo}/topics",
            "-H", "Accept: application/json+git",
            "-q", ".names"
        ])
        if output.strip():
            data = json.loads(output)
            return data if isinstance(data, list) else []
        return []
    except (subprocess.CalledProcessError, json.JSONDecodeError):
        # Topics endpoint might not exist for private repos or if no topics
        return []


def analyze_repo(repo: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze a single repo and determine if it should be private."""
    name = repo["name"].lower()
    description = (repo.get("description") or "").lower()
    topics = [t.lower() for t in fetch_repo_topics(repo["owner"]["login"], repo["name"])]
    
    # Patterns that suggest a repo should be private
    private_indicators = [
        "secret", "token", "key", "credential", "password", "passwd",
        "private", "internal", "confidential", "proprietary", "key",
        "cert", "certificate", "ssh", "gpg", "pem", "p12", "pfx",
        "config", "settings", "env", ".env", "dotenv",
        "cred", "auth", "oauth", "ssl", "tls"
    ]
    
    # Check name and description for indicators
    should_be_private = False
    reasons = []
    
    for indicator in private_indicators:
        if indicator in name:
            should_be_private = True
            reasons.append(f"name contains '{indicator}'")
            break
        if indicator in description:
            should_be_private = True
            reasons.append(f"description contains '{indicator}'")
            break
    
    # Check topics
    for topic in topics:
        if topic in private_indicators:
            should_be_private = True
            reasons.append(f"topic '{topic}'")
            break
    
    # Additional heuristics: if it's a fork, less likely to need privacy
    # but we keep the decision based on patterns
    
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
        "should_be_private": should_be_private,
        "reasons": "; ".join(reasons) if reasons else ""
    }


def main():
    parser = argparse.ArgumentParser(
        description="Audit GitHub repositories and recommend privacy settings"
    )
    parser.add_argument(
        "--user", "-u",
        default=os.environ.get("GH_USER", "toxicwind"),
        help="GitHub username or organization (default: toxicwind or GH_USER)"
    )
    parser.add_argument(
        "--output", "-o",
        default="repo-audit",
        help="Output file basename (default: repo-audit)"
    )
    parser.add_argument(
        "--format", "-f",
        choices=["csv", "parquet", "both"],
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
        "--private-only",
        action="store_true",
        help="Only analyze currently private repositories"
    )
    parser.add_argument(
        "--public-only",
        action="store_true",
        help="Only analyze currently public repositories"
    )
    
    args = parser.parse_args()
    
    print(f"Fetching repositories for {args.user}...")
    repos = fetch_repos(args.user)
    print(f"Total repositories fetched: {len(repos)}")
    
    # Filter by stars
    if args.threshold > 0:
        repos = [r for r in repos if r["stargazers_count"] >= args.threshold]
        print(f"After star threshold (>={args.threshold}): {len(repos)} repos")
    
    # Filter by current visibility
    if args.private_only:
        repos = [r for r in repos if r["private"]]
        print(f"After private-only filter: {len(repos)} repos")
    elif args.public_only:
        repos = [r for r in repos if not r["private"]]
        print(f"After public-only filter: {len(repos)} repos")
    
    # Handle empty results
    if not repos:
        print("No repositories to analyze after filtering.")
        # Create empty output files
        basename = args.output
        if args.format in ["csv", "both"]:
            csv_path = f"{basename}.csv"
            with open(csv_path, 'w') as f:
                f.write("owner,name,visibility,private,should_be_private,reasons,stars,fork,description,topics,html_url\n")
            print(f"Empty CSV output written to: {csv_path}")
        if args.format in ["parquet", "both"] and HAS_PANDAS and HAS_PYARROW:
            parquet_path = f"{basename}.parquet"
            # Create empty DataFrame with correct columns
            df = pd.DataFrame(columns=["owner", "name", "visibility", "private", "should_be_private",
                                      "reasons", "stars", "fork", "description", "topics", "html_url"])
            df.to_parquet(parquet_path, index=False)
            print(f"Empty Parquet output written to: {parquet_path}")
        elif args.format in ["parquet", "both"]:
            print("Parquet output skipped (missing pandas or pyarrow)", file=sys.stderr)
        print("\n=== Summary ===")
        print("Total repositories analyzed: 0")
        print("Public repos that should be private: 0")
        print("Private repos that could be public: 0")
        return
    
    # Analyze each repo
    print("Analyzing repositories...")
    results = []
    for i, repo in enumerate(repos, 1):
        if i % 10 == 0 or i == len(repos):
            print(f"  Progress: {i}/{len(repos)}")
        results.append(analyze_repo(repo))
    
    # Convert to DataFrame if pandas available
    if HAS_PANDAS:
        df = pd.DataFrame(results)
        # Reorder columns for readability
        expected_cols = ["owner", "name", "visibility", "private", "should_be_private",
                        "reasons", "stars", "fork", "description", "topics", "html_url"]
        # Only select columns that exist
        existing_cols = [col for col in expected_cols if col in df.columns]
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
            else:
                # Write header only
                with open(csv_path, 'w', newline='') as f:
                    writer = csv.DictWriter(f, fieldnames=["owner", "name", "visibility", "private", "should_be_private",
                                                          "reasons", "stars", "fork", "description", "topics", "html_url"])
                    writer.writeheader()
        print(f"CSV output written to: {csv_path}")
    
    if args.format in ["parquet", "both"] and HAS_PANDAS and HAS_PYARROW:
        parquet_path = f"{basename}.parquet"
        df.to_parquet(parquet_path, index=False)
        print(f"Parquet output written to: {parquet_path}")
    elif args.format in ["parquet", "both"]:
        print("Parquet output skipped (missing pandas or pyarrow)", file=sys.stderr)
    
    # Print summary
    if HAS_PANDAS and len(df) > 0:
        to_private = df[df["should_be_private"] & (~df["private"])].shape[0] if "should_be_private" in df.columns and "private" in df.columns else 0
        should_public = df[~df["should_be_private"] & df["private"]].shape[0] if "should_be_private" in df.columns and "private" in df.columns else 0
        print("\n=== Summary ===")
        print(f"Total repositories analyzed: {len(df)}")
        print(f"Public repos that should be private: {to_private}")
        print(f"Private repos that could be public: {should_public}")
        if to_private > 0 and "should_be_private" in df.columns and "private" in df.columns:
            print("\nRepos recommended to be made private:")
            for _, row in df[df["should_be_private"] & (~df["private"])].iterrows():
                print(f"  {row['owner']}/{row['name']} - {row.get('reasons', '')}")
    else:
        # Manual summary
        to_private = sum(1 for r in results if r["should_be_private"] and not r["private"])
        should_public = sum(1 for r in results if not r["should_be_private"] and r["private"])
        print("\n=== Summary ===")
        print(f"Total repositories analyzed: {len(results)}")
        print(f"Public repos that should be private: {to_private}")
        print(f"Private repos that could be public: {should_public}")
        if to_private > 0:
            print("\nRepos recommended to be made private:")
            for r in results:
                if r["should_be_private"] and not r["private"]:
                    print(f"  {r['owner']}/{r['name']} - {r['reasons']}")


if __name__ == "__main__":
    main()