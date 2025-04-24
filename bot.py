import asyncio
import re

from telethon import TelegramClient, events, Button
from telethon.tl.functions.messages import ForwardMessagesRequest
from telethon.errors import RPCError
#₹
#==== CONFIG ====

api_id = 23416992 
api_hash = 'bebe7b8b7bc74aeaa08f658e8aa799fe' 
bot_token = '7666600493:AAGCCLNZQspatmzwylmcpM-AQUo1FI2FYMA'

===============

bot = TelegramClient('forwardbot', api_id, api_hash).start(bot_token=bot_token) forward_sessions = {}  # Stores active forwarding sessions

async def resolve_entity(peer_str): """Get an InputPeer from username or URL string.""" try: return await bot.get_input_entity(peer_str) except Exception: return None

@bot.on(events.NewMessage(pattern=r'/fwd\s+(https?://t.me/[^/]+/\d+)(?:\s+(\d+))?')) async def start_forward(event): # parse parameters link = event.pattern_match.group(1) count_arg = event.pattern_match.group(2) m = re.match(r'https?://t.me/([^/]+)/([0-9]+)', link) if not m: return await event.reply("Invalid message link. Use https://t.me/channel/123")

src_username, start_id = m.group(1), int(m.group(2))
end_id = int(count_arg) if count_arg else start_id + 100

# check admin rights
try:
    perms = await bot.get_permissions(event.chat_id, event.sender_id)
    if not perms.is_admin:
        return await event.reply("❌ You must be an admin.")
except RPCError:
    return await event.reply("❌ Cannot verify permissions. Make sure bot is admin.")

# resolve source entity
src_entity = await resolve_entity(src_username)
if not src_entity:
    return await event.reply(f"❌ Could not find channel @{src_username}.")

# store session
forward_sessions[event.sender_id] = dict(
    src_entity=src_entity,
    start_id=start_id,
    end_id=end_id,
    dst_chat=event.chat_id
)

await event.reply(
    f"Forward messages {start_id} to {end_id} from @{src_username}?",
    buttons=[
        [Button.inline("✅ Yes", b'start')], [Button.inline("❌ No", b'cancel')]
    ]
)

@bot.on(events.CallbackQuery(data=b'start')) async def on_confirm(event): session = forward_sessions.pop(event.sender_id, None) if not session: return await event.answer("No active session.", alert=True)

await event.edit("🚀 Starting forwarding...")
src = session['src_entity']
dst = session['dst_chat']
s, e = session['start_id'], session['end_id']

for msg_id in range(s, e + 1):
    try:
        await bot(ForwardMessagesRequest(
            from_peer=src,
            id=[msg_id],
            to_peer=dst
        ))
    except RPCError as exc:
        # skip missing or restricted messages
        print(f"Skip {msg_id}: {exc}")
    await asyncio.sleep(0.5)  # adjust rate-limit

await bot.send_message(dst, "✅ Done forwarding.")

@bot.on(events.CallbackQuery(data=b'cancel')) async def on_cancel(event): forward_sessions.pop(event.sender_id, None) await event.edit("❌ Cancelled.")

if name == 'main': print("Bot running...") bot.run_until_disconnected()

