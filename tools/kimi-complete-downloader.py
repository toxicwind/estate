#!/usr/bin/env python3
"""
kimi_complete_downloader.py - Complete Kimi file downloader with project discovery.
Fetches from API (projects + feeds) and parses all local HAR files.
Organizes by project name and chat ID.
"""

import argparse
import hashlib
import json
import os
import re
import sys
import urllib.request
import urllib.error
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
from urllib.parse import unquote, urlparse

# ── CONFIG ───────────────────────────────────────────────────────────────────
DEFAULT_JWT = "eyJhbGciOiJIUzUxMiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJ1c2VyLWNlbnRlciIsImV4cCI6MTc4NjkzOTUxMiwiaWF0IjoxNzg0MzQ3NTEyLCJqdGkiOiJkOWRmbXUyZTBtN2ZvZmppMnBoZyIsInR5cCI6ImFjY2VzcyIsImFwcF9pZCI6ImtpbWkiLCJzdWIiOiJkODdicjJvaDhuamtyOTBqZjUyMCIsInNwYWNlX2lkIjoiZDg3YnIyZ2g4bmprcjkwamU5N2ciLCJhYnN0cmFjdF91c2VyX2lkIjoiZDg3YnIyZ2g4bmprcjkwamU5NzAiLCJzc2lkIjoiMTczMTczNzQxMDg0MjU0NzAzMyIsImRldmljZV9pZCI6Ijc2NTI1NTE1ODg3MzY4MDcxODMiLCJyZWdpb24iOiJvdmVyc2VhcyIsIm1lbWJlcnNoaXAiOnsibGV2ZWwiOjEwfX0.-9-OczLe8Ghkb28wYdTQSFb-UHZW0hxaByfVEZU-Dsc9zWWcMdyAPWK3v5ZrQAz8BIg4om89-VODnXDyT7RPMw"

BASE_API = "https://www.kimi.com/apiv2"
DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:155.0) Gecko/20100101 Firefox/155.0",
    "Accept": "*/*",
    "Accept-Language": "en",
    "authorization": f"Bearer {DEFAULT_JWT}",
    "connect-protocol-version": "1",
    "content-type": "application/json",
    "r-timezone": "Atlantic/Reykjavik",
    "x-language": "en-US",
    "x-msh-device-id": "7652551588736807183",
    "x-msh-platform": "web",
    "x-msh-session-id": "1731737410842547033",
    "x-msh-version": "2.0.0",
    "x-traffic-id": "d87br2oh8njkr90jf520",
}

CHUNK_SIZE = 65536
MAX_WORKERS = 8
TIMEOUT = 60

# ── HAR DISCOVERY ────────────────────────────────────────────────────────────
def find_all_hars() -> List[str]:
    """Find all Kimi HAR files in common locations."""
    search_paths = [
        "/home/toxic",
        "/home/toxic/Documents",
        "/home/toxic/Downloads",
        "/home/toxic/Downloads/mnt_agents/upload",
    ]
    har_files = []
    for base in search_paths:
        if not os.path.exists(base):
            print(f"[DEBUG] Search path does not exist: {base}")
            continue
        print(f"[DEBUG] Walking: {base}")
        for root, dirs, files in os.walk(base):
            for f in files:
                if "kimi.com" in f and ("har" in f.lower() or f.endswith(".har") or f.endswith(".har.txt") or f.endswith(".har.pdf")):
                    full = os.path.join(root, f)
                    har_files.append(full)
                    print(f"[DEBUG] Found HAR: {full}")
    result = sorted(set(har_files))
    print(f"[DEBUG] Total HAR files found: {len(result)}")
    return result


