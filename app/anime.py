import telebot
from telebot import types
from flask import Flask
from threading import Thread
import time
import os

# 1. WEB SERVER (Render o'chirib yubormasligi uchun)
app = Flask('')

@app.route('/')
def home(): 
    return "Bot status: Active"

def run():
    # Render avtomatik port beradi, agar bo'lmasa 8080 ishlatiladi
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()

# 2. BOT SOZLAMALARI (O'zingizga moslang)
TOKEN = "8635058894:AAGY1CnFnsa1tj9gVpuRC012i3z7CxBbjbk"
ADMIN_ID = 7253593181
CHANNEL_ID = "@AnimeFonuzbaza" 
BOT_USERNAME = "AnimeFon_uz_Bot" 

bot = telebot.TeleBot(TOKEN)
anime_db = {} # Vaqtinchalik xotira

# --- ADMIN PANEL ---
@bot.message_handler(commands=['admin'])
def admin(message):
    if message.from_user.id == ADMIN_ID:
        m = types.ReplyKeyboardMarkup(resize_keyboard=True)
        m.add("Yangi Anime ➕", "Qism qo'shish 📽", "Animeni o'chirish 🗑")
        bot.send_message(message.chat.id, "🛠 Admin Panelga xush kelibsiz:", reply_markup=m)

# Yangi anime qo'shish (Poster + Ma'lumot)
@bot.message_handler(func=lambda m: m.text == "Yangi Anime ➕")
def new_anime(message):
    if message.from_user.id == ADMIN_ID:
        msg = bot.send_message(message.chat.id, "🖼 Anime posterini (rasm) yuboring:")
        bot.register_next_step_handler(msg, get_poster)

def get_poster(message):
    if message.photo:
        p_id = message.photo[-1].file_id
        msg = bot.send_message(message.chat.id, "📝 Ma'lumotlarni yuboring:\nFormat: `Nomi - Kod - Tavsif`", parse_mode="Markdown")
        bot.register_next_step_handler(msg, save_and_post, p_id)

def save_and_post(message, p_id):
    try:
        data = message.text.split(' - ')
        nomi, kodi, tavsif = data[0], data[1], data[2]
        anime_db[kodi] = {"rasm": p_id, "nomi": nomi, "qismlar": {}}
        
        # Kanalga yuborish uchun tugma
        markup = types.InlineKeyboardMarkup()
        btn = types.InlineKeyboardButton("🍿 Tomosha qilish", url=f"https://t.me/{BOT_USERNAME}?start={kodi}")
        markup.add(btn)
        
        post_text = f"🆕 **YANGI ANIME!**\n\n📺 **Nomi:** {nomi}\n📝 **Tavsif:** {tavsif}\n\n📥 Ko'rish uchun pastdagi tugmani bosing:"
        bot.send_photo(CHANNEL_ID, p_id, caption=post_text, reply_markup=markup, parse_mode="Markdown")
        bot.send_message(message.chat.id, f"✅ Kanalga yuborildi! Kod: `{kodi}`")
    except:
        bot.send_message(message.chat.id, "⚠️ Xato! Iltimos formatga amal qiling: `Nomi - Kod - Tavsif`")

# Videolarni qismlarga bo'lib qo'shish
@bot.message_handler(func=lambda m: m.text == "Qism qo'shish 📽")
def ask_code(message):
    if message.from_user.id == ADMIN_ID:
        msg = bot.send_message(message.chat.id, "🔢 Anime kodini kiriting:")
        bot.register_next_step_handler(msg, ask_video)

def ask_video(message, code=None):
    if not code: code = message.text
    if code in anime_db:
        msg = bot.send_message(message.chat.id, f"📽 {anime_db[code]['nomi']} uchun videoni yuboring:")
        bot.register_next_step_handler(msg, get_video_file, code)
    else:
        bot.send_message(message.chat.id, "❌ Bunday kodli anime bazada yo'q!")

def get_video_file(message, code):
    v_id = message.video.file_id if message.video else None
    if v_id:
        msg = bot.send_message(message.chat.id, "🔢 Bu nechanchi qism? (Faqat raqam yozing):")
        bot.register_next_step_handler(msg, final_save, code, v_id)
    else:
        bot.send_message(message.chat.id, "⚠️ Iltimos, video fayl yuboring!")

def final_save(message, code, v_id):
    try:
        qism_nomeri = int(message.text)
        anime_db[code]['qismlar'][qism_nomeri] = v_id
        bot.send_message(message.chat.id, f"✅ {qism_nomeri}-qism muvaffaqiyatli saqlandi!")
    except:
        bot.send_message(message.chat.id, "⚠️ Qism raqami faqat raqam bo'lishi kerak!")

# Animeni o'chirish
@bot.message_handler(func=lambda m: m.text == "Animeni o'chirish 🗑")
def ask_delete(message):
    if message.from_user.id == ADMIN_ID:
        msg = bot.send_message(message.chat.id, "🗑 O'chirish uchun anime kodini kiriting:")
        bot.register_next_step_handler(msg, process_delete)

def process_delete(message):
    code = message.text
    if code in anime_db:
        del anime_db[code]
        bot.send_message(message.chat.id, "✅ Anime va barcha qismlari o'chirildi!")
    else:
        bot.send_message(message.chat.id, "❌ Kod topilmadi.")

# --- FOYDALANUVCHILAR UCHUN ---
@bot.message_handler(commands=['start'])
def start(message):
    args = message.text.split()
    if len(args) > 1:
        code = args[1]
        if code in anime_db:
            send_anime_details(message.chat.id, code)
    else:
        bot.send_message(message.chat.id, "👋 Salom! Anime ko'rish uchun kodni yuboring yoki kanalimizdagi havolalardan foydalaning.")

# Shunchaki kod yuborganda qidirish
@bot.message_handler(func=lambda m: True)
def search_anime(message):
    code = message.text
    if code in anime_db:
        send_anime_details(message.chat.id, code)
    else:
        bot.send_message(message.chat.id, "🔍 Kechirasiz, bu kod bilan anime topilmadi.")

def send_anime_details(chat_id, code):
    anime = anime_db[code]
    markup = types.InlineKeyboardMarkup(row_width=5)
    # Qismlarni raqamli tugma qilib chiqarish
    buttons = [types.InlineKeyboardButton(f"{q}", callback_data=f"vid_{code}_{q}") for q in sorted(anime['qismlar'].keys())]
    markup.add(*buttons)
    
    bot.send_photo(chat_id, anime['rasm'], caption=f"📺 **{anime['nomi']}**\n\n🍿 Tomosha qilish uchun qismni tanlang:", reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data.startswith('vid_'))
def play_video(call):
    _, code, qism = call.data.split('_')
    video_id = anime_db[code]['qismlar'][int(qism)]
    bot.send_video(call.message.chat.id, video_id, caption=f"🎬 {anime_db[code]['nomi']} | {qism}-qism\n\n@AnimeFonuzbaza")

# --- ISHGA TUSHIRISH ---
if __name__ == "__main__":
    keep_alive() # Flask'ni ishga tushirish
    bot.infinity_polling(skip_pending=True)
