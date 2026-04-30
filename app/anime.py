import telebot
from telebot import types
from flask import Flask
from threading import Thread
import os

# 1. WEB SERVER (Render/VPS uchun)
app = Flask('')
@app.route('/')
def home(): return "Bot Active"
def run(): app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080)))
def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()

# 2. SOZLAMALAR
TOKEN = "8635058894:AAG8_Ad_3RFc1N4bRkFN2UTZEwuk2ruwK6c"
ADMIN_ID = 7253593181
CHANNEL_ID = "@AnimeFonuzbaza"
BOT_USERNAME = "AnimeFon_uz_Bot"

bot = telebot.TeleBot(TOKEN)
anime_db = {} 

# --- 🟢 MAJBURIY OBUNA ---
def is_subscribed(user_id):
    if int(user_id) == ADMIN_ID: return True
    try:
        status = bot.get_chat_member(CHANNEL_ID, user_id).status
        return status in ['member', 'administrator', 'creator']
    except: return False

def send_sub_msg(chat_id):
    markup = types.InlineKeyboardMarkup()
    btn1 = types.InlineKeyboardButton("Kanalga a'zo bo'lish ➕", url=f"https://t.me/{CHANNEL_ID.replace('@','')}")
    btn2 = types.InlineKeyboardButton("✅ Tekshirish", callback_data="recheck")
    markup.add(btn1, btn2)
    bot.send_message(chat_id, "⚠️ Botdan foydalanish uchun kanalga a'zo bo'ling!", reply_markup=markup)

# --- 🔵 ADMIN PANEL (DIQQAT: BU ENG TEPADA ISHLAYDI) ---
@bot.message_handler(commands=['admin'])
def admin_menu(message):
    if int(message.from_user.id) == ADMIN_ID:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add("➕ Anime qo'shish", "🎬 Qism qo'shish")
        bot.send_message(message.chat.id, "Boshqaruv paneli ochildi ✅", reply_markup=markup)
    else:
        bot.send_message(message.chat.id, "❌ Siz admin emassiz!")

@bot.message_handler(func=lambda m: m.text == "➕ Anime qo'shish")
def add_anime_start(message):
    if int(message.from_user.id) == ADMIN_ID:
        msg = bot.send_message(message.chat.id, "🖼 Anime rasm (poster) yuboring:")
        bot.register_next_step_handler(msg, get_poster)

def get_poster(message):
    if message.photo:
        p_id = message.photo[-1].file_id
        msg = bot.send_message(message.chat.id, "📝 Format: `Nomi | Kod | Tavsif`", parse_mode="Markdown")
        bot.register_next_step_handler(msg, save_anime, p_id)
    else: bot.send_message(message.chat.id, "❌ Rasm yubormadingiz!")

def save_anime(message, p_id):
    try:
        n, k, t = message.text.split(" | ")
        anime_db[k] = {'nomi': n, 'rasm': p_id, 'tavsif': t, 'qismlar': {}}
        
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("Tomosha qilish 🎬", url=f"https://t.me/{BOT_USERNAME}?start={k}"))
        
        bot.send_photo(CHANNEL_ID, p_id, caption=f"📺 **Yangi Anime!**\n\n🆔 Kod: `{k}`\n🌟 Nomi: {n}\n📑 {t}", reply_markup=markup, parse_mode="Markdown")
        bot.send_message(message.chat.id, f"✅ Qo'shildi! Kod: `{k}`")
    except: bot.send_message(message.chat.id, "❌ Xato! Format: `Nomi | Kod | Tavsif` (Tayoqchani unutmang)")

@bot.message_handler(func=lambda m: m.text == "🎬 Qism qo'shish")
def add_ep_start(message):
    if int(message.from_user.id) == ADMIN_ID:
        msg = bot.send_message(message.chat.id, "🔢 Anime kodini yozing:")
        bot.register_next_step_handler(msg, get_code)

def get_code(message):
    k = message.text
    if k in anime_db:
        msg = bot.send_message(message.chat.id, f"🎞 {anime_db[k]['nomi']} uchun video yuboring:")
        bot.register_next_step_handler(msg, save_video, k)
    else: bot.send_message(message.chat.id, "❌ Kod topilmadi.")

def save_video(message, k):
    if message.video:
        q = str(len(anime_db[k]['qismlar']) + 1)
        anime_db[k]['qismlar'][q] = message.video.file_id
        bot.send_message(message.chat.id, f"✅ {q}-qism saqlandi!")
    else: bot.send_message(message.chat.id, "❌ Video yubormadingiz!")

# --- 🟡 FOYDALANUVCHI QISMI ---
@bot.message_handler(commands=['start'])
def start_handler(message):
    if not is_subscribed(message.from_user.id):
        send_sub_msg(message.chat.id)
        return
    
    args = message.text.split()
    if len(args) > 1:
        k = args[1]
        if k in anime_db: show_anime(message.chat.id, k)
    else:
        bot.send_message(message.chat.id, "👋 Xush kelibsiz! Anime kodini yuboring.")

@bot.message_handler(func=lambda m: True)
def msg_handler(message):
    # Majburiy obuna tekshiruvi
    if not is_subscribed(message.from_user.id):
        send_sub_msg(message.chat.id)
        return
    
    # AGAR ADMIN /admin deb yozsa yoki tugmalarni bossa
    if int(message.from_user.id) == ADMIN_ID:
        if message.text == "/admin" or message.text in ["➕ Anime qo'shish", "🎬 Qism qo'shish"]:
            return

    # Kodni tekshirish
    k = message.text
    if k in anime_db:
        show_anime(message.chat.id, k)
    else:
        bot.reply_to(message, "❌ Bunday kod mavjud emas.")

def show_anime(chat_id, k):
    a = anime_db[k]
    markup = types.InlineKeyboardMarkup(row_width=4)
    btns = [types.InlineKeyboardButton(f"{q}-qism", callback_data=f"play_{k}_{q}") for q in a['qismlar']]
    markup.add(*btns)
    bot.send_photo(chat_id, a['rasm'], caption=f"🎬 **{a['nomi']}**\n\n{a['tavsif']}", reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    if call.data == "recheck":
        if is_subscribed(call.from_user.id):
            bot.delete_message(call.message.chat.id, call.message.message_id)
            bot.send_message(call.message.chat.id, "✅ Rahmat! Endi kod yuboring.")
        else:
            bot.answer_callback_query(call.id, "❌ A'zo bo'lmadingiz!", show_alert=True)
    elif call.data.startswith("play_"):
        _, k, q = call.data.split("_")
        bot.send_video(call.message.chat.id, anime_db[k]['qismlar'][q], caption=f"🎬 {anime_db[k]['nomi']} | {q}-qism")

if __name__ == "__main__":
    keep_alive()
    bot.infinity_polling(skip_pending=True)