def extract_urls_from_har(har_path: str) -> Set[Tuple[str, str, str]]:
    """Parse HAR and extract (filename, signUrl, checksum) from all entries."""
    files = set()
    try:
        with open(har_path, "r", encoding="utf-8", errors="ignore") as f:
            data = json.load(f)
    except Exception as e:
        print(f"[!] Failed to parse HAR {har_path}: {e}")
        return files

    entries = data.get("log", {}).get("entries", [])

    for entry in entries:
        content = entry.get("response", {}).get("content", {}).get("text", "")
        if not content:
            continue

        # Find all file objects with signUrl
        for m in re.finditer(r'signUrl["\s:=]+([^"\s,}]+)', content):
            url = m.group(1).rstrip('",}')
            ctx_start = max(0, m.start() - 500)
            ctx_end = min(len(content), m.end() + 500)
            ctx = content[ctx_start:ctx_end]

            fname = "unknown"
            checksum = ""

            fn_match = re.search(r'filename["\s:=]+([^"\s,}]+)', ctx)
            if fn_match:
                fname = fn_match.group(1).rstrip('",}')

            cs_match = re.search(r'checksum["\s:=]+([^"\s,}]+)', ctx)
            if cs_match:
                checksum = cs_match.group(1).rstrip('",}')

            files.add((fname, url, checksum))

    print(f"[*] HAR {Path(har_path).name}: {len(files)} files")
    return files


# ── API CLIENT ───────────────────────────────────────────────────────────────
def api_request(endpoint: str, body: dict, jwt: str = DEFAULT_JWT) -> dict:
    """Make a Connect-RPC POST request."""
    url = f"{BASE_API}/{endpoint}"
    headers = dict(DEFAULT_HEADERS)
    headers["authorization"] = f"Bearer {jwt}"

    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode(),
        headers=headers,
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            return json.loads(resp.read().decode())
    except Exception as e:
        return {"_error": str(e)}


def fetch_all_projects(jwt: str = DEFAULT_JWT) -> List[dict]:
    """Fetch all projects."""
    body = {"page_size": 100, "include_pinned": True}
    resp = api_request("kimi.gateway.project.v1.ProjectService/ListProjects", body, jwt)
    return resp.get("projects", [])


def fetch_project_files(project_id: str, jwt: str = DEFAULT_JWT) -> List[dict]:
    """Fetch all files for a project (handles pagination)."""
    all_files = []
    page_token = ""
    while True:
        body = {"project_id": project_id, "page_size": 100}
        if page_token:
            body["page_token"] = page_token
        resp = api_request("kimi.gateway.project.v1.ProjectService/ListProjectFiles", body, jwt)
        files = resp.get("files", [])
        all_files.extend(files)
        page_token = resp.get("nextPageToken", "")
        if not page_token:
            break
    return all_files


def fetch_all_feeds(jwt: str = DEFAULT_JWT) -> List[dict]:
    """Paginate through ListFeeds and return all chat items with files."""
    all_items = []
    page_token = ""
    page = 0
    while True:
        body = {
            "page_size": 50,
            "project_id": "",
            "filter_types": ["FEED_TYPE_CHAT", "FEED_TYPE_TASK"],
            "include_pinned": False,
        }
        if page_token:
            body["page_token"] = page_token
        resp = api_request("kimi.gateway.feed.v1.FeedService/ListFeeds", body, jwt)
        items = resp.get("items", [])
        if not items:
            break
        all_items.extend(items)
        page += 1
        print(f"[*] Feed page {page}: +{len(items)} items (total {len(all_items)})")
        page_token = resp.get("nextPageToken", "")
        if not page_token:
            break
    return all_items


# ── FILE EXTRACTION ──────────────────────────────────────────────────────────
def extract_project_files(projects: List[dict], jwt: str) -> Dict[str, List[Tuple[str, str, str, str]]]:
    """Extract (project_name, rel_path, url, checksum) for all project files."""
    result = {}  # project_name -> list of (rel_path, url, checksum, size)
    for proj in projects:
        pid = proj["id"]
        name = proj["name"]
        print(f"[*] Fetching files for project: {name} ({pid})")
        files = fetch_project_files(pid, jwt)
        result[name] = []
        for f in files:
            if f.get("isDir"):
                continue
            rel_path = f.get("path", f.get("name", "unknown"))
            url = f.get("url", "")
            size = f.get("size", "")
            # Extract checksum from URL if present
            checksum = ""
            cs_match = re.search(r'checksum=([^&]+)', url)
            if cs_match:
                checksum = unquote(cs_match.group(1))
            result[name].append((rel_path, url, checksum, size))
        print(f"    -> {len(result[name])} files")
    return result


