import telebot
from telebot import types
from flask import Flask
from threading import Thread
import time

# 1. WEB SERVER (Render va UptimeRobot uchun)
app = Flask('')

@app.route('/')
def home():
    return "Bot Online!"

def run():
    # Render porti 8080
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()

# 2. BOT SOZLAMALARI (Yangi Token)
TOKEN = "8635058894:AAGFI6uBoJhoh7GbICC5FSksl0zqPMcTQz8"
ADMIN_ID = 7253593181
bot = telebot.TeleBot(TOKEN)

# Vaqtinchalik baza
anime_db = {}

# --- START ---
@bot.message_handler(commands=['start'])
def start(message):
    args = message.text.split()
    if len(args) > 1:
        code = args[1]
        if code in anime_db:
            bot.send_video(message.chat.id, anime_db[code])
        else:
            bot.send_message(message.chat.id, "🔍 Topilmadi.")
    else:
        bot.send_message(message.chat.id, "👋 Salom! Kod yuboring yoki /admin deb yozing.")

# --- ADMIN PANEL ---
@bot.message_handler(commands=['admin'])
def admin(message):
    if message.from_user.id == ADMIN_ID:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add("Anime qo'shish ➕", "Animeni o'chirish 🗑")
        bot.send_message(message.chat.id, "Admin panel:", reply_markup=markup)

# --- QO'SHISH ---
@bot.message_handler(func=lambda m: m.text == "Anime qo'shish ➕")
def add_start(message):
    if message.from_user.id == ADMIN_ID:
        bot.send_message(message.chat.id, "📹 Videoni yuboring:")
        bot.register_next_step_handler(message, get_video)

def get_video(message):
    if message.video:
        f_id = message.video.file_id
        bot.send_message(message.chat.id, "🔢 KOD yuboring:")
        bot.register_next_step_handler(message, save_anime, f_id)
    else:
        bot.send_message(message.chat.id, "❌ Video yuboring.")

def save_anime(message, f_id):
    code = message.text
    anime_db[code] = f_id
    bot.send_message(message.chat.id, f"✅ Saqlandi: {code}")

# --- O'CHIRISH ---
@bot.message_handler(func=lambda m: m.text == "Animeni o'chirish 🗑")
def del_start(message):
    if message.from_user.id == ADMIN_ID:
        bot.send_message(message.chat.id, "🗑 Kodni yuboring:")
        bot.register_next_step_handler(message, del_proc)

def del_proc(message):
    code = message.text
    if code in anime_db:
        del anime_db[code]
        bot.send_message(message.chat.id, f"✅ {code} o'chirildi.")
    else:
        bot.send_message(message.chat.id, "🔍 Topilmadi.")

# --- KOD QIDIRISH ---
@bot.message_handler(func=lambda m: True)
def handle_text(message):
    code = message.text
    if code in anime_db:
        bot.send_video(message.chat.id, anime_db[code])
    elif not code.startswith('/'):
        bot.send_message(message.chat.id, "🔍 Hech narsa topilmadi.")

# --- ISHGA TUSHIRISH ---
if __name__ == "__main__":
    keep_alive()
    bot.remove_webhook()
    time.sleep(1)
    bot.infinity_polling(skip_pending=True)
