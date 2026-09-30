import sqlite3
db = sqlite3.connect('/home/toxic/sovereign/data/ast_matrix.db')
rows = db.execute("SELECT provider, status, COUNT(*) FROM requests WHERE ts > strftime('%s','now')-600 GROUP BY provider, status ORDER BY provider").fetchall()
for p, s, c in rows:
    print(p, s, 'x'+str(c))
