import telebot
from telethon import TelegramClient
from telethon.sessions import StringSession
import asyncio
import re
import os
import time
from flask import Flask
from threading import Thread
from telebot import types

# --- [CONFIG - NO TOUCH] ---
API_ID = 34871644 
API_HASH = '9ab73b2a48115feed25b5029c812ea29'
SESSION_STR = os.environ.get('TELETHON_SESSION') 
BOT_TOKEN = os.environ.get('BOT_TOKEN')

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask('')

user_selection = {}
MY_TG_LINK = "https://t.me/beast_harry"
MY_USERNAME = "@beast_harry"
TARGET_BOT_UID = '@LootVerseInfo_Bot' 
TARGET_BOT_NUM = '@LootVerseinfoBot'

# --- [BEAST CLEANER - YOUR ORIGINAL LOGIC] ---
def beast_cleaner(text):
    if not isinstance(text, str): return text
    tg_link_pattern = r'(https?://)?(t\.me|telegram\.me)/[a-zA-Z0-9_+/-]+'
    username_pattern = r'@[a-zA-Z0-9_]+'
    text = re.sub(tg_link_pattern, MY_TG_LINK, text)
    def replace_un(m):
        found = m.group(0)
        if found.lower() in [TARGET_BOT_UID.lower(), TARGET_BOT_NUM.lower()]: return found
        return MY_USERNAME
    text = re.sub(username_pattern, replace_un, text)
    # Professional Developer Branding
    text = re.sub(r'(?i)(powered by|made by|developer|owner|api_developer)', f'Developer: {MY_USERNAME}', text)
    return text

# --- [CORE ENGINE - YOUR ORIGINAL LOGIC] ---
async def fetch_intel(search_val, mode):
    client = TelegramClient(StringSession(SESSION_STR), API_ID, API_HASH)
    await client.connect()
    target = TARGET_BOT_NUM if mode == 'num' else TARGET_BOT_UID
    try:
        async with client.conversation(target, timeout=45) as conv:
            await conv.send_message(str(search_val))
            for _ in range(15): 
                response = await conv.get_response()
                raw_text = response.text
                if "processing" in raw_text.lower(): continue
                success_indicators = ["RESULT FETCHED", "DETAILS FOR", "USER DATA", "METADATA", "{"]
                if any(x in raw_text.upper() for x in success_indicators) or len(raw_text) > 100:
                    clean_res = beast_cleaner(raw_text)
                    await client.disconnect()
                    return clean_res
                if any(x in raw_text.upper() for x in ["NOT AVAILABLE", "NOT FOUND", "ERROR"]):
                    await client.disconnect()
                    return "NOT_FOUND"
                await asyncio.sleep(1)
            await client.disconnect()
            return "TIMEOUT"
    except:
        if client.is_connected(): await client.disconnect()
        return "TIMEOUT"

# --- [AUTO-DELETE TIMER FUNCTION] ---
def disappear_msg(chat_id, message_id, base_text):
    for i in range(20, -1, -1):
        try:
            bot.edit_message_text(f"{base_text}\n\n━━━━━━━━━━━━━━━━━━━━\n⏳ `Auto-Disappearing in {i}s...`", 
                                  chat_id, message_id, parse_mode="Markdown")
            time.sleep(1)
        except: break
    try: bot.delete_message(chat_id, message_id)
    except: pass

# --- [UI HANDLERS] ---

@bot.message_handler(commands=['start'])
def welcome(message):
    user_name = message.from_user.first_name
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(types.KeyboardButton("👤 USER ID Search"), types.KeyboardButton("📱 NUMBER Search"))
    
    welcome_msg = (
        f"💀 **TERMINAL_ACCESS_GRANTED: {user_name}**\n\n"
        "⚡ **PARDHAN OSINT v5.0 [HACKER_EDITION]**\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "☣️ `SYSTEM: READY_TO_FETCH`\n"
        f"👤 `OWNER: @beast_harry`\n\n"
        "**Niche diye gaye buttons se mode select karein.**"
    )
    bot.send_message(message.chat.id, welcome_msg, parse_mode="Markdown", reply_markup=markup)

@bot.message_handler(func=lambda message: message.text in ["👤 USER ID Search", "📱 NUMBER Search"])
def set_search_mode(message):
    mode = 'uid' if "USER" in message.text else 'num'
    user_selection[message.chat.id] = mode
    prompt = "ENTER_TARGET_ID" if mode == 'uid' else "ENTER_TARGET_MOBILE"
    bot.reply_to(message, f"🛰 **SYSTEM_PROMPT:** `PROCEED_{prompt}:`", parse_mode="Markdown")

@bot.message_handler(func=lambda message: message.chat.id in user_selection)
def handle_input(message):
    if message.text.startswith('/'):
        user_selection.pop(message.chat.id, None)
        return

    mode = user_selection.pop(message.chat.id)
    
    # --- Progress Bar Simulation ---
    status_msg = bot.reply_to(message, "🛰 `INITIALIZING_FETCH...`", parse_mode="Markdown")
    time.sleep(1)
    bot.edit_message_text("🛰 `ACCESSING_SECURE_NODE...` \n`[▓▓▓░░░░░░░] 30%`", message.chat.id, status_msg.message_id, parse_mode="Markdown")
    
    # Core Logic Call (No Touch)
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    result = loop.run_until_complete(fetch_intel(message.text, mode))
    loop.close()
    
    # Final Hacker Layout
    if result == "NOT_FOUND":
        final_text = "❌ `ERROR: RECORD_NOT_FOUND_IN_DATABASE`"
    elif result == "TIMEOUT":
        final_text = "⚠️ `STATUS: SERVER_UNDER_MAINTENANCE`"
    else:
        final_text = (
            "☢️ **PARDHAN_INTELLIGENCE_REPORT**\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            f"```json\n{result}\n```\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            f"⚡ **Developer:** {MY_USERNAME}"
        )

    # Disappearing Thread Start
    Thread(target=disappear_msg, args=(message.chat.id, status_msg.message_id, final_text)).start()

# --- [RENDER SETUP] ---
@app.route('/')
def home(): return "SYSTEM_ACTIVE"

if __name__ == "__main__":
    Thread(target=lambda: app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080)))).start()
    bot.infinity_polling()
