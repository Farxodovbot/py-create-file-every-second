import telebot
from telebot import types
from flask import Flask
from threading import Thread
import time

# 1. WEB SERVER (Botni uyg'oq saqlash uchun)
app = Flask('')
@app.route('/')
def home(): 
    return "Bot 24/7 rejimida ishlamoqda!"

def run(): 
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()

# 2. BOT SOZLAMALARI
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
        bot.send_message(message.chat.id, "🛠 Admin Panel:", reply_markup=m)

@bot.message_handler(func=lambda m: m.text == "Yangi Anime ➕")
def new_anime(message):
    if message.from_user.id == ADMIN_ID:
        msg = bot.send_message(message.chat.id, "🖼 Anime posterini (rasm) yuboring:")
        bot.register_next_step_handler(msg, get_poster)

def get_poster(message):
    if message.photo:
        p_id = message.photo[-1].file_id
        msg = bot.send_message(message.chat.id, "📝 Formatda yozing: `Nom - Kod - Tavsif`", parse_mode="Markdown")
        bot.register_next_step_handler(msg, save_and_post, p_id)

def save_and_post(message, p_id):
    try:
        data = message.text.split(' - ')
        nomi, kodi, tavsif = data[0], data[1], data[2]
        anime_db[kodi] = {"rasm": p_id, "nomi": nomi, "qismlar": {}}
        
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🍿 Tomosha qilish", url=f"https://t.me/{BOT_USERNAME}?start={kodi}"))
        
        post_text = f"🆕 **YANGI ANIME!**\n\n📺 **Nomi:** {nomi}\n📝 **Tavsif:** {tavsif}\n\n📥 Ko'rish uchun pastdagi tugmani bosing:"
        bot.send_photo(CHANNEL_ID, p_id, caption=post_text, reply_markup=markup, parse_mode="Markdown")
        bot.send_message(message.chat.id, f"✅ Kanalga yuborildi! Kod: `{kodi}`")
    except:
        bot.send_message(message.chat.id, "⚠️ Xato! Format: `Nom - Kod - Tavsif`")

@bot.message_handler(func=lambda m: m.text == "Qism qo'shish 📽")
def ask_code(message):
    if message.from_user.id == ADMIN_ID:
        msg = bot.send_message(message.chat.id, "🔢 Anime kodini kiriting:")
        bot.register_next_step_handler(msg, ask_video)

def ask_video(message):
    code = message.text
    if code in anime_db:
        msg = bot.send_message(message.chat.id, f"📽 {anime_db[code]['nomi']} uchun videoni yuboring:")
        bot.register_next_step_handler(msg, get_video_file, code)
    else:
        bot.send_message(message.chat.id, "❌ Kod topilmadi!")

def get_video_file(message, code):
    v_id = message.video.file_id if message.video else None
    if v_id:
        msg = bot.send_message(message.chat.id, "🔢 Qism raqami?")
        bot.register_next_step_handler(msg, final_save, code, v_id)

def final_save(message, code, v_id):
    try:
        q = int(message.text)
        anime_db[code]['qismlar'][q] = v_id
        bot.send_message(message.chat.id, f"✅ {q}-qism saqlandi!")
    except: bot.send_message(message.chat.id, "❌ Faqat raqam!")

@bot.message_handler(func=lambda m: m.text == "Animeni o'chirish 🗑")
def ask_del(message):
    msg = bot.send_message(message.chat.id, "🗑 O'chirish uchun kodni yuboring:")
    bot.register_next_step_handler(msg, delete_proc)

def delete_proc(message):
    code = message.text
    if code in anime_db:
        del anime_db[code]
        bot.send_message(message.chat.id, "✅ O'chirildi!")
    else: bot.send_message(message.chat.id, "❌ Topilmadi!")

# --- FOYDALANUVCHILAR UCHUN ---
@bot.message_handler(commands=['start'])
def start_cmd(message):
    args = message.text.split()
    if len(args) > 1:
        send_anime_info(message.chat.id, args[1])
    else:
        bot.send_message(message.chat.id, "👋 Salom! Anime kodini yuboring yoki kanalimizdagi tugmalarni bosing.")

@bot.message_handler(func=lambda m: True)
def find_by_code(message):
    code = message.text
    if code in anime_db:
        send_anime_info(message.chat.id, code)
    else:
        bot.send_message(message.chat.id, "🔍 Bu kod bilan anime topilmadi.")

def send_anime_info(chat_id, code):
    anime = anime_db[code]
    markup = types.InlineKeyboardMarkup(row_width=5)
    btns = [types.InlineKeyboardButton(f"{q}", callback_data=f"v_{code}_{q}") for q in sorted(anime['qismlar'].keys())]
    markup.add(*btns)
    bot.send_photo(chat_id, anime['rasm'], caption=f"📺 **{anime['nomi']}**\n\n🍿 Qismlar:", reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data.startswith('v_'))
def play_video(call):
    _, code, qism = call.data.split('_')
    v_id = anime_db[code]['qismlar'][int(qism)]
    bot.send_video(call.message.chat.id, v_id, caption=f"🎬 {anime_db[code]['nomi']} | {qism}-qism")

if __name__ == "__main__":
    keep_alive()
    bot.infinity_polling(skip_pending=True)
