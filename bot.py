import asyncio
import re
from telethon import TelegramClient, events, Button
from telethon.tl.functions.messages import ForwardMessagesRequest, UpdatePinnedMessage

# ==== CONFIG ====
api_id = 23416992
api_hash = 'bebe7b8b7bc74aeaa08f658e8aa799fe'
bot_token = '7666600493:AAGCCLNZQspatmzwylmcpM-AQUo1FI2FYMA'  # Replace with your actual bot token
# ===============

bot = TelegramClient('forwardbot', api_id, api_hash).start(bot_token=bot_token)

forward_sessions = {}

@bot.on(events.NewMessage(pattern='/start'))
async def welcome(event):
    if event.is_private:
        msg = await event.respond(
            "**Welcome to Kidilo Bot!**\n\nPress the button below to start forwarding.",
            buttons=[Button.inline("Forward Messages", b'start_forward_pm')]
        )
        try:
            await bot(UpdatePinnedMessage(peer=event.chat_id, id=msg.id, silent=True))
        except:
            pass

@bot.on(events.NewMessage(pattern=r'/kidilo ([\S]+)(?:\s+(\d+))?(?:\s+(\d+))?'))
async def start_forward(event):
    sender = await event.get_sender()
    chat_input = event.pattern_match.group(1)
    start_id = event.pattern_match.group(2)
    end_id = event.pattern_match.group(3)

    if not start_id:
        await event.reply("❌ Usage: `/kidilo <chat/link> <start_id> <end_id>`")
        return

    try:
        if chat_input.startswith("https://t.me/"):
            match = re.match(r'https?://t\.me/([^/]+)/(\d+)', chat_input)
            if not match:
                return await event.reply("❌ Invalid message link format.")
            chat = match.group(1)
            start_id = int(match.group(2))
            end_id = int(end_id) if end_id else start_id
        else:
            chat = int(chat_input) if chat_input.lstrip("-").isdigit() else chat_input
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
            f"Forward messages from `{start_id}` to `{end_id}` from `{chat}`?",
            buttons=[
                [Button.inline("✅ Yes", b'start_forward')],
                [Button.inline("❌ Cancel", b'cancel_forward')]
            ]
        )

        try:
            await bot(UpdatePinnedMessage(peer=event.chat_id, id=msg.id, silent=True))
        except:
            pass

    except Exception as e:
        await event.reply(f"❌ Error resolving source: `{e}`")

@bot.on(events.CallbackQuery(data=b'start_forward'))
async def confirm_forward(event):
    sender_id = event.sender_id
    if sender_id not in forward_sessions:
        return await event.answer("Session expired or not found.", alert=True)

    session = forward_sessions.pop(sender_id)
    src = session["src_entity"]
    dst = session["dst_chat"]
    start = session["start_id"]
    end = session["end_id"]

    await event.edit(f"⏩ Forwarding messages from {start} to {end}...")

    try:
        for msg_id in range(start, end + 1):
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
        await bot.send_message(dst, "✅ Forwarding complete.")
    except Exception as e:
        await bot.send_message(dst, f"❌ Forwarding failed: {e}")

@bot.on(events.CallbackQuery(data=b'cancel_forward'))
async def cancel_forward(event):
    sender_id = event.sender_id
    forward_sessions.pop(sender_id, None)
    await event.edit("❌ Forwarding cancelled.")

@bot.on(events.CallbackQuery(data=b'start_forward_pm'))
async def from_welcome_forward(event):
    msg = await event.respond("Please use `/kidilo <chat> <start_id> <end_id>` to begin.")
    await event.edit("Instruction sent.")

print("Bot running...")
bot.run_until_disconnected()