def extract_feed_files(feed_items: List[dict]) -> Dict[str, List[Tuple[str, str, str]]]:
    """Extract (chat_id, filename, signUrl, checksum) from feed items."""
    result = {}  # chat_id -> list of (filename, url, checksum)
    for item in feed_items:
        chat = item.get("chat", {})
        chat_id = chat.get("id", "unknown")[:12]
        files = chat.get("files", [])
        if not files:
            continue
        result[chat_id] = []
        for f in files:
            meta = f.get("meta", {})
            blob = f.get("blob", {})
            name = meta.get("name", "unknown")
            sign = blob.get("signUrl", "")
            checksum = meta.get("checksum", "")
            if sign:
                result[chat_id].append((name, sign, checksum))
        print(f"[*] Chat {chat_id}: {len(result[chat_id])} files")
    return result


# ── DOWNLOADER ───────────────────────────────────────────────────────────────
def is_valid_url(url: str) -> bool:
    """Check if URL is a valid HTTP/HTTPS URL."""
    if not url or not isinstance(url, str):
        return False
    # Skip javascript code snippets, null patterns, etc.
    if any(bad in url for bad in ["null===", "file.preview", "void 0", "javascript:", "$signUrl", "$blob"]):
        return False
    # Must be a proper HTTP URL
    return url.startswith("http://") or url.startswith("https://")


def download_file(url: str, out_path: Path, checksum: str = "", headers: dict = None) -> dict:
    """Download a single file with resume support and checksum verify."""
    result = {"url": url, "path": str(out_path), "status": "ok", "bytes": 0, "error": None}

    # Validate URL first
    if not is_valid_url(url):
        result["status"] = "skipped (invalid url)"
        result["error"] = f"invalid url: {url[:80]}"
        return result

    # Skip if exists and checksum matches
    if out_path.exists() and checksum:
        try:
            existing = hashlib.sha256(out_path.read_bytes()).hexdigest()
            if existing.lower() == checksum.lower():
                result["status"] = "skipped (checksum match)"
                return result
        except:
            pass

    try:
        req_headers = {"User-Agent": DEFAULT_HEADERS["User-Agent"]}
        if headers:
            req_headers.update(headers)
        req = urllib.request.Request(url, headers=req_headers)
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            out_path.parent.mkdir(parents=True, exist_ok=True)
            with open(out_path, "wb") as f:
                while True:
                    chunk = resp.read(CHUNK_SIZE)
                    if not chunk:
                        break
                    f.write(chunk)
                    result["bytes"] += len(chunk)

        # Verify checksum if provided
        if checksum:
            downloaded = hashlib.sha256(out_path.read_bytes()).hexdigest()
            if downloaded.lower() != checksum.lower():
                result["status"] = "checksum mismatch"
                result["error"] = f"expected {checksum[:16]}... got {downloaded[:16]}..."

    except urllib.error.HTTPError as e:
        result["status"] = "error"
        result["error"] = f"HTTP {e.code}: {e.reason}"
    except urllib.error.URLError as e:
        result["status"] = "error"
        result["error"] = f"URL error: {e.reason}"
    except Exception as e:
        result["status"] = "error"
        result["error"] = str(e)

    return result


def sanitize_filename(name: str, max_len: int = 128) -> str:
    """Sanitize filename for filesystem."""
    name = re.sub(r'[<>:"/\\|?*]', "_", name)
    name = name.strip(". ")
    if len(name) > max_len:
        name = name[:max_len]
    return name or "unknown"


