#!/usr/bin/env python3
"""
kimi_fast_downloader.py - High-performance Kimi downloader with:
- HAR-based project/chat discovery
- Live API for fresh signed URLs
- Checksum-based deduplication (global)
- Connection pooling + streaming
- Rate-limit aware with exponential backoff
- Resume support via state file
- Progress tracking
"""

import argparse
import hashlib
import json
import os
import re
import sys
import time
import urllib.request
import urllib.error
import urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
from collections import defaultdict
from dataclasses import dataclass, asdict
import threading

# ── CONFIG ───────────────────────────────────────────────────────────────────
DEFAULT_JWT = "eyJhbGciOiJIUzUxMiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJ1c2VyLWNlbnRlciIsImV4cCI6MTc4NjkzOTUxMiwiaWF0IjoxNzg0MzQ3NTEyLCJqdGkiOiJkOWRmbXUyZTBtN2ZvZmppMnBoZyIsInR5cCI6ImFjY2VzcyIsImFwcF9pZCI6ImtpbWkiLCJzdWIiOiJkODdicjJvaDhuamtyOTBqZjUyMCIsInNwYWNlX2lkIjoiZDg3YnIyZ2g4bmprcjkwamU5N2ciLCJhYnN0cmFjdF91c2VyX2lkIjoiZDg3YnIyZ2g4bmprcjkwamU5NzAiLCJzc2lkIjoiMTczMTczNzQxMDg0MjU0NzAzMyIsImRldmljZV9pZCI6Ijc2NTI1NTE1ODg3MzY4MDcxODMiLCJyZWdpb24iOiJvdmVyc2VhcyIsIm1lbWJlcnNoaXAiOnsibGV2ZWwiOjEwfX0.-9-OczLe8Ghkb28wYdTQSFb-UHZW0hxaByfVEZU-Dsc9zWWcMdyAPWK3v5ZrQAz8BIg4om89-VODnXDyT7RPMw"

BASE_API = "https://www.kimi.com/apiv2"
BASE_FILES = "https://www.kimi.com/apiv2-files"

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

CHUNK_SIZE = 1024 * 1024  # 1MB chunks
MAX_WORKERS = 16
TIMEOUT = 60
STATE_FILE = "kimi_download_state.json"
RATE_LIMIT_DELAY = 0.1  # base delay between requests
MAX_RETRIES = 3

# ── DATA CLASSES ─────────────────────────────────────────────────────────────
@dataclass
class FileRecord:
    """Single file to download with all metadata."""
    checksum: str
    name: str
    url: str
    source: str  # "project:new", "chat:19ff784b", "har"
    size: int = 0
    rel_path: str = ""

    def __hash__(self):
        return hash(self.checksum)

    def __eq__(self, other):
        return isinstance(other, FileRecord) and self.checksum == other.checksum


@dataclass
class DownloadState:
    """Persistent download state for resume."""
    completed_checksums: Set[str]
    failed_checksums: Dict[str, int]  # checksum -> failure count
    total_bytes: int
    started_at: float

    @classmethod
    def load(cls, path: Path) -> "DownloadState":
        if path.exists():
            try:
                data = json.loads(path.read_text())
                return cls(
                    completed_checksums=set(data.get("completed", [])),
                    failed_checksums=data.get("failed", {}),
                    total_bytes=data.get("total_bytes", 0),
                    started_at=data.get("started_at", time.time()),
                )
            except:
                pass
        return cls(set(), {}, 0, time.time())

    def save(self, path: Path):
        data = {
            "completed": list(self.completed_checksums),
            "failed": self.failed_checksums,
            "total_bytes": self.total_bytes,
            "started_at": self.started_at,
        }
        path.write_text(json.dumps(data))


# ── RATE LIMITER ─────────────────────────────────────────────────────────────
class RateLimiter:
    """Token bucket rate limiter with exponential backoff on 429."""
    def __init__(self, base_delay: float = 0.1):
        self.base_delay = base_delay
        self.current_delay = base_delay
        self.last_request = 0
        self.lock = threading.Lock()

    def wait(self):
        with self.lock:
            elapsed = time.time() - self.last_request
            if elapsed < self.current_delay:
                time.sleep(self.current_delay - elapsed)
            self.last_request = time.time()

    def success(self):
        with self.lock:
            self.current_delay = max(self.base_delay, self.current_delay * 0.9)

    def rate_limited(self):
        with self.lock:
            self.current_delay = min(30.0, self.current_delay * 2)

    def error(self):
        with self.lock:
            self.current_delay = min(30.0, self.current_delay * 1.5)


