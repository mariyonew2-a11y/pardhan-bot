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

# --- [CONFIG - NO TOUCH] ---
API_ID = 34871644 
API_HASH = '9ab73b2a48115feed25b5029c812ea29'
SESSION_STR = os.environ.get('TELETHON_SESSION') 
BOT_TOKEN = os.environ.get('BOT_TOKEN')

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask('')

# Admin & Channel Setup
ADMIN_ID = 1431950109
FORCE_JOIN_CHANNEL = "@pardhan_g"
force_join_active = False
user_selection = {}

# 🔥 NEW STORAGE
active_keys = {}   # key: {expiry, uses}
user_verified = {}

# Branding Setup
MY_TG_LINK = "https://t.me/beast_harry"
MY_USERNAME = "@beast_harry"
TARGET_BOT_UID = '@LootVerseInfo_Bot' 
TARGET_BOT_NUM = '@LootVerseinfoBot'

# --- 🔥 KEY GENERATOR ---
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
    except:
        return False

# 🔥 VERIFY BUTTON (existing system compatible)
@bot.callback_query_handler(func=lambda call: call.data == "verify_join")
def verify_join(call):
    if check_membership(call.from_user.id):
        bot.answer_callback_query(call.id, "✅ Verified!")
        bot.delete_message(call.message.chat.id, call.message.message_id)
    else:
        bot.answer_callback_query(call.id, "❌ Join first!")

# 🔥 ADMIN KEY GENERATE
@bot.callback_query_handler(func=lambda call: call.data == "gen_key")
def ask_key(call):
    bot.send_message(call.message.chat.id,
        "🔑 Send:\nTIME USES\nExample: 10 3\n(10 min, 3 users)")
    user_selection[call.message.chat.id] = "gen_key"

@bot.message_handler(func=lambda m: m.chat.id in user_selection and user_selection[m.chat.id] == "gen_key")
def create_key(message):
    try:
        time_min, uses = map(int, message.text.split())
        key = generate_key()
        expiry = datetime.now() + timedelta(minutes=time_min)

        active_keys[key] = {
            "expiry": expiry,
            "uses": uses
        }

        bot.reply_to(message,
            f"🔑 Key: `{key}`\n⏳ {time_min} min\n👥 {uses} users",
            parse_mode="Markdown"
        )
    except:
        bot.reply_to(message, "❌ Invalid Format")

    user_selection.pop(message.chat.id, None)

# 🔥 USER KEY VERIFY
@bot.message_handler(func=lambda m: m.text and m.text.startswith("KEY "))
def verify_key(message):
    key = message.text.split(" ",1)[1]

    if key in active_keys:
        data = active_keys[key]

        if datetime.now() > data["expiry"]:
            bot.reply_to(message, "❌ Key Expired")
            return

        if data["uses"] <= 0:
            bot.reply_to(message, "❌ Key Limit Over")
            return

        data["uses"] -= 1
        user_verified[message.from_user.id] = True

        bot.reply_to(message, "✅ Successfully Verified")
    else:
        bot.reply_to(message, "❌ Invalid Key")

# --- [UI HANDLERS] ---

@bot.message_handler(commands=['start'])
def welcome(message):
    user_name = message.from_user.first_name
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(types.KeyboardButton("👤 USER ID Search"), types.KeyboardButton("📱 NUMBER Search"))
    
    if message.from_user.id == ADMIN_ID:
        markup.add(types.KeyboardButton("🛠 ADMIN PANEL"))
    
    welcome_text = (
        f"💀 **Welcome, {user_name}!** 💀\n\n"
        "⚡ **PARDHAN JI OSINT** ⚡\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "🛰 **USAGE GUIDE:**\n"
        "Select search mode. Send User ID or Mobile Number.\n\n"
        "💡 **EXAMPLES:**\n"
        "• **UserID:** `123456789` \n"
        "• **Mobile:** `917282942060` \n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"Developer: @beast\_harry"
    )
    bot.send_message(message.chat.id, welcome_text, parse_mode="Markdown", reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == "🛠 ADMIN PANEL" and message.from_user.id == ADMIN_ID)
def admin_menu(message):
    global force_join_active
    status = "✅ ON" if force_join_active else "❌ OFF"
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton(f"Force Join: {status}", callback_data="toggle_fj"),
        types.InlineKeyboardButton("Generate Key 🔑", callback_data="gen_key")  # 🔥 added
    )
    bot.send_message(message.chat.id, "🛠 **ADMIN CONTROL CENTER**\nClick below:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "toggle_fj")
def toggle_fj(call):
    global force_join_active
    force_join_active = not force_join_active
    status = "✅ ON" if force_join_active else "❌ OFF"
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(f"Force Join: {status}", callback_data="toggle_fj"))
    bot.edit_message_text("🛠 Updated!", call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.message_handler(func=lambda message: message.text in ["👤 USER ID Search", "📱 NUMBER Search"])
def ask_for_input(message):
    mode = 'uid' if "USER" in message.text else 'num'
    user_selection[message.chat.id] = mode
    bot.reply_to(message, f"🎯 **Please Enter {'User ID' if mode == 'uid' else 'Mobile Number'}:**", parse_mode="Markdown")

@bot.message_handler(func=lambda message: message.chat.id in user_selection)
def handle_input(message):
    if message.text.startswith('/'):
        user_selection.pop(message.chat.id, None)
        return

    # 🔥 FORCE JOIN + PASSWORD FLOW
    if force_join_active:

        if not check_membership(message.from_user.id):
            markup = types.InlineKeyboardMarkup()
            markup.add(
                types.InlineKeyboardButton("Join Channel 📢", url="https://t.me/pardhan_g"),
                types.InlineKeyboardButton("Verify ✅", callback_data="verify_join")
            )
            bot.reply_to(message, "⚠️ Join channel first", reply_markup=markup)
            return

        if not user_verified.get(message.from_user.id):
            bot.reply_to(message, "🔐 Enter Password:\nUse → KEY XXXXX")
            return

    mode = user_selection.pop(message.chat.id)
    status_msg = bot.reply_to(message, "🛰 **Accessing Database...**", parse_mode="Markdown")
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    final_output = loop.run_until_complete(fetch_intel(message.text, mode))
    loop.close()
    
    final_design = f"🏁 **INTEL DECRYPTED SUCCESSFULLY**\n━━━━━━━━━━━━━━━━━━━━━━━━\n{final_output}\n━━━━━━━━━━━━━━━━━━━━━━━━"
    
    markup_inline = types.InlineKeyboardMarkup()
    markup_inline.add(types.InlineKeyboardButton(text="Developer ⚡", url=MY_TG_LINK))
    
    bot.edit_message_text(final_design, message.chat.id, status_msg.message_id, 
                          parse_mode="Markdown", reply_markup=markup_inline)
    
    Thread(target=disappear_timer, args=(message.chat.id, status_msg.message_id)).start()

# --- [RENDER SETUP] ---
@app.route('/')
def home(): return "SYSTEM_ACTIVE"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    Thread(target=lambda: app.run(host='0.0.0.0', port=port)).start()
    bot.infinity_polling()
