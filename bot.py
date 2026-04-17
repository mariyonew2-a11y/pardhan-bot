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

# --- [PROFESSIONAL CLEANER] ---
def beast_cleaner(text):
    if not isinstance(text, str): return text
    # Remove external links/usernames and replace with Beast Harry branding
    text = re.sub(r'(https?://)?(t\.me|telegram\.me)/[a-zA-Z0-9_+/-]+', MY_TG_LINK, text)
    text = re.sub(r'@[a-zA-Z0-9_]+', lambda m: m.group(0) if m.group(0).lower() in [TARGET_BOT_UID.lower(), TARGET_BOT_NUM.lower()] else MY_USERNAME, text)
    text = re.sub(r'(?i)(powered by|made by|developer|owner|api_developer|LootVersegc)', 'Powered by Pardhan ji', text)
    return text

# --- [TELETHON ENGINE - FIXED FOR /NUM] ---
async def fetch_intel(search_val, mode):
    client = TelegramClient(StringSession(SESSION_STR), API_ID, API_HASH)
    await client.connect()
    target = TARGET_BOT_NUM if mode == 'num' else TARGET_BOT_UID
    try:
        async with client.conversation(target, timeout=60) as conv:
            await conv.send_message(str(search_val))
            
            for _ in range(20): # Increased polling for slow bots
                response = await conv.get_response()
                raw_text = response.text
                
                # Skip all intermediate/waiting messages
                skip_keywords = ["processing", "wait", "fetching", "searching", "hold"]
                if any(x in raw_text.lower() for x in skip_keywords) and len(raw_text) < 150:
                    continue
                
                # Check for Actual Data (JSON or Result text)
                success_indicators = ["RESULT", "DETAILS", "FOUND", "{", "total_records"]
                if any(x in raw_text.upper() for x in success_indicators) or len(raw_text) > 200:
                    clean_res = beast_cleaner(raw_text)
                    await client.disconnect()
                    return clean_res
                
                # Error detection
                if any(x in raw_text.upper() for x in ["NOT AVAILABLE", "NOT FOUND", "ERROR"]):
                    await client.disconnect()
                    return "❌ **Record Not Found in Pardhan Database!**"

            await client.disconnect()
            return "❌ **Server is busy. Please try again later!**"
    except Exception as e:
        if client.is_connected(): await client.disconnect()
        return f"❌ **System Error:** `{str(e)}`"

# --- [PROFESSIONAL COMMANDS] ---
@bot.message_handler(commands=['start'])
def welcome(message):
    user_name = message.from_user.first_name
    welcome_text = (
        f"👋 **Welcome, {user_name}!**\n\n"
        "⚡ **PARDHAN OSINT TERMINAL v2.0** ⚡\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "Use the commands below to extract digital intel. "
        "Click on the examples to copy them instantly.\n\n"
        "📊 **Available Commands:**\n"
        "🔹 `/uid` - Get mobile from UserID\n"
        "🔹 `/num` - Get full data from Number\n\n"
        "💡 **Examples:**\n"
        "• `/uid 5412896320`\n"
        "• `/num 919876543210`\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "**Owner:** @beast\_harry"
    )
    
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("Developer", url=MY_TG_LINK),
               InlineKeyboardButton("Join Channel", url="https://t.me/beast_harry")) # Update your channel link
    
    bot.reply_to(message, welcome_text, parse_mode="Markdown", reply_markup=markup)

@bot.message_handler(commands=['uid', 'num'])
def handle_search(message):
    cmd_parts = message.text.split()
    if len(cmd_parts) < 2:
        bot.reply_to(message, "⚠️ **Please provide a Target ID/Number!**\nExample: `/num 91XXXXXXXXXX`", parse_mode="Markdown")
        return

    mode = 'uid' if 'uid' in cmd_parts[0] else 'num'
    val = cmd_parts[1]
    
    status_msg = bot.reply_to(message, "🛰 **Accessing Secure Database...**\n*Please wait, Pardhan Ji is fetching data...*", parse_mode="Markdown")
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    result = loop.run_until_complete(fetch_intel(val, mode))
    loop.close()
    
    # Final Output Design
    final_output = f"🏁 **INTEL DECRYPTED SUCCESSFULLY**\n\n{result}"
    bot.edit_message_text(final_output, message.chat.id, status_msg.message_id, parse_mode="Markdown")

# --- [RENDER SETUP] ---
@app.route('/')
def home(): return "Pardhan Bot is Online ⚡"

if __name__ == "__main__":
    Thread(target=lambda: app.run(host='0.0.0.0', port=8080)).start()
    print("Beast OSINT Bot is Live! 🚀")
    bot.infinity_polling()
