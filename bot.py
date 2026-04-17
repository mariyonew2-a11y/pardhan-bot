import telebot
from telethon import TelegramClient
from telethon.sessions import StringSession
import asyncio
import re
import os
from flask import Flask
from threading import Thread
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# --- [CONFIG] ---
API_ID = 34871644 
API_HASH = '9ab73b2a48115feed25b5029c812ea29'
SESSION_STR = os.environ.get('TELETHON_SESSION') 
BOT_TOKEN = os.environ.get('BOT_TOKEN')

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask('')

# Branding
MY_TG_LINK = "https://t.me/beast_harry"
MY_USERNAME = "@beast_harry"
TARGET_BOT_UID = '@LootVerseInfo_Bot' 
TARGET_BOT_NUM = '@LootVerseinfoBot'

def beast_cleaner(text):
    if not isinstance(text, str): return text
    # External links aur usernames ko Harry ke branding se badlo
    text = re.sub(r'(https?://)?(t\.me|telegram\.me)/[a-zA-Z0-9_+/-]+', MY_TG_LINK, text)
    text = re.sub(r'@[a-zA-Z0-9_]+', lambda m: m.group(0) if m.group(0).lower() in [TARGET_BOT_UID.lower(), TARGET_BOT_NUM.lower()] else MY_USERNAME, text)
    text = re.sub(r'(?i)(powered by|made by|developer|owner|api_developer|LootVersegc)', 'Powered by Pardhan ji', text)
    return text

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
                
                # Metadata detection
                if any(x in raw_text.upper() for x in ["RESULT", "DETAILS", "FOUND", "{"]):
                    await client.disconnect()
                    return beast_cleaner(raw_text)
                
            await client.disconnect()
            return "❌ Response timeout. Dobara try karein."
    except Exception as e:
        if client.is_connected(): await client.disconnect()
        return f"❌ Error: {str(e)}"

# --- [COMMANDS] ---
@bot.message_handler(commands=['start'])
def welcome(message):
    # Underscore ko escape kiya taaki crash na ho
    help_text = (
        "⚡ *PARDHAN OSINT TERMINAL ACTIVE* ⚡\n\n"
        "Bataiye Harry bhai, kya nikalna hai?\n\n"
        "Commands:\n"
        "🔹 `/uid [ID]` - User ID Lookup\n"
        "🔹 `/num [Number]` - Mobile Lookup\n\n"
        "Owner: @beast\_harry"
    )
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("SUPPORT", url=MY_TG_LINK))
    bot.reply_to(message, help_text, parse_mode="Markdown", reply_markup=markup)

@bot.message_handler(commands=['uid', 'num'])
def handle_search(message):
    cmd_parts = message.text.split()
    if len(cmd_parts) < 2:
        bot.reply_to(message, "⚠️ ID ya Number toh likho, Pardhan ji!")
        return

    mode = 'uid' if 'uid' in cmd_parts[0] else 'num'
    val = cmd_parts[1]
    status_msg = bot.reply_to(message, "🔍 *Searching Pardhan Database...*", parse_mode="Markdown")
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    result = loop.run_until_complete(fetch_intel(val, mode))
    loop.close()
    
    bot.edit_message_text(result, message.chat.id, status_msg.message_id)

@app.route('/')
def home(): return "Pardhan Bot is Alive!"

if __name__ == "__main__":
    Thread(target=lambda: app.run(host='0.0.0.0', port=8080)).start()
    bot.infinity_polling()
