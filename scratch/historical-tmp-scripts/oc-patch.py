import sys

P = "/home/toxic/sovereign/agents/oracle-market/bin/oracle_chat.py"
src = open(P).read()

OLD = '''def extract_query(meta, body):
    """Return the addressed query text, or None if not for the oracle."""
    if meta.get("from", "").strip().lower() == FROM:
        return None  # own message -- never reply
    m = re.sub(r"^\\s*oracle\\b\\s*[:,]?\\s*", "", body, flags=re.I)
    if m != body:
        q = m.strip()
    elif "@oracle" in body.lower():
        q = re.sub(r"@oracle\\b", "", body, flags=re.I).strip(" :,-\\n")
    else:
        return None
    return q or None'''

NEW = '''def extract_query(meta, body):
    """Return the addressed query text, or None if not for the oracle.

    Address forms: a leading "oracle:" or "oracle," (colon/comma required --
    a bare "oracle <word>" is someone labeling text ABOUT the oracle, e.g.
    "oracle note: ...", not addressing it), or an @oracle mention anywhere.
    """
    if meta.get("from", "").strip().lower() == FROM:
        return None  # own message -- never reply
    m = re.sub(r"^\\s*oracle\\s*[:,]\\s*", "", body, flags=re.I)
    if m != body:
        q = m.strip()
    elif "@oracle" in body.lower():
        q = re.sub(r"@oracle\\b", "", body, flags=re.I).strip(" :,-\\n")
    else:
        return None
    return q or None'''

assert src.count(OLD) == 1, "anchor not found exactly once: %d" % src.count(OLD)
open(P, "w").write(src.replace(OLD, NEW))
print("patched OK")

# regression test the new trigger logic in-process
import importlib.util
spec = importlib.util.spec_from_file_location("oc", P)
oc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(oc)
M = {"from": "ember"}
cases = [
    ("oracle: are you alive?", "are you alive?"),
    ("Oracle, should we ship it?", "should we ship it?"),
    ("  oracle:hi", "hi"),
    ("hey @oracle what do you think?", "hey  what do you think?"),
    ("@oracle: fix the probe", "fix the probe"),
    ("oracle note: this is a label", None),
    ("oracle verdict: triaged things", None),
    ("oracle for the keeper lane", None),
    ("the oracle said no", None),
    ("just chatting here", None),
]
fails = 0
for body, want in cases:
    got = oc.extract_query(M, body)
    ok = (got == want)
    fails += (not ok)
    print(("PASS " if ok else "FAIL "), repr(body), "->", repr(got))
assert oc.extract_query({"from": "oracle"}, "oracle: hi") is None
print("own-message suppression OK")
sys.exit(1 if fails else 0)
