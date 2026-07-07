import os
import asyncio
from telethon import TelegramClient
from telethon.tl.functions.channels import InviteToChannelRequest
from telethon.tl.functions.messages import AddChatUserRequest
from dotenv import load_dotenv

load_dotenv()

API_ID = int(os.getenv('TELEGRAM_API_ID') or 30317797)
API_HASH = os.getenv('TELEGRAM_API_HASH') or 'f4037e7c41dc5bc4bb0a7f96608e475c'

client = TelegramClient('sovfang', API_ID, API_HASH)

async def main():
    await client.connect()
    if not await client.is_user_authorized():
        print("Session is not authorized. Please run authorization first.")
        return

    print("User session connected via MTProto!")
    
    dialogs = await client.get_dialogs()
    print(f"Found {len(dialogs)} dialogs/chats.")
    
    target_username = 'puppertrix'
    
    for dialog in dialogs:
        if dialog.is_group or dialog.is_channel:
            try:
                if dialog.is_channel:
                    await client(InviteToChannelRequest(
                        channel=dialog.id,
                        users=[target_username]
                    ))
                else:
                    await client(AddChatUserRequest(
                        chat_id=dialog.id,
                        user_id=target_username,
                        fwd_limit=0
                    ))
                print(f"Successfully invited {target_username} to {dialog.name}")
            except Exception as e:
                print(f"Failed to invite {target_username} to {dialog.name}: {e}")

if __name__ == '__main__':
    asyncio.run(main())
