import telebot
from telebot import types
from flask import Flask
from threading import Thread
import time

# 1. WEB SERVER (UptimeRobot uchun)
app = Flask('')
@app.route('/')
def home(): return "Bot Online!"

def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()

# 2. BOT SOZLAMALARI
TOKEN = "8635058894:AAGFI6uBoJhoh7GbICC5FSksl0zqPMcTQz8"
ADMIN_ID = 7253593181
CHANNEL_ID = "@AnimeFonuzbaza" # Kanalingiz manzili (Bot u yerda admin bo'lishi shart)
BOT_USERNAME = "AnimeFon_uz_Bot" # Bot manzili (@ belgisiz)
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
            send_anime_info(message.chat.id, code)
        else:
            bot.send_message(message.chat.id, "🔍 Anime topilmadi.")
    else:
        bot.send_message(message.chat.id, "👋 Salom! Anime kodini kiriting.")

def send_anime_info(chat_id, code):
    anime = anime_db[code]
    markup = types.InlineKeyboardMarkup(row_width=3)
    buttons = [types.InlineKeyboardButton(f"{q}-qism", callback_data=f"vid_{code}_{q}") for q in sorted(anime['qismlar'].keys())]
    markup.add(*buttons)
    bot.send_photo(chat_id, anime['rasm'], caption=f"📺 {anime['nomi']}\n\nQismlar:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('vid_'))
def callback_video(call):
    _, code, qism = call.data.split('_')
    video_id = anime_db[code]['qismlar'][int(qism)]
    bot.send_video(call.message.chat.id, video_id, caption=f"🎬 {anime_db[code]['nomi']} | {qism}-qism")

# --- ADMIN PANEL ---
@bot.message_handler(commands=['admin'])
def admin(message):
    if message.from_user.id == ADMIN_ID:
        m = types.ReplyKeyboardMarkup(resize_keyboard=True)
        m.add("Yangi Anime qo'shish ➕", "Qism qo'shish 📽", "Animeni o'chirish 🗑")
        bot.send_message(message.chat.id, "🔐 Admin Panel:", reply_markup=m)

# --- YANGI ANIME VA KANALGA POST ---
@bot.message_handler(func=lambda m: m.text == "Yangi Anime qo'shish ➕")
def new_anime(message):
    if message.from_user.id == ADMIN_ID:
        bot.send_message(message.chat.id, "🖼 Anime posterini (rasm) yuboring:")
        bot.register_next_step_handler(message, get_poster)

def get_poster(message):
    if message.photo:
        p_id = message.photo[-1].file_id
        bot.send_message(message.chat.id, "📝 Format: Nom - Kod - Tavsif\n(Masalan: Arra odam - 101 - Arra odam haqida anime)")
        bot.register_next_step_handler(message, save_and_post, p_id)

def save_and_post(message, p_id):
    try:
        data = message.text.split(' - ')
        nomi, kodi, tavsif = data[0], data[1], data[2]
        anime_db[kodi] = {"rasm": p_id, "nomi": nomi, "qismlar": {}}
        
        # KANALGA POST YUBORISH
        channel_markup = types.InlineKeyboardMarkup()
        btn = types.InlineKeyboardButton("🍿 Tomosha qilish", url=f"https://t.me/{BOT_USERNAME}?start={kodi}")
        channel_markup.add(btn)
        
        post_text = f"🆕 **YANGI ANIME!**\n\n📺 **Nomi:** {nomi}\n📝 **Tavsif:** {tavsif}\n\n📥 Ko'rish uchun pastdagi tugmani bosing:"
        bot.send_photo(CHANNEL_ID, p_id, caption=post_text, reply_markup=channel_markup, parse_mode="Markdown")
        
        bot.send_message(message.chat.id, f"✅ Anime bazaga qo'shildi va kanalga post yuborildi! Kod: {kodi}")
    except:
        bot.send_message(message.chat.id, "⚠️ Xato! Format: Nom - Kod - Tavsif")

# --- QISM QO'SHISH ---
@bot.message_handler(func=lambda m: m.text == "Qism qo'shish 📽")
def add_part(message):
    if message.from_user.id == ADMIN_ID:
        bot.send_message(message.chat.id, "🔢 Anime kodini yuboring:")
        bot.register_next_step_handler(message, lambda msg: bot.send_message(msg.chat.id, "📹 Videoni yuboring:") or bot.register_next_step_handler(msg, get_video_part, msg.text))

def get_video_part(message, code):
    if message.video:
        v_id = message.video.file_id
        bot.send_message(message.chat.id, "🔢 Qism raqami:")
        bot.register_next_step_handler(message, lambda m: save_part(m, code, v_id))

def save_part(message, code, v_id):
    qism = int(message.text)
    anime_db[code]['qismlar'][qism] = v_id
    bot.send_message(message.chat.id, f"✅ {qism}-qism qo'shildi!")

# --- ISHGA TUSHIRISH ---
if __name__ == "__main__":
    keep_alive()
    bot.remove_webhook()
    time.sleep(1)
    bot.infinity_polling(skip_pending=True)
