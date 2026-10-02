import sqlite3, msgpack, json, sys
con = sqlite3.connect('file:/home/toxic/.openfang/data/openfang.db?mode=ro', uri=True)
tables = [r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")]
print("tables:", tables, file=sys.stderr)
for t in tables:
    try:
        cols = [c[1] for c in con.execute(f"PRAGMA table_info({t})")]
        print(f"--- {t}: {cols}", file=sys.stderr)
        for row in con.execute(f"SELECT * FROM {t} LIMIT 3"):
            s = str(row)
            if '4e15ae1e' in s or 'assistant' in s.lower():
                print(f"MATCH in {t}:", s[:500])
    except Exception as e:
        print(f"{t}: {e}", file=sys.stderr)
