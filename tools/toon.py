"""TOON encoder — gated on uniform arrays >=10 items."""
import json
MARKER = "[mcpproxy:toon/v1]"

def _is_prim(v): return isinstance(v, (str, int, float, bool, type(None)))
def _fmt(v):
    if v is None: return "null"
    if isinstance(v, bool): return "true" if v else "false"
    if isinstance(v, str):
        if any(c in v for c in ',\n:"{}[]') or v != v.strip():
            return json.dumps(v, ensure_ascii=False)
        return v
    return str(v)

def _has_uniform_array(obj, min_len):
    def check(v):
        if isinstance(v, list) and len(v) >= min_len:
            if all(isinstance(x, dict) and x for x in v):
                keys = set(v[0].keys())
                if all(set(x.keys()) == keys for x in v):
                    return True
        if isinstance(v, dict): return any(check(x) for x in v.values())
        if isinstance(v, list): return any(check(x) for x in v)
        return False
    return check(obj)

def _enc(obj, indent=0):
    pad = "  " * indent
    if _is_prim(obj): return [pad + _fmt(obj)]
    if isinstance(obj, list):
        if not obj: return [pad + "[]"]
        if all(_is_prim(x) for x in obj):
            return [pad + f"[{len(obj)}]: " + ",".join(_fmt(x) for x in obj)]
        if all(isinstance(x, dict) and x for x in obj):
            ks = set(obj[0].keys())
            if all(set(x.keys()) == ks for x in obj):
                keys = sorted(ks)
                out = [pad + f"[{len(obj)}]{{{','.join(keys)}}}:"]
                for x in obj:
                    out.append(pad + "  " + ",".join(_fmt(x.get(k)) for k in keys))
                return out
        out = [pad + f"[{len(obj)}]:"]
        for x in obj:
            if isinstance(x, dict):
                first = True
                for k, v in x.items():
                    if first:
                        out.append(pad + "  - " + _enc_kv(k, v, indent+2)[0].lstrip())
                        first = False
                    else:
                        out.extend(pad + "    " + l for l in _enc_kv(k, v, indent+2))
            else:
                out.append(pad + "  - " + _fmt(x))
        return out
    if isinstance(obj, dict):
        if not obj: return [pad + "{}"]
        out = []
        for k, v in obj.items():
            out.extend(_enc_kv(k, v, indent))
        return out
    return [pad + _fmt(obj)]

def _enc_kv(k, v, indent):
    pad = "  " * indent
    if isinstance(v, dict) and v:
        return [pad + f"{k}:"] + _enc(v, indent+1)
    if isinstance(v, list) and v and all(_is_prim(x) for x in v):
        return [pad + f"{k}" + _enc(v, 0)[0].lstrip()]
    if isinstance(v, list) and v:
        return [pad + f"{k}:"] + _enc(v, indent+1)
    return [pad + f"{k}: " + _fmt(v)]

def encode(obj, *, min_uniform=10):
    if not _has_uniform_array(obj, min_uniform):
        return json.dumps(obj, ensure_ascii=False)
    return MARKER + "\n" + "\n".join(_enc(obj))

def decode(text):
    if text.startswith(MARKER): text = text[len(MARKER):].lstrip("\n")
    try: return json.loads(text)
    except Exception: return {"_toon_raw": text}

def savings(obj, *, min_uniform=10):
    j = json.dumps(obj, ensure_ascii=False)
    t = encode(obj, min_uniform=min_uniform)
    return {"json_bytes": len(j), "toon_bytes": len(t),
            "saved_pct": round(100*(1 - len(t)/max(1, len(j))), 2),
            "toon_applied": t.startswith(MARKER)}
