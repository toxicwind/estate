import yaml
p = "/home/toxic/sovereign/config/herd.yaml"
s = open(p).read()
# The alias-shim /health gates herd's readiness wait: the target MUST appear
# in herd /v1/models, which advertises peer models ONLY as peer/<id>.
# Bare targets -> "unroutable" -> herd waits forever -> client hangs.
fixes = [
    ("--target nex-agi/nex-n2.5-mini:free --standby nex-agi/nex-n2.5-pro:free",
     "--target openrouter-free/nex-agi/nex-n2.5-mini:free --standby openrouter-free/nex-agi/nex-n2.5-pro:free"),
    ("--target nex-agi/nex-n2.5-pro:free --standby poolside/laguna-s-2.1:free",
     "--target openrouter-free/nex-agi/nex-n2.5-pro:free --standby openrouter-free/poolside/laguna-s-2.1:free"),
    ("--target poolside/laguna-s-2.1:free --standby nex-agi/nex-n2.5-mini:free",
     "--target openrouter-free/poolside/laguna-s-2.1:free --standby openrouter-free/nex-agi/nex-n2.5-mini:free"),
    ("alias_of: nex-agi/nex-n2.5-mini:free",
     "alias_of: openrouter-free/nex-agi/nex-n2.5-mini:free"),
    ("alias_of: nex-agi/nex-n2.5-pro:free",
     "alias_of: openrouter-free/nex-agi/nex-n2.5-pro:free"),
    ("alias_of: poolside/laguna-s-2.1:free",
     "alias_of: openrouter-free/poolside/laguna-s-2.1:free"),
    ('(alias -> nex-agi/nex-n2.5-mini:free)',
     '(alias -> openrouter-free/nex-agi/nex-n2.5-mini:free)'),
    ('(alias -> nex-agi/nex-n2.5-pro:free)',
     '(alias -> openrouter-free/nex-agi/nex-n2.5-pro:free)'),
    ('(alias -> poolside/laguna-s-2.1:free)',
     '(alias -> openrouter-free/poolside/laguna-s-2.1:free)'),
]
n = 0
for old, new in fixes:
    if old in s:
        s = s.replace(old, new)
        n += 1
print("replacements:", n, "/", len(fixes))
open(p, "w").write(s)
yaml.safe_load(open(p))
print("live herd.yaml: oracle-judge targets prefixed, YAML valid")
