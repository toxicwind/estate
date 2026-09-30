import yaml
p = "/home/toxic/sovereign/config/herd.yaml"
s = open(p).read()
s2 = s.replace("--target moonshot/kimi-k2.6", "--target kimi-k2.6")
s2 = s2.replace("--target moonshot/kimi-k2.7-code", "--target kimi-k2.7-code")
s2 = s2.replace("alias_of: moonshot/kimi-k2.6", "alias_of: kimi-k2.6")
s2 = s2.replace("alias_of: moonshot/kimi-k2.7-code", "alias_of: kimi-k2.7-code")
s2 = s2.replace("(alias -> moonshot/kimi-k2.6)", "(alias -> kimi-k2.6)")
s2 = s2.replace("(alias -> moonshot/kimi-k2.7-code)", "(alias -> kimi-k2.7-code)")
old_note = '# "Insufficient credits" until the account is topped up.'
new_note = ('# "Insufficient credits" until the account is topped up.\n'
            '  # 2026-09-21 modelmap: targets were `moonshot/<id>` -- peer.go does\n'
            '  # EXACT-match lookups, no `peer/` prefix stripping, so those 404\'d.\n'
            '  # Targets are the bare upstream IDs the moonshot peer claims.')
assert old_note in s2, "anchor comment not found"
s2 = s2.replace(old_note, new_note, 1)
assert s2 != s, "no replacements made"
open(p, "w").write(s2)
yaml.safe_load(open(p))
print("live herd.yaml: kimi targets fixed, YAML valid")
print("remaining '--target moonshot/' occurrences:", s2.count("--target moonshot/"))
