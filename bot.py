import os
import json
import time
import asyncio

from telethon import TelegramClient, events
from telethon.sessions import StringSession
from telethon.errors import FloodWaitError

from config import (
    API_ID,
    API_HASH,
    BOT_TOKEN,
    OWNER_ID,
    config,
    get,
    save_config
)

# ================= BOT CLIENT =================

bot = TelegramClient(
    "manager_bot",
    API_ID,
    API_HASH
).start(bot_token=BOT_TOKEN)

# ================= GLOBALS =================

clients = []
ab_tasks = {}

SESSIONS_FILE = "sessions.json"

# ================= SESSION STORAGE =================

if not os.path.exists(SESSIONS_FILE):
    with open(SESSIONS_FILE, "w") as f:
        json.dump({"sessions": []}, f, indent=4)


def load_sessions():
    with open(SESSIONS_FILE) as f:
        data = json.load(f)

    return data.get("sessions", [])


def save_session(session):
    data = load_sessions()

    if session not in data:
        data.append(session)

        with open(SESSIONS_FILE, "w") as f:
            json.dump({"sessions": data}, f, indent=4)


# ================= AUTH =================

def is_auth(uid):
    return uid == OWNER_ID or uid in config.get("sudo", [])


# ================= FAST REPLY =================

async def fast_reply(event, text):
    try:
        return await event.reply(text)
    except:
        return None


# ================= REGISTER COMMANDS =================

