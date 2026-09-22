#!/usr/bin/env python3
import sys
sys.path.insert(0, "/tmp")
import importlib.util
spec = importlib.util.spec_from_file_location("prs", "/tmp/parse_rs.py")
prs = importlib.util.module_from_spec(spec)
spec.loader.exec_module(prs)
import sqlite3, traceback
db = sqlite3.connect("file:/tmp/nimbus-audit-20260921-172124/3870112724rsegmnoittet-es.sqlite?mode=ro", uri=True)
c = db.cursor()
target = sys.argv[1]
for (k, d) in c.execute("SELECT key,data FROM object_data WHERE object_store_id=1"):
    cid, rid = prs.dec_key(k)
    if target in rid:
        print("decoding", rid, "bloblen", len(d), flush=True)
        try:
            rec = prs.P(b"").record(d)
            print("OK", sorted(rec.keys()), flush=True)
        except Exception as e:
            traceback.print_exc()
        break