def download_project_files(project_name: str, files: List[Tuple[str, str, str, str]], output_dir: Path, max_workers: int):
    """Download all files for a project preserving folder structure."""
    proj_dir = output_dir / "projects" / sanitize_filename(project_name)
    proj_dir.mkdir(parents=True, exist_ok=True)

    total = len(files)
    completed = 0
    errors = 0
    skipped = 0
    total_bytes = 0

    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        futures = {}
        for rel_path, url, checksum, size in files:
            if not url:
                continue
            # Preserve folder structure
            safe_path = Path(*[sanitize_filename(p) for p in Path(rel_path).parts])
            out_path = proj_dir / safe_path
            # Handle duplicates
            counter = 1
            orig = out_path
            while out_path in {f[1] for f in futures.items()}:
                stem = orig.stem
                suffix = orig.suffix
                out_path = orig.parent / f"{stem}_{counter}{suffix}"
                counter += 1

            fut = ex.submit(download_file, url, out_path, checksum)
            futures[fut] = (url, rel_path)

        for fut in as_completed(futures):
            url, rel_path = futures[fut]
            try:
                res = fut.result()
                completed += 1
                if res["status"] == "ok":
                    total_bytes += res["bytes"]
                    print(f"[{completed}/{total}] OK {res['bytes']//1024}KB {project_name}/{rel_path[:60]}")
                elif "skipped" in res["status"]:
                    skipped += 1
                    print(f"[{completed}/{total}] SKIP {project_name}/{rel_path[:60]}")
                else:
                    errors += 1
                    print(f"[{completed}/{total}] ERR {res['status']} {project_name}/{rel_path[:60]} {res.get('error','')[:60]}")
            except Exception as e:
                errors += 1
                print(f"[{completed}/{total}] FATAL {project_name}/{rel_path[:60]} {e}")

    return completed, skipped, errors, total_bytes


def download_chat_files(chat_id: str, files: List[Tuple[str, str, str]], output_dir: Path, max_workers: int):
    """Download all files for a chat."""
    chat_dir = output_dir / "chats" / sanitize_filename(chat_id)
    chat_dir.mkdir(parents=True, exist_ok=True)

    total = len(files)
    completed = 0
    errors = 0
    skipped = 0
    total_bytes = 0

    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        futures = {}
        for name, url, checksum in files:
            if not url:
                continue
            safe_name = sanitize_filename(name)
            out_path = chat_dir / safe_name
            # Handle duplicates by appending checksum
            counter = 1
            orig = out_path
            while out_path in {f[1] for f in futures.items()}:
                stem = orig.stem
                suffix = orig.suffix
                out_path = orig.parent / f"{stem}_{checksum[:8]}{suffix}"
                counter += 1

            fut = ex.submit(download_file, url, out_path, checksum)
            futures[fut] = (url, name)

        for fut in as_completed(futures):
            url, name = futures[fut]
            try:
                res = fut.result()
                completed += 1
                if res["status"] == "ok":
                    total_bytes += res["bytes"]
                    print(f"[{completed}/{total}] OK {res['bytes']//1024}KB {chat_id}/{name[:60]}")
                elif "skipped" in res["status"]:
                    skipped += 1
                    print(f"[{completed}/{total}] SKIP {chat_id}/{name[:60]}")
                else:
                    errors += 1
                    print(f"[{completed}/{total}] ERR {res['status']} {chat_id}/{name[:60]} {res.get('error','')[:60]}")
            except Exception as e:
                errors += 1
                print(f"[{completed}/{total}] FATAL {chat_id}/{name[:60]} {e}")

    return completed, skipped, errors, total_bytes


def download_har_files(har_files: Set[Tuple[str, str, str]], output_dir: Path, max_workers: int):
    """Download files extracted from HARs (unorganized)."""
    har_dir = output_dir / "har_extracted"
    har_dir.mkdir(parents=True, exist_ok=True)

    total = len(har_files)
    completed = 0
    errors = 0
    skipped = 0
    total_bytes = 0

    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        futures = {}
        for name, url, checksum in har_files:
            if not url:
                continue
            safe_name = sanitize_filename(name)
            out_path = har_dir / safe_name
            counter = 1
            orig = out_path
            while out_path in {f[1] for f in futures.items()}:
                stem = orig.stem
                suffix = orig.suffix
                out_path = orig.parent / f"{stem}_{checksum[:8]}{suffix}"
                counter += 1

            fut = ex.submit(download_file, url, out_path, checksum)
            futures[fut] = (url, name)

        for fut in as_completed(futures):
            url, name = futures[fut]
            try:
                res = fut.result()
                completed += 1
                if res["status"] == "ok":
                    total_bytes += res["bytes"]
                    print(f"[{completed}/{total}] OK {res['bytes']//1024}KB har/{name[:60]}")
                elif "skipped" in res["status"]:
                    skipped += 1
                    print(f"[{completed}/{total}] SKIP har/{name[:60]}")
                else:
                    errors += 1
                    print(f"[{completed}/{total}] ERR {res['status']} har/{name[:60]} {res.get('error','')[:60]}")
            except Exception as e:
                errors += 1
                print(f"[{completed}/{total}] FATAL har/{name[:60]} {e}")

    return completed, skipped, errors, total_bytes


