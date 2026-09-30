#!/usr/bin/env python3
"""Seed elo_state in the LIVE HealthDB from the running router's /status.

Run this immediately before the owned restart so the newly deployed
Elo-persistence code restores live-learned values instead of priors.
"""
import json
import sqlite3
import time
import urllib.request

DB = "/home/toxic/sovereign/data/sovereign_router.db"

st = json.load(urllib.request.urlopen("http://127.0.0.1:25104/status", timeout=15))
elos = {p: float(v["elo"]) for p, v in st["providers"].items()}

db = sqlite3.connect(DB, timeout=15)
db.execute(
    """CREATE TABLE IF NOT EXISTS elo_state (
         provider TEXT PRIMARY KEY,
         elo REAL NOT NULL,
         updated_at REAL NOT NULL
       )"""
)
now = time.time()
for p, e in elos.items():
    db.execute(
        """INSERT INTO elo_state (provider, elo, updated_at)
           VALUES (?,?,?)
           ON CONFLICT(provider) DO UPDATE SET
             elo=excluded.elo, updated_at=excluded.updated_at""",
        (p, e, now),
    )
db.commit()
rows = db.execute("SELECT provider, elo FROM elo_state ORDER BY provider").fetchall()
db.close()
print("seeded:", json.dumps(elos, sort_keys=True))
print("in-db:", json.dumps({p: e for p, e in rows}, sort_keys=True))
assert {p: e for p, e in rows} == elos, "DB contents do not match /status"
print("SEED OK")
