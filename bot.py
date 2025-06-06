import asyncio
import re
from telethon import TelegramClient, events, Button
from telethon.tl.functions.messages import ForwardMessagesRequest, UpdatePinnedMessageRequest

# ==== CONFIG ====
api_id = 23416992
api_hash = 'bebe7b8b7bc74aeaa08f658e8aa799fe'
bot_token = '7666600493:AAEGhUx5e8PwES9uC99ml-QBi9mKH9ARkaU'
# ===============

bot = TelegramClient('forwardbot', api_id, api_hash).start(bot_token=bot_token)

forward_sessions = {}
forwarding_in_progress = {}

@bot.on(events.NewMessage(pattern=r'/kidilo ([\S]+)(?:\s+(\d+))?(?:\s+(\d+))?'))
async def start_forward(event):
    sender = await event.get_sender()
    chat_input = event.pattern_match.group(1)
    start_id = event.pattern_match.group(2)
    end_id = event.pattern_match.group(3)

    try:
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

        if not start_id:
            messages = await bot.get_messages(src_entity, limit=10)
            latest_msg = next((m for m in messages if m.media or m.message), None)
            if not latest_msg:
                return await event.reply("❌ No messages with media or text found.")
            start_id = end_id = latest_msg.id
        else:
            end_id = int(end_id) if end_id else start_id

        forward_sessions[sender.id] = {
            "src_entity": src_entity,
            "start_id": start_id,
            "end_id": end_id,
            "dst_chat": event.chat_id
        }

        msg = await event.reply(
            f"Forward messages from {start_id} to {end_id} from {chat}?",
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
        await event.reply(f"❌ Error: {e}")

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
        f"⏩ Forwarding messages from {start} to {end}...",
        buttons=[[Button.inline("❌ Cancel", b'cancel_forward')]]
    )

    forwarding_in_progress[sender_id] = True

    try:
        for msg_id in range(start, end + 1):
            if not forwarding_in_progress.get(sender_id):
                break
            try:
                await bot(ForwardMessagesRequest(
                    from_peer=src,
                    id=[msg_id],
                    to_peer=dst
                ))
                await asyncio.sleep(1.2)
            except Exception as e:
                print(f"Failed to forward {msg_id}: {e}")
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
    await event.respond("Use this command:\n\n/kidilo <chat> or /kidilo <chat> <start_id> <end_id>")
    await event.edit("Instructions sent!")

print("Bot running...")
bot.run_until_disconnected()
