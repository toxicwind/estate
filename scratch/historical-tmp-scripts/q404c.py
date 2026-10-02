import sqlite3, datetime
db = sqlite3.connect('/home/toxic/sovereign/data/ast_matrix.db')
rows = db.execute("SELECT ts FROM requests WHERE provider='google' AND model='models/gemini-2.5-flash' AND status=404 AND ts > strftime('%s','now')-1800 ORDER BY ts").fetchall()
for (ts,) in rows:
    print(datetime.datetime.fromtimestamp(ts, datetime.timezone.utc).strftime('%H:%M:%S'))
