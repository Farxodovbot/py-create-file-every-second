import telebot
from telebot import types
from flask import Flask
from threading import Thread
import os

# 1. WEB SERVER (Fonda ishlashi uchun)
app = Flask('')
@app.route('/')
def home(): return "Bot Active"

def run(): app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080)))
def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()

# 2. SOZLAMALAR
TOKEN = "8635058894:AAGY1CnFnsa1tj9gVpuRC012i3z7CxBbjbk"
ADMIN_ID = 7253593181
CHANNEL_ID = "@AnimeFonuzbaza"
BOT_USERNAME = "AnimeFon_uz_Bot"

bot = telebot.TeleBot(TOKEN)
anime_db = {} # { '123': {'nomi': '...', 'rasm': '...', 'tavsif': '...', 'qismlar': {'1': 'file_id'}} }

# --- MAJBURIY OBUNA ---
def check_sub(user_id):
    try:
        status = bot.get_chat_member(CHANNEL_ID, user_id).status
        return status in ['member', 'administrator', 'creator']
    except: return False

# --- ADMIN PANEL BOSHQARUVI ---
@bot.message_handler(commands=['admin'])
def admin_menu(message):
    if message.from_user.id == ADMIN_ID:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add("➕ Anime qo'shish", "🎬 Qism qo'shish")
        markup.add("🗑 O'chirish")
        bot.send_message(message.chat.id, "Admin panelga xush kelibsiz:", reply_markup=markup)

# --- ANIME QO'SHISH JARAYONI ---
@bot.message_handler(func=lambda m: m.text == "➕ Anime qo'shish")
def add_anime_start(message):
    if message.from_user.id == ADMIN_ID:
        msg = bot.send_message(message.chat.id, "🖼 Anime uchun rasm (poster) yuboring:")
        bot.register_next_step_handler(msg, get_anime_poster)

def get_anime_poster(message):
    if message.photo:
        file_id = message.photo[-1].file_id
        msg = bot.send_message(message.chat.id, "📝 Ma'lumotlarni yuboring:\nFormat: `Nomi | Kod | Tavsif`", parse_mode="Markdown")
        bot.register_next_step_handler(msg, finalize_anime, file_id)
    else:
        bot.send_message(message.chat.id, "❌ Rasm yubormadingiz. Qaytadan urinib ko'ring.")

def finalize_anime(message, file_id):
    try:
        nomi, kod, tavsif = message.text.split(" | ")
        anime_db[kod] = {'nomi': nomi, 'rasm': file_id, 'tavsif': tavsif, 'qismlar': {}}
        
        # Kanalga yuborish
        markup = types.InlineKeyboardMarkup()
        btn = types.InlineKeyboardButton("Tomosha qilish 🎬", url=f"https://t.me/{BOT_USERNAME}?start={kod}")
        markup.add(btn)
        
        caption = f"📺 **Yangi Anime!**\n\n🆔 **Kod:** `{kod}`\n🌟 **Nomi:** {nomi}\n📑 **Tavsif:** {tavsif}"
        bot.send_photo(CHANNEL_ID, file_id, caption=caption, reply_markup=markup, parse_mode="Markdown")
        bot.send_message(message.chat.id, f"✅ Anime bazaga qo'shildi va kanalga yuborildi. Kod: `{kod}`", parse_mode="Markdown")
    except:
        bot.send_message(message.chat.id, "❌ Xato! Format: `Nomi | Kod | Tavsif` (Ajratuvchi tayoqchaga e'tibor bering)")

# --- QISM QO'SHISH (KOD ORQALI) ---
@bot.message_handler(func=lambda m: m.text == "🎬 Qism qo'shish")
def add_episode_start(message):
    if message.from_user.id == ADMIN_ID:
        msg = bot.send_message(message.chat.id, "🔢 Anime kodini kiriting:")
        bot.register_next_step_handler(msg, get_code_for_ep)

def get_code_for_ep(message):
    kod = message.text
    if kod in anime_db:
        msg = bot.send_message(message.chat.id, f"🎞 {anime_db[kod]['nomi']} uchun videoni yuboring:")
        bot.register_next_step_handler(msg, save_video, kod)
    else:
        bot.send_message(message.chat.id, "❌ Bunday kodli anime bazada yo'q.")

def save_video(message, kod):
    if message.video:
        qism_nomeri = len(anime_db[kod]['qismlar']) + 1
        anime_db[kod]['qismlar'][str(qism_nomeri)] = message.video.file_id
        bot.send_message(message.chat.id, f"✅ {qism_nomeri}-qism muvaffaqiyatli saqlandi!")
    else:
        bot.send_message(message.chat.id, "❌ Bu video emas.")

# --- FOYDALANUVCHILAR UCHUN START ---
@bot.message_handler(commands=['start'])
def start_handler(message):
    user_id = message.from_user.id
    if not check_sub(user_id):
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("Kanalga a'zo bo'lish ➕", url=f"https://t.me/{CHANNEL_ID.replace('@','') }"))
        markup.add(types.InlineKeyboardButton("✅ Tekshirish", callback_data="recheck"))
        bot.send_message(message.chat.id, "Botdan foydalanish uchun kanalimizga a'zo bo'ling!", reply_markup=markup)
        return

    # Agar start bilan kod kelsa (Kanal orqali o'tganda)
    args = message.text.split()
    if len(args) > 1:
        kod = args[1]
        if kod in anime_db:
            send_anime_card(message.chat.id, kod)
        else:
            bot.send_message(message.chat.id, "❌ Anime topilmadi.")
    else:
        bot.send_message(message.chat.id, "👋 Xush kelibsiz! Anime ko'rish uchun anime kodini yuboring.")

@bot.message_handler(func=lambda m: True)
def handle_code(message):
    if not check_sub(message.from_user.id): return
    kod = message.text
    if kod in anime_db:
        send_anime_card(message.chat.id, kod)
    else:
        bot.reply_to(message, "❌ Bunday kodli anime topilmadi.")

def send_anime_card(chat_id, kod):
    anime = anime_db[kod]
    markup = types.InlineKeyboardMarkup(row_width=4)
    btns = [types.InlineKeyboardButton(f"{q}-qism", callback_data=f"play_{kod}_{q}") for q in anime['qismlar']]
    markup.add(*btns)
    bot.send_photo(chat_id, anime['rasm'], caption=f"🎬 **{anime['nomi']}**\n\n{anime['tavsif']}\n\nQismni tanlang:", reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data.startswith("play_"))
def play_video(call):
    _, kod, qism = call.data.split("_")
    video_id = anime_db[kod]['qismlar'][qism]
    bot.send_video(call.message.chat.id, video_id, caption=f"🎬 {anime_db[kod]['nomi']} | {qism}-qism")

@bot.callback_query_handler(func=lambda call: call.data == "recheck")
def recheck(call):
    if check_sub(call.from_user.id):
        bot.answer_callback_query(call.id, "Rahmat! Endi foydalanishingiz mumkin.")
        bot.delete_message(call.message.chat.id, call.message.message_id)
        bot.send_message(call.message.chat.id, "Anime kodini yuboring:")
    else:
        bot.answer_callback_query(call.id, "❌ Hali a'zo bo'lmadingiz!", show_alert=True)

# 3. ISHGA TUSHIRISH
if __name__ == "__main__":
    keep_alive()
    print("Bot ishlamoqda...")
    bot.infinity_polling(skip_pending=True)
