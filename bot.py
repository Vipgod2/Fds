import asyncio
import re
from telethon import TelegramClient, events

# ==== CONFIG ====
api_id = 23416992
api_hash = 'bebe7b8b7bc74aeaa08f658e8aa799fe'
bot_token = '8185486294:AAH1Zk30VvNuHEf3zZIWx0IjmZuhIPgaAmA'
# ===============

bot = TelegramClient('forwardbot', api_id, api_hash).start(bot_token=bot_token)

@bot.on(events.NewMessage(pattern=r'/kidilo ([\S]+)(?:\s+(\d+))?(?:\s+(\d+))?'))
async def forward_messages(event):
    chat_input = event.pattern_match.group(1)
    start_id = event.pattern_match.group(2)
    end_id = event.pattern_match.group(3)

    try:
        # Parse chat info from link or ID
        if chat_input.startswith("https://t.me/"):
            match = re.match(r'https?://t\.me/([^/]+)/(\d+)?', chat_input)
            if not match:
                return await event.reply("❌ Invalid message link format.")
            chat = match.group(1)
            if match.group(2):
                start_id = int(match.group(2))
        else:
            chat = int(chat_input) if chat_input.lstrip("-").isdigit() else chat_input
            if start_id:
                start_id = int(start_id)

        src_entity = await bot.get_entity(chat)

        # Get latest message if no ID provided
        if not start_id:
            messages = await bot.get_messages(src_entity, limit=10)
            latest_msg = next((m for m in messages if m.media or m.message), None)
            if not latest_msg:
                return await event.reply("❌ No messages with media or text found.")
            start_id = end_id = latest_msg.id
        else:
            end_id = int(end_id) if end_id else start_id

        await event.reply(f"⏩ Forwarding messages from {start_id} to {end_id}...")

        # Forwarding loop with delay
        for msg_id in range(start_id, end_id + 1):
            try:
                msg = await bot.get_messages(src_entity, ids=msg_id)
                if msg and msg.media:
                    await bot.send_file(event.chat_id, file=msg.media)  # No caption
                elif msg and msg.text:
                    await bot.send_message(event.chat_id, msg.text)
                await asyncio.sleep(1.2)  # Safe delay
            except Exception as e:
                print(f"❌ Failed to forward message {msg_id}: {e}")
                continue

        await event.reply("✅ Forwarding complete.")

    except Exception as e:
        await event.reply(f"❌ Error: {e}")

print("🤖 Bot is running...")
bot.run_until_disconnected()
