import telebot
from telebot import types
import json
import os
from threading import Thread
from flask import Flask

# --- FLASK SERVER (Keep Alive uchun) ---
app = Flask('')

@app.route('/')
def home():
    return "Bot status: Active"

def run():
    # Portni 8080 dan 8081 ga o'zgartirdik (mojaro bo'lmasligi uchun)
    app.run(host='0.0.0.0', port=8081)

def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()

# --- ASOSIY SOZLAMALAR ---
TOKEN = "8635058894:AAHt945xJp5f6emU5IDaG0qDHNBOhqiGzKs" # Tokeningizni yangilang!
ADMIN_ID = 7253539181
CHANNEL_ID = "@AnimeFonzbaza"
BOT_USERNAME = "AnimeFon_uz_Bot"

bot = telebot.TeleBot(TOKEN)
DB_FILE = 'anime_data.json'

# --- JSON BAZA BILAN ISHLASH ---
def load_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_db(data):
    with open(DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

# Ma'lumotlarni yuklaymiz
anime_db = load_db()

# --- MAJBURIY OBUNA TEKSHIRUVI ---
def is_subscribed(user_id):
    if int(user_id) == ADMIN_ID:
        return True
    try:
        status = bot.get_chat_member(CHANNEL_ID, user_id).status
        return status in ['member', 'administrator', 'creator']
    except:
        return False

def send_sub_msg(chat_id):
    markup = types.InlineKeyboardMarkup()
    btn1 = types.InlineKeyboardButton("Kanalga a'zo bo'lish ➕", url=f"https://t.me/{CHANNEL_ID.replace('@','')}")
    btn2 = types.InlineKeyboardButton("✅ Tekshirish", callback_data="recheck")
    markup.add(btn1, btn2)
    bot.send_message(chat_id, "⚠️ Botdan foydalanish uchun kanalga a'zo bo'ling!", reply_markup=markup)

# --- ADMIN PANEL ---
@bot.message_handler(commands=['admin'])
def admin_menu(message):
    if int(message.from_user.id) == ADMIN_ID:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add("➕ Anime qo'shish")
        markup.add("🎬 Qism qo'shish", "🗑 Animeni o'chirish")
        bot.send_message(message.chat_id, "Boshqaruv paneli ochildi ✅", reply_markup=markup)
    else:
        bot.send_message(message.chat_id, "❌ Siz admin emassiz!")

# --- ANIME QO'SHISH ---
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
    else:
        bot.send_message(message.chat.id, "❌ Rasm yubormadingiz!")

def save_anime(message, p_id):
    try:
        n, k, t = message.text.split(" | ")
        anime_db[k] = {'nomi': n, 'rasm': p_id, 'tavsif': t, 'qismlar': {}}
        save_db(anime_db) # Faylga saqlash
        
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("Tomosha qilish", url=f"https://t.me/{BOT_USERNAME}?start={k}"))
        bot.send_photo(CHANNEL_ID, p_id, caption=f"✨ Yangi Anime!\n\n🆔 Kod: `{k}`\n🎬 Nomi: {n}\n\n📝 {t}", reply_markup=markup, parse_mode="Markdown")
        bot.send_message(message.chat.id, f"✅ Qo'shildi! Kod: {k}")
    except Exception as e:
        bot.send_message(message.chat.id, "❌ Xato! Tayoqcha (|) dan to'g'ri foydalaning.")

# --- QISM QO'SHISH ---
@bot.message_handler(func=lambda m: m.text == "🎬 Qism qo'shish")
def add_ep_start(message):
    if int(message.from_user.id) == ADMIN_ID:
        msg = bot.send_message(message.chat.id, "Anime kodini yozing:")
        bot.register_next_step_handler(msg, get_code_for_ep)

def get_code_for_ep(message):
    k = message.text
    if k in anime_db:
        msg = bot.send_message(message.chat.id, f"**{anime_db[k]['nomi']}** uchun video yuboring.")
        bot.register_next_step_handler(msg, save_video, k)
    else:
        bot.send_message(message.chat.id, "⚠️ Bunday kodli anime yo'q!")

def save_video(message, k):
    if message.video:
        q = str(len(anime_db[k]['qismlar']) + 1)
        anime_db[k]['qismlar'][q] = message.video.file_id
        save_db(anime_db) # Faylga saqlash
        bot.send_message(message.chat.id, f"✅ {q}-qism saqlandi!")
    else:
        bot.send_message(message.chat.id, "❌ Video yubormadingiz!")

# --- O'CHIRISH ---
@bot.message_handler(func=lambda m: m.text == "🗑 Animeni o'chirish")
def delete_anime_start(message):
    if int(message.from_user.id) == ADMIN_ID:
        msg = bot.send_message(message.chat.id, "O'chirmoqchi bo'lgan anime kodini yuboring:")
        bot.register_next_step_handler(msg, finalize_delete)

def finalize_delete(message):
    k = message.text
    if k in anime_db:
        del anime_db[k]
        save_db(anime_db) # Fayldan ham o'chirish
        bot.send_message(message.chat.id, f"✅ Anime {k} bazadan o'chirildi!")
    else:
        bot.send_message(message.chat.id, "❌ Bunday kod topilmadi.")

# --- FOYDALANUVCHI QISMI ---
@bot.message_handler(commands=['start'])
def start_handler(message):
    if not is_subscribed(message.from_user.id):
        send_sub_msg(message.chat.id)
        return
    
    args = message.text.split()
    if len(args) > 1:
        k = args[1]
        if k in anime_db:
            show_anime(message.chat.id, k)
        else:
            bot.send_message(message.chat.id, "❌ Bunday kod mavjud emas.")
    else:
        bot.send_message(message.chat.id, "👋 Salom! Anime kodini yuboring.")

@bot.message_handler(func=lambda m: True)
def msg_handler(message):
    if not is_subscribed(message.from_user.id):
        send_sub_msg(message.chat.id)
        return
    
    # Admin xabarlarini o'tkazib yubormaslik uchun
    if int(message.from_user.id) == ADMIN_ID and message.text in ["➕ Anime qo'shish", "🎬 Qism qo'shish", "🗑 Animeni o'chirish"]:
        return

    k = message.text
    if k in anime_db:
        show_anime(message.chat.id, k)
    else:
        bot.reply_to(message, "⚠️ Bunday kod mavjud emas.")

def show_anime(chat_id, k):
    a = anime_db[k]
    markup = types.InlineKeyboardMarkup(row_width=4)
    btns = [types.InlineKeyboardButton(f"{q}-qism", callback_data=f"p_{k}_{q}") for q in a['qismlar']]
    markup.add(*btns)
    bot.send_photo(chat_id, a['rasm'], caption=f"🎬 **{a['nomi']}**\n\n📝 {a['tavsif']}", reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    if call.data == "recheck":
        if is_subscribed(call.from_user.id):
            bot.delete_message(call.message.chat.id, call.message.message_id)
            bot.send_message(call.message.chat.id, "✅ Rahmat! Endi kod yuboring.")
        else:
            bot.answer_callback_query(call.id, "❌ A'zo bo'lmadingiz!", show_alert=True)
    
    elif call.data.startswith("p_"):
        _, k, q = call.data.split("_")
        video_id = anime_db[k]['qismlar'][q]
        bot.send_video(call.message.chat.id, video_id, caption=f"🎬 {anime_db[k]['nomi']} | {q}-qism")

# --- ISHGA TUSHIRISH ---
if __name__ == "__main__":
    keep_alive()
    print("Bot ishlamoqda...")
    bot.infinity_polling(skip_pending=True)
