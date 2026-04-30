import telebot
from telebot import types
from flask import Flask
from threading import Thread
import os

# 1. WEB SERVER
app = Flask('')
@app.route('/')
def home(): return "Active"
def run(): app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080)))
def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()

# 2. SOZLAMALAR
TOKEN = "8635058894:AAGY1CnFnsa1tj9gVpuRC012i3z7CxBbjbk"
ADMIN_ID = 7253593181
CHANNEL_ID = "@AnimeFonuzbaza" # @ belgisi bilan yoziladi
BOT_USERNAME = "AnimeFon_uz_Bot"

bot = telebot.TeleBot(TOKEN)
anime_db = {} 

# --- 🟢 OBUNANI NAZORAT QILISH FUNKSIYASI ---
def is_subscribed(user_id):
    try:
        # Bot foydalanuvchining statusini kanaldan tekshiradi
        status = bot.get_chat_member(CHANNEL_ID, user_id).status
        # Agar status quyidagilardan biri bo'lsa, u a'zo hisoblanadi
        if status in ['member', 'administrator', 'creator']:
            return True
        return False
    except Exception as e:
        # Agar bot kanalda admin bo'lmasa yoki kanal topilmasa xato beradi
        print(f"Xatolik: {e}")
        return False

# --- 🔴 OBUNA BO'LMAGANLAR UCHUN XABAR ---
def send_sub_message(chat_id):
    markup = types.InlineKeyboardMarkup()
    # Kanalga o'tish tugmasi
    btn_link = types.InlineKeyboardButton("Kanalga a'zo bo'lish ➕", url=f"https://t.me/{CHANNEL_ID.replace('@', '')}")
    # Tekshirish tugmasi
    btn_check = types.InlineKeyboardButton("✅ Tekshirish", callback_data="verify_sub")
    markup.add(btn_link)
    markup.add(btn_check)
    
    bot.send_message(chat_id, f"⚠️ Kechirasiz, botdan foydalanish uchun kanalimizga a'zo bo'lishingiz kerak!\n\nKanal: {CHANNEL_ID}", reply_markup=markup)

# --- START VA KODLARNI TEKSHIRISH ---
@bot.message_handler(commands=['start'])
def start_handler(message):
    user_id = message.from_user.id
    
    # Birinchi navbatda obunani nazorat qilamiz
    if not is_subscribed(user_id):
        send_sub_message(message.chat.id)
        return

    # Agar a'zo bo'lsa, bot davom etadi
    args = message.text.split()
    if len(args) > 1:
        kod = args[1]
        if kod in anime_db:
            send_anime(message.chat.id, kod)
        else:
            bot.send_message(message.chat.id, "❌ Kod noto'g'ri.")
    else:
        bot.send_message(message.chat.id, "👋 Salom! Anime ko'rish uchun kodini yuboring.")

# Foydalanuvchi shunchaki kod yozsa ham tekshiramiz
@bot.message_handler(func=lambda m: True)
def handle_all_messages(message):
    user_id = message.from_user.id
    
    # Har bir xabarda obunani tekshirish (Nazorat)
    if not is_subscribed(user_id):
        send_sub_message(message.chat.id)
        return
        
    kod = message.text
    if kod in anime_db:
        send_anime(message.chat.id, kod)
    elif message.from_user.id == ADMIN_ID:
        # Admin uchun menyularni ko'rsatish mumkin
        pass
    else:
        bot.reply_to(message, "❌ Bunday kod mavjud emas.")

# --- CALLBACK (TEKSHIRISH TUGMASI BOSILGANDA) ---
@bot.callback_query_handler(func=lambda call: call.data == "verify_sub")
def verify_callback(call):
    if is_subscribed(call.from_user.id):
        bot.answer_callback_query(call.id, "✅ Rahmat! Endi botdan foydalanishingiz mumkin.")
        bot.delete_message(call.message.chat.id, call.message.message_id)
        bot.send_message(call.message.chat.id, "Xush kelibsiz! Anime kodini yuboring:")
    else:
        bot.answer_callback_query(call.id, "❌ Hali a'zo bo'lmadingiz! Iltimos, kanalga kiring.", show_alert=True)

# Admin va boshqa funksiyalarni shu yerga qo'shasiz...
def send_anime(chat_id, kod):
    anime = anime_db[kod]
    bot.send_photo(chat_id, anime['rasm'], caption=f"🎬 {anime['nomi']}")

if __name__ == "__main__":
    keep_alive()
    bot.infinity_polling(skip_pending=True)
