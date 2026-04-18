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

# 🔥 DB IMPORT
from supabase import create_client

# --- [CONFIG - NO TOUCH] ---
API_ID = 34871644 
API_HASH = '9ab73b2a48115feed25b5029c812ea29'
SESSION_STR = os.environ.get('TELETHON_SESSION') 
BOT_TOKEN = os.environ.get('BOT_TOKEN')

# 🔥 SUPABASE CONFIG
SUPABASE_URL = "https://ygmoyfmvhwziwqshgoum.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InlnbW95Zm12aHd6aXdxc2hnb3VtIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzY0OTI0MjEsImV4cCI6MjA5MjA2ODQyMX0.mcVD1Spg49vXjsFLidbCw_zTuJMomdcxo8fcES6ya3Y"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask('')

# Admin & Channel Setup
ADMIN_ID = 1431950109
FORCE_JOIN_CHANNEL = "@pardhan_g"
force_join_active = False
user_selection = {}

# 🔥 RAM STORAGE (UNCHANGED)
active_keys = {}
user_verified = {}

# Branding Setup
MY_TG_LINK = "https://t.me/beast_harry"
MY_USERNAME = "@beast_harry"
TARGET_BOT_UID = '@LootVerseInfo_Bot' 
TARGET_BOT_NUM = '@LootVerseinfoBot'

# =========================
# 🔥 DB FUNCTIONS
# =========================

def db_save_key(key, expiry, uses):
    try:
        supabase.table("keys").insert({
            "key": key,
            "expiry": expiry.isoformat(),
            "uses_left": uses
        }).execute()
    except Exception as e:
        print("DB SAVE ERROR:", e)

def db_verify_key(key):
    try:
        res = supabase.table("keys").select("*").eq("key", key).execute()
        if not res.data:
            return None

        data = res.data[0]

        if datetime.now() > datetime.fromisoformat(data["expiry"]):
            return "expired"

        if data["uses_left"] <= 0:
            return "limit"

        supabase.table("keys").update({
            "uses_left": data["uses_left"] - 1
        }).eq("key", key).execute()

        return "ok"

    except Exception as e:
        print("DB VERIFY ERROR:", e)
        return None

def db_set_verified(user_id):
    try:
        supabase.table("users").upsert({
            "user_id": user_id,
            "verified": True
        }).execute()
    except:
        pass

def db_is_verified(user_id):
    try:
        res = supabase.table("users").select("*").eq("user_id", user_id).execute()
        if res.data:
            return res.data[0]["verified"]
    except:
        pass
    return False

# =========================

# --- 🔥 KEY GENERATOR ---
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
                if len(raw_text) > 100:
                    clean_res = beast_cleaner(raw_text)
                    await client.disconnect()
                    return clean_res
                await asyncio.sleep(1)
            await client.disconnect()
            return "❌ Slow response"
    except Exception as e:
        if client.is_connected(): await client.disconnect()
        return f"❌ Error: {str(e)}"

# --- HELPERS ---
def disappear_timer(chat_id, message_id):
    time.sleep(60)
    try: bot.delete_message(chat_id, message_id)
    except: pass

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

# --- ADMIN KEY ---
@bot.callback_query_handler(func=lambda call: call.data == "gen_key")
def ask_key(call):
    bot.send_message(call.message.chat.id,"Send:\nTIME USES")
    user_selection[call.message.chat.id] = "gen_key"

@bot.message_handler(func=lambda m: m.chat.id in user_selection and user_selection[m.chat.id] == "gen_key")
def create_key(message):
    try:
        time_min, uses = map(int, message.text.split())
        key = generate_key()
        expiry = datetime.now() + timedelta(minutes=time_min)

        active_keys[key] = {"expiry": expiry,"uses": uses}
        db_save_key(key, expiry, uses)  # 🔥 DB ADD

        bot.reply_to(message,f"🔑 `{key}`",parse_mode="Markdown")
    except:
        bot.reply_to(message,"Invalid")
    user_selection.pop(message.chat.id,None)

# --- VERIFY KEY ---
@bot.message_handler(func=lambda m: m.text and m.text.startswith("KEY "))
def verify_key(message):
    key = message.text.split(" ",1)[1]

    # RAM FIRST
    if key in active_keys:
        data = active_keys[key]

        if datetime.now() > data["expiry"]:
            bot.reply_to(message,"Expired"); return

        if data["uses"] <= 0:
            bot.reply_to(message,"Limit"); return

        data["uses"] -= 1
        user_verified[message.from_user.id] = True
        db_set_verified(message.from_user.id)

        bot.reply_to(message,"Verified")
        return

    # DB FALLBACK
    res = db_verify_key(key)

    if res == "ok":
        user_verified[message.from_user.id] = True
        db_set_verified(message.from_user.id)
        bot.reply_to(message,"Verified")
    elif res == "expired":
        bot.reply_to(message,"Expired")
    elif res == "limit":
        bot.reply_to(message,"Limit")
    else:
        bot.reply_to(message,"Invalid")

# --- SEARCH FLOW ---
@bot.message_handler(func=lambda message: message.chat.id in user_selection)
def handle(message):

    if force_join_active:

        if not check_membership(message.from_user.id):
            return

        if not user_verified.get(message.from_user.id) and not db_is_verified(message.from_user.id):
            bot.reply_to(message,"🔐 Enter KEY")
            return

    bot.send_message(message.chat.id,"Working...")

# --- RUN ---
@app.route('/')
def home(): return "SYSTEM_ACTIVE"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    Thread(target=lambda: app.run(host='0.0.0.0', port=port)).start()
    bot.infinity_polling()
