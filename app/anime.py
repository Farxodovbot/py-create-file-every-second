import telebot
from telebot import types
from flask import Flask
from threading import Thread
import os

# 1. WEB SERVER VA PORT SOZLAMASI
app = Flask('')

@app.route('/')
def home():
    return "Bot Online! Port 8080 ishlamoqda."

def run():
    # Render va boshqa serverlar uchun 8080 porti
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()

# 2. TELEGRAM BOT SOZLAMALARI
TOKEN = "8635058894:AAHnof_upa_bWpcL3b6SNVt7wNO-t74zBxg"
ADMIN_ID = 7253593181
CHANNEL_ID = "@AnimeFonuzbaza"
bot = telebot.TeleBot(TOKEN)

# Bazani vaqtincha saqlash
anime_db = {}

# Majburiy obunani tekshirish funksiyasi
def check_sub(user_id):
    try:
        status = bot.get_chat_member(CHANNEL_ID, user_id).status
        return status in ['member', 'administrator', 'creator']
    except:
        return False

# --- START BUYRUG'I ---
@bot.message_handler(commands=['start'])
def start(message):
    if not check_sub(message.from_user.id):
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("A'zo bo'lish ➕", url=f"https://t.me/{CHANNEL_ID[1:]}"))
        bot.send_message(message.chat.id, "Botdan foydalanish uchun kanalga a'zo bo'ling!", reply_markup=markup)
        return

    text = message.text.split()
    if len(text) > 1:
        code = text[1]
        if code in anime_db:
            bot.send_video(message.chat.id, anime_db[code], caption=f"🍿 Kod: {code}")
        else:
            bot.send_message(message.chat.id, "😔 Bunday kodli anime topilmadi.")
    else:
        bot.send_message(message.chat.id, "👋 Salom! Anime kodini yuboring.")

# --- ADMIN PANEL ---
@bot.message_handler(commands=['admin'])
def admin(message):
    if message.from_user.id == ADMIN_ID:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add("Anime qo'shish ➕", "Post yaratish 📝")
        bot.send_message(message.chat.id, "Admin panelga xush kelibsiz!", reply_markup=markup)

# --- ANIME QO'SHISH ---
@bot.message_handler(func=lambda m: m.text == "Anime qo'shish ➕")
def add_anime(message):
    if message.from_user.id == ADMIN_ID:
        bot.send_message(message.chat.id, "📹 Anime videosini yuboring:")
        bot.register_next_step_handler(message, get_video)

def get_video(message):
    if message.video or message.document:
        file_id = message.video.file_id if message.video else message.document.file_id
        bot.send_message(message.chat.id, "🔢 Ushbu anime uchun kod bering:")
        bot.register_next_step_handler(message, save_anime, file_id)
    else:
        bot.send_message(message.chat.id, "⚠️ Bu video emas. Qaytadan urinib ko'ring.")

def save_anime(message, file_id):
    code = message.text
    anime_db[code] = file_id
    bot.send_message(message.chat.id, f"✅ Saqlandi! Kod: {code}")

# --- POST YARATISH (KANAL UCHUN) ---
@bot.message_handler(func=lambda m: m.text == "Post yaratish 📝")
def create_post(message):
    if message.from_user.id == ADMIN_ID:
        bot.send_message(message.chat.id, "🖼 Rasm yuboring (ma'lumotlarni captionga yozing):")
        bot.register_next_step_handler(message, get_photo)

def get_photo(message):
    if message.photo:
        photo_id = message.photo[-1].file_id
        caption = message.caption
        bot.send_message(message.chat.id, "🔢 Bu post qaysi kodga ulansin?")
        bot.register_next_step_handler(message, send_post, photo_id, caption)
    else:
        bot.send_message(message.chat.id, "⚠️ Bu rasm emas.")

def send_post(message, photo_id, caption):
    code = message.text
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🎬 Tomosha qilish", url=f"https://t.me/{bot.get_me().username}?start={code}"))
    bot.send_photo(CHANNEL_ID, photo_id, caption=caption, reply_markup=markup)
    bot.send_message(message.chat.id, "✅ Post kanalga chiqdi!")

# --- BOTNI ISHGA TUSHIRISH ---
if __name__ == "__main__":
    keep_alive() # Web serverni yoqish
    print("Bot va Port 8080 ishga tushdi...")
    bot.infinity_polling(timeout=10, long_polling_timeout=5)
