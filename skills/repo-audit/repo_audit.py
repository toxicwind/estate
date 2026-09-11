#!/usr/bin/env python3
"""
Repo Audit Skill
Analyzes GitHub repository visibility and identifies anomalies.
"""

import subprocess
import json
import pandas as pd
import argparse
import sys
from typing import List, Dict


def run_gh_api(query: str) -> List[Dict]:
    """Execute gh api command and return parsed JSON."""
    cmd = ["gh", "api"] + query.split()
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Error running gh api: {e.stderr}", file=sys.stderr)
        return []
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON: {e}", file=sys.stderr)
        return []


def fetch_repos(username: str) -> List[Dict]:
    """Fetch all repositories for a user."""
    query = f"users/{username}/repos?per_page=100"
    repos = run_gh_api(query)
    # Handle pagination
    page = 1
    while len(repos) >= 100 and page < 10:  # safety limit
        page += 1
        query = f"users/{username}/repos?per_page=100&page={page}"
        more = run_gh_api(query)
        if not more:
            break
        repos.extend(more)
    return repos


def analyze_repos(repos: List[Dict]) -> pd.DataFrame:
    """Convert repos to DataFrame and add analysis columns."""
    df = pd.DataFrame(repos)
    if df.empty:
        return df
    
    # Ensure required columns exist
    for col in ['name', 'private', 'visibility', 'fork', 'description', 'topics']:
        if col not in df.columns:
            df[col] = None
    
    # Analysis columns
    df['should_be_private'] = False
    df['should_be_public'] = False
    df['anomaly_reason'] = ''
    
    # Heuristics for what should be private
    private_indicators = [
        'private', 'secret', 'key', 'token', 'credential', 'password',
        'internal', 'internal-only', 'infra', 'infrastructure',
        'config', 'configuration', 'keys', 'secrets'
    ]
    
    # Heuristics for what should be public
    public_indicators = [
        'public', 'open', 'source', 'oss', 'library', 'sdk', 'api',
        'demo', 'example', 'tutorial', 'blog', 'website', 'docs',
        'skill', 'skills', 'template', 'boilerplate'
    ]
    
    for idx, row in df.iterrows():
        name_lower = str(row['name']).lower()
        desc_lower = str(row['description'] or '').lower()
        topics = [str(t).lower() for t in (row['topics'] or [])]
        
        # Check if should be private
        if any(ind in name_lower or ind in desc_lower or ind in ' '.join(topics) 
               for ind in private_indicators):
            df.at[idx, 'should_be_private'] = True
            if not row['private']:
                df.at[idx, 'anomaly_reason'] = 'Name/description suggests private but is public'
        
        # Check if should be public
        elif any(ind in name_lower or ind in desc_lower or ind in ' '.join(topics) 
                 for ind in public_indicators):
            df.at[idx, 'should_be_public'] = True
            if row['private']:
                df.at[idx, 'anomaly_reason'] = 'Name/description suggests public but is private'
    
    # Additional heuristics
    # Forks are usually public unless they're internal forks
    df.loc[df['fork'] == True, 'should_be_public'] = True
    
    # Repos with no description might need review
    no_desc = df['description'].isna() | (df['description'] == '')
    df.loc[no_desc & df['private'], 'anomaly_reason'] = df.loc[no_desc & df['private'], 'anomaly_reason'].fillna('') + 'No description; review needed'
    
    return df


def print_report(df: pd.DataFrame):
    """Print audit report."""
    if df.empty:
        print("No repositories found.")
        return
    
    print(f"\n=== GitHub Repository Audit ===")
    print(f"Total repositories: {len(df)}")
    print(f"Public: {len(df[~df['private']])}")
    print(f"Private: {len(df[df['private']])}")
    
    print(f"\n=== Anomalies Detected ===")
    anomalies = df[df['anomaly_reason'] != '']
    if len(anomalies) == 0:
        print("No anomalies detected based on heuristics.")
    else:
        print(f"Found {len(anomalies)} potential anomalies:")
        for _, row in anomalies.iterrows():
            print(f"  - {row['name']}: {row['anomaly_reason']}")
            print(f"    Currently: {'Private' if row['private'] else 'Public'}")
            if row['should_be_private']:
                print(f"    Suggested: Private")
            if row['should_be_public']:
                print(f"    Suggested: Public")
            print()
    
    print(f"\n=== Recommendations ===")
    # Suggest making private
    to_private = df[(df['should_be_private'] == True) & (df['private'] == False)]
    if len(to_private) > 0:
        print(f"Consider making PRIVATE ({len(to_private)} repos):")
        for _, row in to_private.iterrows():
            print(f"  gh api --method PATCH repos/toxicwind/{row['name']} -f private=true")
    
    # Suggest making public
    to_public = df[(df['should_be_public'] == True) & (df['private'] == True)]
    if len(to_public) > 0:
        print(f"Consider making PUBLIC ({len(to_public)} repos):")
        for _, row in to_public.iterrows():
            print(f"  gh api --method PATCH repos/toxicwind/{row['name']} -f private=false")


def main():
    parser = argparse.ArgumentParser(description='Audit GitHub repository visibility')
    parser.add_argument('--user', default='toxicwind', help='GitHub username or org')
    parser.add_argument('--format', choices=['table', 'csv', 'json'], default='table',
                        help='Output format')
    args = parser.parse_args()
    
    print(f"Fetching repositories for {args.user}...")
    repos = fetch_repos(args.user)
    
    if not repos:
        print("No repositories found or error occurred.", file=sys.stderr)
        sys.exit(1)
    
    df = analyze_repos(repos)
    
    if args.format == 'csv':
        print(df.to_csv(index=False))
    elif args.format == 'json':
        print(df.to_json(orient='records', indent=2))
    else:
        print_report(df)


if __name__ == '__main__':
    main()