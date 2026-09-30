#!/usr/bin/env python3
"""Nimbus/RS enrollment audit: decode the Remote Settings IDB snapshot (read-only)."""
import sqlite3, json, sys, datetime

DB = sys.argv[1] if len(sys.argv) > 1 else "/tmp/nimbus-audit-20260921-172124/3870112724rsegmnoittet-es.sqlite"

def rot1(b: bytes) -> str:
    return bytes((x - 1) & 0xff for x in b).decode("utf-8", "replace")

def snappy_raw(data: bytes) -> bytes:
    pos = 0; shift = 0; n = 0
    while True:
        b = data[pos]; pos += 1
        n |= (b & 0x7f) << shift
        if not (b & 0x80):
            break
        shift += 7
    out = bytearray()
    mv = memoryview(data)
    while pos < len(data):
        tag = data[pos]; pos += 1
        t = tag & 0x03
        if t == 0:
            ln = tag >> 2
            if ln < 60:
                ln += 1
            else:
                nb = ln - 59
                ln = int.from_bytes(mv[pos:pos+nb], "little") + 1
                pos += nb
            out += mv[pos:pos+ln]; pos += ln
        else:
            if t == 1:
                ln = ((tag >> 2) & 0x07) + 4
                off = ((tag >> 5) << 8) | data[pos]; pos += 1
            elif t == 2:
                ln = (tag >> 2) + 1
                off = int.from_bytes(mv[pos:pos+2], "little"); pos += 2
            else:
                ln = (tag >> 2) + 1
                off = int.from_bytes(mv[pos:pos+4], "little"); pos += 4
            start = len(out) - off
            for i in range(ln):
                out.append(out[start + i])
    assert len(out) == n, (len(out), n)
    return bytes(out)

def ts(x):
    if not x:
        return "?"
    return datetime.datetime.fromtimestamp(x / 1000 if x > 1e12 else x,
           datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

db = sqlite3.connect("file:%s?mode=ro" % DB, uri=True)
c = db.cursor()

# ---- collections meta (store 3) ----
coll_meta = {}
for (k, d) in c.execute("SELECT key,data FROM object_data WHERE object_store_id=3"):
    cid = rot1(k)
    try:
        coll_meta[cid] = json.loads(snappy_raw(d))
    except Exception as e:
        coll_meta[cid] = {"_decode_error": str(e)}

# ---- timestamps (store 2) ----
sync_ts = {}
for (k, d) in c.execute("SELECT key,data FROM object_data WHERE object_store_id=2"):
    cid = rot1(k)
    try:
        sync_ts[cid] = json.loads(snappy_raw(d))
    except Exception as e:
        sync_ts[cid] = {"_decode_error": str(e)}

# ---- records (store 1) ----
records = {}   # cid -> list of (id, rec)
decode_fail = 0
for (k, d) in c.execute("SELECT key,data FROM object_data WHERE object_store_id=1"):
    key = k[1:] if k[:1] == b"\x80" else k
    parts = key.split(b"\x00")
    cid = rot1(parts[0]); rid = rot1(parts[1]) if len(parts) > 1 else "?"
    try:
        rec = json.loads(snappy_raw(d))
    except Exception:
        decode_fail += 1
        continue
    records.setdefault(cid, []).append((rid, rec))

print("=== PER-COLLECTION SUMMARY ===")
print("decode failures: %d" % decode_fail)
total = 0
for cid in sorted(records):
    recs = records[cid]
    total += len(recs)
    newest = max((r.get("last_modified", 0) for _, r in recs), default=0)
    meta = coll_meta.get(cid, {})
    sync = sync_ts.get(cid, {})
    print("COLL %-60s n=%-5d newest_record=%s" % (cid, len(recs), ts(newest)))
    print("     sync_meta=%s" % json.dumps(sync)[:200])
    if meta and not str(meta).startswith('{"_decode'):
        print("     coll_meta_keys=%s" % sorted(meta.keys())[:8])
print("TOTAL records:", total)

print("\n=== SYNC TIMESTAMP STORE (raw) ===")
for cid in sorted(sync_ts):
    print("%-60s %s" % (cid, json.dumps(sync_ts[cid])[:160]))

print("\n=== NIMBUS RECIPE ENUMERATION ===")
for bucket in ("/main/nimbus-desktop-experiments", "/main/nimbus-secure-experiments"):
    recs = records.get(bucket, [])
    print("## %s : %d recipes" % (bucket, len(recs)))
    for rid, r in sorted(recs, key=lambda x: x[0]):
        slug = r.get("slug") or r.get("id") or rid
        print(json.dumps({
            "slug": slug,
            "isRollout": r.get("isRollout"),
            "isEnrollmentPaused": r.get("isEnrollmentPaused"),
            "last_modified": ts(r.get("last_modified", 0)),
            "branches": [b.get("slug") for b in r.get("branches", [])],
            "featureIds": (r.get("experimentType") and [r.get("experimentType")]) or
                          [f.get("featureId") for f in r.get("featureConfig", {}).get("features", [])] or
                          list((r.get("features") or {}).keys()) or
                          [r.get("featureId")] if r.get("featureId") else None,
            "targeting": (r.get("targeting") or "")[:120],
            "bucket": r.get("bucketConfig", {}).get("namespace"),
        }, indent=None))
