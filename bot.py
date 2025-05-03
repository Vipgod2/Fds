from telethon import TelegramClient, events
from telethon.tl.functions.messages import ForwardMessagesRequest

# ==== CONFIG ====
api_id = 23416992
api_hash = 'bebe7b8b7bc74aeaa08f658e8aa799fe'
bot_token = '8123499594:AAEKktirHvejXL5-T8fhq211b7jmTML1kG0'  # Add your bot token here
# ===============

bot = TelegramClient('forwardbot', api_id, api_hash).start(bot_token=bot_token)

@bot.on(events.NewMessage(pattern=r'/get https://t.me/([^/]+)/(\d+)'))
async def forward_message(event):
    # Extract the channel username and message ID
    channel_username = event.pattern_match.group(1)
    message_id = int(event.pattern_match.group(2))
    
    try:
        # Fetch the channel entity
        channel = await bot.get_entity(channel_username)
        
        # Fetch the message from the channel
        message = await bot.get_messages(channel, ids=message_id)
        
        if message:
            # Prepare the peer to forward the message to (can forward to the same or another chat)
            forward_peer = await bot.get_input_entity(event.chat_id)

            # Forward the message directly (without downloading or uploading the media)
            await bot(ForwardMessagesRequest(
                from_peer=channel,
                id=[message_id],
                to_peer=forward_peer
            ))
            
            await event.reply("✅ Message forwarded successfully.")
        else:
            await event.reply("❌ Message not found or could not be fetched.")
    
    except Exception as e:
        await event.reply(f"❌ Error: {e}")

print("Bot is running...")
bot.run_until_disconnected()
