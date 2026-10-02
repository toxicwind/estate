#!/usr/bin/env python3
"""Fork renaming and rebranding engine.

Order matters: URL anchors are rewritten first so fork-hosted links win, then
the bare token is replaced across all case variants.
"""

import argparse
import subprocess
import sys
from pathlib import Path

DEFAULT_REPO = Path("/home/toxic/workspace/untracked/roundup")

SKIP_SUFFIX = {
    ".png", ".gif", ".jpg", ".jpeg", ".webp", ".ico",
    ".whl", ".so", ".pyc", ".bin", ".node", ".wasm", ".pdf"
}
SKIP_NAMES = {"uv.lock", "bun.lock", "package-lock.json", "Cargo.lock"}


def tracked_files(repo_path: Path) -> list[Path]:
    try:
        out = subprocess.run(
            ["git", "ls-files", "-z"],
            cwd=repo_path,
            capture_output=True,
            text=True,
            check=True
        ).stdout
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print(f"Error querying git ls-files in {repo_path}: {e}", file=sys.stderr)
        return []
    return [repo_path / p for p in out.split("\0") if p]


def build_rules(old_token: str, new_token: str, old_org: str, new_org: str):
    url_rules = [
        (f"github.com/{old_org}/{old_token}", f"github.com/{new_org}/{new_token}"),
        (f"{old_org}.github.io/{old_token}", f"{new_org}.github.io/{new_token}"),
        (f"pypi.org/project/{old_token}", f"pypi.org/project/{new_token}"),
    ]
    token_rules = [
        (old_token.upper(), new_token.upper()),
        (old_token.capitalize(), new_token.capitalize()),
        (old_token.title(), new_token.title()),
        (old_token.lower(), new_token.lower()),
    ]
    # Remove duplicates while preserving order
    seen = set()
    dedup_tokens = []
    for o, n in token_rules:
        if (o, n) not in seen:
            seen.add((o, n))
            dedup_tokens.append((o, n))
    return url_rules, dedup_tokens


def main() -> int:
    parser = argparse.ArgumentParser(description="Automated fork rename/rebranding tool")
    parser.add_argument("--repo", type=Path, default=DEFAULT_REPO, help="Repository root path")
    parser.add_argument("--old", default="guidellm", help="Old token/name to replace")
    parser.add_argument("--new", default="roundup", help="New token/name")
    parser.add_argument("--old-org", default="vllm-project", help="Old GitHub/upstream org")
    parser.add_argument("--new-org", default="toxicwind", help="New GitHub/fork org")
    parser.add_argument("--dry-run", action="store_true", help="Report changes without writing")
    args = parser.parse_args()

    repo = args.repo.resolve()
    if not repo.exists():
        print(f"Warning: repo directory does not exist: {repo}", file=sys.stderr)
        return 1

    url_rules, token_rules = build_rules(args.old, args.new, args.old_org, args.new_org)

    changed = []
    for path in tracked_files(repo):
        try:
            rel = path.relative_to(repo)
        except ValueError:
            continue
        if len(rel.parts) > 0 and (rel.parts[0] in ("build", "dist") or "egg-info" in rel.parts[0]):
            continue
        if path.suffix.lower() in SKIP_SUFFIX or path.name in SKIP_NAMES:
            continue
        if path.is_dir() or path.is_symlink():
            continue

        try:
            original = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, FileNotFoundError):
            continue

        text = original
        for old, new in url_rules:
            text = text.replace(old, new)
        for old, new in token_rules:
            text = text.replace(old, new)

        if text != original:
            if not args.dry_run:
                path.write_text(text, encoding="utf-8")
            changed.append(str(rel))

    action = "would rewrite" if args.dry_run else "rewrote"
    print(f"{action} {len(changed)} files in {repo}")
    for name in changed:
        print(f"  {name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
