#!/usr/bin/env python3
"""
commit_extractor.py: Bulk GitHub commit extraction with resumable state.
Usage: python commit_extractor.py --owner toxicwind --output ./commits
"""
import requests, json, os, argparse
from time import sleep
from pathlib import Path

def extract_commits(token, owner, output_dir, per_repo=20):
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"}
    os.makedirs(output_dir, exist_ok=True)
    state_file = os.path.join(output_dir, "_state.json")

    processed = set()
    if os.path.exists(state_file):
        with open(state_file) as f:
            processed = set(json.load(f).get("processed", []))

    all_repos = []
    page = 1
    while True:
        r = requests.get(f"https://api.github.com/user/repos?per_page=100&page={page}&sort=updated", headers=headers, timeout=10)
        if r.status_code != 200: break
        repos = r.json()
        if not repos: break
        all_repos.extend(repos)
        if len(repos) < 100: break
        page += 1

    for repo in all_repos:
        name = repo["full_name"]
        if name in processed: continue
        try:
            r = requests.get(f"https://api.github.com/repos/{name}/commits?per_page={per_repo}", headers=headers, timeout=10)
            if r.status_code == 200:
                with open(os.path.join(output_dir, f"{name.replace('/', '_')}_commits.jsonl"), "w") as f:
                    for c in r.json():
                        f.write(json.dumps(c) + "\n")
            processed.add(name)
        except Exception as e:
            print(f"Error on {name}: {e}")
            processed.add(name)
        sleep(0.15)

    with open(state_file, "w") as f:
        json.dump({"processed": list(processed)}, f)
    print(f"Done: {len(processed)}/{len(all_repos)} repos")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--token", required=True)
    parser.add_argument("--output", default="./commits")
    parser.add_argument("--per-repo", type=int, default=20)
    args = parser.parse_args()
    extract_commits(args.token, "toxicwind", args.output, args.per_repo)
