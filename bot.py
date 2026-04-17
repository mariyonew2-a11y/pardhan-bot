import telebot
from telethon import TelegramClient
from telethon.sessions import StringSession
import asyncio
import re
import os
from flask import Flask
from threading import Thread

# --- [CONFIG] ---
# Render ke Environment Variables se values uthayenge
API_ID = 34871644 
API_HASH = '9ab73b2a48115feed25b5029c812ea29'
SESSION_STR = os.environ.get('TELETHON_SESSION') 
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
    
    # Sab external links aur usernames mita kar Harry ka branding chipkao
    tg_link_pattern = r'(https?://)?(t\.me|telegram\.me)/[a-zA-Z0-9_+/-]+'
    username_pattern = r'@[a-zA-Z0-9_]+'
    
    text = re.sub(tg_link_pattern, MY_TG_LINK, text)
    
    def replace_un(m):
        found = m.group(0)
        # Target bots ko ignore karo, baaki sab replace
        if found.lower() in [TARGET_BOT_UID.lower(), TARGET_BOT_NUM.lower()]: 
            return found
        return MY_USERNAME
    
    text = re.sub(username_pattern, replace_un, text)
    
    # Credit swap logic
    text = re.sub(r'(?i)(powered by|made by|developer|owner|api_developer)', 'Powered by Pardhan ji', text)
    return text

# --- [TELETHON CORE ENGINE] ---
async def fetch_intel(search_val, mode):
    client = TelegramClient(StringSession(SESSION_STR), API_ID, API_HASH)
    await client.connect()
    
    target = TARGET_BOT_NUM if mode == 'num' else TARGET_BOT_UID
    
    try:
        async with client.conversation(target, timeout=45) as conv:
            await conv.send_message(str(search_val))
            
            # Bot response ke liye wait loop
            for _ in range(15): 
                response = await conv.get_response()
                raw_text = response.text
                
                # Processing skip karo
                if "processing" in raw_text.lower():
                    continue
                
                # --- [/num Fix & Success Logic] ---
                # Check for keywords, JSON format, or substantial data length
                success_indicators = ["RESULT FETCHED", "DETAILS FOR", "USER DATA", "METADATA", "{"]
                
                if any(x in raw_text.upper() for x in success_indicators) or len(raw_text) > 100:
                    clean_res = beast_cleaner(raw_text)
                    await client.disconnect()
                    return clean_res
                
                # Failure detection
                if any(x in raw_text.upper() for x in ["NOT AVAILABLE", "NOT FOUND", "ERROR"]):
                    await client.disconnect()
                    return "❌ Database mein koi record nahi mila, Boss!"

                await asyncio.sleep(1)

            await client.disconnect()
            return "❌ Response kaafi slow hai, thodi der baad try karein."
            
    except Exception as e:
        if client.is_connected(): await client.disconnect()
        return f"❌ System Error: {str(e)}"

# --- [TELEGRAM BOT COMMANDS] ---
@bot.message_handler(commands=['start'])
def welcome(message):
    help_text = (
        "⚡ **PARDHAN OSINT TERMINAL ACTIVE** ⚡\n\n"
        "Bataiye Harry bhai, kya nikalna hai?\n\n"
        "Commands:\n"
        "🔹 `/uid [TelegramID]` - User ID se Number\n"
        "🔹 `/num [MobileNo]` - Number se Full Details\n\n"
        "Owner: @beast_harry"
    )
    bot.reply_to(message, help_text, parse_mode="Markdown")

@bot.message_handler(commands=['uid', 'num'])
def handle_search(message):
    cmd_parts = message.text.split()
    if len(cmd_parts) < 2:
        bot.reply_to(message, "⚠️ Error: Command ke saath ID ya Number bhi daalo!")
        return

    mode = 'uid' if 'uid' in cmd_parts[0] else 'num'
    target_val = cmd_parts[1]
    
    status_msg = bot.reply_to(message, "🔍 **Searching in Pardhan Database...**", parse_mode="Markdown")
    
    # Running async function in telebot thread
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    final_output = loop.run_until_complete(fetch_intel(target_val, mode))
    loop.close()
    
    bot.edit_message_text(final_output, message.chat.id, status_msg.message_id)

# --- [RENDER 24/7 SETUP] ---
@app.route('/')
def home(): 
    return "Pardhan Bot is Live & Active!"

def run_flask(): 
    app.run(host='0.0.0.0', port=8080)

if __name__ == "__main__":
    print("Beast Bot Starting...")
    Thread(target=run_flask).start() # Flask server starts in background
    bot.infinity_polling()
