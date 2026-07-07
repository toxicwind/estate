#!/usr/bin/env python3
"""
Telethon Overlord – production version
Based on: https://github.com/LonamiWebs/Telethon/tree/v1/telethon_examples
- print_messages.py
- print_updates.py

Emits one JSON line per new message to stdout (perfect for n8n, pipelines, or logging).
"""

import os, sys, json, asyncio, logging
from dotenv import load_dotenv
from telethon import TelegramClient, events, utils
from telethon.sessions import StringSession

load_dotenv()
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s %(message)s')

# Support both your names and the upstream TG_* names
API_ID = int(os.getenv('TELEGRAM_API_ID') or os.getenv('TG_API_ID') or 0)
API_HASH = os.getenv('TELEGRAM_API_HASH') or os.getenv('TG_API_HASH') or ''
SESSION_STR = os.getenv('TELEGRAM_SESSION') or os.getenv('TG_SESSION') or 'overlord'
CHANNELS = [c.strip() for c in os.getenv('TELEGRAM_CHANNELS', '').split(',') if c.strip()]

if not API_ID or not API_HASH:
    logging.error("Set TELEGRAM_API_ID and TELEGRAM_API_HASH in .env – get them from https://my.telegram.org")
    sys.exit(1)

# Use StringSession if you pasted a long string, else file session
try:
    session = StringSession(SESSION_STR) if len(SESSION_STR) > 50 else SESSION_STR
except ValueError:
    logging.warning("TELEGRAM_SESSION is not a valid StringSession format. Falling back to file session 'overlord'.")
    session = 'overlord'

client = TelegramClient(session, API_ID, API_HASH)

@client.on(events.NewMessage(chats=CHANNELS if CHANNELS else None))
async def handler(event):
    sender = await event.get_sender()
    data = {
        "chat_id": event.chat_id,
        "chat_title": getattr(event.chat, 'title', None),
        "sender": utils.get_display_name(sender),
        "sender_id": event.sender_id,
        "text": event.message.message,
        "date": event.date.isoformat(),
        "id": event.id
    }
    # print JSON for n8n/OpenFang/yote to consume
    print(json.dumps(data), flush=True)

async def main():
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN_OVERLORD')
    if bot_token:
        logging.info("Starting Telethon with Bot Token...")
        await client.start(bot_token=bot_token)
    else:
        logging.info("Starting Telethon (interactive/session)...")
        await client.start()
        
    me = await client.get_me()
    logging.info(f"Overlord connected as {me.username} – listening to {CHANNELS or 'ALL'}")
    await client.run_until_disconnected()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
