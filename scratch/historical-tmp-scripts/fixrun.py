import sqlite3, time
db = sqlite3.connect("/home/toxic/.super-ralph/workflow.db")
now = int(time.time() * 1000)
cur = db.execute(
    "UPDATE _smithers_runs SET status='cancelled', finished_at_ms=? "
    "WHERE run_id='sr-mub8qjzz-abbb8b19' AND status='running'", (now,))
db.execute(
    "UPDATE _smithers_attempts SET state='cancelled', finished_at_ms=? "
    "WHERE run_id='sr-mub8qjzz-abbb8b19' AND state='in-progress'", (now,))
db.commit()
print("runs updated:", cur.rowcount)
print(db.execute("SELECT run_id, status FROM _smithers_runs "
                 "WHERE run_id='sr-mub8qjzz-abbb8b19'").fetchall())
