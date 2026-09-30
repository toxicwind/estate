import sqlite3, datetime
db = sqlite3.connect('/home/toxic/sovereign/data/ast_matrix.db')
rows = db.execute("SELECT ts, provider, model, status FROM requests WHERE status=404 AND ts > strftime('%s','now')-900 ORDER BY ts DESC LIMIT 6").fetchall()
for r in rows:
    t = datetime.datetime.fromtimestamp(r[0], datetime.timezone.utc).strftime('%H:%M:%S')
    print(t, r[1], r[3], r[2][:50])
