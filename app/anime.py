import telebot
from telebot import types
from flask import Flask
from threading import Thread
import time
import os

# 1. WEB SERVER (Render yoki boshqa platformalar uchun)
app = Flask('')

@app.route('/')
def home():
    return "Bot status: Active"

def run():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()

# 2. BOT SOZLAMALARI
TOKEN = "8635058894:AAGY1CnFnsa1tj9gVpuRC012i3z7CxBbjbk"
ADMIN_ID = 7253593181
CHANNEL_ID = "@AnimeFonuzbaza" # Kanal manzili
BOT_USERNAME = "AnimeFon_uz_Bot"

bot = telebot.TeleBot(TOKEN)
anime_db = {} # Vaqtinchalik xotira (Serverda bazaga o'tkazish tavsiya etiladi)

# --- MAJBURIY OBUNA FUNKSIYASI ---
def check_sub(user_id):
    try:
        status = bot.get_chat_member(CHANNEL_ID, user_id).status
        if status in ['member', 'administrator', 'creator']:
            return True
        return False
    except Exception:
        return False

# --- ADMIN PANEL ---
@bot.message_handler(commands=['admin'])
def admin(message):
    if message.from_user.id == ADMIN_ID:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add("➕ Yangi Anime", "🗑 Animeni o'chirish")
        bot.send_message(message.chat.id, "Boshqaruv markazi:", reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == "➕ Yangi Anime")
def new_anime(message):
    if message.from_user.id == ADMIN_ID:
        msg = bot.send_message(message.chat.id, "🖼 Anime posterini (rasm) yuboring:")
        bot.register_next_step_handler(msg, get_poster)

def get_poster(message):
    if message.photo:
        p_id = message.photo[-1].file_id
        msg = bot.send_message(message.chat.id, "📝 Ma'lumotlarni yuboring:\nFormat: Nomi - Kod - Tavsif")
        bot.register_next_step_handler(msg, save_and_post, p_id)

def save_and_post(message, p_id):
    try:
        data = message.text.split(" - ")
        nomi, kod, tavsif = data[0], data[1], data[2]
        anime_db[kod] = {'nomi': nomi, 'rasm': p_id, 'tavsif': tavsif, 'qismlar': {}}
        
        markup = types.InlineKeyboardMarkup()
        btn = types.InlineKeyboardButton("Tomosha qilish", url=f"https://t.me/{BOT_USERNAME}?start={kod}")
        markup.add(btn)
        
        post_text = f"**YANGI ANIME!**\n\n**Nomi:** {nomi}\n**Tavsif:** {tavsif}"
        bot.send_photo(CHANNEL_ID, p_id, caption=post_text, reply_markup=markup, parse_mode="Markdown")
        bot.send_message(message.chat.id, f"✅ Kanalga yuborildi! Kod: {kod}")
    except:
        bot.send_message(message.chat.id, "❌ Xato! Format: Nomi - Kod - Tavsif")

# --- FOYDALANUVCHILAR UCHUN (START VA TEKSHIRUV) ---
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    
    if check_sub(user_id):
        args = message.text.split()
        if len(args) > 1:
            code = args[1]
            if code in anime_db:
                send_anime_details(message.chat.id, code)
            else:
                bot.send_message(message.chat.id, "❌ Kechirasiz, bu kod bilan anime topilmadi.")
        else:
            bot.send_message(message.chat.id, "Xush kelibsiz! Anime kodini yuboring.")
    else:
        markup = types.InlineKeyboardMarkup()
        btn = types.InlineKeyboardButton("Kanalga a'zo bo'lish", url=f"https://t.me/{CHANNEL_ID.replace('@', '')}")
        check_btn = types.InlineKeyboardButton("✅ Tekshirish", callback_data="check_sub")
        markup.add(btn)
        markup.add(check_btn)
        bot.send_message(message.chat.id, f"⚠️ Botdan foydalanish uchun kanalga a'zo bo'ling!", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "check_sub")
def check_callback(call):
    if check_sub(call.from_user.id):
        bot.delete_message(call.message.chat.id, call.message.message_id)
        bot.send_message(call.message.chat.id, "Rahmat! Endi kod yuborishingiz mumkin.")
    else:
        bot.answer_callback_query(call.id, "❌ Hali a'zo bo'lmadingiz!", show_alert=True)

def send_anime_details(chat_id, code):
    anime = anime_db[code]
    markup = types.InlineKeyboardMarkup(row_width=5)
    buttons = [types.InlineKeyboardButton(f"Q-{q}", callback_data=f"vid_{code}_{q}") for q in anime['qismlar'].keys()]
    markup.add(*buttons)
    bot.send_photo(chat_id, anime['rasm'], caption=f"**{anime['nomi']}**\n\nQismni tanlang:", reply_markup=markup, parse_mode="Markdown")

# --- ISHGA TUSHIRISH ---
if __name__ == "__main__":
    keep_alive()
    print("Bot ishga tushdi...")
    bot.infinity_polling(skip_pending=True)
