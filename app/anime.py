import telebot
from telebot import types
from flask import Flask
from threading import Thread
import time

# 1. WEB SERVER
app = Flask('')
@app.route('/')
def home(): return "Anime Bot Online!"

def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()

# 2. BOT SOZLAMALARI
TOKEN = "8635058894:AAGFI6uBoJhoh7GbICC5FSksl0zqPMcTQz8"
ADMIN_ID = 7253593181
bot = telebot.TeleBot(TOKEN)

# Bazada endi: anime_db[kod] = {"rasm": file_id, "nomi": "...", "qismlar": {1: "file_id", 2: "file_id"}}
anime_db = {}

# --- START ---
@bot.message_handler(commands=['start'])
def start(message):
    args = message.text.split()
    if len(args) > 1:
        code = args[1]
        if code in anime_db:
            send_anime_info(message.chat.id, code)
        else:
            bot.send_message(message.chat.id, "🔍 Anime topilmadi.")
    else:
        bot.send_message(message.chat.id, "👋 Salom! Anime kodini kiriting.")

# Anime ma'lumotlarini qismlar bilan yuborish
def send_anime_info(chat_id, code):
    anime = anime_db[code]
    markup = types.InlineKeyboardMarkup(row_width=3)
    
    # Qismlar tugmalarini yasash
    buttons = []
    for qism in sorted(anime['qismlar'].keys()):
        buttons.append(types.InlineKeyboardButton(f"{qism}-qism", callback_data=f"vid_{code}_{qism}"))
    
    markup.add(*buttons)
    bot.send_photo(chat_id, anime['rasm'], caption=f"📺 {anime['nomi']}\n\nQismlarni tanlang:", reply_markup=markup)

# Qismlarni yuborish (Callback)
@bot.callback_query_handler(func=lambda call: call.data.startswith('vid_'))
def callback_video(call):
    _, code, qism = call.data.split('_')
    qism = int(qism)
    video_id = anime_db[code]['qismlar'][qism]
    bot.send_video(call.message.chat.id, video_id, caption=f"🎬 {anime_db[code]['nomi']} | {qism}-qism")

# --- ADMIN PANEL (Yashirin) ---
@bot.message_handler(commands=['admin'])
def admin(message):
    if message.from_user.id == ADMIN_ID:
        m = types.ReplyKeyboardMarkup(resize_keyboard=True)
        m.add("Yangi Anime qo'shish ➕", "Qism qo'shish 📽")
        bot.send_message(message.chat.id, "🔐 Admin Panel:", reply_markup=m)

# Yangi Anime (Rasm va Nomi) qo'shish
@bot.message_handler(func=lambda m: m.text == "Yangi Anime qo'shish ➕")
def new_anime(message):
    if message.from_user.id == ADMIN_ID:
        bot.send_message(message.chat.id, "🖼 Anime uchun rasm (poster) yuboring:")
        bot.register_next_step_handler(message, get_poster)

def get_poster(message):
    if message.photo:
        p_id = message.photo[-1].file_id
        bot.send_message(message.chat.id, "📝 Anime nomini va kodini bunday yuboring:\nNom - Kod\n(Masalan: Arra odam - 101)")
        bot.register_next_step_handler(message, save_new_anime, p_id)

def save_new_anime(message, p_id):
    try:
        nomi, kodi = message.text.split(' - ')
        anime_db[kodi] = {"rasm": p_id, "nomi": nomi, "qismlar": {}}
        bot.send_message(message.chat.id, f"✅ Anime yaratildi! Kod: {kodi}. Endi qismlarni qo'shishingiz mumkin.")
    except:
        bot.send_message(message.chat.id, "⚠️ Xato! 'Nom - Kod' ko'rinishida yuboring.")

# Qismlarni qo'shish
@bot.message_handler(func=lambda m: m.text == "Qism qo'shish 📽")
def add_part(message):
    if message.from_user.id == ADMIN_ID:
        bot.send_message(message.chat.id, "🔢 Anime kodini yuboring:")
        bot.register_next_step_handler(message, get_code_for_part)

def get_code_for_part(message):
    code = message.text
    if code in anime_db:
        bot.send_message(message.chat.id, "📹 Videoni yuboring:")
        bot.register_next_step_handler(message, get_video_part, code)
    else:
        bot.send_message(message.chat.id, "❌ Bunday kodli anime yo'q.")

def get_video_part(message, code):
    if message.video:
        v_id = message.video.file_id
        bot.send_message(message.chat.id, "🔢 Nechanchi qism ekanligini yozing:")
        bot.register_next_step_handler(message, save_part, code, v_id)

def save_part(message, code, v_id):
    qism = int(message.text)
    anime_db[code]['qismlar'][qism] = v_id
    bot.send_message(message.chat.id, f"✅ {code} ga {qism}-qism qo'shildi!")

if __name__ == "__main__":
    keep_alive()
    bot.remove_webhook()
    time.sleep(1)
    bot.infinity_polling(skip_pending=True)
