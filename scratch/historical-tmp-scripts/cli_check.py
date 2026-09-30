import sys
sys.path.insert(0, "/home/toxic/sovereign/projects/mesh/squawk")
from pathlib import Path
import chat
p = Path("/home/toxic/.shingle/squawk-root/fleet/11978-estate-reconcile.md")
for fn in ("parse_message_file", "parse_frontmatter", "read_message"):
    if hasattr(chat, fn):
        try:
            rec = getattr(chat, fn)(p)
            print(fn, "->", str(rec)[:160])
        except Exception as e:
            print(fn, "ERR", str(e)[:120])