# ── MAIN ─────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="Complete Kimi File Downloader")
    parser.add_argument("--jwt", default=DEFAULT_JWT, help="JWT token")
    parser.add_argument("--output", default="./kimi_complete", help="Output directory")
    parser.add_argument("--workers", type=int, default=MAX_WORKERS, help="Concurrent downloads")
    parser.add_argument("--no-api", action="store_true", help="Skip API calls, only use HARs")
    parser.add_argument("--no-har", action="store_true", help="Skip HAR parsing, only use API")
    parser.add_argument("--list-only", action="store_true", help="Only list what would be downloaded")
    args = parser.parse_args()

    out_dir = Path(args.output)
    out_dir.mkdir(parents=True, exist_ok=True)

    all_stats = {"completed": 0, "skipped": 0, "errors": 0, "bytes": 0}

    # 1. API: Projects + Files
    if not args.no_api:
        print("\n=== FETCHING PROJECTS FROM API ===")
        projects = fetch_all_projects(args.jwt)
        print(f"[*] Found {len(projects)} projects")

        project_files = extract_project_files(projects, args.jwt)

        if args.list_only:
            for pname, files in project_files.items():
                print(f"\nProject: {pname}")
                for rel_path, url, checksum, size in files:
                    print(f"  {rel_path} -> {url[:80]}... (checksum: {checksum[:16]}...)")
        else:
            for pname, files in project_files.items():
                c, s, e, b = download_project_files(pname, files, out_dir, args.workers)
                all_stats["completed"] += c
                all_stats["skipped"] += s
                all_stats["errors"] += e
                all_stats["bytes"] += b

        print("\n=== FETCHING CHAT FILES FROM FEEDS ===")
        feed_items = fetch_all_feeds(args.jwt)
        chat_files = extract_feed_files(feed_items)

        if args.list_only:
            for cid, files in chat_files.items():
                print(f"\nChat: {cid}")
                for name, url, checksum in files:
                    print(f"  {name} -> {url[:80]}... (checksum: {checksum[:16]}...)")
        else:
            for cid, files in chat_files.items():
                c, s, e, b = download_chat_files(cid, files, out_dir, args.workers)
                all_stats["completed"] += c
                all_stats["skipped"] += s
                all_stats["errors"] += e
                all_stats["bytes"] += b

    # 2. HAR files
    if not args.no_har:
        print("\n=== PARSING LOCAL HAR FILES ===")
        har_paths = find_all_hars()
        print(f"[*] Found {len(har_paths)} HAR files")

        all_har_files = set()
        for har_path in har_paths:
            har_files = extract_urls_from_har(har_path)
            all_har_files.update(har_files)

        print(f"[*] Total unique files from HARs: {len(all_har_files)}")

        if args.list_only:
            for name, url, checksum in sorted(all_har_files):
                print(f"  {name} -> {url[:80]}... (checksum: {checksum[:16]}...)")
        else:
            c, s, e, b = download_har_files(all_har_files, out_dir, args.workers)
            all_stats["completed"] += c
            all_stats["skipped"] += s
            all_stats["errors"] += e
            all_stats["bytes"] += b

    # Summary
    print(f"\n{'='*60}")
    print(f"SUMMARY")
    print(f"{'='*60}")
    print(f"Completed: {all_stats['completed']}")
    print(f"Skipped:   {all_stats['skipped']}")
    print(f"Errors:    {all_stats['errors']}")
    print(f"Downloaded: {all_stats['bytes'] / 1024 / 1024:.1f} MB")
    print(f"Output:    {out_dir.absolute()}")


if __name__ == "__main__":
    main()