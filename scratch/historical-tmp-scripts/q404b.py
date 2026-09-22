import sqlite3
db = sqlite3.connect('/home/toxic/sovereign/data/ast_matrix.db')
rows = db.execute("SELECT model, COUNT(*) FROM requests WHERE provider='google' AND status=404 AND ts > strftime('%s','now')-1800 GROUP BY model").fetchall()
for m, c in rows: print(c, 'x', m)
