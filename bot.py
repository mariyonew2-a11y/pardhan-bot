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

# --- [CONFIG - NO TOUCH] ---
API_ID = 34871644 
API_HASH = '9ab73b2a48115feed25b5029c812ea29'
SESSION_STR = os.environ.get('TELETHON_SESSION') 
BOT_TOKEN = os.environ.get('BOT_TOKEN')

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask('')

ADMIN_ID = 1431950109
FORCE_JOIN_CHANNEL = "@pardhan_g"
user_selection = {}

# Branding Setup
MY_TG_LINK = "https://t.me/beast_harry"
MY_USERNAME = "@beast_harry"
TARGET_BOT_UID = '@LootVerseInfo_Bot' 
TARGET_BOT_NUM = '@LootVerseinfoBot'

# --- [SUPABASE DB HELPERS] ---

def get_db_setting(name):
    try:
        res = supabase.table("bot_settings").select("setting_value").eq("setting_name", name).execute()
        return res.data[0]['setting_value'] if res.data else False
    except: return False

def set_db_setting(name, value):
    try:
        supabase.table("bot_settings").upsert({"setting_name": name, "setting_value": value}).execute()
    except: pass

def check_user_verified_db(user_id):
    try:
        res = supabase.table("verified_users").select("*").eq("user_id", user_id).execute()
        return len(res.data) > 0
    except: return False

def add_verified_user_db(user_id):
    try:
        supabase.table("verified_users").insert({"user_id": user_id}).execute()
    except: pass

# --- [KEY GENERATOR] ---
def generate_key(length=8):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

# --- [BEAST CLEANER - NO TOUCH] ---
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

# --- [CORE ENGINE - NO TOUCH] ---
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

# --- [HELPERS] ---
def disappear_timer(chat_id, message_id):
    time.sleep(60)
    try: bot.delete_message(chat_id, message_id)
    except: pass

def check_membership(user_id):
    try:
        member = bot.get_chat_member(FORCE_JOIN_CHANNEL, user_id)
        return member.status in ['member', 'administrator', 'creator']
    except: return False

# --- [UI HANDLERS] ---

@bot.callback_query_handler(func=lambda call: call.data == "verify_join")
def verify_join(call):
    if check_membership(call.from_user.id):
        bot.answer_callback_query(call.id, "✅ Verified!")
        bot.delete_message(call.message.chat.id, call.message.message_id)
    else:
        bot.answer_callback_query(call.id, "❌ Join first!", show_alert=True)

@bot.message_handler(commands=['start'])
def welcome(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(types.KeyboardButton("👤 USER ID Search"), types.KeyboardButton("📱 NUMBER Search"))
    if message.from_user.id == ADMIN_ID:
        markup.add(types.KeyboardButton("🛠 ADMIN PANEL"))
    
    welcome_text = (
        f"💀 **Welcome, {message.from_user.first_name}!** 💀\n\n"
        "⚡ **PARDHAN JI OSINT** ⚡\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "Select search mode. Send User ID or Mobile Number.\n\n"
        f"Developer: {MY_USERNAME}"
    )
    bot.send_message(message.chat.id, welcome_text, parse_mode="Markdown", reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == "🛠 ADMIN PANEL" and message.from_user.id == ADMIN_ID)
def admin_menu(message):
    fj_status = get_db_setting("force_join_active")
    status_txt = "✅ ON" if fj_status else "❌ OFF"
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton(f"Force Join: {status_txt}", callback_data="toggle_fj"),
        types.InlineKeyboardButton("Generate Key 🔑", callback_data="gen_key")
    )
    bot.send_message(message.chat.id, "🛠 **ADMIN CONTROL CENTER**", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "toggle_fj")
def toggle_fj(call):
    current = get_db_setting("force_join_active")
    new_val = not current
    set_db_setting("force_join_active", new_val)
    status_txt = "✅ ON" if new_val else "❌ OFF"
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton(f"Force Join: {status_txt}", callback_data="toggle_fj"),
        types.InlineKeyboardButton("Generate Key 🔑", callback_data="gen_key")
    )
    bot.edit_message_text("🛠 Admin Settings Updated!", call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "gen_key")
