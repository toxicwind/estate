import re
names = ["ANTHROPIC_CUSTOM_MODEL_OPTION","ANTHROPIC_DEFAULT_HAIKU_MODEL","ANTHROPIC_DEFAULT_OPUS_MODEL","ANTHROPIC_DEFAULT_SONNET_MODEL","CLAUDE_CODE_SUBAGENT_MODEL","NIM_MODEL","NIM_MODEL_DEEP","SCOUT_MODEL","SCOUT_MODEL_1","FLOCK_MODEL","NIM_PROXY_MODEL","RALPH_MODEL"]
vals = {}
for line in open("/home/toxic/.secrets", errors="replace"):
    m = re.match(r"^\s*(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)=(.*)$", line.strip())
    if m:
        v = m.group(2).strip()
        if (v.startswith('"') and v.endswith('"')) or (v.startswith("'") and v.endswith("'")):
            v = v[1:-1]
        vals[m.group(1)] = v
for n in names:
    if n in vals:
        print(n + "=" + vals[n])
