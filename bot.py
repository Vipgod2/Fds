import asyncio
import re
from telethon import TelegramClient, events, Button
from telethon.tl.functions.messages import GetMessagesRequest

# ==== CONFIG ====
api_id = 23416992
api_hash = 'bebe7b8b7bc74aeaa08f658e8aa799fe'
bot_token = '7666600493:AAFnPpaPZXweKkG0IigZPf3F2G_1JksGfjY'  # Replace with your bot token
# ===============

bot = TelegramClient('forwardbot', api_id, api_hash).start(bot_token=bot_token)

# Welcome message when /start is called
@bot.on(events.NewMessage(pattern='/start'))
async def welcome(event):
    if event.is_private:
        await event.respond(
            "**Hey there!**\n\nI'm **Kidilo Bot**, here to help you fetch full messages from public channels.\n\nPress the button below to get started!",
            buttons=[Button.inline("Start Fetching", b'start_fetch_pm')]
        )

# Command to fetch the message using a link
@bot.on(events.NewMessage(pattern=r'/kidilo (https?://t\.me/\S+)'))
async def fetch_message(event):
    chat_input = event.pattern_match.group(1)

    if chat_input.startswith("https://t.me/"):
        match = re.match(r'https?://t\.me/([^/]+)/(\d+)', chat_input)
        if match:
            chat = match.group(1)
            message_id = int(match.group(2))

            try:
                # Get the entity for the channel
                src_entity = await bot.get_entity(chat)

                # Fetch the full message (including text and media)
                messages = await bot(GetMessagesRequest(
                    peer=src_entity,  # Corrected argument name
                    id=[message_id]
                ))

                # Retrieve the full message content
                full_message = messages.messages[0]

                # Send the full message content (text and media) to the chat
                message_text = full_message.text if full_message.text else "No text content."
                await event.reply(f"**Full Message Content from `{chat}`**:\n\n{message_text}")

                # If the message has media, notify the user
                if full_message.media:
                    await event.reply("This message contains media, such as images or videos.")

            except Exception as e:
                await event.reply(f"❌ Error: `{e}`")
        else:
            await event.reply("❌ Invalid message link format.")
    else:
        await event.reply("❌ Please provide a valid `t.me/username/message_id` link.")

# Start fetching instructions
@bot.on(events.CallbackQuery(data=b'start_fetch_pm'))
async def from_welcome_forward(event):
    msg = await event.respond("Use this command to start:\n\n`/kidilo https://t.me/HDthought/582574`")
    await event.edit("Instructions sent!")

# Running the bot
print("Bot running...")
bot.run_until_disconnected()