# ── API CLIENT ───────────────────────────────────────────────────────────────
class KimiAPI:
    def __init__(self, jwt: str, rate_limiter: RateLimiter):
        self.jwt = jwt
        self.rate_limiter = rate_limiter
        self.session_headers = dict(DEFAULT_HEADERS)
        self.session_headers["authorization"] = f"Bearer {jwt}"

    def _request(self, endpoint: str, body: dict) -> dict:
        url = f"{BASE_API}/{endpoint}"
        headers = dict(self.session_headers)

        for attempt in range(MAX_RETRIES):
            self.rate_limiter.wait()
            req = urllib.request.Request(
                url, data=json.dumps(body).encode(), headers=headers, method="POST"
            )
            try:
                with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
                    self.rate_limiter.success()
                    return json.loads(resp.read().decode())
            except urllib.error.HTTPError as e:
                if e.code == 429:
                    self.rate_limiter.rate_limited()
                    time.sleep(self.rate_limiter.current_delay)
                    continue
                elif e.code >= 500:
                    self.rate_limiter.error()
                    time.sleep(self.rate_limiter.current_delay)
                    continue
                else:
                    return {"_error": f"HTTP {e.code}: {e.reason}"}
            except Exception as e:
                self.rate_limiter.error()
                if attempt == MAX_RETRIES - 1:
                    return {"_error": str(e)}
                time.sleep(self.rate_limiter.current_delay)
        return {"_error": "max retries exceeded"}

    def list_projects(self) -> List[dict]:
        return self._request("kimi.gateway.project.v1.ProjectService/ListProjects", 
                            {"page_size": 100, "include_pinned": True}).get("projects", [])

    def list_project_files(self, project_id: str, path: str = "") -> List[dict]:
        """Recursively list all files under a project directory tree."""
        all_files = []
        dirs = [path]  # dirs to recurse, '' = root
        visited = set()
        while dirs:
            cur = dirs.pop(0)
            if cur in visited:
                continue
            visited.add(cur)
            page_token = ""
            while True:
                body = {"project_id": project_id, "page_size": 100}
                if cur:
                    body["path"] = cur
                if page_token:
                    body["page_token"] = page_token
                resp = self._request("kimi.gateway.project.v1.ProjectService/ListProjectFiles", body)
                files = resp.get("files", [])
                for f in files:
                    if f.get("isDir"):
                        sub = f.get("path")
                        if sub and sub not in visited:
                            dirs.append(sub)
                    else:
                        all_files.append(f)
                page_token = resp.get("nextPageToken", "")
                if not page_token:
                    break
        return all_files

    def list_feeds(self) -> List[dict]:
        all_items = []
        page_token = ""
        while True:
            body = {
                "page_size": 50,
                "project_id": "",
                "filter_types": ["FEED_TYPE_CHAT", "FEED_TYPE_TASK"],
                "include_pinned": False,
            }
            if page_token:
                body["page_token"] = page_token
            resp = self._request("kimi.gateway.feed.v1.FeedService/ListFeeds", body)
            items = resp.get("items", [])
            if not items:
                break
            all_items.extend(items)
            page_token = resp.get("nextPageToken", "")
            if not page_token:
                break
        return all_items


# ── HAR PARSER ───────────────────────────────────────────────────────────────
def find_all_hars() -> List[str]:
    # NOTE: never os.walk('/home/toxic') recursively - that traverses millions of files.
    # Only scandir the specific dirs where kimi HARs actually live (shallow).
    search_paths = ["/home/toxic", "/home/toxic/Documents", "/home/toxic/Downloads", 
                    "/home/toxic/Downloads/mnt_agents/upload"]
    har_files = []
    seen = set()
    for base in search_paths:
        if not os.path.isdir(base):
            continue
        try:
            with os.scandir(base) as it:
                for entry in it:
                    if not entry.is_file():
                        continue
                    f = entry.name
                    if "kimi.com" in f and ("har" in f.lower() or f.endswith((".har", ".har.txt", ".har.pdf"))):
                        p = entry.path
                        if p not in seen:
                            seen.add(p)
                            har_files.append(p)
        except OSError:
            continue
    return sorted(har_files)