def ask_key(call):
    bot.send_message(call.message.chat.id, "🔑 **Send:** `TIME USES` (e.g., `60 5`)")
    user_selection[call.message.chat.id] = "gen_key"

@bot.message_handler(func=lambda m: user_selection.get(m.chat.id) == "gen_key")
def create_key(message):
    try:
        time_min, uses = map(int, message.text.split())
        key = generate_key()
        expiry = (datetime.now() + timedelta(minutes=time_min)).isoformat()
        supabase.table("bot_keys").insert({"key_code": key, "expiry_timestamp": expiry, "uses_left": uses}).execute()
        bot.reply_to(message, f"🔑 Key: `{key}`\n⏳ {time_min} min\n👥 {uses} users", parse_mode="Markdown")
    except: bot.reply_to(message, "❌ Invalid Format")
    user_selection.pop(message.chat.id, None)

@bot.message_handler(func=lambda m: m.text and m.text.startswith("KEY "))
def verify_key(message):
    key = message.text.split(" ", 1)[1].strip()
    res = supabase.table("bot_keys").select("*").eq("key_code", key).execute()
    
    if res.data:
        data = res.data[0]
        expiry = datetime.fromisoformat(data['expiry_timestamp'].replace('Z', '+00:00'))
        
        if datetime.now(expiry.tzinfo) > expiry:
            bot.reply_to(message, "❌ Key Expired")
        elif data['uses_left'] <= 0:
            bot.reply_to(message, "❌ Key Limit Reached")
        else:
            supabase.table("bot_keys").update({"uses_left": data['uses_left'] - 1}).eq("key_code", key).execute()
            add_verified_user_db(message.from_user.id)
            bot.reply_to(message, "✅ Successfully Verified! Now you can search.")
    else:
        bot.reply_to(message, "❌ Invalid Key")

@bot.message_handler(func=lambda message: message.text in ["👤 USER ID Search", "📱 NUMBER Search"])
def ask_input(message):
    user_selection[message.chat.id] = 'uid' if "USER" in message.text else 'num'
    bot.reply_to(message, f"🎯 **Please Enter {'User ID' if 'USER' in message.text else 'Mobile Number'}:**", parse_mode="Markdown")

@bot.message_handler(func=lambda message: message.chat.id in user_selection)
def handle_input(message):
    if message.text.startswith('/'):
        user_selection.pop(message.chat.id, None)
        return

    if get_db_setting("force_join_active"):
        if not check_membership(message.from_user.id):
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("Join Channel 📢", url="https://t.me/pardhan_g"),
                       types.InlineKeyboardButton("Verify ✅", callback_data="verify_join"))
            bot.reply_to(message, "⚠️ Join channel first", reply_markup=markup)
            return

        if not check_user_verified_db(message.from_user.id):
            bot.reply_to(message, "🔐 **Access Denied!**\nPlease enter a valid key:\nUse → `KEY YOUR_KEY_HERE`", parse_mode="Markdown")
            return

    mode = user_selection.pop(message.chat.id)
    status_msg = bot.reply_to(message, "🛰 **Accessing Database...**", parse_mode="Markdown")
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    final_output = loop.run_until_complete(fetch_intel(message.text, mode))
    loop.close()
    
    final_design = f"🏁 **INTEL DECRYPTED**\n━━━━━━━━━━━━━━━━━━━━━━━━\n{final_output}\n━━━━━━━━━━━━━━━━━━━━━━━━"
    markup_inline = types.InlineKeyboardMarkup()
    markup_inline.add(types.InlineKeyboardButton(text="Developer ⚡", url=MY_TG_LINK))
    bot.edit_message_text(final_design, message.chat.id, status_msg.message_id, parse_mode="Markdown", reply_markup=markup_inline)
    Thread(target=disappear_timer, args=(message.chat.id, status_msg.message_id)).start()

@app.route('/')
def home(): return "SYSTEM_ACTIVE"

if __name__ == "__main__":
    Thread(target=lambda: app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080)))).start()
    bot.infinity_polling()
