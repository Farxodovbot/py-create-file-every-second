import telebot
from telebot import types
from flask import Flask
from threading import Thread
import time

# 1. WEB SERVER (UptimeRobot uchun botni "uyg'oq" saqlaydi)
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
TOKEN = "8635058894:AAFIU3RzMbMUti0ZrfGJQ3fs_T9tGFqq3u8"
ADMIN_ID = 7253593181
CHANNEL_ID = "@AnimeFonuzbaza" 
BOT_USERNAME = "AnimeFon_uz_Bot" 

bot = telebot.TeleBot(TOKEN)

# Vaqtinchalik xotira (Buni keyinroq MongoDB ga aylantiramiz)
anime_db = {}

# --- FOYDALANUVCHILAR UCHUN ---
@bot.message_handler(commands=['start'])
def start(message):
    args = message.text.split()
    if len(args) > 1:
        code = args[1]
        if code in anime_db:
            send_anime_info(message.chat.id, code)
        else:
            bot.send_message(message.chat.id, "🔍 Kechirasiz, bu kod bilan anime topilmadi.")
    else:
        bot.send_message(message.chat.id, "👋 Salom! Anime ko'rish uchun kanalimizdagi maxsus havolalar orqali kiring yoki kodni yuboring.")

def send_anime_info(chat_id, code):
    anime = anime_db[code]
    markup = types.InlineKeyboardMarkup(row_width=4)
    # Qismlarni chiroyli tugma qilib chiqarish
    buttons = [types.InlineKeyboardButton(f"{q}", callback_data=f"vid_{code}_{q}") for q in sorted(anime['qismlar'].keys())]
    markup.add(*buttons)
    bot.send_photo(chat_id, anime['rasm'], caption=f"📺 **Nomi:** {anime['nomi']}\n\n🍿 **Qismlar ro'yxati:**", reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data.startswith('vid_'))
def callback_video(call):
    _, code, qism = call.data.split('_')
    video_id = anime_db[code]['qismlar'][int(qism)]
    bot.send_video(call.message.chat.id, video_id, caption=f"🎬 {anime_db[code]['nomi']} | {qism}-qism\n\n@AnimeFonuzbaza")

# --- ADMIN PANEL ---
@bot.message_handler(commands=['admin'])
def admin(message):
    if message.from_user.id == ADMIN_ID:
        m = types.ReplyKeyboardMarkup(resize_keyboard=True)
        m.add("Yangi Anime ➕", "Qism qo'shish 📽")
        bot.send_message(message.chat.id, "🛠 Admin Panelga xush kelibsiz:", reply_markup=m)

@bot.message_handler(func=lambda m: m.text == "Yangi Anime ➕")
def new_anime(message):
    if message.from_user.id == ADMIN_ID:
        msg = bot.send_message(message.chat.id, "🖼 Anime posterini (rasm) yuboring:")
        bot.register_next_step_handler(msg, get_poster)

def get_poster(message):
    if message.photo:
        p_id = message.photo[-1].file_id
        msg = bot.send_message(message.chat.id, "📝 Ma'lumotlarni kiriting:\nFormat: `Nom - Kod - Tavsif`", parse_mode="Markdown")
        bot.register_next_step_handler(msg, save_and_post, p_id)

def save_and_post(message, p_id):
    try:
        data = message.text.split(' - ')
        nomi, kodi, tavsif = data[0], data[1], data[2]
        anime_db[kodi] = {"rasm": p_id, "nomi": nomi, "qismlar": {}}
        
        # KANALGA AVTOMATIK POST
        channel_markup = types.InlineKeyboardMarkup()
        btn = types.InlineKeyboardButton("🍿 Tomosha qilish", url=f"https://t.me/{BOT_USERNAME}?start={kodi}")
        channel_markup.add(btn)
        
        post_text = f"🆕 **YANGI ANIME!**\n\n📺 **Nomi:** {nomi}\n📝 **Tavsif:** {tavsif}\n\n📥 Ko'rish uchun pastdagi tugmani bosing:"
        bot.send_photo(CHANNEL_ID, p_id, caption=post_text, reply_markup=channel_markup, parse_mode="Markdown")
        
        bot.send_message(message.chat.id, f"✅ Anime kanalga yuborildi! Kod: `{kodi}`", parse_mode="Markdown")
    except:
        bot.send_message(message.chat.id, "⚠️ Xato! Iltimos formatga rioya qiling: `Nom - Kod - Tavsif`")

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
        bot.send_message(message.chat.id, "❌ Bunday kodli anime yo'q!")

def get_video_file(message, code):
    if message.video:
        v_id = message.video.file_id
        msg = bot.send_message(message.chat.id, "🔢 Qism raqami?")
        bot.register_next_step_handler(msg, final_save, code, v_id)

def final_save(message, code, v_id):
    try:
        qism = int(message.text)
        anime_db[code]['qismlar'][qism] = v_id
        bot.send_message(message.chat.id, f"✅ {qism}-qism muvaffaqiyatli saqlandi!")
    except:
        bot.send_message(message.chat.id, "⚠️ Faqat raqam kiriting!")

# --- ISHGA TUSHIRISH ---
if __name__ == "__main__":
    keep_alive()
    bot.remove_webhook()
    time.sleep(1)
    bot.infinity_polling(skip_pending=True)
