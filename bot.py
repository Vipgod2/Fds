import asyncio
import re
from telethon import TelegramClient, events

# === CONFIG ===
api_id = 23416992
api_hash = 'bebe7b8b7bc74aeaa08f658e8aa799fe'

bot_tokens = [
    '8361725713:AAFAvAzrhTDpLib4pK__C36EGZvemBHbMyM',  # Fetcher bot (in source group)
    'BOT_TOKEN_2',  # Sender bot
    'BOT_TOKEN_3',  # Sender bot
]

bot_clients = []
message_queue = asyncio.Queue()

async def fetch_messages(client, chat, start_id, end_id):
    print(f"📥 Fetching {start_id} to {end_id}")
    for msg_id in range(start_id, end_id + 1):
        try:
            msg = await client.get_messages(chat, ids=msg_id)
            if msg:
                await message_queue.put(msg)
        except Exception as e:
            print(f"❌ Fetch error {msg_id}: {e}")
        await asyncio.sleep(0.5)  # avoid floodwait
    print("✅ Fetch complete")
    await message_queue.put(None)  # signal end

async def send_messages(client, bot_index, target_chat):
    while True:
        msg = await message_queue.get()
        if msg is None:
            message_queue.put_nowait(None)  # pass signal to others
            break
        try:
            if msg.media:
                await client.send_file(target_chat, msg.media, caption=msg.text or "")
            else:
                await client.send_message(target_chat, msg.text)
            print(f"📤 Bot {bot_index} sent message {msg.id}")
        except Exception as e:
            print(f"❌ Send error Bot {bot_index}: {e}")
        await asyncio.sleep(1.2)

async def main():
    # Start all bots
    for i, token in enumerate(bot_tokens):
        client = TelegramClient(f"bot_session_{i+1}", api_id, api_hash)
        await client.start(bot_token=token)
        bot_clients.append((i+1, client))
    print(f"✅ {len(bot_clients)} bots ready")

    fetcher_bot = bot_clients[0][1]  # first bot fetches messages
    command_bot = fetcher_bot  # listens for /kidilo command

    @command_bot.on(events.NewMessage(pattern=r'/kidilo ([\S]+) (\d+) (\d+)'))
    async def handle_command(event):
        chat_input = event.pattern_match.group(1)
        start_id = int(event.pattern_match.group(2))
        end_id = int(event.pattern_match.group(3))
        target_chat = event.chat_id

        if chat_input.startswith("https://t.me/"):
            match = re.match(r'https?://t\.me/([^/]+)', chat_input)
            chat = match.group(1) if match else None
        else:
            chat = int(chat_input) if chat_input.lstrip("-").isdigit() else chat_input

        if not chat:
            return await event.reply("❌ Invalid chat")

        src_entity = await fetcher_bot.get_entity(chat)

        await event.reply(f"🚀 Fetching messages {start_id} to {end_id}...")
        fetch_task = asyncio.create_task(fetch_messages(fetcher_bot, src_entity, start_id, end_id))

        send_tasks = [
            asyncio.create_task(send_messages(client, idx, target_chat))
            for idx, client in bot_clients[1:]
        ]

        await asyncio.gather(fetch_task, *send_tasks)
        await event.reply("✅ Done sending all messages!")

    await command_bot.run_until_disconnected()

asyncio.run(main())
