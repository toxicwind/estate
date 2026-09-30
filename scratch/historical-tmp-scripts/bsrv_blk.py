# --- buildsrv tools -----------------------------------------------------------
# Added 2026-09-21. Native MCP surface for buildsrv, the fleet build server
# on 127.0.0.1:25148. Wraps /home/toxic/bin/buildsrv via argv lists only
# (never shell=True, never raw interpolation). Submit returns immediately
# after queueing; the build itself runs async in buildsrvd.

_BUILDSRV_BIN = "/home/toxic/bin/buildsrv"
_BUILDSRV_JOB_RX = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$")
_BUILDSRV_MAX_CMD = 4000
_BUILDSRV_OUT_CAP = 8000


def _buildsrv_run(argv):
    try:
        p = subprocess.run(argv, capture_output=True, text=True, timeout=90)
    except subprocess.TimeoutExpired:
        return "TIMEOUT after 90s"
    except Exception as e:
        return "error: %s" % e
    out = ((p.stdout or "") + (p.stderr or "")).strip()
    if not out:
        return "[exit=%d] (no output)" % p.returncode
    return out[:_BUILDSRV_OUT_CAP]


def _buildsrv_check_id(job_id):
    if not _BUILDSRV_JOB_RX.match(job_id or ""):
        return "bad job_id: must match ^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$"
    return None


@mcp.tool()
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
    return _buildsrv_run(argv)


@mcp.tool()
def buildsrv_status(job_id: str) -> str:
    """Show buildsrv job status (queued/running/succeeded/failed, exit code)."""
    err = _buildsrv_check_id(job_id)
    if err:
        return err
    return _buildsrv_run([_BUILDSRV_BIN, "status", job_id])


@mcp.tool()
def buildsrv_logs(job_id: str, tail: int = 50) -> str:
    """Show the last N lines of a buildsrv job's log (default 50, max 500)."""
    err = _buildsrv_check_id(job_id)
    if err:
        return err
    try:
        n = int(tail)
    except (TypeError, ValueError):
        return "error: tail must be an integer"
    n = max(1, min(n, 500))
    return _buildsrv_run([_BUILDSRV_BIN, "logs", "-n", str(n), job_id])


@mcp.tool()
def buildsrv_list(limit: int = 10) -> str:
    """List recent buildsrv jobs (default 10, max 50)."""
    try:
        n = int(limit)
    except (TypeError, ValueError):
        return "error: limit must be an integer"
    n = max(1, min(n, 50))
    return _buildsrv_run([_BUILDSRV_BIN, "list", "-n", str(n)])


@mcp.tool()
def buildsrv_health() -> str:
    """Health probe for the buildsrv daemon (:25148): uptime, workers, queue."""
    return _buildsrv_run([_BUILDSRV_BIN, "health"])


# --- end buildsrv tools -------------------------------------------------------
