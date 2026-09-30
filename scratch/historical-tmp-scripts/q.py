import sqlite3
c = sqlite3.connect("/storage/.kodi/userdata/addon_data/plugin.video.redlight/databases/settings.db")
pats = ["monitor", "simkl", "mdblist", "punch", "expiry", "service"]
rows = c.execute("SELECT setting_id, setting_value FROM settings").fetchall()
for sid, val in rows:
    s = sid.lower()
    if any(p in s for p in pats):
        print(sid, "=", val)
print("total:", len(rows))
