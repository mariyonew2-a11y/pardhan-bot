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
import random
import string
from datetime import datetime, timedelta

# --- [CONFIG - NO TOUCH] ---
API_ID = 34871644 
API_HASH = '9ab73b2a48115feed25b5029c812ea29'
SESSION_STR = os.environ.get('TELETHON_SESSION') 
BOT_TOKEN = os.environ.get('BOT_TOKEN')

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask('')

# Admin & Channel Setup
ADMIN_ID = 1431950109
FORCE_JOIN_CHANNEL = "@pardhan_g"   # ✅ FIXED PUBLIC CHANNEL
force_join_active = False
user_selection = {}

# Password System
active_keys = {}
user_verified = {}

# Branding Setup
MY_TG_LINK = "https://t.me/beast_harry"
MY_USERNAME = "@beast_harry"
TARGET_BOT_UID = '@LootVerseInfo_Bot' 
TARGET_BOT_NUM = '@LootVerseinfoBot'

# --- KEY GENERATOR ---
def generate_key(length=8):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

# --- CLEANER ---
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
    text = re.sub(r'(?i)(powered by|made by|developer|owner|api_developer).*', '', text)
    return text.strip()

# --- CORE ---
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
                if len(raw_text) > 50:
                    await client.disconnect()
                    return beast_cleaner(raw_text)
                if any(x in raw_text.upper() for x in ["NOT AVAILABLE", "NOT FOUND", "ERROR"]):
                    await client.disconnect()
                    return "❌ No Data Found"
                await asyncio.sleep(1)
            await client.disconnect()
            return "❌ Timeout"
    except Exception as e:
        if client.is_connected(): await client.disconnect()
        return f"❌ Error: {str(e)}"

# --- FIXED MEMBERSHIP ---
def check_membership(user_id):
    try:
        member = bot.get_chat_member(FORCE_JOIN_CHANNEL, user_id)
        return member.status in ['member', 'administrator', 'creator']
    except Exception as e:
        print("Join Check Error:", e)
        return False

# --- VERIFY BUTTON ---
@bot.callback_query_handler(func=lambda call: call.data == "verify_join")
def verify_join(call):
    if check_membership(call.from_user.id):
        user_verified[call.from_user.id] = True
        bot.answer_callback_query(call.id, "✅ Verified Successfully!")
        bot.delete_message(call.message.chat.id, call.message.message_id)
    else:
        bot.answer_callback_query(call.id, "❌ Join channel first!")

# --- ADMIN PANEL ---
@bot.message_handler(commands=['start'])
def welcome(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("👤 USER ID Search", "📱 NUMBER Search")
    if message.from_user.id == ADMIN_ID:
        markup.add("🛠 ADMIN PANEL")
    bot.send_message(message.chat.id, "Welcome Boss 😎", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text == "🛠 ADMIN PANEL" and m.from_user.id == ADMIN_ID)
def admin_panel(message):
    status = "ON" if force_join_active else "OFF"
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton(f"Force Join: {status}", callback_data="toggle_fj"),
        types.InlineKeyboardButton("Generate Key 🔑", callback_data="gen_key")
    )
    bot.send_message(message.chat.id, "ADMIN PANEL", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "toggle_fj")
def toggle_fj(call):
    global force_join_active
    force_join_active = not force_join_active
    bot.answer_callback_query(call.id, "Updated")

@bot.callback_query_handler(func=lambda call: call.data == "gen_key")
def gen_key(call):
    key = generate_key()
    expiry = datetime.now() + timedelta(minutes=10)
    active_keys[key] = expiry

    bot.send_message(call.message.chat.id,
        f"🔑 KEY: `{key}`\nValid: 10 Minutes",
        parse_mode="Markdown")

# --- KEY VERIFY ---
@bot.message_handler(func=lambda m: m.text and m.text.startswith("KEY "))
def verify_key(message):
    key = message.text.split(" ",1)[1]
    if key in active_keys:
        if datetime.now() < active_keys[key]:
            user_verified[message.from_user.id] = True
            bot.reply_to(message, "✅ Access Granted")
        else:
            bot.reply_to(message, "❌ Key Expired")
    else:
        bot.reply_to(message, "❌ Invalid Key")

# --- INPUT FLOW ---
@bot.message_handler(func=lambda m: m.text in ["👤 USER ID Search","📱 NUMBER Search"])
def ask(message):
    user_selection[message.chat.id] = 'uid' if "USER" in message.text else 'num'
    bot.reply_to(message,"Send Value")

@bot.message_handler(func=lambda m: m.chat.id in user_selection)
def handle(message):
    
    # FORCE JOIN
    if force_join_active and not check_membership(message.from_user.id):
        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton("Join Channel 📢", url="https://t.me/pardhan_g"),
            types.InlineKeyboardButton("Verify ✅", callback_data="verify_join")
        )
        bot.reply_to(message,"Join channel then verify", reply_markup=markup)
        return

    # PASSWORD
    if force_join_active and not user_verified.get(message.from_user.id):
        bot.reply_to(message,"Enter Key: KEY XXXXX")
        return

    mode = user_selection.pop(message.chat.id)

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    result = loop.run_until_complete(fetch_intel(message.text, mode))
    loop.close()

    bot.send_message(message.chat.id, f"RESULT:\n{result}")

# --- RUN ---
@app.route('/')
def home(): return "OK"

if __name__ == "__main__":
    Thread(target=lambda: app.run(host='0.0.0.0', port=8080)).start()
    bot.infinity_polling()
