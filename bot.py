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

# --- [BEAST CLEANER - BRANDING UPDATED] ---
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
    # Branding changed to Developer Credits
    text = re.sub(r'(?i)(powered by|made by|developer|owner|api_developer)', f'Developer: {MY_USERNAME}', text)
    return text

# --- [CORE ENGINE - PROGRESS SYNCED] ---
async def fetch_intel(search_val, mode, message, status_msg):
    client = TelegramClient(StringSession(SESSION_STR), API_ID, API_HASH)
    await client.connect()
    target = TARGET_BOT_NUM if mode == 'num' else TARGET_BOT_UID
    
    start_time = time.time()
    try:
        async with client.conversation(target, timeout=30) as conv:
            await conv.send_message(str(search_val))
            
            for i in range(15):
                # Percentage calculation for hacker look
                percent = int((i + 1) * 6.6)
                bar = "▓" * (percent // 10) + "░" * (10 - (percent // 10))
                
                # Update progress every few loops
                if i % 3 == 0:
                    try:
                        bot.edit_message_text(
                            f"🛰 **ACCESSING_SECURE_NODE...**\n`[{bar}] {percent}%` \n\n`STATUS: DECRYPTING_PACKETS...`",
                            message.chat.id, status_msg.message_id, parse_mode="Markdown"
                        )
                    except: pass

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
                
                # 30-Second Limit Check
                if time.time() - start_time > 30: break
                await asyncio.sleep(1)

            await client.disconnect()
            return "MAINTENANCE"
    except:
        if client.is_connected(): await client.disconnect()
        return "MAINTENANCE"

# --- [DISAPPEARING TIMER THREAD] ---
def disappear_timer(chat_id, message_id, final_text):
    for i in range(20, -1, -1):
        time.sleep(1)
        try:
            # Update countdown every second
            bot.edit_message_text(
                f"{final_text}\n\n━━━━━━━━━━━━━━━━━━━━\n⏳ `Message disappearing in {i}s...`",
                chat_id, message_id, parse_mode="Markdown"
            )
        except: break
    
    # Final Delete
    try: bot.delete_message(chat_id, message_id)
    except: pass

# --- [HACKER INTERFACE] ---

@bot.message_handler(commands=['start'])
def welcome(message):
    user_name = message.from_user.first_name
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(types.KeyboardButton("👤 USER ID Search"), types.KeyboardButton("📱 NUMBER Search"))
    
    welcome_text = (
        f"💀 **TERMINAL_ACCESS_GRANTED: {user_name}**\n\n"
        "⚡ **PARDHAN OSINT v5.0 [ELITE]**\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "☣️ `STATUS: SYSTEM_READY`\n"
        "🛰 `NODE: ENCRYPTED_BY_BEAST`\n\n"
        f"**Developer:** {MY_USERNAME}\n"
        "━━━━━━━━━━━━━━━━━━━━"
    )
    bot.send_message(message.chat.id, welcome_text, parse_mode="Markdown", reply_markup=markup)

@bot.message_handler(func=lambda message: message.text in ["👤 USER ID Search", "📱 NUMBER Search"])
def ask_for_input(message):
    mode = 'uid' if "USER" in message.text else 'num'
    user_selection[message.chat.id] = mode
    icon = "👤" if mode == 'uid' else "📱"
    prompt = "ENTER_TARGET_UID" if mode == 'uid' else "ENTER_TARGET_MOBILE"
    
    bot.reply_to(message, f"{icon} **SYSTEM_PROMPT:** `PROCEED_{prompt}:`", parse_mode="Markdown")

@bot.message_handler(func=lambda message: message.chat.id in user_selection)
def process_data_input(message):
    if message.text.startswith('/'):
        user_selection.pop(message.chat.id, None)
        return

    mode = user_selection.pop(message.chat.id)
    status_msg = bot.reply_to(message, "🛰 `INITIALIZING_SECURE_FETCH...`", parse_mode="Markdown")
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    result = loop.run_until_complete(fetch_intel(message.text, mode, message, status_msg))
    loop.close()
    
    # Error Handling Logic
    if result == "NOT_FOUND":
        final_text = "❌ `ERROR: DATA_NOT_FOUND_IN_ARCHIVES`"
    elif result == "MAINTENANCE":
        final_text = "⚠️ `STATUS: SERVER_UNDER_MAINTENANCE`"
    else:
        # Professional Hacker Layout Output
        final_text = (
            "☢️ **PARDHAN_INTELLIGENCE_REPORT**\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            f"```json\n{result}\n```\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            f"⚡ **Developer:** {MY_USERNAME}"
        )
    
    # Start Disappearing Thread
    Thread(target=disappear_timer, args=(message.chat.id, status_msg.message_id, final_text)).start()

@app.route('/')
def home(): return "SYSTEM_ONLINE"

if __name__ == "__main__":
    Thread(target=lambda: app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080)))).start()
    bot.infinity_polling()
