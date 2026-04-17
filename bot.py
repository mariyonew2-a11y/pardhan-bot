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

# --- [CONFIG - NO TOUCH] ---
API_ID = 34871644 
API_HASH = '9ab73b2a48115feed25b5029c812ea29'
SESSION_STR = os.environ.get('TELETHON_SESSION') 
BOT_TOKEN = os.environ.get('BOT_TOKEN')

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask('')

# Admin & Channel Setup
ADMIN_ID = 1431950109
FORCE_JOIN_CHANNEL = "@ANONYMOUS_GROUP_KING" # Tera naya channel link
force_join_active = False 
user_selection = {}

# Branding Setup
MY_TG_LINK = "https://t.me/beast_harry"
MY_USERNAME = "@beast_harry"
TARGET_BOT_UID = '@LootVerseInfo_Bot' 
TARGET_BOT_NUM = '@LootVerseinfoBot'

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
        status = bot.get_chat_member(FORCE_JOIN_CHANNEL, user_id).status
        return status in ['member', 'administrator', 'creator']
    except:
        return False # Agar error aaye toh False rakho verification ke liye

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
        "Select search mode and send your target ID/Number.\n\n"
        f"**Developer:** {MY_USERNAME}"
    )
    bot.send_message(message.chat.id, welcome_text, parse_mode="Markdown", reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == "🛠 ADMIN PANEL" and message.from_user.id == ADMIN_ID)
def admin_menu(message):
    global force_join_active
    status = "✅ ON" if force_join_active else "❌ OFF"
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(f"Force Join: {status}", callback_data="toggle_fj"))
    bot.send_message(message.chat.id, "🛠 **ADMIN CONTROL CENTER**\n\nManage Force Join verification:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "toggle_fj")
def toggle_fj(call):
    global force_join_active
    force_join_active = not force_join_active
    status = "✅ ON" if force_join_active else "❌ OFF"
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(f"Force Join: {status}", callback_data="toggle_fj"))
    bot.edit_message_text("🛠 **ADMIN CONTROL CENTER**\nSettings Updated!", call.message.chat.id, call.message.message_id, reply_markup=markup)

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

    # --- [CHANNEL VERIFICATION CHECK] ---
    if force_join_active and not check_membership(message.from_user.id):
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("Join Channel 📢", url=f"https://t.me/ANONYMOUS_GROUP_KING"))
        bot.reply_to(message, "⚠️ **Verification Required!**\n\nPlease join our channel first to access the database search result.", reply_markup=markup)
        return

    mode = user_selection.pop(message.chat.id)
    status_msg = bot.reply_to(message, "🛰 **Accessing Database...**\n*Pardhan Ji is fetching intel...*", parse_mode="Markdown")
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    final_output = loop.run_until_complete(fetch_intel(message.text, mode))
    loop.close()
    
    final_design = f"🏁 **INTEL DECRYPTED SUCCESSFULLY**\n━━━━━━━━━━━━━━━━━━━━━━━━\n{final_output}\n━━━━━━━━━━━━━━━━━━━━━━━━"
    markup_inline = types.InlineKeyboardMarkup()
    markup_inline.add(types.InlineKeyboardButton(text="Developer ⚡", url=MY_TG_LINK))
    
    bot.edit_message_text(final_design, message.chat.id, status_msg.message_id, parse_mode="Markdown", reply_markup=markup_inline)
    Thread(target=disappear_timer, args=(message.chat.id, status_msg.message_id)).start()

# --- [RENDER SETUP] ---
@app.route('/')
def home(): return "SYSTEM_ACTIVE"

if __name__ == "__main__":
    Thread(target=lambda: app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080)))).start()
    bot.infinity_polling()
