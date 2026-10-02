"""Generate canonical agent.toml files from the live OpenFang DB manifests.
Reads /home/toxic/.openfang/data/openfang.db (read-only), emits TOML with
exact field fidelity so the kernel's disk-vs-DB merge is a no-op except for
the intended model-route changes. Run on yote."""
import sqlite3
import msgpack
import os


def tstr(s):
    s = str(s)
    s = s.replace("\\", "\\\\").replace('"', '\\"')
    s = s.replace("\n", "\\n").replace("\r", "\\r").replace("\t", "\\t")
    return '"%s"' % s


def tarr(items):
    return "[" + ", ".join(tstr(x) for x in items) + "]"


def gen_toml(m, model_override=None, header_note=""):
    L = []
    L.append("# Canonical source: sovereign/agents/%s/agent.toml" % m["name"])
    L.append("# Live copy: ~/.openfang/agents/%s/agent.toml (kernel re-seeds from disk on boot)" % m["name"])
    if header_note:
        L.append("# NOTE: " + header_note)
    L.append("name = %s" % tstr(m["name"]))
    L.append("version = %s" % tstr(m.get("version") or "1.0.0"))
    L.append("description = %s" % tstr(m.get("description") or ""))
    L.append("author = %s" % tstr(m.get("author") or ""))
    L.append("module = %s" % tstr(m.get("module") or "builtin:chat"))
    L.append("schedule = %s" % tstr(m.get("schedule") or "reactive"))
    if m.get("fallback_models") is not None:
        L.append("fallback_models = %s" % tarr(m["fallback_models"]))
    if m.get("priority"):
        L.append("priority = %s" % tstr(m["priority"]))
    if m.get("skills") is not None:
        L.append("skills = %s" % tarr(m["skills"]))
    if m.get("mcp_servers") is not None:
        L.append("mcp_servers = %s" % tarr(m["mcp_servers"]))
    if m.get("tags") is not None:
        L.append("tags = %s" % tarr(m["tags"]))
    if m.get("workspace"):
        L.append("workspace = %s" % tstr(m["workspace"]))
    if m.get("state_dir"):
        L.append("state_dir = %s" % tstr(m["state_dir"]))
    if m.get("generate_identity_files") is not None:
        L.append("generate_identity_files = %s" % str(bool(m["generate_identity_files"])).lower())
    if m.get("tool_allowlist") is not None:
        L.append("tool_allowlist = %s" % tarr(m["tool_allowlist"]))
    if m.get("tool_blocklist") is not None:
        L.append("tool_blocklist = %s" % tarr(m["tool_blocklist"]))
    if m.get("cache_context") is not None:
        L.append("cache_context = %s" % str(bool(m["cache_context"])).lower())
    L.append("")
    L.append("[model]")
    mo = dict(m["model"])
    if model_override:
        mo.update(model_override)
    L.append("provider = %s" % tstr(mo["provider"]))
    L.append("model = %s" % tstr(mo["model"]))
    if mo.get("base_url"):
        L.append("base_url = %s" % tstr(mo["base_url"]))
    if mo.get("max_tokens") is not None:
        L.append("max_tokens = %d" % mo["max_tokens"])
    if mo.get("temperature") is not None:
        L.append("temperature = %s" % repr(float(mo["temperature"])))
    if mo.get("system_prompt"):
        L.append("system_prompt = %s" % tstr(mo["system_prompt"]))
    L.append("")
    r = m.get("resources")
    if r:
        L.append("[resources]")
        for k in ("max_memory_bytes", "max_cpu_time_ms", "max_tool_calls_per_minute",
                  "max_llm_tokens_per_hour", "max_network_bytes_per_hour"):
            if r.get(k) is not None:
                L.append("%s = %d" % (k, r[k]))
        for k in ("max_cost_per_hour_usd", "max_cost_per_day_usd", "max_cost_per_month_usd"):
            if r.get(k) is not None:
                L.append("%s = %s" % (k, repr(float(r[k]))))
        L.append("")
    c = m.get("capabilities")
    if c:
        L.append("[capabilities]")
        for k in ("network", "tools", "memory_read", "memory_write",
                  "agent_message", "shell", "ofp_connect"):
            v = c.get(k)
            if v is not None:
                L.append("%s = %s" % (k, tarr(v)))
        for k in ("agent_spawn", "ofp_discover"):
            v = c.get(k)
            if v is not None:
                L.append("%s = %s" % (k, str(bool(v)).lower()))
        L.append("")
    return "\n".join(L) + "\n"


def main():
    con = sqlite3.connect("file:/home/toxic/.openfang/data/openfang.db?mode=ro", uri=True)
    manifests = {}
    for name in ("assistant", "squawk-relay"):
        row = con.execute("SELECT manifest FROM agents WHERE name=?", (name,)).fetchone()
        manifests[name] = msgpack.unpackb(row[0], raw=False)

    out = {}
    # assistant: re-route off dead Anthropic key -> herd free (doctrine: FREE BEATS LOCAL).
    # The ANTHROPIC_API_KEY in .secrets is revoked (Anthropic 401 invalid x-api-key);
    # new key is Chris's call. This keeps the agent serving until then.
    out["assistant"] = gen_toml(
        manifests["assistant"],
        model_override={
            "provider": "llama-swap",
            "model": "nex-agi/nex-n2.5-mini:free",
            "base_url": "http://127.0.0.1:25100/v1",
        },
        header_note=("anthropic/claude-sonnet-4-20250514 route PARKED 2026-09-20: stored "
                     "ANTHROPIC_API_KEY revoked (Anthropic 401 invalid x-api-key). "
                     "Restore provider=anthropic + model=claude-sonnet-4-20250514 once "
                     "Chris supplies a fresh key. Until then this herd-free route serves."),
    )
    # squawk-relay: faithful copy of the WORKING config (nvidia/openai/gpt-oss-20b
    # verified serving 2026-09-20). Durability only: DB row already correct.
    out["squawk-relay"] = gen_toml(manifests["squawk-relay"])

    for name, text in out.items():
        d = "/home/toxic/sovereign/agents/%s" % name
        os.makedirs(d, exist_ok=True)
        p = os.path.join(d, "agent.toml")
        with open(p, "w") as f:
            f.write(text)
        print("wrote", p, len(text), "bytes")

    # sanity: assistant TOML must contain the new route and no anthropic leftovers
    a = out["assistant"]
    assert 'provider = "llama-swap"' in a and "nex-agi/nex-n2.5-mini:free" in a
    assert "anthropic" not in a.split("[model]")[1].split("[resources]")[0].replace(
        "ANTHROPIC_API_KEY", "").replace("anthropic/", "")
    print("sanity OK")


if __name__ == "__main__":
    main()
