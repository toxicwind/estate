import sqlite3, struct, re, datetime
con = sqlite3.connect('/tmp/rsdb/rs.sqlite')
cur = con.cursor()
sid = cur.execute("SELECT id FROM object_store WHERE name='timestamps'").fetchone()[0]
rows = cur.execute("SELECT key, data FROM object_data WHERE object_store_id=?", (sid,)).fetchall()
print("collections with sync timestamps:", len(rows))
for key, data in sorted(rows):
    ks = key.decode('utf-8', 'ignore')
    m = re.search(r'main/[A-Za-z0-9_\-\.]+', ks)
    name = m.group(0) if m else ks[:40]
    hits = []
    for i in range(len(data) - 7):
        v = struct.unpack('<d', data[i:i+8])[0]
        if 1577836800000 < v < 1830297600000:
            ts = datetime.datetime.fromtimestamp(v/1000, datetime.timezone.utc)
            hits.append(ts.strftime('%Y-%m-%d %H:%M UTC'))
    uniq = sorted(set(hits))
    print(name, '->', ', '.join(uniq) if uniq else 'NO TIMESTAMP FOUND')
