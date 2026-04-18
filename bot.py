import telebot
from telethon import TelegramClient
from telethon.sessions import StringSession
import asyncio
import re
import os
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

# State storage for users (Kaunsa button dabaya hai)
user_selection = {}

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
                    return "❌ Database mein koi record nahi mila, Boss!"
                await asyncio.sleep(1)
            await client.disconnect()
            return "❌ Response kaafi slow hai, thodi der baad try karein."
    except Exception as e:
        if client.is_connected(): await client.disconnect()
        return f"❌ System Error: {str(e)}"

# --- [BUTTON INTERFACE UPGRADE] ---

@bot.message_handler(commands=['start'])
def welcome(message):
    user_name = message.from_user.first_name
    
    # Niche wale buttons (Reply Keyboard)
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    btn1 = types.KeyboardButton("👤 USER ID Search")
    btn2 = types.KeyboardButton("📱 NUMBER Search")
    markup.add(btn1, btn2)
    
    welcome_text = (
        f"👋 **Namaste {user_name} ji!**\n\n"
        "⚡ **PARDHAN OSINT TERMINAL v4.0** ⚡\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "Niche diye gaye buttons ka use karke intel nikalna shuru karein. "
        "Bas mode select karein aur ID ya Number bhejein.\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "**Owner:** @beast\_harry"
    )
    
    bot.send_message(message.chat.id, welcome_text, parse_mode="Markdown", reply_markup=markup)

# Button Click Handler (Mode Selection)
@bot.message_handler(func=lambda message: message.text in ["👤 USER ID Search", "📱 NUMBER Search"])
def ask_for_input(message):
    if message.text == "👤 USER ID Search":
        user_selection[message.chat.id] = 'uid'
        bot.reply_to(message, "👤 **Please Enter Telegram User ID:**\n*(Example: 5412896320)*", parse_mode="Markdown")
    else:
        user_selection[message.chat.id] = 'num'
        bot.reply_to(message, "📱 **Please Enter Mobile Number:**\n*(Example: 917282942060)*", parse_mode="Markdown")

# Data Input Handler (Final Search Processing)
@bot.message_handler(func=lambda message: message.chat.id in user_selection)
def process_data_input(message):
    # Agar user koi command bhej de beech mein toh use skip karo
    if message.text.startswith('/'):
        user_selection.pop(message.chat.id, None)
        return

    mode = user_selection[message.chat.id]
    target_val = message.text
    
    # Selection remove karo taaki agle search ke liye button dabana pade
    user_selection.pop(message.chat.id, None)

    status_msg = bot.reply_to(message, "🛰 **Accessing Secure Database...**\n*Pardhan Ji is fetching intel, please wait...*", parse_mode="Markdown")
    
    # Async loop handling
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    final_output = loop.run_until_complete(fetch_intel(target_val, mode))
    loop.close()
    
    final_design = (
        "🏁 **INTEL DECRYPTED SUCCESSFULLY**\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"{final_output}\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "**Verified by:** @beast\_harry"
    )
    
    bot.edit_message_text(final_design, message.chat.id, status_msg.message_id, parse_mode="Markdown")

# --- [RENDER SERVER SETUP] ---
@app.route('/')
def home(): 
    return "Pardhan Bot is Live & Active! ⚡"

def run_flask():
    # Render dynamic port handler
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

if __name__ == "__main__":
    print("Beast Bot Starting...")
    # Flask starts in a separate thread to not block the bot
    Thread(target=run_flask).start()
    bot.infinity_polling()
