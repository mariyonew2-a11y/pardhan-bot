import telebot
from telethon import TelegramClient
from telethon.sessions import StringSession
import asyncio
import re
import os
from flask import Flask
from threading import Thread
from telebot import types

# 🔥 NEW IMPORTS (ONLY ADD)
from supabase import create_client
from datetime import datetime, timedelta
import random
import string

# --- [CONFIG - NO TOUCH] ---
API_ID = 34871644 
API_HASH = '9ab73b2a48115feed25b5029c812ea29'
SESSION_STR = os.environ.get('TELETHON_SESSION') 
BOT_TOKEN = os.environ.get('BOT_TOKEN')

# 🔥 SUPABASE INIT (ADD ONLY)
SUPABASE_URL = "https://ygmoyfmvhwziwqshgoum.supabase.co"
SUPABASE_KEY = "PASTE_YOUR_FULL_KEY"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask('')

# State storage for users (Kaunsa button dabaya hai)
user_selection = {}

# 🔥 DB VERIFY CACHE (ADD ONLY)
user_verified_cache = {}

# Branding Setup
MY_TG_LINK = "https://t.me/beast_harry"
MY_USERNAME = "@beast_harry"
TARGET_BOT_UID = '@LootVerseInfo_Bot' 
TARGET_BOT_NUM = '@LootVerseinfoBot'

# --- 🔑 KEY GENERATOR (ADD ONLY) ---
def generate_key(length=8):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

# --- 🔥 DB FUNCTIONS (ADD ONLY) ---
def save_key(key, expiry, uses):
    try:
        supabase.table("keys").insert({
            "key": key,
            "expiry": expiry.isoformat(),
            "uses_left": uses
        }).execute()
    except Exception as e:
        print("SAVE KEY ERROR:", e)

def verify_key_db(key):
    try:
        res = supabase.table("keys").select("*").eq("key", key).execute()
        if not res.data:
            return "invalid"

        data = res.data[0]

        if datetime.fromisoformat(data["expiry"]) < datetime.now():
            return "expired"

        if data["uses_left"] <= 0:
            return "limit"

        supabase.table("keys").update({
            "uses_left": data["uses_left"] - 1
        }).eq("key", key).execute()

        return "ok"

    except Exception as e:
        print("VERIFY ERROR:", e)
        return "invalid"

def set_user_verified(user_id):
    user_verified_cache[user_id] = True
    try:
        supabase.table("users").upsert({
            "user_id": user_id,
            "verified": True
        }).execute()
    except:
        pass

def is_user_verified(user_id):
    if user_verified_cache.get(user_id):
        return True
    try:
        res = supabase.table("users").select("*").eq("user_id", user_id).execute()
        if res.data:
            return res.data[0]["verified"]
    except:
        pass
    return False

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

# --- [BUTTON INTERFACE - SAME] ---

@bot.message_handler(commands=['start'])
def welcome(message):
    user_name = message.from_user.first_name
    
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    btn1 = types.KeyboardButton("👤 USER ID Search")
    btn2 = types.KeyboardButton("📱 NUMBER Search")
    markup.add(btn1, btn2)
    
    welcome_text = (
        f"👋 **Namaste {user_name} ji!**\n\n"
        "⚡ **PARDHAN OSINT TERMINAL v4.0** ⚡\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "Niche diye gaye buttons ka use karke intel nikalna shuru karein.\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "**Owner:** @beast\_harry"
    )
    
    bot.send_message(message.chat.id, welcome_text, parse_mode="Markdown", reply_markup=markup)

# --- MODE SELECT ---
@bot.message_handler(func=lambda message: message.text in ["👤 USER ID Search", "📱 NUMBER Search"])
def ask_for_input(message):
    if message.text == "👤 USER ID Search":
        user_selection[message.chat.id] = 'uid'
        bot.reply_to(message, "👤 Enter User ID:", parse_mode="Markdown")
    else:
        user_selection[message.chat.id] = 'num'
        bot.reply_to(message, "📱 Enter Number:", parse_mode="Markdown")

# --- 🔐 KEY VERIFY HANDLER (ADD ONLY) ---
@bot.message_handler(func=lambda m: m.text and m.text.startswith("KEY "))
def verify_key(message):
    key = message.text.split(" ",1)[1]
    res = verify_key_db(key)

    if res == "ok":
        set_user_verified(message.from_user.id)
        bot.reply_to(message, "✅ Verified! Ab use kar sakte ho")
    elif res == "expired":
        bot.reply_to(message, "❌ Key Expired")
    elif res == "limit":
        bot.reply_to(message, "❌ Key Limit Over")
    else:
        bot.reply_to(message, "❌ Invalid Key")

# --- MAIN FLOW ---
@bot.message_handler(func=lambda message: message.chat.id in user_selection)
def process_data_input(message):
    if message.text.startswith('/'):
        user_selection.pop(message.chat.id, None)
        return

    # 🔥 PASSWORD CHECK ADD ONLY
    if not is_user_verified(message.from_user.id):
        bot.reply_to(message, "🔐 Enter Key:\nKEY XXXXX")
        return

    mode = user_selection[message.chat.id]
    target_val = message.text
    user_selection.pop(message.chat.id, None)

    status_msg = bot.reply_to(message, "🛰 Fetching data...", parse_mode="Markdown")
    
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

# --- SERVER ---
@app.route('/')
def home(): 
    return "Pardhan Bot is Live!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

if __name__ == "__main__":
    Thread(target=run_flask).start()
    bot.infinity_polling()
