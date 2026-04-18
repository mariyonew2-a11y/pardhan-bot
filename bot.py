import telebot
from telethon import TelegramClient
from telethon.sessions import StringSession
import asyncio
import re
import os
import time
import random
import string
from datetime import datetime, timedelta
from flask import Flask
from threading import Thread
from telebot import types
from supabase import create_client, Client

# --- [SUPABASE CONFIG] ---
SUPABASE_URL = "https://rfspcxzcenqujyzkposx.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJmc3BjeHpjZW5xdWp5emtwb3N4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzY0OTQzNjAsImV4cCI6MjA5MjA3MDM2MH0.fe0bGuIS8NStvbQzeCiJ-gqYpW1xqkl3xmWxJfGlD6U"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- [CONFIG] ---
API_ID = 34871644 
API_HASH = '9ab73b2a48115feed25b5029c812ea29'
SESSION_STR = os.environ.get('TELETHON_SESSION') 
BOT_TOKEN = os.environ.get('BOT_TOKEN')

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask('')

ADMIN_ID = 1431950109
FORCE_JOIN_CHANNEL = "@pardhan_g"

# --- [HYBRID STORAGE - RAM] ---
force_join_active = False
verified_users_local = set() 
user_selection = {}
pending_searches = {}

# Branding Setup
MY_TG_LINK = "https://t.me/beast_harry"
MY_USERNAME = "@beast\_harry" # Backslash lagaya hai Markdown fix ke liye
TARGET_BOT_UID = '@LootVerseInfo_Bot' 
TARGET_BOT_NUM = '@LootVerseinfoBot'

# --- [DB SYNC - STARTUP] ---
def sync_db_to_ram():
    global force_join_active, verified_users_local
    try:
        # Sync Settings
        res = supabase.table("bot_settings").select("setting_value").eq("setting_name", "force_join_active").execute()
        if res.data: force_join_active = res.data[0]['setting_value']
        
        # Sync Verified Users
        res_users = supabase.table("verified_users").select("user_id").execute()
        verified_users_local = {user['user_id'] for user in res_users.data}
        print("✅ Hybrid Sync Complete: DB to RAM Loaded.")
    except Exception as e:
        print(f"⚠️ Sync Error: {e}")

# --- [KEY GENERATOR] ---
def generate_key(length=8):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

# --- [BEAST CLEANER] ---
def beast_cleaner(text):
    if not isinstance(text, str): return text
    text = re.sub(r'(https?://)?(t\.me|telegram\.me)/[a-zA-Z0-9_+/-]+', MY_TG_LINK, text)
    def replace_un(m):
        found = m.group(0)
        if found.lower() in [TARGET_BOT_UID.lower(), TARGET_BOT_NUM.lower()]: return found
        return "@beast_harry" # Clean text output
    text = re.sub(r'@[a-zA-Z0-9_]+', replace_un, text)
    text = re.sub(r'(?i)(powered by|made by|developer|owner|api_developer).*', '', text)
    return text.strip()

# --- [CORE ENGINE] ---
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
                if any(x in raw_text.upper() for x in ["RESULT FETCHED", "DETAILS FOR", "{"]) or len(raw_text) > 100:
                    clean_res = beast_cleaner(raw_text)
                    await client.disconnect(); return clean_res
                if any(x in raw_text.upper() for x in ["NOT AVAILABLE", "NOT FOUND"]):
                    await client.disconnect(); return "❌ No record found!"
                await asyncio.sleep(1)
            await client.disconnect(); return "❌ Slow Response."
    except Exception as e:
        if client.is_connected(): await client.disconnect()
        return f"❌ Error: {str(e)}"

# --- [HELPERS] ---
def check_membership(user_id):
    try:
        status = bot.get_chat_member(FORCE_JOIN_CHANNEL, user_id).status
        return status in ['member', 'administrator', 'creator']
    except: return False

def run_osint(chat_id, val, mode, reply_id):
    m = bot.send_message(chat_id, "🛰 `SEARCHING_DATABASE...`", parse_mode="Markdown", reply_to_message_id=reply_id)
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    res = loop.run_until_complete(fetch_intel(val, mode))
    loop.close()
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("Developer ⚡", url=MY_TG_LINK))
    bot.edit_message_text(f"🏁 **INTEL DECRYPTED**\n━━━━━━━━━━━━━\n{res}\n━━━━━━━━━━━━━", 
                          chat_id, m.message_id, parse_mode="Markdown", reply_markup=markup)
    Thread(target=lambda: (time.sleep(60), bot.delete_message(chat_id, m.message_id))).start()

# --- [HANDLERS] ---