def register_handlers(client):

    # ================= PING =================

    @client.on(events.NewMessage(pattern=r"\.ping"))
    async def ping(event):
        if not is_auth(event.sender_id):
            return

        start = time.time()

        msg = await fast_reply(event, "⚡")

        end = time.time()

        if msg:
            await msg.edit(f"⚡ {round((end-start)*1000)} ms")

    # ================= STATS =================

    @client.on(events.NewMessage(pattern=r"\.stats"))
    async def stats(event):
        if not is_auth(event.sender_id):
            return

        dialogs = await client.get_dialogs(limit=None)

        groups = sum(1 for d in dialogs if d.is_group)

        await fast_reply(
            event,
            f"👥 Groups: {groups}\n💬 Chats: {len(dialogs)}"
        )

    # ================= SUDO LIST =================

    @client.on(events.NewMessage(pattern=r"\.sudolist"))
    async def sudolist(event):
        if not is_auth(event.sender_id):
            return

        await fast_reply(
            event,
            f"👤 SUDO USERS:\n{config.get('sudo', [])}"
        )

    # ================= ADD SUDO =================

    @client.on(events.NewMessage(pattern=r"\.sudo (\d+)"))
    async def add_sudo(event):

        if event.sender_id != OWNER_ID:
            return

        uid = int(event.pattern_match.group(1))

        config.setdefault("sudo", [])

        if uid not in config["sudo"]:
            config["sudo"].append(uid)

            save_config(config)

        await fast_reply(event, f"✅ Added sudo: {uid}")

    # ================= REMOVE SUDO =================

    @client.on(events.NewMessage(pattern=r"\.rmsudo (\d+)"))
    async def rmsudo(event):

        if event.sender_id != OWNER_ID:
            return

        uid = int(event.pattern_match.group(1))

        if uid in config.get("sudo", []):
            config["sudo"].remove(uid)

            save_config(config)

        await fast_reply(event, f"❌ Removed sudo: {uid}")

    # ================= SETTINGS =================

    @client.on(events.NewMessage(pattern=r"\.delay (\d+)"))
    async def set_delay(event):

        if not is_auth(event.sender_id):
            return

        config["delay"] = int(event.pattern_match.group(1))

        save_config(config)

        await fast_reply(
            event,
            f"⏱ Delay = {config['delay']}s"
        )

    @client.on(events.NewMessage(pattern=r"\.dp (\d*\.?\d+)"))
    async def set_dp(event):

        if not is_auth(event.sender_id):
            return

        config["dp"] = float(event.pattern_match.group(1))

        save_config(config)

        await fast_reply(
            event,
            f"⚡ DP = {config['dp']}s"
        )

    @client.on(events.NewMessage(pattern=r"\.(batch|parallel)"))
    async def set_mode(event):

        if not is_auth(event.sender_id):
            return

        config["mode"] = event.pattern_match.group(1)

        save_config(config)

        await fast_reply(
            event,
            f"⚙ Mode = {config['mode']}"
        )

    @client.on(events.NewMessage(pattern=r"\.max (\d+)"))
    async def set_max(event):

        if not is_auth(event.sender_id):
            return

        config["max"] = int(event.pattern_match.group(1))

        save_config(config)

        await fast_reply(
            event,
            f"🚀 Max = {config['max']}"
        )

    # ================= AUTO TIME =================

    @client.on(events.NewMessage(pattern=r"\.setime (\d+)"))
    async def setime(event):

        if not is_auth(event.sender_id):
            return

        sec = int(event.pattern_match.group(1))

        config["ab_time"] = sec

        save_config(config)

        await fast_reply(
            event,
            f"⏱ Auto Broadcast Time = {sec}s"
        )

    # ================= SPAMBOT =================

    @client.on(events.NewMessage(pattern=r"\.send$"))
    async def spam_start(event):

        if not is_auth(event.sender_id):
            return

        await client.send_message("SpamBot", "/start")

        await fast_reply(event, "✅ SpamBot Started")

    @client.on(events.NewMessage(pattern=r"\.send check"))
    async def spam_check(event):

        if not is_auth(event.sender_id):
            return

        m = await fast_reply(event, "Checking...")

        await client.send_message("SpamBot", "/start")

        await asyncio.sleep(3)

        msgs = await client.get_messages("SpamBot", limit=1)

        if not msgs:
            return await m.edit("No Response")

        t = (msgs[0].text or "").lower()

        if "free" in t:
            s = "🟢 FREE"

        elif "limited" in t:
            s = "🟡 LIMITED"

        elif "blocked" in t:
            s = "🔴 BLOCKED"

        else:
            s = "❓ UNKNOWN"

        await m.edit(f"Status: {s}")

    # ================= RESET =================

    @client.on(events.NewMessage(pattern=r"\.reset"))
    async def reset(event):

        if event.sender_id != OWNER_ID:
            return

        if os.path.exists("config.json"):
            os.remove("config.json")

        await fast_reply(event, "♻️ Reset Done")

        os._exit(0)

    # ================= BROADCAST =================

    async def broadcast_func(text):

        dialogs = await client.get_dialogs(limit=None)

        delay = get("delay", 3)

        dp = get("dp", 0.05)

        mode = get("mode", "batch")

        maxw = get("max", 2)

        sem = asyncio.Semaphore(maxw)

        me = await client.get_me()

        sent = 0
        fail = 0

        async def send(d):

            nonlocal sent, fail

            async with sem:

                try:

                    if d.id == me.id:
                        return

                    if d.is_channel and not d.is_group:
                        return

                    await client.send_message(d.id, text)

                    sent += 1

                    if dp:
                        await asyncio.sleep(dp)

                    if mode == "batch":
                        await asyncio.sleep(delay)

                except FloodWaitError as e:

                    await asyncio.sleep(e.seconds)

                except:

                    fail += 1

        if mode == "parallel":

            await asyncio.gather(*(send(d) for d in dialogs))

        else:

            for d in dialogs:
                await send(d)

        return sent, fail

    @client.on(events.NewMessage(pattern=r"\.b"))
    async def broadcast(event):

        if not is_auth(event.sender_id):
            return

        status = await fast_reply(event, "Starting Broadcast...")

        if event.is_reply:
            text = (await event.get_reply_message()).text or ""

        else:
            text = event.text.replace(".b", "").strip()

        if not text:
            return await fast_reply(event, "No Message Found")

        sent, fail = await broadcast_func(text)

        await status.edit(
            f"✅ Done\nSent: {sent}\nFailed: {fail}"
        )

    # ================= AUTO BROADCAST =================

    async def ab_loop(client, text):

        while True:

            try:

                await broadcast_func(text)

                await asyncio.sleep(get("ab_time", 180))

            except:

                break

    @client.on(events.NewMessage(pattern=r"\.ab"))
    async def auto_broadcast(event):

        if not is_auth(event.sender_id):
            return

        if event.is_reply:
            text = (await event.get_reply_message()).text or ""

        else:
            text = event.text.replace(".ab", "").strip()

        if not text:
            return await fast_reply(event, "No Message Found")

        if client in ab_tasks:

            ab_tasks[client].cancel()

        task = asyncio.create_task(ab_loop(client, text))

        ab_tasks[client] = task

        await fast_reply(
            event,
            f"✅ Auto Broadcast Started\n⏱ Every {get('ab_time',180)} sec"
        )

    @client.on(events.NewMessage(pattern=r"\.stopab"))
    async def stopab(event):

        if not is_auth(event.sender_id):
            return

        if client in ab_tasks:

            ab_tasks[client].cancel()

            del ab_tasks[client]

        await fast_reply(event, "🛑 Auto Broadcast Stopped")

    # ================= HELP =================

    @client.on(events.NewMessage(pattern=r"\.help"))
    async def help_cmd(event):

        if not is_auth(event.sender_id):
            return

        text = """
🔥 USERBOT COMMANDS

⚡ BASIC
.ping
.stats

📢 BROADCAST
.b <msg>
.b (reply)

🔁 AUTO BROADCAST
.ab <msg>
.ab (reply)
.stopab
.setime <sec>

⚙ SETTINGS
.delay <sec>
.dp <sec>
.batch
.parallel
.max <num>

👤 SUDO
.sudo <id>
.rmsudo <id>
.sudolist

🧪 SPAMBOT
.send
.send check

♻ SYSTEM
.reset
"""

        await event.reply(text + "\n\n🔰 MULTI USERBOT ACTIVE")


# ================= START USERBOT =================

async def start_userbot(session):

    try:

        client = TelegramClient(
            StringSession(session),
            API_ID,
            API_HASH
        )

        await client.start()

        register_handlers(client)

        clients.append(client)

        me = await client.get_me()

        print(f"🔥 Started Userbot: {me.first_name}")

    except Exception as e:

        print(e)


# ================= BOT COMMANDS =================

@bot.on(events.NewMessage(pattern="/start"))
async def start(event):

    if event.sender_id != OWNER_ID:
        return

    await event.reply("🔥 CONTROLLER BOT ACTIVE")


@bot.on(events.NewMessage(pattern="/setvar"))
async def setvar(event):

    if event.sender_id != OWNER_ID:
        return

    if not event.is_reply:
        return await event.reply("Reply To String Session")

    reply = await event.get_reply_message()

    session = reply.text.strip()

    save_session(session)

    await start_userbot(session)

    await event.reply("✅ USERBOT CONNECTED")


# ================= MAIN =================

async def main():

    sessions = load_sessions()

    for s in sessions:

        await start_userbot(s)

    print("🔥 ALL USERBOTS RUNNING")

    await bot.run_until_disconnected()


asyncio.run(main())
