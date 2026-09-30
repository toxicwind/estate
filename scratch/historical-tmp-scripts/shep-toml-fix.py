import sys
p = "/home/toxic/sovereign/pitchfork.toml"
lines = open(p).read().split("\n")
i = next(n for n, l in enumerate(lines) if l.strip() == "[daemons.shep]")
j = next(n for n in range(i, min(i + 15, len(lines))) if lines[n].strip() == "port = 25127")
assert lines[j + 1].strip() == "", "expected blank remnant line, got: %r" % lines[j + 1]
lines[j + 1:j + 2] = [
    '# shep-serve.sh self-heals: bootstraps gitignored mcp_config.json from .dist when missing,',
    '# injects secrets from /home/toxic/.secrets (shep direct-run crash-loops without it).',
    'run = "exec /home/toxic/sovereign/mesh/bin/shep-serve.sh"',
]
open(p, "w").write("\n".join(lines))
import tomllib
d = tomllib.load(open(p, "rb"))
print("toml OK; shep run =", d["daemons"]["shep"]["run"])
