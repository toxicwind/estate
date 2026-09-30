"""YAML loader: PyYAML preferred; tiny fallback for the subset we use."""
import re


def load(text: str) -> dict:
    try:
        import yaml
        d = yaml.safe_load(text)
        if isinstance(d, dict):
            return d
    except Exception:
        pass
    pools: dict = {}
    cur_pool = None
    for raw in text.splitlines():
        line = raw.split("#", 1)[0].rstrip()
        if not line.strip():
            continue
        ind = len(line) - len(line.lstrip())
        s = line.strip()
        if ind == 0 and s == "pools:":
            continue
        if ind == 2 and s.endswith(":"):
            cur_pool = s[:-1]
            pools[cur_pool] = {"keys": []}
            continue
        if cur_pool is None:
            continue
        if ind == 4 and ":" in s:
            k, v = s.split(":", 1)
            v = v.strip()
            if k.strip() == "keys":
                continue
            if v.startswith("["):
                v = [x.strip().strip("\"'") for x in v[1:-1].split(",") if x.strip()]
            elif v in ("true", "false"):
                v = v == "true"
            elif re.fullmatch(r"-?\d+", v):
                v = int(v)
            pools[cur_pool][k.strip()] = v
        elif s.startswith("- "):
            item = s[2:].strip()
            if "{" in item:
                d = {}
                for pair in item.strip("{}").split(","):
                    if ":" in pair:
                        k, v = pair.split(":", 1)
                        v = v.strip().strip("\"'")
                        if v == "true": v = True
                        elif v == "false": v = False
                        d[k.strip()] = v
                pools[cur_pool]["keys"].append(d)
            else:
                pools[cur_pool]["keys"].append(item.strip("\"'"))
    return {"pools": pools}
