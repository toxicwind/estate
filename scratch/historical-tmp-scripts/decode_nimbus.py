import sqlite3, struct, re, datetime
con = sqlite3.connect('/tmp/rsdb/rs.sqlite')
cur = con.cursor()
stores = {r[1]: r[0] for r in cur.execute("SELECT id, name FROM object_store").fetchall()}
rid = stores['records']
# find nimbus records: key contains 'nimbus-desktop-experiments' (+1 shifted in key col)
rows = cur.execute("SELECT key, data FROM object_data WHERE object_store_id=?", (rid,)).fetchall()
print("total records:", len(rows))
nimbus = []
for key, data in rows:
    ks = key.decode('utf-8', 'ignore')
    # shift -1 to decode
    dec = ''.join(chr((ord(c) - 1) % 256) if 32 <= ord(c) < 127 else c for c in ks)
    if 'nimbus-desktop-experiments' in dec:
        nimbus.append((key, data, dec))
print("nimbus-desktop-experiments records:", len(nimbus))
# check last_modified values in record data blobs
for key, data, dec in nimbus[:3]:
    hits = []
    for i in range(len(data) - 7):
        v = struct.unpack('<d', data[i:i+8])[0]
        if 1577836800000 < v < 1830297600000:
            ts = datetime.datetime.fromtimestamp(v/1000, datetime.timezone.utc)
            hits.append(ts.strftime('%Y-%m-%d %H:%M'))
    uniq = sorted(set(hits))
    print(dec[:80], '->', ', '.join(uniq[:4]) if uniq else 'none')
