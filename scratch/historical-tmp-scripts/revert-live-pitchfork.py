import tomllib
p = "/home/toxic/sovereign/pitchfork.toml"
s = open(p).read()
old_run = ("run = \"exec python3 /home/toxic/sovereign/config/herd.d/alias-shim.py"
           " --port ${KIMI_AUTO_SHIM_PORT} --target kimi-k2.6"
           " --standby kimi-k2.7-code --name kimi-auto\"")
new_run = ("run = \"exec python3 /home/toxic/sovereign/config/herd.d/alias-shim.py"
           " --port ${KIMI_AUTO_SHIM_PORT} --target moonshot/kimi-k2.6"
           " --standby moonshot/kimi-k2.7-code --name kimi-auto\"")
assert old_run in s, "kimi-auto-shim run line not found"
s = s.replace(old_run, new_run, 1)
s = s.replace(
  "# 2026-09-21 modelmap: was --target ministral-14b-latest (paid Mistral) --\n"
  "# a kimi-named alias serving a non-Kimi model. Doctrine (AGENTS.md):\n"
  "# \"kimi-auto is Kimi-only. Honest 503 when no Kimi route is healthy;\n"
  "# never a silent fallback.\" Retargeted to the moonshot peer's Kimi IDs.",
  "# 2026-09-21 modelmap: was --target ministral-14b-latest (paid Mistral) --\n"
  "# a kimi-named alias serving a non-Kimi model. Doctrine (AGENTS.md):\n"
  "# \"kimi-auto is Kimi-only. Honest 503 when no Kimi route is healthy;\n"
  "# never a silent fallback.\" Retargeted to the moonshot peer's Kimi IDs\n"
  "# in peer/<id> form (live-probed: prefixed routes directly, bare IDs\n"
  "# are unreliable -- kimi-k2.7-code bare -> 404).")
open(p, "w").write(s)
d = tomllib.load(open(p, "rb"))
run = d["daemons"]["kimi-auto-shim"]["run"]
assert "--target moonshot/kimi-k2.6" in run and "ministral" not in run
print("live pitchfork.toml: kimi-auto-shim -> moonshot/<id>, TOML valid")