def parse_har_for_structure(har_path: str) -> Tuple[Dict[str, List[FileRecord]], Dict[str, List[FileRecord]]]:
    """Parse HAR to extract project and chat file structures."""
    try:
        with open(har_path, "r", encoding="utf-8", errors="ignore") as f:
            data = json.load(f)
    except:
        return {}, {}

    entries = data.get("log", {}).get("entries", [])
    project_files = defaultdict(list)
    chat_files = defaultdict(list)

    for entry in entries:
        url = entry.get("request", {}).get("url", "")
        content = entry.get("response", {}).get("content", {}).get("text", "")
        if not content:
            continue

        # Project files
        if "ListProjectFiles" in url:
            try:
                resp = json.loads(content)
                for f in resp.get("files", []):
                    if f.get("isDir"):
                        continue
                    name = f.get("name", "unknown")
                    path = f.get("path", name)
                    download_url = f.get("url", "")
                    checksum_match = re.search(r"checksum=([^&]+)", download_url)
                    checksum = urllib.parse.unquote(checksum_match.group(1)) if checksum_match else hashlib.sha256(name.encode()).hexdigest()[:32]
                    project_files["new"].append(FileRecord(
                        checksum=checksum, name=name, url=download_url,
                        source="project:new", size=int(f.get("size", 0)), rel_path=path
                    ))
            except:
                pass

        # Chat files from feeds
        if "ListFeeds" in url:
            try:
                resp = json.loads(content)
                for item in resp.get("items", []):
                    chat = item.get("chat", {})
                    chat_id = chat.get("id", "unknown")[:12]
                    for f in chat.get("files", []):
                        meta = f.get("meta", {})
                        blob = f.get("blob", {})
                        name = meta.get("name", "unknown")
                        sign = blob.get("signUrl", "")
                        checksum = meta.get("checksum", hashlib.sha256(name.encode()).hexdigest()[:32])
                        if sign:
                            chat_files[chat_id].append(FileRecord(
                                checksum=checksum, name=name, url=sign,
                                source=f"chat:{chat_id}", size=0, rel_path=name
                            ))
            except:
                pass

    return dict(project_files), dict(chat_files)


# ── DOWNLOADER ───────────────────────────────────────────────────────────────
def download_file(url: str, out_path: Path, checksum: str, rate_limiter: RateLimiter) -> Tuple[bool, int, str]:
    """Download single file with streaming, returns (success, bytes, error)."""
    if out_path.exists() and checksum:
        try:
            if hashlib.sha256(out_path.read_bytes()).hexdigest().lower() == checksum.lower():
                return True, 0, "skipped"
        except:
            pass

    # Strip preview=1 (har preview URLs) to get full download links
    cleaned_url = url
    if "preview=1" in url:
        parsed = urllib.parse.urlparse(url)
        qs = urllib.parse.parse_qsl(parsed.query)
        qs = [(k, v) for k, v in qs if k != "preview"]
        cleaned_url = urllib.parse.urlunparse(parsed._replace(query=urllib.parse.urlencode(qs)))
        url = cleaned_url

    for attempt in range(MAX_RETRIES):
        rate_limiter.wait()
        req = urllib.request.Request(url, headers={"User-Agent": DEFAULT_HEADERS["User-Agent"]})
        try:
            with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
                rate_limiter.success()
                out_path.parent.mkdir(parents=True, exist_ok=True)
                bytes_written = 0
                with open(out_path, "wb") as f:
                    while True:
                        chunk = resp.read(CHUNK_SIZE)
                        if not chunk:
                            break
                        f.write(chunk)
                        bytes_written += len(chunk)

                if checksum:
                    downloaded = hashlib.sha256(out_path.read_bytes()).hexdigest()
                    if downloaded.lower() != checksum.lower():
                        # Don't delete: HAR checksums are name-based (weak), keep file
                        return True, bytes_written, f"checksum mismatch (kept): expected {checksum[:16]}, got {downloaded[:16]}"
                return True, bytes_written, "ok"
        except urllib.error.HTTPError as e:
            if e.code == 429:
                rate_limiter.rate_limited()
                time.sleep(rate_limiter.current_delay)
                continue
            elif e.code == 400:
                return False, 0, f"HTTP 400: expired signature"
            elif e.code >= 500:
                rate_limiter.error()
                time.sleep(rate_limiter.current_delay)
                continue
            return False, 0, f"HTTP {e.code}: {e.reason}"
        except Exception as e:
            rate_limiter.error()
            if attempt == MAX_RETRIES - 1:
                return False, 0, str(e)
            time.sleep(rate_limiter.current_delay)
    return False, 0, "max retries"


