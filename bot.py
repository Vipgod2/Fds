import asyncio
import re
from telethon import TelegramClient, events, Button
from telethon.errors import FloodWaitError
from telethon.tl.functions.messages import ForwardMessagesRequest, UpdatePinnedMessageRequest

# ==== CONFIG ====
api_id = 23416992
api_hash = 'bebe7b8b7bc74aeaa08f658e8aa799fe'
bot_token = '7666600493:AAEGhUx5e8PwES9uC99ml-QBi9mKH9ARkaU'
# ===============

bot = TelegramClient('forwardbot', api_id, api_hash).start(bot_token=bot_token)

forward_sessions = {}
forwarding_in_progress = {}

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

        if event.is_group or event.is_channel:
            permissions = await bot.get_permissions(event.chat_id, sender.id)
            if not permissions.is_admin:
                return await event.reply("❌ You must be an admin to use this command.")

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

    await event.edit(
        f"⏩ Forwarding messages from {start} to {end}...\n(This may take some time)"
    )

    forwarding_in_progress[sender_id] = True

    msg_ids = list(range(start, end + 1))
    batch_size = 100

    try:
        for i in range(0, len(msg_ids), batch_size):
            if not forwarding_in_progress.get(sender_id):
                break
            batch = msg_ids[i:i + batch_size]
            try:
                await bot(ForwardMessagesRequest(
                    from_peer=src,
                    id=batch,
                    to_peer=dst
                ))
                await asyncio.sleep(1.2)
            except FloodWaitError as fw:
                print(f"FloodWait: sleeping {fw.seconds}s")
                await asyncio.sleep(fw.seconds)
                continue
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

@bot.on(events.CallbackQuery(data=b'cancel_forward'))
async def cancel_forward(event):
    sender_id = event.sender_id
    forwarding_in_progress[sender_id] = False
    await event.edit("❌ Forwarding cancelled.")

@bot.on(events.CallbackQuery(data=b'start_forward_pm'))
async def from_welcome_forward(event):
    await event.respond("Use this command to start:\n\n`/kidilo <chat/link> <start_id> <end_id>`")
    await event.edit("Instructions sent!")

print("Bot running...")
bot.run_until_disconnected()
