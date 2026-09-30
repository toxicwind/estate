import tomllib
p = "/home/toxic/sovereign/pitchfork.toml"
s = open(p).read()
old_run = ("run = \"exec python3 /home/toxic/sovereign/config/herd.d/alias-shim.py"
           " --port ${KIMI_AUTO_SHIM_PORT} --target ministral-14b-latest"
           " --standby qwen3.5-9b-tool --name kimi-auto\"")
new_run = ("run = \"exec python3 /home/toxic/sovereign/config/herd.d/alias-shim.py"
           " --port ${KIMI_AUTO_SHIM_PORT} --target kimi-k2.6"
           " --standby kimi-k2.7-code --name kimi-auto\"")
assert old_run in s, "kimi-auto-shim run line not found"
s = s.replace(old_run, new_run, 1)
old_note = ("# Router-configured alias forwarder (2026-09-20): same routing as the herd\n"
            "# kimi-auto entry (--config-dir fragment). --target/--standby MUST match\n"
            "# /home/toxic/kimi-auto/herd.d/kimi-auto.yaml. Selection lives in router\n"
            "# config; this shim never selects models.")
new_note = ("# Router-configured alias forwarder: same routing as the herd\n"
            "# kimi-auto entry (--config-dir fragment). --target/--standby MUST match\n"
            "# /home/toxic/kimi-auto/herd.d/kimi-auto.yaml. Selection lives in router\n"
            "# config; this shim never selects models.\n"
            "# 2026-09-21 modelmap: was --target ministral-14b-latest (paid Mistral) --\n"
            "# a kimi-named alias serving a non-Kimi model. Doctrine (AGENTS.md):\n"
            "# \"kimi-auto is Kimi-only. Honest 503 when no Kimi route is healthy;\n"
            "# never a silent fallback.\" Retargeted to the moonshot peer's Kimi IDs.")
assert old_note in s, "comment anchor not found"
s = s.replace(old_note, new_note, 1)
open(p, "w").write(s)
d = tomllib.load(open(p, "rb"))
run = d["daemons"]["kimi-auto-shim"]["run"]
assert "--target kimi-k2.6" in run and "ministral" not in run
print("live pitchfork.toml: kimi-auto-shim retargeted, TOML valid")
