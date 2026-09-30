import re, os

files = {
    "src/components/playground/SpeechInterface.svelte": "../../lib/apiBase",
    "src/lib/audioApi.ts": "./apiBase",
    "src/lib/chatApi.ts": "./apiBase",
    "src/lib/imageApi.ts": "./apiBase",
    "src/lib/rerankApi.ts": "./apiBase",
    "src/lib/sdApi.ts": "./apiBase",
    "src/lib/speechApi.ts": "./apiBase",
    "src/stores/api.ts": "../lib/apiBase",
    "src/stores/modelLogs.ts": "../lib/apiBase",
}

base = "/tmp/ranch-work/ui"
pat = re.compile(r'fetch\(\s*("(?:[^"\\]|\\.)*"|`(?:[^`\\]|\\.)*`|url)\s*(?=[,)])')

changed = []
for rel, imp in files.items():
    p = os.path.join(base, rel)
    if not os.path.exists(p):
        print("MISSING", rel)
        continue
    src = open(p).read()

    def repl(m):
        arg = m.group(1)
        inner = arg[1:-1] if arg[0] in "\"`" else arg
        if arg == "url" or inner.startswith("/"):
            return "fetch(api(" + arg + ")"
        return m.group(0)

    new = pat.sub(repl, src)
    if new != src:
        if "apiBase" not in new:
            stmt = 'import { api } from "%s";\n' % imp
            if rel.endswith(".svelte"):
                new = re.sub(
                    r"(<script[^>]*>\s*\n)(\s*import)",
                    lambda m: m.group(1) + stmt.rstrip("\n") + "\n" + m.group(2),
                    new,
                    count=1,
                )
            else:
                m2 = re.search(r"^import .*$", new, re.M)
                if m2:
                    new = new[: m2.start()] + stmt + new[m2.start() :]
                else:
                    new = stmt + new
        open(p, "w").write(new)
        changed.append(rel)

print("changed:", len(changed))
for c in changed:
    print(" ", c)
