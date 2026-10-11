import subprocess
import os

def run(cmd: str, cwd: str | None = None, timeout: float = 10.0) -> str:
    """
    First-class shell runner with explicit, reliable cwd support.
    Safely executes shell commands in the target working directory with a timeout.
    """
    try:
        res = subprocess.run(
            cmd,
            shell=True,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout
        )
        out = res.stdout.decode('utf-8', errors='replace').strip()
        err = res.stderr.decode('utf-8', errors='replace').strip()
        if res.returncode != 0 and err:
            return f"{out}\n[stderr: {err}]" if out else f"[stderr: {err}]"
        return out
    except subprocess.TimeoutExpired:
        return f"[timeout after {timeout}s: {cmd}]"
    except Exception as e:
        return f"[error executing {cmd} in {cwd}: {e}]"
