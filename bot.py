from pyrogram import Client, filters
from pyrogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
import asyncio
import re

# ==== CONFIG ====
api_id = 23416992  # Replace with your own API ID
api_hash = 'bebe7b8b7bc74aeaa08f658e8aa799fe'  # Replace with your own API hash
bot_token = '7666600493:AAGCCLNZQspatmzwylmcpM-AQUo1FI2FYMA'  # Your bot token
# ===============

# Initialize the Pyrogram client with the bot token
bot = Client("forwardbot", api_id, api_hash, bot_token=bot_token)

forward_sessions = {}
forwarding_in_progress = {}

@bot.on(filters.command("start") & filters.private)
async def welcome(event: Message):
    await event.reply(
        "**Hey there!**\n\nI'm **Kidilo Bot**, here to help you forward messages from other chats.\n\nPress the button below to get started!",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Start Forwarding", callback_data="start_forward_pm")]
        ])
    )

@bot.on(filters.command("kidilo") & filters.private)
async def start_forward(event: Message):
    # Command format: /kidilo <chat_id> <start_id> <end_id>
    chat_input = event.text.split()[1]
    start_id = event.text.split()[2] if len(event.text.split()) > 2 else None
    end_id = event.text.split()[3] if len(event.text.split()) > 3 else start_id

    try:
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

        forward_sessions[event.from_user.id] = {
            "src_entity": src_entity,
            "start_id": start_id,
            "end_id": end_id,
            "dst_chat": event.chat.id
        }

        msg = await event.reply(
            f"⏩ Forward messages from `{chat}` ID `{start_id}` to `{end_id}`?",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ Start Forwarding", callback_data="start_forward")],
                [InlineKeyboardButton("❌ Cancel", callback_data="cancel_forward")]
            ])
        )

    except Exception as e:
        await event.reply(f"❌ Error: `{e}`")

@bot.on(filters.callback_data("start_forward"))
async def confirm_forward(event: CallbackQuery):
    sender_id = event.from_user.id
    if sender_id not in forward_sessions:
        return await event.answer("Session expired or not found.", alert=True)

    session = forward_sessions[sender_id]
    src = session["src_entity"]
    dst = session["dst_chat"]
    start = session["start_id"]
    end = session["end_id"]

    await event.edit(f"⏩ Forwarding messages from {start} to {end}...\n(This may take some time)")

    forwarding_in_progress[sender_id] = True

    msg_ids = list(range(start, end + 1))
    batch_size = 100

    try:
        for i in range(0, len(msg_ids), batch_size):
            if not forwarding_in_progress.get(sender_id):
                break
            batch = msg_ids[i:i + batch_size]
            try:
                await bot.forward_messages(
                    chat_id=dst,
                    from_chat_id=src,
                    message_ids=batch
                )
                await asyncio.sleep(1.2)
            except Exception as e:
                print(f"Batch failed ({batch[0]}-{batch[-1]}): {e}")
                continue

        if forwarding_in_progress.get(sender_id):
            await bot.send_message(dst, "✅ Forwarding complete.")
        else:
            await bot.send_message(dst, "⛔ Forwarding cancelled.")

    finally:
        forward_sessions.pop(sender_id, None)
        forwarding_in_progress.pop(sender_id, None)

@bot.on(filters.callback_data("cancel_forward"))
async def cancel_forward(event: CallbackQuery):
    sender_id = event.from_user.id
    forwarding_in_progress[sender_id] = False
    await event.edit("❌ Forwarding cancelled.")

@bot.on(filters.callback_data("start_forward_pm"))
async def from_welcome_forward(event: CallbackQuery):
    await event.message.reply("Use this command to start:\n\n`/kidilo <chat/link> <start_id> <end_id>`")
    await event.edit("Instructions sent!")

# Run the bot
print("Bot running...")
bot.run()
