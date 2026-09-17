#!/usr/bin/env python3
"""
local-audit — Local-First Repository Auditor

Scans all local git repos without GitHub API calls. Builds a pandas DataFrame
with tree hierarchy, identifies duplicates, symlinks, orphans, and recent activity.

Usage:
    python local_audit.py --path /home/toxic/projects
    python local_audit.py --path /home/toxic/sovereign --parquet out.parquet
    python local_audit.py --all --json out.json
"""

import subprocess
import json
import sys
import time
from pathlib import Path
from collections import defaultdict
from typing import List, Dict, Optional
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import argparse


def scan_git_repos(path: str) -> List[Dict]:
    """Scan all .git directories under path and collect metadata."""
    root = Path(path)
    rows = []
    t0 = time.perf_counter()
    
    for d in sorted(root.iterdir()):
        if not d.is_dir():
            continue
        git_dir = d / ".git"
        if not git_dir.exists():
            continue
        
        try:
            r = subprocess.run(
                ["git", "-C", str(d), "log", "-1", "--format=%ci|%s|%H|%an"],
                capture_output=True, text=True, timeout=5,
            )
            if r.returncode == 0:
                parts = r.stdout.strip().split("|")
                last_commit = parts[0] if len(parts) > 0 else ""
                message = parts[1] if len(parts) > 1 else ""
                commit = parts[2] if len(parts) > 2 else ""
                author = parts[3] if len(parts) > 3 else ""
            else:
                last_commit = message = commit = author = ""
        except Exception:
            last_commit = message = commit = author = ""
        
        # Determine area
        abs_path = str(d.resolve())
        if abs_path.startswith("/home/toxic/sovereign/"):
            area = "sovereign"
        elif abs_path.startswith("/home/toxic/projects/"):
            area = "projects"
        else:
            area = "other"
        
        rows.append({
            "name": d.name,
            "path": abs_path,
            "area": area,
            "last_commit": last_commit,
            "message": message,
            "commit": commit[:8] if commit else "",
            "author": author,
        })
    
    elapsed = (time.perf_counter() - t0) * 1000
    print(f"[SCAN] {len(rows)} repos in {elapsed:.0f}ms")
    return rows


def build_dataframe(rows: List[Dict]) -> pd.DataFrame:
    """Build DataFrame with tree hierarchy."""
    df = pd.DataFrame(rows)
    if df.empty:
        return df
    df = df.sort_values("last_commit", ascending=False).reset_index(drop=True)
    return df


def find_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    """Find repos with same name in different areas."""
    if df.empty:
        return pd.DataFrame()
    name_counts = df["name"].value_counts()
    dup_names = name_counts[name_counts > 1].index.tolist()
    return df[df["name"].isin(dup_names)]


def find_orphans(df: pd.DataFrame) -> pd.DataFrame:
    """Find repos with no recent activity (>90 days)."""
    if df.empty:
        return pd.DataFrame()
    from datetime import datetime, timedelta
    cutoff = datetime.now() - timedelta(days=90)
    orphans = df[df["last_commit"].apply(
        lambda x: datetime.strptime(x[:10], "%Y-%m-%d") < cutoff if x else True
    )]
    return orphans.sort_values("last_commit")


def find_symlinks(path: str) -> pd.DataFrame:
    """Find all symlinks under path."""
    root = Path(path)
    rows = []
    for d in sorted(root.iterdir()):
        if d.is_symlink():
            target = str(d.resolve()) if d.exists() else "BROKEN"
            rows.append({
                "name": d.name,
                "path": str(d),
                "target": target,
                "type": "symlink",
            })
    return pd.DataFrame(rows)


def print_tree(df: pd.DataFrame):
    """Print tree hierarchy by area."""
    if df.empty:
        print("No repos found.")
        return
    
    areas = df["area"].unique()
    print(f"\n{'=' * 100}")
    print(f"  LOCAL REPO TREE — {len(df)} repos")
    print(f"{'=' * 100}")
    
    for area in sorted(areas):
        area_df = df[df["area"] == area]
        print(f"\n🌿 {area.upper()} ({len(area_df)} repos)")
        print(f"{'─' * 100}")
        for _, row in area_df.head(20).iterrows():
            commit = row["last_commit"][:19] if row["last_commit"] else "never"
            name = row["name"][:38]
            msg = row["message"][:28]
            print(f"  📁 {name:<40} {commit:<22} {msg}")
    
    print(f"\n{'=' * 100}")


