import telebot
from telebot import types
from flask import Flask
from threading import Thread
import time
import os

# 1. WEB SERVER (UptimeRobot va Render uchun)
app = Flask('')

@app.route('/')
def home():
    return "Bot Online!"

def run():
    # Render uchun majburiy port
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()

# 2. BOT 8635058894:AAGFI6uBoJhoh7GbICC5FSksl0zqPMcTQz8
TOKEN = ""
ADMIN_ID = 7253593181
bot = telebot.TeleBot(TOKEN)

# Vaqtinchalik xotira
anime_db = {}

# --- START ---
@bot.message_handler(commands=['start'])
def start(message):
    text = message.text.split()
    if len(text) > 1:
        code = text[1]
        if code in anime_db:
            bot.send_video(message.chat.id, anime_db[code])
        else:
            bot.send_message(message.chat.id, "🔍 Topilmadi.")
    else:
        bot.send_message(message.chat.id, "Salom! Kod yuboring yoki /admin yozing.")

# --- ADMIN PANEL ---
@bot.message_handler(commands=['admin'])
def admin(message):
    if message.from_user.id == ADMIN_ID:
        m = types.ReplyKeyboardMarkup(resize_keyboard=True)
        m.add("Anime qo'shish ➕")
        bot.send_message(message.chat.id, "Admin panel:", reply_markup=m)

@bot.message_handler(func=lambda m: m.text == "Anime qo'shish ➕")
def add_video(message):
    if message.from_user.id == ADMIN_ID:
        bot.send_message(message.chat.id, "Videoni yuboring:")
        bot.register_next_step_handler(message, get_video)

def get_video(message):
    if message.video:
        f_id = message.video.file_id
        bot.send_message(message.chat.id, "Kod bering:")
        bot.register_next_step_handler(message, save_video, f_id)

def save_video(message, f_id):
    code = message.text
    anime_db[code] = f_id
    bot.send_message(message.chat.id, f"✅ Saqlandi: {code}")

# --- KOD YOZILGANDA ---
@bot.message_handler(func=lambda m: True)
def handle_text(message):
    code = message.text
    if code in anime_db:
        bot.send_video(message.chat.id, anime_db[code])
    elif not code.startswith('/'):
        bot.send_message(message.chat.id, "🔍 Bunday kod yo'q.")

# --- ISHGA TUSHIRISH ---
if __name__ == "__main__":
    keep_alive()
    bot.remove_webhook()
    time.sleep(1)
    print("Bot tayyor!")
    bot.infinity_polling(skip_pending=True)
