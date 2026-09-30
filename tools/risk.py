"""Session risk assessment — the lethal trifecta, computed live."""
DESTRUCTIVE = {"delete","remove","drop","revoke","disable","destroy",
               "purge","reset","clear","unsubscribe","cancel","terminate",
               "close","archive","ban","block","disconnect","kill",
               "wipe","truncate","force","hard"}
WRITE_VERBS = {"create","update","write","push","commit","merge","send",
               "post","put","patch","insert","add","append","move","copy"}
OPEN_WORLD  = {"web","search","browse","fetch","url","http","arxiv",
               "wikipedia","google","bing","reddit","twitter"}

def _has(name: str, verbs: set[str]) -> bool:
    n = name.lower()
    return any(v in n for v in verbs)

def assess(tools: list[dict]) -> dict:
    has_destructive = any(_has(t.get("id",""), DESTRUCTIVE) for t in tools)
    has_write       = any(_has(t.get("id",""), WRITE_VERBS) for t in tools)
    has_open        = any(_has(t.get("id",""), OPEN_WORLD) for t in tools)
    trifecta = has_destructive and has_write and has_open
    level = "low"
    if has_destructive and has_write: level = "medium"
    if trifecta: level = "high"
    return {
        "has_destructive_tools": has_destructive,
        "has_write_tools": has_write,
        "has_open_world_tools": has_open,
        "lethal_trifecta": trifecta,
        "level": level,
        "tool_count": len(tools),
    }
