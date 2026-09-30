import sqlite3
con = sqlite3.connect('/tmp/rsdb/rs.sqlite')
cur = con.cursor()
stores = {r[1]: r[0] for r in cur.execute("SELECT id, name FROM object_store").fetchall()}
cid = stores['collections']
rows = cur.execute("SELECT key, data FROM object_data WHERE object_store_id=?", (cid,)).fetchall()
print("collections store rows:", len(rows))
for key, data in rows:
    ks = key.decode('utf-8', 'ignore')
    dec = ''.join(chr((ord(c) - 1) % 256) if 32 <= ord(c) < 127 else c for c in ks)
    # check if data blob has a 'metadata' marker
    has_meta = b'metadata' in data or 'metadata' in dec
    if 'nimbus' in dec:
        print(repr(dec[:70]), 'len(data)=', len(data), 'has_metadata_marker=', has_meta)