def print_summary(df: pd.DataFrame):
    """Print audit summary."""
    if df.empty:
        return
    
    print(f"\n{'=' * 60}")
    print(f"  SUMMARY")
    print(f"{'=' * 60}")
    print(f"  Total repos: {len(df)}")
    print(f"  Areas: {df['area'].nunique()}")
    for area in sorted(df["area"].unique()):
        count = len(df[df["area"] == area])
        print(f"    {area}: {count}")
    
    # Recent activity (last 7 days)
    from datetime import datetime, timedelta
    cutoff = datetime.now() - timedelta(days=7)
    recent = df[df["last_commit"].apply(
        lambda x: datetime.strptime(x[:10], "%Y-%m-%d") >= cutoff if x else False
    )]
    print(f"  Recently pushed (<7d): {len(recent)}")
    
    # Stale (>90d)
    stale = find_orphans(df)
    print(f"  Stale (>90d): {len(stale)}")
    
    # Symlinks
    symlinks = find_symlinks("/home/toxic/projects")
    if not symlinks.empty:
        print(f"  Symlinks: {len(symlinks)}")
        for _, s in symlinks.iterrows():
            status = "✅" if s["target"] != "BROKEN" else "❌"
            print(f"    {status} {s['name']} -> {s['target'][:50]}")
    
    print(f"{'=' * 60}\n")


def main():
    parser = argparse.ArgumentParser(prog="local-audit", description="Local-First Repository Auditor")
    parser.add_argument("--path", default="/home/toxic/projects", help="Path to scan")
    parser.add_argument("--all", action="store_true", help="Scan both projects and sovereign")
    parser.add_argument("--format", choices=["table", "csv", "json", "parquet"], default="table")
    parser.add_argument("--parquet", default="local-repos.parquet", help="Parquet output path")
    parser.add_argument("--csv", default="local-repos.csv", help="CSV output path")
    parser.add_argument("--json", default="local-repos.json", help="JSON output path")
    parser.add_argument("--duplicates", action="store_true", help="Show duplicates")
    parser.add_argument("--orphans", action="store_true", help="Show stale repos")
    parser.add_argument("--stream", action="store_true", help="Enable streaming output")
    args = parser.parse_args()

    paths = ["/home/toxic/projects", "/home/toxic/sovereign"] if args.all else [args.path]
    
    all_rows = []
    for p in paths:
        print(f"[SCAN] Scanning {p}...")
        all_rows.extend(scan_git_repos(p))
    
    df = build_dataframe(all_rows)
    print_tree(df)
    print_summary(df)
    
    # Show duplicates if requested
    if args.duplicates:
        dups = find_duplicates(df)
        if not dups.empty:
            print(f"\n🔍 DUPLICATES ({len(dups)}):")
            for name in dups["name"].unique():
                dupes = dups[dups["name"] == name]
                print(f"  {name}: {len(dupes)} copies")
                for _, r in dupes.iterrows():
                    print(f"    {r['area']}: {r['path']}")
    
    # Show orphans if requested
    if args.orphans:
        stale = find_orphans(df)
        if not stale.empty:
            print(f"\n⚠️  STALE REPOS ({len(stale)}):")
            for _, r in stale.head(20).iterrows():
                print(f"  {r['name']}: last commit {r['last_commit'][:19]}")
    
    # Export
    if args.format == "parquet" or args.parquet:
        table = pa.Table.from_pandas(df)
        pq.write_table(table, args.parquet)
        print(f"[EXPORT] Parquet: {args.parquet} ({len(df)} rows)")
    if args.format == "csv" or args.csv:
        df.to_csv(args.csv, index=False)
        print(f"[EXPORT] CSV: {args.csv}")
    if args.format == "json" or args.json:
        df.to_json(args.json, orient="records", indent=2)
        print(f"[EXPORT] JSON: {args.json}")
    
    return df


if __name__ == "__main__":
    main()
