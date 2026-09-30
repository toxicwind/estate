import sqlite3, os
p = os.path.expanduser('~/.local/state/pitchfork/logs.db')
db = sqlite3.connect(p)
for (name, sql) in db.execute("SELECT name, sql FROM sqlite_master"):
    print(name, '::', (sql or '')[:100].replace('\n',' '))
print('---')
try:
    for row in db.execute("SELECT daemon_id, substr(line,1,160), ts FROM daemon_logs ORDER BY rowid DESC LIMIT 8"):
        print(row)
except Exception as e:
    print('q1 err', e)
