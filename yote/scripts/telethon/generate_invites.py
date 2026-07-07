import os
import asyncio
from telethon import TelegramClient
from telethon.tl.functions.messages import ExportChatInviteRequest
from dotenv import load_dotenv

load_dotenv()

API_ID = int(os.getenv('TELEGRAM_API_ID') or 30317797)
API_HASH = os.getenv('TELEGRAM_API_HASH') or 'f4037e7c41dc5bc4bb0a7f96608e475c'
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN') or '8932201107:AAEZ7I2NBcGR_CcJvT9IjKwbZ8honLNc_zM'
TARGET_USER = int(os.getenv('TARGET_USER') or 716302190)

client = TelegramClient('bot_invite_session', API_ID, API_HASH)

async def main():
    await client.start(bot_token=BOT_TOKEN)
    print("Bot connected via MTProto!")
    
    dialogs = await client.get_dialogs()
    print(f"Found {len(dialogs)} dialogs/chats.")
    
    for dialog in dialogs:
        if dialog.is_group or dialog.is_channel:
            try:
                # Generate invite link
                link = await client(ExportChatInviteRequest(peer=dialog.id))
                invite_url = link.link
                print(f"Chat: {dialog.name} ({dialog.id}) -> Invite: {invite_url}")
                # Send to target user
                await client.send_message(TARGET_USER, f"Invite link for *{dialog.name}*:\n{invite_url}", parse_mode='markdown')
            except Exception as e:
                print(f"Failed to generate invite for {dialog.name}: {e}")

if __name__ == '__main__':
    asyncio.run(main())