@bot.message_handler(commands=['start'])
def welcome(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(types.KeyboardButton("👤 USER ID Search"), types.KeyboardButton("📱 NUMBER Search"))
    if message.from_user.id == ADMIN_ID: markup.add(types.KeyboardButton("🛠 ADMIN PANEL"))
    
    # Fix: Markdown Underscore Escaped
    bot.send_message(message.chat.id, f"💀 **Welcome, {message.from_user.first_name}!**\n\n⚡ **PARDHAN JI OSINT**\n━━━━━━━━━━━━━\nSelect Mode.\n\nDeveloper: {MY_USERNAME}", 
                     parse_mode="Markdown", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text == "🛠 ADMIN PANEL" and m.from_user.id == ADMIN_ID)
def admin(message):
    status = "✅ ON" if force_join_active else "❌ OFF"
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(f"Force Join: {status}", callback_data="toggle"),
               types.InlineKeyboardButton("Gen Key 🔑", callback_data="gen"))
    bot.send_message(message.chat.id, "🛠 **ADMIN PANEL**", reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data == "toggle")
def toggle(call):
    global force_join_active
    force_join_active = not force_join_active
    supabase.table("bot_settings").upsert({"setting_name": "force_join_active", "setting_value": force_join_active}).execute()
    admin(call.message) # Refresh
    bot.answer_callback_query(call.id, "Updated!")

@bot.callback_query_handler(func=lambda c: c.data == "gen")
def gen_btn(call):
    bot.send_message(call.message.chat.id, "🔑 Send: `TIME USES` (Ex: `60 5`)")
    user_selection[call.message.chat.id] = "gen"

@bot.message_handler(func=lambda m: user_selection.get(m.chat.id) == "gen")
def make_key(message):
    try:
        t, u = map(int, message.text.split())
        key = generate_key()
        exp = (datetime.now() + timedelta(minutes=t)).isoformat()
        supabase.table("bot_keys").insert({"key_code": key, "expiry_timestamp": exp, "uses_left": u}).execute()
        bot.reply_to(message, f"🔑 Key: `{key}`")
    except: bot.reply_to(message, "❌ Format error")
    user_selection.pop(message.chat.id, None)

@bot.message_handler(func=lambda m: m.text and m.text.startswith("KEY "))
def verify_key(message):
    key_input = message.text.split(" ", 1)[1].strip()
    res = supabase.table("bot_keys").select("*").eq("key_code", key_input).execute()
    if res.data:
        d = res.data[0]
        exp = datetime.fromisoformat(d['expiry_timestamp'].replace('Z', '+00:00'))
        if datetime.now(exp.tzinfo) < exp and d['uses_left'] > 0:
            supabase.table("bot_keys").update({"uses_left": d['uses_left'] - 1}).eq("key_code", key_input).execute()
            supabase.table("verified_users").insert({"user_id": message.from_user.id}).execute()
            verified_users_local.add(message.from_user.id)
            bot.reply_to(message, "✅ Verified!")
            return
    bot.reply_to(message, "❌ Invalid/Expired Key")

@bot.message_handler(func=lambda m: m.text in ["👤 USER ID Search", "📱 NUMBER Search"])
def ask_val(message):
    user_selection[message.chat.id] = 'uid' if "USER" in message.text else 'num'
    bot.reply_to(message, "🎯 **Enter Target:**")

@bot.message_handler(func=lambda m: m.chat.id in user_selection)
def process(message):
    if message.text.startswith('/'): return
    mode = user_selection.pop(message.chat.id)
    
    # Hybrid Check (Local RAM for Speed)
    if force_join_active:
        if not check_membership(message.from_user.id):
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("Join Channel 📢", url="https://t.me/pardhan_g"),
                       types.InlineKeyboardButton("Verify ✅", callback_data="check"))
            pending_searches[message.from_user.id] = {'v': message.text, 'm': mode, 'id': message.message_id}
            bot.reply_to(message, "⚠️ Join first!", reply_markup=markup)
            return
        if message.from_user.id not in verified_users_local:
            bot.reply_to(message, "🔐 Enter Key (KEY XXXX)")
            return
            
    run_osint(message.chat.id, message.text, mode, message.message_id)

@bot.callback_query_handler(func=lambda c: c.data == "check")
def check_btn(call):
    if check_membership(call.from_user.id):
        if call.from_user.id in pending_searches:
            d = pending_searches.pop(call.from_user.id)
            run_osint(call.message.chat.id, d['v'], d['m'], d['id'])
    else: bot.answer_callback_query(call.id, "Join first!", show_alert=True)

# --- [SERVER] ---
@app.route('/')
def home(): return "ACTIVE"

if __name__ == "__main__":
    sync_db_to_ram() # Start mein DB se RAM load karega
    Thread(target=lambda: app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080)))).start()
    bot.infinity_polling()
