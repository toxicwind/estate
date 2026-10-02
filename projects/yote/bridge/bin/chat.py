#!/usr/bin/env python3
"""chat.py — first-class agent coordination chat client.

Talks to chat-coord server on awrawr-pc via tailscale funnel.
Uses same credential as awrawr-mcp (custom.awrawr-mcp).

Usage:
  chat.py join <room> --agent-id <id> [--display-name <name>]
  chat.py send <room> --sender <id> --body <text> [--metadata-json <json>]
  chat.py read <room> [--since-id N] [--limit N]
  chat.py list-rooms
  chat.py list-members <room>
  chat.py leave <room> --agent-id <id>
"""
import json
import sys
import os
import uuid
import asyncio

sys.path.insert(0, "/opt/hatch/skills/skill-creator/bin")
from dynamic_credentials import add_surrogate_to_request

CRED = "custom.awrawr-mcp"
HOST = "github-mcp-host.tailc9ac71.ts.net"
WS_URL = f"wss://{HOST}/chat-ws"

def _get_token_surrogate():
    # Use the same mechanism as exec.py - get surrogate via helper
    # For simplicity, we use exec.py's session approach: call via bridge
    # to get a one-shot token? Instead, we directly use the WS via exec.py
    # remote execution for now (MVP): run chat via remote exec.
    pass

