import sys
p = "/home/toxic/.tau/agent/config.yml"
s = open(p).read()
old = "  fallbackChains:\n    {}"
new = ('  fallbackChains:\n'
       '    default:\n'
       '      - "sovereign/free"\n'
       '      - "herd/qwen-flash-da-128k"\n'
       '    "google-antigravity/*":\n'
       '      - "sovereign/free"\n'
       '      - "herd/qwen-flash-da-128k"')
if old not in s:
    print("pattern not found or already applied")
    sys.exit(1)
open(p, "w").write(s.replace(old, new, 1))
print("ok")
