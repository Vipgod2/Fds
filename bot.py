import asyncio
import re
from telethon import TelegramClient, events, Button
from telethon.errors import FloodWaitError
from telethon.tl.functions.messages import UpdatePinnedMessageRequest
from pyrogram import Client as PyrogramClient
from pyrogram.errors import FloodWait

# ==== CONFIG ====
api_id = 23416992  # Your API ID (replace with your own)
api_hash = 'bebe7b8b7bc74aeaa08f658e8aa799fe'  # Your API hash (replace with your own)
bot_token = '7666600493:AAGCCLNZQspatmzwylmcpM-AQUo1FI2FYMA'  # Your bot token (replace with your own)
pyrogram_session = "pyrogram_session"  # Pyrogram session name
# ===============

# Initialize Telethon Client for bot (telethon)
bot = TelegramClient('forwardbot', api_id, api_hash).start(bot_token=bot_token)

# Initialize Pyrogram Client (pyrogram)
pyrogram_bot = PyrogramClient(pyrogram_session, api_id, api_hash).start()

forward_sessions = {}
forwarding_in_progress = {}

# === Telethon Bot Handlers ===

@bot.on(events.NewMessage(pattern='/start'))
async def welcome(event):
    if event.is_private:
        await event.respond(
            "**Hey there!**\n\nI'm **Kidilo Bot**, here to help you forward messages from other chats.\n\nPress the button below to get started!",
            buttons=[Button.inline("Start Forwarding", b'start_forward_pm')]
        )

@bot.on(events.NewMessage(pattern=r'/kidilo ([\S]+)(?:\s+(\d+))?(?:\s+(\d+))?'))
async def start_forward(event):
    sender = await event.get_sender()
    chat_input = event.pattern_match.group(1)
    start_id = event.pattern_match.group(2)
    end_id = event.pattern_match.group(3)

    try:
        # If the chat_input is a link, extract the chat and start ID.
        if chat_input.startswith("https://t.me/"):
            match = re.match(r'https?://t\.me/([^/]+)/(\d+)', chat_input)
            if not match:
                return await event.reply("❌ Invalid message link format.")
            chat = match.group(1)
            start_id = int(match.group(2))

            src_entity = await bot.get_entity(chat)
            messages = await bot.get_messages(src_entity, limit=1)
            if not messages:
                return await event.reply("❌ Couldn't retrieve latest message.")
            end_id = messages[0].id
        else:
            chat = int(chat_input) if chat_input.lstrip("-").isdigit() else chat_input
            if not start_id:
                return await event.reply("❌ Usage: `/kidilo <chat> <start_id> <end_id>`")
            start_id = int(start_id)
            end_id = int(end_id) if end_id else start_id
            src_entity = await bot.get_entity(chat)

        forward_sessions[sender.id] = {
            "src_entity": src_entity,
            "start_id": start_id,
            "end_id": end_id,
            "dst_chat": event.chat_id
        }

        msg = await event.reply(
            f"⏩ Forward messages from `{chat}` ID `{start_id}` to `{end_id}`?",
            buttons=[
                [Button.inline("✅ Start Forwarding", b'start_forward')],
                [Button.inline("❌ Cancel", b'cancel_forward')]
            ]
        )

        if not event.is_private:
            try:
                await bot(UpdatePinnedMessageRequest(peer=event.chat_id, id=msg.id, silent=True))
            except:
                pass

    except Exception as e:
        await event.reply(f"❌ Error: `{e}`")

# === Confirmation and Forwarding Logic ===

@bot.on(events.CallbackQuery(data=b'start_forward'))
async def confirm_forward(event):
    sender_id = event.sender_id
    if sender_id not in forward_sessions:
        return await event.answer("Session expired or not found.", alert=True)

    session = forward_sessions[sender_id]
    src = session["src_entity"]
    dst = session["dst_chat"]
    start = session["start_id"]
    end = session["end_id"]

    await event.edit(f"⏩ Forwarding messages from {start} to {end}...\n(This may take some time)")

    forwarding_in_progress[sender_id] = True

    # Forward the messages using Pyrogram for efficient resending
    try:
        for msg_id in range(start, end + 1):
            if not forwarding_in_progress.get(sender_id):
                break
            try:
                message = await pyrogram_bot.get_messages(src, msg_id)
                await pyrogram_bot.forward_messages(dst, message.id, chat_id=dst)
                await asyncio.sleep(1.2)
            except FloodWait as fw:
                print(f"FloodWait: sleeping {fw.x} seconds")
                await asyncio.sleep(fw.x)
            except Exception as e:
                print(f"Error with message {msg_id}: {e}")
                continue

        if forwarding_in_progress.get(sender_id):
            await bot.send_message(dst, "✅ Forwarding complete.")
        else:
            await bot.send_message(dst, "⛔ Forwarding cancelled.")

    finally:
        forward_sessions.pop(sender_id, None)
        forwarding_in_progress.pop(sender_id, None)

@bot.on(events.CallbackQuery(data=b'cancel_forward'))
async def cancel_forward(event):
    sender_id = event.sender_id
    forwarding_in_progress[sender_id] = False
    await event.edit("❌ Forwarding cancelled.")

@bot.on(events.CallbackQuery(data=b'start_forward_pm'))
async def from_welcome_forward(event):
    await event.respond("Use this command to start:\n\n`/kidilo <chat/link> <start_id> <end_id>`")
    await event.edit("Instructions sent!")

# === Running the Bot ===
print("Bot running...")
bot.run_until_disconnected()