async def _remote_chat(op_data):
    """MVP: run chat operation via exec.py bridge (remote exec to localhost:8380).
    This avoids needing direct WS from cell until funnel is verified.
    """
    import subprocess
    import json as js
    # Build a python one-liner to run on awrawr-pc
    payload = js.dumps(op_data)
    remote_py = f"""
import json, socket
import sys
payload = {payload!r}
data = json.loads(payload)
# Simple HTTP client to chat-coord (we'll add HTTP API later)
# For now, use sqlite directly as fallback
print(json.dumps({{"ok": True, "note": "direct-db-fallback", "op": data}}))
"""
    # Use exec.py via subprocess
    exec_py = os.path.join(os.path.dirname(os.path.abspath(__file__)), "exec.py")
    result = subprocess.run(
        [sys.executable, exec_py, "--json", "--timeout", "15", "--argv",
         "python3", "-c", remote_py],
        capture_output=True, text=True, timeout=30
    )
    try:
        return json.loads(result.stdout)
    except Exception:
        return {"ok": False, "error": result.stdout[:500], "stderr": result.stderr[:500]}

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    cmd = sys.argv[1]
    # For MVP, we implement via direct bridge exec to sqlite
    # Full WS client comes after funnel route is verified
    import subprocess
    exec_py = os.path.join(os.path.dirname(os.path.abspath(__file__)), "exec.py")
    if cmd == "join":
        room = sys.argv[2]
        agent_id = ""
        display_name = ""
        for i, a in enumerate(sys.argv):
            if a == "--agent-id" and i+1 < len(sys.argv):
                agent_id = sys.argv[i+1]
            if a == "--display-name" and i+1 < len(sys.argv):
                display_name = sys.argv[i+1]
        if not display_name:
            display_name = agent_id
        remote_cmd = (
            f"python3 - << 'PYEOF'\n"
            f"import sqlite3, json, os\n"
            f"from datetime import datetime, timezone\n"
            f"db='/home/toxic/chat-coord/data/chat.db'\n"
            f"os.makedirs(os.path.dirname(db), exist_ok=True)\n"
            f"conn=sqlite3.connect(db)\n"
            f"now=datetime.now(timezone.utc).isoformat()\n"
            f"conn.execute('CREATE TABLE IF NOT EXISTS rooms (name TEXT PRIMARY KEY, created_at TEXT, created_by TEXT)')\n"
            f"conn.execute('CREATE TABLE IF NOT EXISTS members (room TEXT, agent_id TEXT, display_name TEXT, joined_at TEXT, last_seen TEXT, PRIMARY KEY (room, agent_id))')\n"
            f"conn.execute('CREATE TABLE IF NOT EXISTS messages (id INTEGER PRIMARY KEY AUTOINCREMENT, room TEXT, sender TEXT, body TEXT, metadata TEXT, ts TEXT)')\n"
            f"conn.execute('INSERT OR IGNORE INTO rooms VALUES (?, ?, ?)', ('{room}', now, '{agent_id}'))\n"
            f"conn.execute('INSERT OR REPLACE INTO members VALUES (?, ?, ?, COALESCE((SELECT joined_at FROM members WHERE room=? AND agent_id=?), ?), ?)', ('{room}', '{agent_id}', '{display_name}', '{room}', '{agent_id}', now, now))\n"
            f"conn.commit()\n"
            f"members=[dict(zip(['agent_id','display_name'], r)) for r in conn.execute('SELECT agent_id, display_name FROM members WHERE room=?', ('{room}',))]\n"
            f"print(json.dumps({{'ok': True, 'room': '{room}', 'members': members}}))\n"
            f"PYEOF"
        )
        r = subprocess.run([sys.executable, exec_py, "--json", "--timeout", "15",
                            "--argv", "bash", "-c", remote_cmd],
                           capture_output=True, text=True, timeout=30)
        print(r.stdout)
    elif cmd == "send":
        room = sys.argv[2]
        sender = ""
        body = ""
        for i, a in enumerate(sys.argv):
            if a == "--sender" and i+1 < len(sys.argv):
                sender = sys.argv[i+1]
            if a == "--body" and i+1 < len(sys.argv):
                body = sys.argv[i+1]
        # Escape single quotes
        body_esc = body.replace("'", "''")
        remote_cmd = (
            f"python3 - << 'PYEOF'\n"
            f"import sqlite3, json\n"
            f"from datetime import datetime, timezone\n"
            f"db='/home/toxic/chat-coord/data/chat.db'\n"
            f"conn=sqlite3.connect(db)\n"
            f"now=datetime.now(timezone.utc).isoformat()\n"
            f"cur=conn.execute('INSERT INTO messages (room, sender, body, metadata, ts) VALUES (?, ?, ?, ?, ?)', ('{room}', '{sender}', '{body_esc}', '{{}}', now))\n"
            f"conn.commit()\n"
            f"print(json.dumps({{'ok': True, 'msg_id': cur.lastrowid}}))\n"
            f"PYEOF"
        )
        r = subprocess.run([sys.executable, exec_py, "--json", "--timeout", "15",
                            "--argv", "bash", "-c", remote_cmd],
                           capture_output=True, text=True, timeout=30)
        print(r.stdout)
    elif cmd == "read":
        room = sys.argv[2]
        since_id = "0"
        limit = "50"
        for i, a in enumerate(sys.argv):
            if a == "--since-id" and i+1 < len(sys.argv):
                since_id = sys.argv[i+1]
            if a == "--limit" and i+1 < len(sys.argv):
                limit = sys.argv[i+1]
        remote_cmd = (
            f"python3 - << 'PYEOF'\n"
            f"import sqlite3, json\n"
            f"db='/home/toxic/chat-coord/data/chat.db'\n"
            f"conn=sqlite3.connect(db)\n"
            f"conn.row_factory=sqlite3.Row\n"
            f"rows=conn.execute('SELECT id, room, sender, body, ts FROM messages WHERE room=? AND id > ? ORDER BY id ASC LIMIT ?', ('{room}', {since_id}, {limit})).fetchall()\n"
            f"msgs=[dict(r) for r in rows]\n"
            f"print(json.dumps({{'ok': True, 'messages': msgs}}))\n"
            f"PYEOF"
        )
        r = subprocess.run([sys.executable, exec_py, "--json", "--timeout", "15",
                            "--argv", "bash", "-c", remote_cmd],
                           capture_output=True, text=True, timeout=30)
        # Parse nested JSON
        try:
            outer = json.loads(r.stdout)
            inner = json.loads(outer.get("stdout", "{}"))
            print(json.dumps(inner, indent=2))
        except Exception:
            print(r.stdout)
    elif cmd == "list-rooms":
        remote_cmd = (
            f"python3 - << 'PYEOF'\n"
            f"import sqlite3, json\n"
            f"db='/home/toxic/chat-coord/data/chat.db'\n"
            f"conn=sqlite3.connect(db)\n"
            f"rooms=[r[0] for r in conn.execute('SELECT name FROM rooms ORDER BY name')]\n"
            f"print(json.dumps({{'ok': True, 'rooms': rooms}}))\n"
            f"PYEOF"
        )
        r = subprocess.run([sys.executable, exec_py, "--json", "--timeout", "15",
                            "--argv", "bash", "-c", remote_cmd],
                           capture_output=True, text=True, timeout=30)
        print(r.stdout)
    else:
        print(f"unknown cmd: {cmd}")
        sys.exit(1)

if __name__ == "__main__":
    main()
