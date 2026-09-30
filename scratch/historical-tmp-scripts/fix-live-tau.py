import yaml
p = "/home/toxic/.tau/agent/config.yml"
s = open(p).read()
# modelRoles: default/smol off the local 9B -> sovereign/free (ranked #1)
old_roles = "  smol: herd/qwen-flash-da-128k\n"
assert old_roles in s, "smol role not found"
s = s.replace(old_roles, "  smol: sovereign/free\n", 1)
old_default = "  default: herd/qwen-flash-da-128k\n"
assert old_default in s, "default role not found"
s = s.replace(old_default, "  default: sovereign/free\n", 1)
old_note = ("  # ranker live-measurements 2026-09-20 (sovereign/free: 0% errors, nemotron\n"
            "  # winner; herd local: fast, /bin/bash, private; pollinations: backup lane only).\n")
new_note = (old_note +
            "  # 2026-09-21 modelmap: default/smol were herd/qwen-flash-da-128k (local 9B\n"
            "  # beellama) -- absurd for the DEFAULT: measured ranking is nim 0.8087 >\n"
            "  # pollinations 0.7535 > herd-local 0.5791, and the routing doctrine says\n"
            "  # \"Local models are the fallback, never the default\". -> sovereign/free.\n"
            "  # tiny keeps the local 1.2B -- the one role where local is sane.\n")
assert old_note in s, "roles comment anchor not found"
s = s.replace(old_note, new_note, 1)
# subagents.defaultModel: dead kimi-k3-nim -> sovereign/free
old_dm = "  defaultModel: herd/kimi-k3-nim\n"
assert old_dm in s, "defaultModel not found"
s = s.replace(old_dm,
              "  # 2026-09-21 modelmap: was herd/kimi-k3-nim -- existed ONLY in the\n"
              "  # disabled flock.modelMap (flock.enabled: false), so every subagent\n"
              "  # spawn 404'd. -> sovereign/free (ranked #1, 0% errors 2026-09-20).\n"
              "  defaultModel: sovereign/free\n", 1)
open(p, "w").write(s)
d = yaml.safe_load(open(p))
assert d["modelRoles"]["default"] == "sovereign/free"
assert d["modelRoles"]["smol"] == "sovereign/free"
assert d["subagents"]["defaultModel"] == "sovereign/free"
print("live tau config.yml: modelRoles + defaultModel fixed, YAML valid")
