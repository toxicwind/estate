import io

p = "/home/toxic/hw-audit.sh"
s = open(p, encoding="utf-8").read()

old = 'if have cpuid; then\n'
old += '  cpuid -1 2>/dev/null | base64 -w0 | jq -c -Rs \'{section:"cpuid",sub:"raw_b64",data:.}\' >> "$OUT"\n'
old += '  for leaf in 0 1 7 0x80000000 0x80000001 0x80000002 0x80000003 0x80000004 0x80000006 0x80000007 0x80000008 0x8000001E 0x8000001F; do\n'
old += '    cpuid -1 -l "$leaf" 2>/dev/null | base64 -w0 | jq -c -Rs --arg leaf "$leaf" \\\n'
old += '      \'{section:"cpuid_leaf",leaf:$leaf,data:.}\' >> "$OUT"\n'
old += '  done\n'
old += 'fi\n'

new = '# Classic cpuid per-leaf dumps: only when the binary really supports -1/-l.\n'
new += '# Arch minimal cpuid prints usage to stderr otherwise, yielding empty records.\n'
new += 'if have cpuid && cpuid -1 -l 0 2>/dev/null | grep -q .; then\n'
new += '  cpuid -1 2>/dev/null | base64 -w0 | jq -c -Rs \'{section:"cpuid",sub:"raw_b64",data:.}\' >> "$OUT"\n'
new += '  for leaf in 0 1 7 0x80000000 0x80000001 0x80000002 0x80000003 0x80000004 0x80000006 0x80000007 0x80000008 0x8000001E 0x8000001F; do\n'
new += '    cpuid -1 -l "$leaf" 2>/dev/null | base64 -w0 | jq -c -Rs --arg leaf "$leaf" \\\n'
new += '      \'{section:"cpuid_leaf",leaf:$leaf,data:.}\' >> "$OUT"\n'
new += '  done\n'
new += 'fi\n'

assert old in s, "pattern not found in hw-audit.sh"
s = s.replace(old, new)
open(p, "w", encoding="utf-8").write(s)
print("patched OK")
