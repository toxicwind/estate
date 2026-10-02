"""Update omp-kimi README for the integrated web gateway."""
import pathlib

p = pathlib.Path("/home/toxic/tau-extensions-merge/packages/omp-kimi/README.md")
text = p.read_text()

old_row = "| `/kimi-web [--port <n>]` | Start `kimi web` detached on loopback (default port 58627) and print the URL + bearer token. Never uses `--dangerous-bypass-auth`. |"
new_row = "| `/kimi-web [--port <n>]` | Start the integrated tau+kimi web gateway on loopback (default port 58627): kimi's full WebUI plus the tau shell (Kimi + collab-web tabs) behind one URL + token. Never uses `--dangerous-bypass-auth`. |"
assert old_row in text, "kimi-web row not found"
text = text.replace(old_row, new_row)

old_stop = "| `/kimi-web-stop` | Stop the web server started by `/kimi-web`. |"
new_stop = "| `/kimi-web-stop` | Stop the web gateway started by `/kimi-web`. |"
assert old_stop in text, "kimi-web-stop row not found"
text = text.replace(old_stop, new_stop)

old_note = "- `/kimi-web` binds loopback only. The bearer token it prints is a secret:\n  don't paste it into chats, tickets, or logs."
new_note = (
    "- `/kimi-web` runs ONE gateway on loopback (default port 58627): kimi's full\n"
    "  WebUI is proxied at `/`, and the tau shell at `/tau/` shows Kimi and\n"
    "  collab-web side by side. The gateway token it prints is a secret: don't\n"
    "  paste it into chats, tickets, or logs. The backend's own bearer token\n"
    "  never leaves the gateway process — it is swapped server-side."
)
assert old_note in text, "loopback note not found"
text = text.replace(old_note, new_note)

old_env = "| `KIMI_DEBUG` | — | Set to `1` for debug logging on stderr. |"
new_env = (
    "| `KIMI_DEBUG` | — | Set to `1` for debug logging on stderr. |\n"
    "| `KIMI_WEB_PORT` | 58627 | Preferred `/kimi-web` gateway port (auto-increments on conflict). |\n"
    "| `TAU_COLLAB_WEB_URL` | — | URL of a collab-web client to embed in the tau shell's Collab tab. |"
)
assert old_env in text, "env table anchor not found"
text = text.replace(old_env, new_env)

p.write_text(text)
print("README updated")
