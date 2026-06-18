#!/usr/bin/env python3
"""
yote_telegram.py — Autonomous Telegram bot service for Sovereign Stack
Bot: @crawlspace_coyote_bot (identity: Yote)

Handles:
  - /start → registers chat, sends welcome
  - /status → shows stack health
  - /chat <msg> → forwards to OpenFang default agent
  - Incoming text → proxied to nfcot_proxy for inference
  - Boot notification on startup
"""
import os, sys, time, json, logging, requests, threading
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s %(message)s',
    handlers=[
        logging.FileHandler('/home/toxic/sovereign/logs/yote_telegram.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
log = logging.getLogger("yote")

# ── Config ───────────────────────────────────────────────────────────
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
ALLOWED_USERS = os.environ.get("TELEGRAM_ALLOWED_USERS", "13036673831")
ALLOWED_IDS = set()
for u in ALLOWED_USERS.split(","):
    u = u.strip()
    if u.isdigit():
        ALLOWED_IDS.add(int(u))

NFCOT_URL = "http://127.0.0.1:25008/v1/chat/completions"
LLAMA_HEALTH = "http://127.0.0.1:25001/health"
NFCOT_HEALTH = "http://127.0.0.1:25008/v1/models"
OPENFANG_HEALTH = "http://127.0.0.1:25004/api/health"

REGISTERED_CHATS_FILE = "/home/toxic/sovereign/config/yote_chats.json"

# ── State ────────────────────────────────────────────────────────────
registered_chats = {}
last_update_id = 0


def load_chats():
    global registered_chats
    try:
        if os.path.exists(REGISTERED_CHATS_FILE):
            with open(REGISTERED_CHATS_FILE) as f:
                registered_chats = json.load(f)
            log.info(f"Loaded {len(registered_chats)} registered chats")
    except Exception as e:
        log.error(f"Failed to load chats: {e}")


def save_chats():
    try:
        os.makedirs(os.path.dirname(REGISTERED_CHATS_FILE), exist_ok=True)
        with open(REGISTERED_CHATS_FILE, "w") as f:
            json.dump(registered_chats, f, indent=2)
    except Exception as e:
        log.error(f"Failed to save chats: {e}")


def tg_api(method, **kwargs):
    """Call Telegram Bot API."""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/{method}"
    try:
        r = requests.post(url, json=kwargs, timeout=30)
        return r.json()
    except Exception as e:
        log.error(f"TG API {method} failed: {e}")
        return {"ok": False}


def send_msg(chat_id, text, parse_mode="Markdown", message_thread_id=None):
    """Send a message, splitting if too long."""
    MAX = 4000
    kwargs = {"chat_id": chat_id, "text": text, "parse_mode": parse_mode}
    if message_thread_id is not None:
        kwargs["message_thread_id"] = message_thread_id

    if len(text) <= MAX:
        return tg_api("sendMessage", **kwargs)
    # Split on newlines
    chunks = []
    current = ""
    for line in text.split("\n"):
        if len(current) + len(line) + 1 > MAX:
            chunks.append(current)
            current = line
        else:
            current += "\n" + line if current else line
    if current:
        chunks.append(current)
    for chunk in chunks:
        kwargs["text"] = chunk
        tg_api("sendMessage", **kwargs)
        time.sleep(0.3)


def check_health():
    """Quick stack health check."""
    results = {}
    for name, url in [("llama", LLAMA_HEALTH), ("nfcot", NFCOT_HEALTH), ("openfang", OPENFANG_HEALTH)]:
        try:
            r = requests.get(url, timeout=3)
            results[name] = r.status_code == 200
        except:
            results[name] = False
    return results


def handle_start(chat_id, user, message_thread_id=None):
    """Register a chat and send welcome."""
    user_id = user.get("id", 0)
    username = user.get("username", "unknown")
    first_name = user.get("first_name", "")

    registered_chats[str(chat_id)] = {
        "user_id": user_id,
        "username": username,
        "first_name": first_name,
        "registered_at": datetime.utcnow().isoformat()
    }
    if message_thread_id is not None:
        registered_chats[str(chat_id)]["message_thread_id"] = message_thread_id
    save_chats()

    health = check_health()
    status_lines = []
    for svc, ok in health.items():
        status_lines.append(f"  • {svc}: {'✅' if ok else '❌'}")

    send_msg(chat_id,
        f"🐺 *Yote is online.*\n\n"
        f"Welcome, {first_name}. You're registered.\n\n"
        f"*Stack Status:*\n" + "\n".join(status_lines) + "\n\n"
        f"*Commands:*\n"
        f"  /status — stack health\n"
        f"  /chat <message> — talk to the AI\n"
        f"  Any text → direct inference\n",
        message_thread_id=message_thread_id
    )
    log.info(f"Registered chat {chat_id} (thread {message_thread_id}) for user {username} ({user_id})")


def handle_status(chat_id, message_thread_id=None):
    """Send stack status."""
    health = check_health()
    lines = ["🐺 *Yote — Stack Status*\n"]
    port_map = {"llama": 25001, "nfcot": 25008, "openfang": 25004}
    for svc, ok in health.items():
        port = port_map.get(svc, "?")
        lines.append(f"  • {svc} (:{port}): {'✅ UP' if ok else '❌ DOWN'}")

    # GPU info
    try:
        import subprocess
        out = subprocess.run(
            ['nvidia-smi', '--query-gpu=memory.used,memory.total,temperature.gpu,utilization.gpu',
             '--format=csv,noheader,nounits'],
            capture_output=True, text=True, timeout=5
        )
        if out.returncode == 0:
            parts = [p.strip() for p in out.stdout.strip().split(',')]
            lines.append(f"\n*GPU:* {parts[0]}/{parts[1]} MB | {parts[2]}°C | {parts[3]}% util")
    except:
        pass

    lines.append(f"\n_Updated: {datetime.utcnow().strftime('%H:%M:%S UTC')}_")
    send_msg(chat_id, "\n".join(lines), message_thread_id=message_thread_id)


def handle_chat(chat_id, text, message_thread_id=None):
    """Forward to nfcot_proxy for inference."""
    tg_api("sendChatAction", chat_id=chat_id, action="typing", message_thread_id=message_thread_id)

    try:
        payload = {
            "model": "qwen3.6-27b",
            "messages": [
                {"role": "system", "content": "You are Yote, a sovereign AI assistant running on local hardware (RTX 3090, Ryzen 7 8700F). Be concise, direct, and helpful. You are part of the Sovereign Stack."},
                {"role": "user", "content": text}
            ],
            "max_tokens": 1024,
            "temperature": 0.7,
        }
        r = requests.post(NFCOT_URL, json=payload, timeout=120)
        if r.ok:
            data = r.json()
            reply = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            if reply:
                send_msg(chat_id, reply, parse_mode=None, message_thread_id=message_thread_id)
            else:
                send_msg(chat_id, "⚠️ Empty response from model.", parse_mode=None, message_thread_id=message_thread_id)
        else:
            send_msg(chat_id, f"⚠️ Inference error: HTTP {r.status_code}", parse_mode=None, message_thread_id=message_thread_id)
    except requests.exceptions.Timeout:
        send_msg(chat_id, "⏳ Request timed out (model may be under load).", parse_mode=None, message_thread_id=message_thread_id)
    except Exception as e:
        log.error(f"Chat error: {e}")
        send_msg(chat_id, f"⚠️ Error: {e}", parse_mode=None, message_thread_id=message_thread_id)


def process_update(update):
    """Process a single Telegram update."""
    global last_update_id
    update_id = update.get("update_id", 0)
    if update_id > last_update_id:
        last_update_id = update_id

    msg = update.get("message")
    if not msg:
        return

    chat_id = msg.get("chat", {}).get("id")
    message_thread_id = msg.get("message_thread_id")
    user = msg.get("from", {})
    user_id = user.get("id", 0)
    text = msg.get("text", "").strip()

    if not chat_id or not text:
        return

    # Access control
    if ALLOWED_IDS and user_id not in ALLOWED_IDS:
        log.warning(f"Unauthorized user {user_id} ({user.get('username', '?')})")
        send_msg(chat_id, "🔒 Unauthorized.", parse_mode=None, message_thread_id=message_thread_id)
        return

    # Route commands
    if text == "/start":
        handle_start(chat_id, user, message_thread_id=message_thread_id)
    elif text == "/status":
        handle_status(chat_id, message_thread_id=message_thread_id)
    elif text.startswith("/chat "):
        handle_chat(chat_id, text[6:].strip(), message_thread_id=message_thread_id)
    elif text.startswith("/"):
        send_msg(chat_id, "Unknown command. Try /status or /chat <message>", parse_mode=None, message_thread_id=message_thread_id)
    else:
        # Direct text → inference
        handle_chat(chat_id, text, message_thread_id=message_thread_id)


def send_boot_notification():
    """Send boot message to all registered chats."""
    health = check_health()
    lines = ["🟢 *Yote — Stack Boot Complete*\n"]
    port_map = {"llama": 25001, "nfcot": 25008, "openfang": 25004}
    for svc, ok in health.items():
        port = port_map.get(svc, "?")
        lines.append(f"  • {svc} (:{port}): {'✅' if ok else '❌'}")
    lines.append(f"\n_{datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}_")
    msg = "\n".join(lines)

    for chat_id, chat_info in registered_chats.items():
        thread_id = chat_info.get("message_thread_id")
        send_msg(int(chat_id), msg, message_thread_id=thread_id)
        log.info(f"Sent boot notification to chat {chat_id} (thread {thread_id})")


def poll_loop():
    """Long-polling loop for Telegram updates."""
    global last_update_id
    log.info("Starting Telegram long-poll loop")

    while True:
        try:
            params = {"timeout": 30, "allowed_updates": ["message"]}
            if last_update_id:
                params["offset"] = last_update_id + 1

            r = requests.get(
                f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates",
                params=params, timeout=35
            )
            if r.ok:
                data = r.json()
                for update in data.get("result", []):
                    try:
                        process_update(update)
                    except Exception as e:
                        log.error(f"Error processing update: {e}")
            else:
                log.warning(f"getUpdates HTTP {r.status_code}")
                time.sleep(5)

        except requests.exceptions.Timeout:
            continue  # Normal for long polling
        except Exception as e:
            log.error(f"Poll error: {e}")
            time.sleep(5)


def main():
    if not BOT_TOKEN:
        log.error("TELEGRAM_BOT_TOKEN not set!")
        sys.exit(1)

    log.info("=" * 50)
    log.info("YOTE TELEGRAM SERVICE — Starting")
    log.info(f"Bot token: ...{BOT_TOKEN[-8:]}")
    log.info(f"Allowed users: {ALLOWED_IDS}")
    log.info("=" * 50)

    load_chats()

    # Wait for stack to come up
    log.info("Waiting for stack health...")
    for _ in range(30):
        health = check_health()
        if health.get("llama") and health.get("nfcot") and health.get("openfang"):
            break
        time.sleep(5)

    # Send boot notification to registered chats
    if registered_chats:
        send_boot_notification()

    # Start polling
    poll_loop()


if __name__ == "__main__":
    main()
