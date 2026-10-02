"""Deprecated — use payload_builder.build() which reads
the live gatehouse catalog."""
import sys, os, json
sys.path.insert(0, os.path.expanduser("/home/toxic/estate"))
from tools.payload_builder import build

def payload(input_text: str, **kw) -> dict:
    return build(input_text, **kw)

if __name__ == "__main__":
    q = sys.argv[1] if len(sys.argv) > 1 else "git status"
    print(json.dumps(payload(q), indent=2))