def worker_download(args: Tuple[FileRecord, Path, RateLimiter, DownloadState]) -> Tuple[str, bool, int, str]:
    """Worker function for thread pool."""
    record, output_dir, rate_limiter, state = args
    
    # Check if already completed
    if record.checksum in state.completed_checksums:
        return record.checksum, True, 0, "already done"
    
    # Check failure count
    if state.failed_checksums.get(record.checksum, 0) >= MAX_RETRIES:
        return record.checksum, False, 0, "max failures reached"
    
    # Determine output path
    if record.source.startswith("project:"):
        proj_name = record.source.split(":", 1)[1]
        safe_name = re.sub(r'[<>:"/\\|?*]', "_", record.rel_path or record.name)
        out_path = output_dir / "projects" / proj_name / safe_name
    elif record.source.startswith("chat:"):
        chat_id = record.source.split(":", 1)[1]
        safe_name = re.sub(r'[<>:"/\\|?*]', "_", record.name)
        out_path = output_dir / "chats" / chat_id / safe_name
    else:
        safe_name = re.sub(r'[<>:"/\\|?*]', "_", record.name)
        out_path = output_dir / "har" / safe_name
    
    success, bytes_written, error = download_file(record.url, out_path, record.checksum, rate_limiter)
    
    if success:
        state.completed_checksums.add(record.checksum)
        state.total_bytes += bytes_written
    else:
        state.failed_checksums[record.checksum] = state.failed_checksums.get(record.checksum, 0) + 1
    
    return record.checksum, success, bytes_written, error


