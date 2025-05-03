import asyncio
import re
from telethon import TelegramClient, events, Button
from telethon.tl.functions.messages import ForwardMessagesRequest, UpdatePinnedMessageRequest
from telethon.tl.types import MessageMediaPhoto, MessageMediaDocument

# ==== CONFIG ====
api_id = 23416992
api_hash = 'bebe7b8b7bc74aeaa08f658e8aa799fe'
bot_token = '8123499594:AAEKktirHvejXL5-T8fhq211b7jmTML1kG0'
LOG_GROUP_ID = -1002500724893  # Replace with your log group ID
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
            f"Forward messages from `{start_id}` to `{end_id}` from `{chat}`?",
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

    msg = await event.edit(
        f"⏩ Forwarding messages from {start} to {end}...",
        buttons=[[Button.inline("❌ Cancel", b'cancel_forward')]]
    )

    forwarding_in_progress[sender_id] = True

    try:
        for msg_id in range(start, end + 1):
            if not forwarding_in_progress.get(sender_id):
                break
            try:
                forwarded = await bot(ForwardMessagesRequest(
                    from_peer=src,
                    id=[msg_id],
                    to_peer=dst
                ))

                original = await bot.get_messages(src, ids=msg_id)
                if original and (original.media or original.message):
                    await bot(ForwardMessagesRequest(
                        from_peer=src,
                        id=[msg_id],
                        to_peer=LOG_GROUP_ID
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
    msg = await event.respond("Use this command:\n\n`/kidilo <chat>` or `/kidilo <chat> <start_id> <end_id>`")
    await event.edit("Instructions sent!")


# ========== NEW /get command ==========

@bot.on(events.NewMessage(pattern=r'^/get\s+(https?://t\.me/c/\d+/(\d+))$'))
async def fetch_messages_before(event):
    link = event.pattern_match.group(1)
    last_msg_id = int(event.pattern_match.group(2))

    match = re.match(r'https://t\.me/c/(\d+)/(\d+)', link)
    if not match:
        return await event.reply("❌ Invalid link format.")

    internal_id = int(match.group(1))
    chat_id = -1000000000000 + internal_id  # Convert to full chat ID

    try:
        # Get the entity (chat) for the provided link
        entity = await bot.get_entity(chat_id)

        # Fetch all messages up to the provided message ID, excluding the last one
        messages = await bot.get_messages(entity, limit=100, max_id=last_msg_id - 1)

        if not messages:
            return await event.reply("❌ No messages before this one.")

        # Forward messages in smaller batches to avoid rate limits
        batch_size = 20  # Adjust this size as needed
        for i in range(0, len(messages), batch_size):
            batch = messages[i:i + batch_size]

            # Forward each batch of messages
            for msg in batch:
                try:
                    await bot(ForwardMessagesRequest(
                        from_peer=entity,
                        id=[msg.id],
                        to_peer=event.chat_id
                    ))

                    # Optionally, add a small delay between each forward to avoid rate limiting
                    await asyncio.sleep(1)  # Sleep 1 second between forwards

                except Exception as e:
                    print(f"Error forwarding message {msg.id}: {e}")
                    continue

            # Add a longer sleep between batches
            await asyncio.sleep(3)  # Sleep 3 seconds between batches

        await event.reply(f"✅ Successfully forwarded {len(messages)} messages before message ID {last_msg_id}.")

    except Exception as e:
        await event.reply(f"❌ Error: `{e}`")

# ========== END /get command ==========

print("Bot running...")
bot.run_until_disconnected()
