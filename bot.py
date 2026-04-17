import telebot
from telethon import TelegramClient
from telethon.sessions import StringSession
import asyncio
import re
import os
from flask import Flask
from threading import Thread

# --- [CONFIG] ---
# Render ke Environment Variables se uthayenge (Security First!)
API_ID = 34871644 
API_HASH = '9ab73b2a48115feed25b5029c812ea29'
SESSION_STR = os.environ.get('TELETHON_SESSION') # Render pe ye daal dena
BOT_TOKEN = os.environ.get('BOT_TOKEN')

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask('')

# Branding Setup
MY_TG_LINK = "https://t.me/beast_harry"
MY_USERNAME = "@beast_harry"
TARGET_BOT_UID = '@LootVerseInfo_Bot' 
TARGET_BOT_NUM = '@LootVerseinfoBot'

# --- [BEAST CLEANER LOGIC] ---
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
    text = re.sub(r'(?i)(powered by|made by|developer|owner|api_developer)', 'Powered by Pardhan ji', text)
    return text

# --- [TELETHON ENGINE] ---
async def fetch_intel(search_val, mode):
    client = TelegramClient(StringSession(SESSION_STR), API_ID, API_HASH)
    await client.connect()
    target = TARGET_BOT_NUM if mode == 'num' else TARGET_BOT_UID
    try:
        async with client.conversation(target, timeout=45) as conv:
            await conv.send_message(str(search_val))
            for _ in range(10):
                response = await conv.get_response()
                raw_text = response.text
                if "processing" in raw_text.lower(): continue
                
                # Success Check
                if any(x in raw_text.upper() for x in ["RESULT FETCHED", "DETAILS FOR"]):
                    clean_res = beast_cleaner(raw_text)
                    await client.disconnect()
                    return clean_res
            await client.disconnect()
            return "❌ Bot slow hai, thodi der baad try karo."
    except Exception as e:
        if client.is_connected(): await client.disconnect()
        return f"❌ Error: {str(e)}"

# --- [BOT COMMANDS] ---
@bot.message_handler(commands=['start'])
def welcome(message):
    bot.reply_to(message, "⚡ **PARDHAN OSINT TERMINAL ACTIVE** ⚡\n\nCommands:\n/uid [TelegramID]\n/num [MobileNumber]\n\nOwner: @beast_harry")

@bot.message_handler(commands=['uid', 'num'])
def handle_search(message):
    cmd = message.text.split()
    if len(cmd) < 2:
        bot.reply_to(message, "Bhai, value toh daal! Example: `/uid 12345678`", parse_mode="Markdown")
        return

    mode = 'uid' if 'uid' in cmd[0] else 'num'
    val = cmd[1]
    
    sent_msg = bot.reply_to(message, "🔍 **Searching in Database...**")
    
    # Async logic ko sync telebot mein chalane ke liye
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    result = loop.run_until_complete(fetch_intel(val, mode))
    loop.close()
    
    bot.edit_message_text(result, message.chat.id, sent_msg.message_id)

# --- [RENDER KEEP-ALIVE] ---
@app.route('/')
def home(): return "OSINT Bot is Alive!"

def run(): app.run(host='0.0.0.0', port=8080)

if __name__ == "__main__":
    Thread(target=run).start()
    bot.infinity_polling()
