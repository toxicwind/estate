"""Secrets loader: file (NAME=value) or dir (filename=key, content=value)."""
import os


def load(path: str) -> dict[str, str]:
    out: dict[str, str] = {}
    if not os.path.exists(path):
        return out
    if os.path.isfile(path):
        with open(path, encoding="utf-8", errors="ignore") as f:
            for raw in f:
                line = raw.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                if line.startswith("export "):
                    line = line[7:]
                k, v = line.split("=", 1)
                v = v.strip()
                if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
                    v = v[1:-1]
                out[k.strip()] = v
        return out
    for name in os.listdir(path):
        if name.startswith("."):
            continue
        p = os.path.join(path, name)
        if os.path.isfile(p):
            with open(p, encoding="utf-8", errors="ignore") as f:
                v = f.read().strip()
            if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
                v = v[1:-1]
            out[name] = v
    return out
