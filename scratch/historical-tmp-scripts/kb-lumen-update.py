import sys
from pathlib import Path
kb = Path(sys.argv[1])
lines = kb.read_text().splitlines(keepends=True)
for i, l in enumerate(lines):
    if l.startswith("| lumen |"):
        assert "0b33559ad2" not in l, "already updated"
        l = l.rstrip("\n")
        assert l.endswith("|"), l[-40:]
        l = l[:-1] + " markdown render + full bodies 0b33559ad2 (truncate dropped, escape-first md renderer, keeper-verified live) |\n"
        lines[i] = l
        print("lumen row updated")
        break
else:
    print("lumen row not found")
    sys.exit(1)
kb.write_text("".join(lines))
