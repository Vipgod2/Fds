import asyncio
import re
from telethon import TelegramClient, events, Button
from telethon.tl.functions.messages import ForwardMessagesRequest
from telethon.tl.types import PeerChannel

# === CONFIG ===
api_id = 23416992
api_hash = 'bebe7b8b7bc74aeaa08f658e8aa799fe'
bot_token = '7666600493:AAGCCLNZQspatmzwylmcpM-AQUo1FI2FYMA'  # Replace with your actual bot token
# ==============

bot = TelegramClient('forwardbot', api_id, api_hash).start(bot_token=bot_token)
forward_sessions = {}

@bot.on(events.NewMessage(pattern=r'/fwd (https?://t\.me/[^/]+/\d+)(?:\s+(\d+))?'))
async def start_forward(event):
    match = re.match(r'https?://t\.me/([^/]+)/(\d+)', event.pattern_match.group(1))
    if not match:
        await event.reply("❌ Invalid message link.")
        return

    src_channel = match.group(1)
    start_id = int(match.group(2))
    end_id = int(event.pattern_match.group(2)) if event.pattern_match.group(2) else start_id

    try:
        src_entity = await bot.get_entity(src_channel)
    except Exception as e:
        await event.reply(f"❌ Could not find source channel: {e}")
        return

    forward_sessions[event.sender_id] = {
        "src_entity": src_entity,
        "start_id": start_id,
        "end_id": end_id,
        "dst_chat": event.chat_id
    }

    await event.reply(
        f"Forward messages from ID `{start_id}` to `{end_id}` from `{src_channel}` to this chat?",
        buttons=[
            [Button.inline("✅ Yes", b'start_forward')],
            [Button.inline("❌ Cancel", b'cancel_forward')]
        ]
    )

@bot.on(events.CallbackQuery(data=b'start_forward'))
async def confirm_forward(event):
    session = forward_sessions.pop(event.sender_id, None)
    if not session:
        await event.answer("❌ No session found.", alert=True)
        return

    await event.edit("⏳ Forwarding messages...")

    for msg_id in range(session["start_id"], session["end_id"] + 1):
        try:
            await bot(ForwardMessagesRequest(
                from_peer=session["src_entity"],
                id=[msg_id],
                to_peer=session["dst_chat"]
            ))
        except Exception as e:
            print(f"Failed to forward {msg_id}: {e}")
        await asyncio.sleep(1.0)

    await bot.send_message(session["dst_chat"], "✅ Forwarding completed.")

@bot.on(events.CallbackQuery(data=b'cancel_forward'))
async def cancel_forward(event):
    forward_sessions.pop(event.sender_id, None)
    await event.edit("❌ Forwarding cancelled.")

print("Bot is running...")
bot.run_until_disconnected()