# ── MAIN ─────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="Fast Kimi Downloader")
    parser.add_argument("--jwt", default=DEFAULT_JWT, help="JWT token")
    parser.add_argument("--output", default="/home/toxic/kimi_fast", help="Output directory")
    parser.add_argument("--workers", type=int, default=MAX_WORKERS, help="Concurrent downloads")
    parser.add_argument("--no-api", action="store_true", help="Skip API, use HAR only")
    parser.add_argument("--no-har", action="store_true", help="Skip HAR, use API only")
    parser.add_argument("--resume", action="store_true", help="Resume from state file")
    parser.add_argument("--list-only", action="store_true", help="List files without downloading")
    args = parser.parse_args()

    print(f'[DEBUG] Args: {args}')
    out_dir = Path(args.output)
    out_dir.mkdir(parents=True, exist_ok=True)
    state_path = out_dir / STATE_FILE
    print(f'[DEBUG] State path: {state_path}')

    print('[DEBUG] Loading state...', flush=True)
    state = DownloadState.load(state_path) if args.resume else DownloadState(set(), {}, 0, time.time())
    print(f'[DEBUG] State loaded: {len(state.completed_checksums)} completed', flush=True)

    rate_limiter = RateLimiter(RATE_LIMIT_DELAY)
    all_records: Dict[str, FileRecord] = {}  # checksum -> FileRecord (dedup)
    print('[DEBUG] Starting HAR/API fetch...', flush=True)

    # 1. Parse HARs for structure
    if not args.no_har:
        print("[*] Parsing HAR files...", flush=True)
        har_paths = find_all_hars()
        print(f"[*] Found {len(har_paths)} HAR files", flush=True)
        for har_path in har_paths:
            proj_files, chat_files = parse_har_for_structure(har_path)
            for files in list(proj_files.values()) + list(chat_files.values()):
                for rec in files:
                    if rec.checksum not in all_records:
                        all_records[rec.checksum] = rec
        print(f"[*] HAR extracted: {len(all_records)} unique files")

    # 2. Fetch from API for fresh URLs
    if not args.no_api:
        print("[*] Fetching from API...", flush=True)
        api = KimiAPI(args.jwt, rate_limiter)
        
        # Projects
        projects = api.list_projects()
        print(f"[*] Found {len(projects)} projects", flush=True)
        for proj in projects:
            files = api.list_project_files(proj["id"])
            print(f"[*] Project {proj['name']}: {len(files)} files (recursive)", flush=True)
            for f in files:
                if f.get("isDir"):
                    continue
                name = f.get("name", "unknown")
                path = f.get("path", name)
                download_url = f.get("url", "")
                checksum_match = re.search(r"checksum=([^&]+)", download_url)
                checksum = urllib.parse.unquote(checksum_match.group(1)) if checksum_match else hashlib.sha256(name.encode()).hexdigest()[:32]
                rec = FileRecord(
                    checksum=checksum, name=name, url=download_url,
                    source=f"project:{proj['name']}", size=int(f.get("size", 0)), rel_path=path
                )
                all_records[checksum] = rec
        
        # Feeds
        feeds = api.list_feeds()
        print(f"[*] Found {len(feeds)} feed items", flush=True)
        for item in feeds:
            chat = item.get("chat", {})
            chat_id = chat.get("id", "unknown")[:12]
            for f in chat.get("files", []):
                meta = f.get("meta", {})
                blob = f.get("blob", {})
                name = meta.get("name", "unknown")
                sign = blob.get("signUrl", "")
                checksum = meta.get("checksum", hashlib.sha256(name.encode()).hexdigest()[:32])
                if sign:
                    rec = FileRecord(
                        checksum=checksum, name=name, url=sign,
                        source=f"chat:{chat_id}", size=0, rel_path=name
                    )
                    all_records[checksum] = rec

    print(f"[*] Total unique files to download: {len(all_records)}", flush=True)

    # Filter already completed
    pending = [r for r in all_records.values() if r.checksum not in state.completed_checksums]
    print(f"[*] Pending: {len(pending)} (skipped {len(all_records) - len(pending)} already done)", flush=True)

    if args.list_only:
        for rec in sorted(all_records.values(), key=lambda x: x.source):
            status = "DONE" if rec.checksum in state.completed_checksums else "PENDING"
            print(f"  [{status}] {rec.source} | {rec.name} | {rec.checksum[:16]}...")
        return

    if not pending:
        print("[*] Nothing to download!")
        return

    # Download with thread pool
    print(f"[*] Starting download with {args.workers} workers...", flush=True)
    completed = 0
    failed = 0
    total_bytes = 0
    start_time = time.time()

    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futures = {ex.submit(worker_download, (rec, out_dir, rate_limiter, state)): rec for rec in pending}
        
        for fut in as_completed(futures):
            checksum, success, bytes_written, error = fut.result()
            completed += 1
            
            if success:
                total_bytes += bytes_written
                if error != "skipped" and error != "already done":
                    print(f"[{completed}/{len(pending)}] OK {bytes_written//1024}KB {checksum[:16]}...", flush=True)
            else:
                failed += 1
                print(f"[{completed}/{len(pending)}] FAIL {checksum[:16]}: {error}", flush=True)
            
            # Periodic state save
            if completed % 50 == 0:
                state.save(state_path)
                elapsed = time.time() - start_time
                speed = total_bytes / 1024 / 1024 / elapsed if elapsed > 0 else 0
                print(f"    Progress: {completed}/{len(pending)} | {total_bytes/1024/1024:.1f}MB | {speed:.1f}MB/s")

    # Final save
    state.save(state_path)
    
    elapsed = time.time() - start_time
    print(f"\n{'='*60}")
    print(f"COMPLETE in {elapsed:.1f}s")
    print(f"Downloaded: {completed - failed}/{len(pending)}")
    print(f"Failed: {failed}")
    print(f"Total: {total_bytes / 1024 / 1024:.1f} MB")
    print(f"Speed: {total_bytes / 1024 / 1024 / elapsed:.1f} MB/s")
    print(f"Output: {out_dir.absolute()}")


if __name__ == "__main__":
    main()