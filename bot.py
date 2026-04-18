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

# --- NEW IMPORTS ---
import random
import string
from datetime import datetime, timedelta
from supabase import create_client

# --- CONFIG ---
API_ID = 34871644 
API_HASH = '9ab73b2a48115feed25b5029c812ea29'
SESSION_STR = os.environ.get('TELETHON_SESSION') 
BOT_TOKEN = os.environ.get('BOT_TOKEN')

# --- SUPABASE ---
SUPABASE_URL = "https://ygmoyfmvhwziwqshgoum.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InlnbW95Zm12aHd6aXdxc2hnb3VtIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzY0OTI0MjEsImV4cCI6MjA5MjA2ODQyMX0.mcVD1Spg49vXjsFLidbCw_zTuJMomdcxo8fcES6ya3Y"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask('')

# --- SETTINGS ---
ADMIN_ID = 1431950109
FORCE_JOIN_CHANNEL = "@pardhan_g"
force_join_active = False
user_selection = {}

# --- DB HELPERS ---
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
    try:
        supabase.table("users").upsert({
            "user_id": user_id,
            "verified": True
        }).execute()
    except Exception as e:
        print("USER SAVE ERROR:", e)

def is_user_verified(user_id):
    try:
        res = supabase.table("users").select("*").eq("user_id", user_id).execute()
        if res.data:
            return res.data[0]["verified"]
        return False
    except:
        return False

# --- KEY GENERATOR ---
def generate_key(length=8):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

# --- CLEANER (UNCHANGED) ---
def beast_cleaner(text):
    if not isinstance(text, str): return text
    tg_link_pattern = r'(https?://)?(t\.me|telegram\.me)/[a-zA-Z0-9_+/-]+'
    username_pattern = r'@[a-zA-Z0-9_]+'
    text = re.sub(tg_link_pattern, "https://t.me/beast_harry", text)
    text = re.sub(username_pattern, "@beast_harry", text)
    return text.strip()

# --- CORE (UNCHANGED) ---
async def fetch_intel(search_val, mode):
    client = TelegramClient(StringSession(SESSION_STR), API_ID, API_HASH)
    await client.connect()
    target = '@LootVerseinfoBot' if mode == 'num' else '@LootVerseInfo_Bot'
    try:
        async with client.conversation(target, timeout=45) as conv:
            await conv.send_message(str(search_val))
            for _ in range(15): 
                response = await conv.get_response()
                raw_text = response.text

                if "processing" in raw_text.lower():
                    continue

                if len(raw_text) > 50:
                    await client.disconnect()
                    return beast_cleaner(raw_text)

                await asyncio.sleep(1)

            await client.disconnect()
            return "❌ Timeout"

    except Exception as e:
        if client.is_connected(): await client.disconnect()
        return f"❌ Error: {str(e)}"

# --- MEMBERSHIP ---
def check_membership(user_id):
    try:
        member = bot.get_chat_member(FORCE_JOIN_CHANNEL, user_id)
        return member.status in ['member', 'administrator', 'creator']
    except:
        return False

# --- VERIFY BUTTON ---
@bot.callback_query_handler(func=lambda call: call.data == "verify_join")
def verify_join(call):
    if check_membership(call.from_user.id):
        bot.answer_callback_query(call.id, "✅ Verified!")
        bot.delete_message(call.message.chat.id, call.message.message_id)
    else:
        bot.answer_callback_query(call.id, "❌ Join first!")

# --- START (ORIGINAL SAME) ---
@bot.message_handler(commands=['start'])
def welcome(message):
    user_name = message.from_user.first_name
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(types.KeyboardButton("👤 USER ID Search"), types.KeyboardButton("📱 NUMBER Search"))
    
    if message.from_user.id == ADMIN_ID:
        markup.add(types.KeyboardButton("🛠 ADMIN PANEL"))
    
    bot.send_message(message.chat.id, f"Welcome {user_name}", reply_markup=markup)

# --- ADMIN PANEL ---
@bot.message_handler(func=lambda message: message.text == "🛠 ADMIN PANEL" and message.from_user.id == ADMIN_ID)
def admin_menu(message):
    global force_join_active
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

# --- KEY GENERATION ---
@bot.callback_query_handler(func=lambda call: call.data == "gen_key")
def ask_key(call):
    bot.send_message(call.message.chat.id, "Send: TIME USES\nExample: 10 3")
    user_selection[call.message.chat.id] = "gen_key"

@bot.message_handler(func=lambda m: m.chat.id in user_selection and user_selection[m.chat.id] == "gen_key")
def create_key(message):
    try:
        t, u = map(int, message.text.split())
        key = generate_key()
        expiry = datetime.now() + timedelta(minutes=t)

        save_key(key, expiry, u)

        bot.reply_to(message, f"KEY: `{key}`\n{t} min | {u} users", parse_mode="Markdown")
    except:
        bot.reply_to(message, "Invalid format")

    user_selection.pop(message.chat.id, None)

# --- VERIFY KEY ---
@bot.message_handler(func=lambda m: m.text and m.text.startswith("KEY "))
def verify_key(message):
    key = message.text.split(" ", 1)[1]

    result = verify_key_db(key)

    if result == "ok":
        set_user_verified(message.from_user.id)
        bot.reply_to(message, "✅ Successfully Verified")
    elif result == "expired":
        bot.reply_to(message, "❌ Key Expired")
    elif result == "limit":
        bot.reply_to(message, "❌ Key Limit Over")
    else:
        bot.reply_to(message, "❌ Invalid Key")

# --- SEARCH FLOW (ORIGINAL SAME + ADD CHECK) ---
@bot.message_handler(func=lambda message: message.text in ["👤 USER ID Search", "📱 NUMBER Search"])
def ask_for_input(message):
    mode = 'uid' if "USER" in message.text else 'num'
    user_selection[message.chat.id] = mode
    bot.reply_to(message, "Enter value")

@bot.message_handler(func=lambda message: message.chat.id in user_selection)
def handle_input(message):

    if force_join_active:

        if not check_membership(message.from_user.id):
            markup = types.InlineKeyboardMarkup()
            markup.add(
                types.InlineKeyboardButton("Join Channel 📢", url="https://t.me/pardhan_g"),
                types.InlineKeyboardButton("Verify ✅", callback_data="verify_join")
            )
            bot.reply_to(message, "Join channel first", reply_markup=markup)
            return

        if not is_user_verified(message.from_user.id):
            bot.reply_to(message, "🔐 Enter Password\nKEY XXXXX")
            return

    mode = user_selection.pop(message.chat.id)

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    result = loop.run_until_complete(fetch_intel(message.text, mode))
    loop.close()

    bot.send_message(message.chat.id, f"RESULT:\n{result}")

# --- RUN ---
@app.route('/')
def home():
    return "OK"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    Thread(target=lambda: app.run(host='0.0.0.0', port=port)).start()
    bot.infinity_polling()
