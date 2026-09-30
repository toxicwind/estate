import sqlite3
c = sqlite3.connect("/storage/.kodi/userdata/addon_data/plugin.video.redlight/databases/settings.db")
rows = c.execute("SELECT setting_id, setting_value FROM settings").fetchall()
pats = ["trakt", "monitor", "background", "startup", "auto_start", "widget_refresh", "autostart"]
for sid, val in rows:
    s = sid.lower()
    if any(p in s for p in pats):
        print(sid, "=", val)
