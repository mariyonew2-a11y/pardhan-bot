import telebot
from flask import Flask
from threading import Thread
import os

# Yahan hum token direct nahi likhenge (Security ke liye)
BOT_TOKEN = os.environ.get('BOT_TOKEN') 
bot = telebot.TeleBot(BOT_TOKEN)

app = Flask('')

@app.route('/')
def home():
    return "Beast Bot is Running!"

def run():
    # Render hamesha port 8080 ya dynamic port mangta hai
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.start()

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "I am active! How can I help you, Beast Harry?")

if __name__ == "__main__":
    print("Bot is starting...")
    keep_alive()
    bot.infinity_polling()
