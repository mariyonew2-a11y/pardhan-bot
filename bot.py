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

# 🔥 NEW IMPORTS
import random
import string
from datetime import datetime, timedelta
from supabase import create_client

# --- CONFIG ---
API_ID = 34871644 
API_HASH = '9ab73b2a48115feed25b5029c812ea29'
SESSION_STR = os.environ.get('TELETHON_SESSION')
BOT_TOKEN = os.environ.get('BOT_TOKEN')

# 🔥 SUPABASE (FULL KEY REQUIRED)
SUPABASE_URL = "https://ygmoyfmvhwziwqshgoum.supabase.co"
SUPABASE_KEY = "PASTE_FULL_KEY_HERE"  # ⚠️ FULL KEY डालना

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask('')

# --- SETTINGS ---
ADMIN_ID = 1431950109
FORCE_JOIN_CHANNEL = "@pardhan_g"
user_selection = {}

# Branding
MY_TG_LINK = "https://t.me/beast_harry"
MY_USERNAME = "@beast_harry"
TARGET_BOT_UID = '@LootVerseInfo_Bot' 
TARGET_BOT_NUM = '@LootVerseinfoBot'

# --- KEY GEN ---
def generate_key(length=8):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

# --- DB SAFE FUNCTIONS ---

def save_key(key, expiry, uses):
    try:
        supabase.table("keys").insert({
            "key": key,
            "expiry": expiry.isoformat(),
            "uses_left": uses
        }).execute()
    except Exception as e:
        print("Save key error:", e)

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
        print("Verify key error:", e)
        return "invalid"

def set_user_verified(user_id):
    try:
        supabase.table("users").upsert({
            "user_id": user_id,
            "verified": True
        }).execute()
    except:
        pass

def is_user_verified(user_id):
    try:
        res = supabase.table("users").select("*").eq("user_id", user_id).execute()
        return res.data and res.data[0]["verified"]
    except:
        return False

def get_force_join():
    try:
        res = supabase.table("settings").select("*").eq("id", 1).execute()
        return res.data[0]["force_join"]
    except:
        return False

def toggle_force_join_db():
    try:
        current = get_force_join()
        supabase.table("settings").update({
            "force_join": not current
        }).eq("id", 1).execute()
    except:
        pass

# --- CLEANER ---
def beast_cleaner(text):
    if not isinstance(text, str): return text
    text = re.sub(r'@[a-zA-Z0-9_]+', MY_USERNAME, text)
    return text.strip()

# --- CORE ---
async def fetch_intel(search_val, mode):
    client = TelegramClient(StringSession(SESSION_STR), API_ID, API_HASH)
    await client.connect()
    target = TARGET_BOT_NUM if mode == 'num' else TARGET_BOT_UID

    try:
        async with client.conversation(target, timeout=45) as conv:
            await conv.send_message(str(search_val))
            for _ in range(10):
                response = await conv.get_response()
                txt = response.text

                if len(txt) > 50:
                    await client.disconnect()
                    return beast_cleaner(txt)

                await asyncio.sleep(1)

        await client.disconnect()
        return "❌ Timeout"

    except Exception as e:
        if client.is_connected(): await client.disconnect()
        return f"❌ Error: {e}"

# --- JOIN CHECK ---
def check_membership(user_id):
    try:
        member = bot.get_chat_member(FORCE_JOIN_CHANNEL, user_id)
        return member.status in ['member','administrator','creator']
    except:
        return False

# --- VERIFY BTN ---
@bot.callback_query_handler(func=lambda call: call.data == "verify_join")
def verify_join(call):
    if check_membership(call.from_user.id):
        bot.answer_callback_query(call.id, "✅ Verified")
        bot.delete_message(call.message.chat.id, call.message.message_id)
    else:
        bot.answer_callback_query(call.id, "❌ Join first")

# --- START ---
@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("👤 USER ID Search", "📱 NUMBER Search")
    if message.from_user.id == ADMIN_ID:
        markup.add("🛠 ADMIN PANEL")

    bot.send_message(message.chat.id, "Welcome Boss 😎", reply_markup=markup)

# --- ADMIN ---
@bot.message_handler(func=lambda m: m.text == "🛠 ADMIN PANEL" and m.from_user.id == ADMIN_ID)
def admin_panel(message):
    status = "ON" if get_force_join() else "OFF"
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton(f"Force Join: {status}", callback_data="toggle_fj"),
        types.InlineKeyboardButton("Generate Key 🔑", callback_data="gen_key")
    )
    bot.send_message(message.chat.id, "ADMIN PANEL", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "toggle_fj")
def toggle_fj(call):
    toggle_force_join_db()
    bot.answer_callback_query(call.id, "Updated")

# --- KEY GEN ---
@bot.callback_query_handler(func=lambda call: call.data == "gen_key")
def ask_key(call):
    bot.send_message(call.message.chat.id, "Send: TIME USES\nExample: 10 3")
    user_selection[call.message.chat.id] = "gen_key"

@bot.message_handler(func=lambda m: m.chat.id in user_selection and user_selection[m.chat.id]=="gen_key")
def create_key(message):
    try:
        t,u = map(int,message.text.split())
        key = generate_key()
        expiry = datetime.now() + timedelta(minutes=t)

        save_key(key, expiry, u)

        bot.reply_to(message,f"KEY: `{key}`\n{t}min | {u} users",parse_mode="Markdown")
    except:
        bot.reply_to(message,"Invalid format")

    user_selection.pop(message.chat.id,None)

# --- VERIFY KEY ---
@bot.message_handler(func=lambda m: m.text and m.text.startswith("KEY "))
def verify_key(message):
    key = message.text.split(" ",1)[1]

    res = verify_key_db(key)

    if res == "ok":
        set_user_verified(message.from_user.id)
        bot.reply_to(message,"✅ Verified")
    elif res == "expired":
        bot.reply_to(message,"❌ Expired")
    elif res == "limit":
        bot.reply_to(message,"❌ Limit over")
    else:
        bot.reply_to(message,"❌ Invalid")

# --- SEARCH ---
@bot.message_handler(func=lambda m: m.text in ["👤 USER ID Search","📱 NUMBER Search"])
def ask(message):
    user_selection[message.chat.id] = 'uid' if "USER" in message.text else 'num'
    bot.reply_to(message,"Send value")

@bot.message_handler(func=lambda m: m.chat.id in user_selection)
def handle(message):

    if get_force_join():

        if not check_membership(message.from_user.id):
            markup = types.InlineKeyboardMarkup()
            markup.add(
                types.InlineKeyboardButton("Join Channel 📢", url="https://t.me/pardhan_g"),
                types.InlineKeyboardButton("Verify ✅", callback_data="verify_join")
            )
            bot.reply_to(message,"Join channel first",reply_markup=markup)
            return

        if not is_user_verified(message.from_user.id):
            bot.reply_to(message,"Enter KEY XXXXX")
            return

    mode = user_selection.pop(message.chat.id)

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    result = loop.run_until_complete(fetch_intel(message.text,mode))
    loop.close()

    bot.send_message(message.chat.id,f"RESULT:\n{result}")

# --- RUN ---
@app.route('/')
def home(): return "OK"

if __name__ == "__main__":
    Thread(target=lambda: app.run(host='0.0.0.0', port=8080)).start()
    bot.infinity_polling()
