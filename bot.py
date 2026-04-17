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

# Branding Setup
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
    text = re.sub(r'(?i)(powered by|made by|developer|owner|api_developer)', 'Powered by Pardhan ji', text)
    return text

# --- [TELETHON ENGINE - YOUR EXACT FETCH LOGIC] ---
async def fetch_intel(search_val, mode):
    client = TelegramClient(StringSession(SESSION_STR), API_ID, API_HASH)
    await client.connect()
    target = TARGET_BOT_NUM if mode == 'num' else TARGET_BOT_UID
    
    try:
        async with client.conversation(target, timeout=60) as conv:
            await conv.send_message(str(search_val))
            
            # Polling Logic: Wahi 12 attempts wala jo tere pass working tha
            for _ in range(12): 
                response = await conv.get_response()
                raw_text = response.text
                
                if "processing" in raw_text.lower():
                    continue

                # SUCCESS INDICATORS (Your exact regex and keywords)
                mobile_match = re.search(r'(?:mobile|phone|number|📱)\D*(\d{10,12})', raw_text, re.IGNORECASE)
                
                if "RESULT FETCHED" in raw_text.upper() or mobile_match or "{" in raw_text:
                    clean_output = beast_cleaner(raw_text)
                    await client.disconnect()
                    return clean_output

                # Failure Check
                error_keywords = ["NO RECORD FOUND", "INVALID ID", "ERROR OCCURRED", "DETAILS NOT FOUND", "NOT AVAILABLE"]
                if any(x in raw_text.upper() for x in error_keywords):
                    await client.disconnect()
                    return "❌ **Record Not Found in Pardhan Database!**"

                await asyncio.sleep(2) 

            await client.disconnect()
            return "❌ **Timeout: Bot is responding very slow.**"
            
    except Exception as e:
        if client.is_connected(): await client.disconnect()
        return f"❌ **System Error:** `{str(e)}`"

# --- [PROFESSIONAL COMMANDS SETUP] ---
@bot.message_handler(commands=['start'])
def welcome(message):
    user_name = message.from_user.first_name
    help_text = (
        f"👋 **Welcome Boss, {user_name}!**\n\n"
        "⚡ **PARDHAN OSINT TERMINAL v2.5** ⚡\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "Extract digital intel instantly. Copy commands by clicking on them:\n\n"
        "🔹 `/uid` - ID to Number\n"
        "🔹 `/num` - Number to Metadata\n\n"
        "💡 **Examples:**\n"
        "• `/uid 5412896320`\n"
        "• `/num 917282942060`\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "**Owner:** @beast\_harry"
    )
    
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("Developer", url=MY_TG_LINK),
               InlineKeyboardButton("Join Channel", url=MY_TG_LINK))
    
    bot.reply_to(message, help_text, parse_mode="Markdown", reply_markup=markup)

@bot.message_handler(commands=['uid', 'num'])
def handle_search(message):
    cmd_parts = message.text.split()
    if len(cmd_parts) < 2:
        bot.reply_to(message, "⚠️ **Please provide an ID or Number!**", parse_mode="Markdown")
        return

    mode = 'uid' if 'uid' in cmd_parts[0] else 'num'
    val = cmd_parts[1]
    
    status_msg = bot.reply_to(message, "🛰 **Accessing Pardhan Database...**\n*Fetching fresh intel for you...*", parse_mode="Markdown")
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    result = loop.run_until_complete(fetch_intel(val, mode))
    loop.close()
    
    # Final Output Professional Design
    final_output = f"🏁 **INTEL DECRYPTED SUCCESSFULLY**\n\n{result}"
    bot.edit_message_text(final_output, message.chat.id, status_msg.message_id, parse_mode="Markdown")

# --- [RENDER SETUP] ---
@app.route('/')
def home(): return "Pardhan Bot is Online ⚡"

if __name__ == "__main__":
    Thread(target=lambda: app.run(host='0.0.0.0', port=8080)).start()
    print("Beast OSINT Bot is Live! 🚀")
    bot.infinity_polling()
