"""Fix buildsrv_submit defaults to match `buildsrv submit --help` reality.

The CLI requires --name, --repo, --toolchain, --cmd. The old wrapper had
repo="" and toolchain="" defaults that silently omitted the flags, so a
default call always failed. New behavior:
- toolchain is a required MCP param (matches CLI: no default exists)
- repo defaults to the buildsrv tool dir (as the docstring always claimed)
- workdir optional (CLI defaults workdir to repo)
- timeout passthrough added (CLI default 1200)
- repo must be absolute (CLI: "repo root (absolute path)")
"""
import re

OLD_SUBMIT = '''@mcp.tool()
def buildsrv_submit(name: str, cmd: str, repo: str = "",
                    workdir: str = "", toolchain: str = "") -> str:
    """Submit a build job to buildsrv (fleet build server on :25148).

    Queues the job and returns immediately with the job id; the build runs
    async in buildsrvd. Poll with buildsrv_status / buildsrv_logs.
    cmd is capped at 4000 chars. repo defaults to the buildsrv tool dir.
    """
    if not (name or "").strip():
        return "error: name required"
    if not (cmd or "").strip():
        return "error: cmd required"
    if len(cmd) > _BUILDSRV_MAX_CMD:
        return "error: cmd too long (%d > %d)" % (len(cmd), _BUILDSRV_MAX_CMD)
    argv = [_BUILDSRV_BIN, "submit", "--name", name, "--cmd", cmd]
    if repo:
        argv += ["--repo", repo]
    if workdir:
        argv += ["--workdir", workdir]
    if toolchain:
        argv += ["--toolchain", toolchain]
    return _buildsrv_run(argv)'''

NEW_SUBMIT = '''_BUILDSRV_DEFAULT_REPO = "/home/toxic/sovereign/tools/buildsrv"


@mcp.tool()
def buildsrv_submit(name: str, cmd: str, toolchain: str,
                    repo: str = _BUILDSRV_DEFAULT_REPO,
                    workdir: str = "", timeout: int = 1200) -> str:
    """Submit a build job to buildsrv (fleet build server on :25148).

    Queues the job and returns immediately with the job id; the build runs
    async in buildsrvd. Poll with buildsrv_status / buildsrv_logs.
    cmd is capped at 4000 chars. repo defaults to the buildsrv tool dir;
    toolchain is required (rust|cargo|go|bun|node|python|python3|tsc|java|gradle).
    """
    if not (name or "").strip():
        return "error: name required"
    if not (cmd or "").strip():
        return "error: cmd required"
    if not (toolchain or "").strip():
        return "error: toolchain required"
    if len(cmd) > _BUILDSRV_MAX_CMD:
        return "error: cmd too long (%d > %d)" % (len(cmd), _BUILDSRV_MAX_CMD)
    repo = (repo or _BUILDSRV_DEFAULT_REPO).strip()
    if not repo.startswith("/"):
        return "error: repo must be an absolute path"
    try:
        timeout = int(timeout)
    except (TypeError, ValueError):
        return "error: timeout must be an integer"
    timeout = max(30, min(timeout, 7200))
    argv = [_BUILDSRV_BIN, "submit", "--name", name, "--repo", repo,
            "--toolchain", toolchain.strip(), "--cmd", cmd,
            "--timeout", str(timeout)]
    if (workdir or "").strip():
        argv += ["--workdir", workdir.strip()]
    return _buildsrv_run(argv)'''

with open('/home/toxic/sovereign/projects/bridge/yote/awrawr_mcp.py') as f:
    src = f.read()

assert OLD_SUBMIT in src, "OLD_SUBMIT block not found - file changed?"
src = src.replace(OLD_SUBMIT, NEW_SUBMIT)

with open('/home/toxic/sovereign/projects/bridge/yote/awrawr_mcp.py', 'w') as f:
    f.write(src)
print("patched OK")
