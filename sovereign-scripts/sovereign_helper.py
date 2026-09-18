#!/usr/bin/env python3
"""
sovereign-helper: Master hook for GitHub API ops, async parallel, rate limiting,
and env-aware fallbacks. Designed for sovereign-pi / toxicwind workflows.
Python 3.12+ primary, 3.11/3.8 AST fallback where needed.
"""
from __future__ import annotations
import asyncio, aiohttp, json, os, sys, time, subprocess, hashlib
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, Any, Callable
from collections import deque
from functools import wraps

# --- Env Detection ---
ENV = os.environ.get("KIMI_PROJECT_PORTAL_CAPABILITY_ENV", "dev")
GATEWAY = os.environ.get("KIMI_PROJECT_PORTAL_CAPABILITY_PROD_ADDR", "")
VNC_DISPLAY = os.environ.get("DISPLAY", ":99")
CDP_PORT = 9222

# --- Rate Limit State ---
@dataclass
class RateLimit:
    remaining: int = 5000
    reset_at: float = 0.0
    limit: int = 5000
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock)

    async def acquire(self, cost: int = 1):
        async with self._lock:
            if self.remaining < cost:
                wait = max(0, self.reset_at - time.time())
                if wait > 0:
                    await asyncio.sleep(wait + 1)
                self.remaining = self.limit
            self.remaining -= cost

RL = RateLimit()

# --- Async GitHub Client ---
class GitHubClient:
    def __init__(self, token: str | None = None):
        self.token = token or os.environ.get("GITHUB_TOKEN", "")
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        self._session: aiohttp.ClientSession | None = None

    async def __aenter__(self):
        self._session = aiohttp.ClientSession(headers=self.headers)
        return self

    async def __aexit__(self, *args):
        if self._session:
            await self._session.close()

    async def request(self, method: str, url: str, **kwargs) -> dict:
        await RL.acquire()
        if not self._session:
            raise RuntimeError("Client not entered")
        async with self._session.request(method, url, **kwargs) as resp:
            # Update rate limit from headers
            RL.remaining = int(resp.headers.get("X-RateLimit-Remaining", RL.remaining))
            RL.reset_at = float(resp.headers.get("X-RateLimit-Reset", RL.reset_at))
            RL.limit = int(resp.headers.get("X-RateLimit-Limit", RL.limit))
            text = await resp.text()
            try:
                return json.loads(text)
            except json.JSONDecodeError:
                return {"_raw": text, "_status": resp.status}

    async def get_repos(self, per_page: int = 100) -> list[dict]:
        repos = []
        page = 1
        while True:
            data = await self.request(
                "GET",
                f"https://api.github.com/user/repos?per_page={per_page}&page={page}&sort=updated&affiliation=owner"
            )
            if isinstance(data, list):
                if not data:
                    break
                repos.extend(data)
                if len(data) < per_page:
                    break
                page += 1
            else:
                break
        return repos

    async def create_repo(self, name: str, private: bool = True, description: str = "") -> dict:
        payload = {
            "name": name,
            "private": private,
            "description": description,
            "auto_init": True,
            "gitignore_template": "Python",
        }
        return await self.request("POST", "https://api.github.com/user/repos", json=payload)

    async def update_file(self, owner: str, repo: str, path: str, content: str, message: str, sha: str | None = None) -> dict:
        import base64
        payload = {
            "message": message,
            "content": base64.b64encode(content.encode()).decode(),
        }
        if sha:
            payload["sha"] = sha
        return await self.request(
            "PUT",
            f"https://api.github.com/repos/{owner}/{repo}/contents/{path}",
            json=payload
        )

# --- Retry / Fallback Decorator ---
def retry(max_attempts: int = 3, backoff: float = 1.0):
    def decorator(fn: Callable):
        @wraps(fn)
        async def wrapper(*args, **kwargs):
            for attempt in range(max_attempts):
                try:
                    return await fn(*args, **kwargs)
                except Exception as e:
                    if attempt == max_attempts - 1:
                        raise
                    wait = backoff * (2 ** attempt)
                    await asyncio.sleep(wait)
        return wrapper
    return decorator

# --- Module Error Auto-Helpers ---
def ensure_imports(*packages: str):
    """Install missing packages via pip if import fails."""
    missing = []
    for pkg in packages:
        try:
            __import__(pkg)
        except ImportError:
            missing.append(pkg)
    if missing:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--quiet", "--trusted-host", "pypi.org", "--trusted-host", "files.pythonhosted.org"] + missing)

# --- CDN Mirror Helpers ---
PYPI_MIRRORS = [
    "https://pypi.org/simple",
    "https://mirrors.aliyun.com/pypi/simple",
    "https://pypi.tuna.tsinghua.edu.cn/simple",
]

def pip_with_fallback(packages: list[str]):
    for mirror in PYPI_MIRRORS:
        try:
            subprocess.check_call([
                sys.executable, "-m", "pip", "install", "--quiet",
                "-i", mirror, "--trusted-host", mirror.replace("https://", "").split("/")[0]
            ] + packages, timeout=60)
            return mirror
        except subprocess.CalledProcessError:
            continue
    raise RuntimeError("All PyPI mirrors failed")

# --- File Hash / Integrity ---
def file_hash(path: Path | str, algo: str = "sha256") -> str:
    h = hashlib.new(algo)
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

# --- CLI ---
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Sovereign Helper")
    parser.add_argument("--ensure", nargs="+", help="Ensure packages are installed")
    parser.add_argument("--pip-fallback", nargs="+", help="Install with CDN fallback")
    args = parser.parse_args()
    if args.ensure:
        ensure_imports(*args.ensure)
    if args.pip_fallback:
        pip_with_fallback(args.pip_fallback)
