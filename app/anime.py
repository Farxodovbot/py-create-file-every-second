import telebot
from telebot import types
from flask import Flask
from threading import Thread
import os

# 1. WEB SERVER (Render o'chirib yubormasligi uchun)
app = Flask('')
@app.route('/')
def home(): return "Bot status: Active"

def run():
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080)))

def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()

# 2. SOZLAMALAR
TOKEN = "8635058894:AAFJl1zP6rbYyNTqna4j2S5IH451pk0DbRA"
ADMIN_ID = 7253593181
CHANNEL_ID = "@AnimeFonuzbaza"
BOT_USERNAME = "AnimeFon_uz_Bot"

bot = telebot.TeleBot(TOKEN)
anime_db = {} # { 'kod': {'nomi': '...', 'rasm': '...', 'tavsif': '...', 'qismlar': {'1': 'video_id'}} }

# 3. MAJBURIY OBUNA TEKSHIRUVI
def is_subscribed(user_id):
    if user_id == ADMIN_ID: return True # Admin tekshirilmaydi
    try:
        status = bot.get_chat_member(CHANNEL_ID, user_id).status
        return status in ['member', 'administrator', 'creator']
    except: return False

def send_sub_message(chat_id):
    markup = types.InlineKeyboardMarkup()
    btn1 = types.InlineKeyboardButton("Kanalga a'zo bo'lish ➕", url=f"https://t.me/{CHANNEL_ID.replace('@', '')}")
    btn2 = types.InlineKeyboardButton("✅ Tekshirish", callback_data="check_sub")
    markup.add(btn1)
    markup.add(btn2)
    bot.send_message(chat_id, f"⚠️ Botdan foydalanish uchun kanalimizga a'zo bo'ling!\n\nKanal: {CHANNEL_ID}", reply_markup=markup)

# 4. ADMIN FUNKSIYALARI
@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if message.from_user.id == ADMIN_ID:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add("➕ Anime qo'shish", "🎬 Qism qo'shish")
        bot.send_message(message.chat.id, "Admin panelga xush kelibsiz:", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text == "➕ Anime qo'shish")
def start_add_anime(message):
    if message.from_user.id == ADMIN_ID:
        msg = bot.send_message(message.chat.id, "🖼 Anime posterini (rasm) yuboring:")
        bot.register_next_step_handler(msg, get_poster)

def get_poster(message):
    if message.photo:
        p_id = message.photo[-1].file_id
        msg = bot.send_message(message.chat.id, "📝 Ma'lumotlarni yuboring:\nFormat: `Nomi | Kod | Tavsif`", parse_mode="Markdown")
        bot.register_next_step_handler(msg, finalize_anime, p_id)
    else: bot.send_message(message.chat.id, "❌ Rasm yubormadingiz!")

def finalize_anime(message, p_id):
    try:
        n, k, t = message.text.split(" | ")
        anime_db[k] = {'nomi': n, 'rasm': p_id, 'tavsif': t, 'qismlar': {}}
        
        # Kanalga yuborish
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("Tomosha qilish 🎬", url=f"https://t.me/{BOT_USERNAME}?start={k}"))
        bot.send_photo(CHANNEL_ID, p_id, caption=f"📺 **YANGI ANIME!**\n\n🆔 Kod: `{k}`\n🌟 Nomi: {n}\n📑 {t}", reply_markup=markup, parse_mode="Markdown")
        bot.send_message(message.chat.id, f"✅ Qo'shildi! Kod: `{k}`")
    except: bot.send_message(message.chat.id, "❌ Xato! Format: `Nomi | Kod | Tavsif` (Aralashib ketmasin)")

@bot.message_handler(func=lambda m: m.text == "🎬 Qism qo'shish")
def start_add_ep(message):
    if message.from_user.id == ADMIN_ID:
        msg = bot.send_message(message.chat.id, "🔢 Anime kodini yozing:")
        bot.register_next_step_handler(msg, get_code_for_ep)

def get_code_for_ep(message):
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

# 5. ASOSIY XABARLAR VA START
@bot.message_handler(commands=['start'])
def start_cmd(message):
    if not is_subscribed(message.from_user.id):
        send_sub_message(message.chat.id)
        return
    
    args = message.text.split()
    if len(args) > 1:
        k = args[1]
        if k in anime_db: show_anime(message.chat.id, k)
        else: bot.send_message(message.chat.id, "❌ Kod noto'g'ri.")
    else:
        bot.send_message(message.chat.id, "👋 Salom! Anime ko'rish uchun kodini yuboring.")

@bot.message_handler(func=lambda m: True)
def handle_msg(message):
    # Agar admin /admin deb yozsa, uni kod deb tekshirmaslik uchun:
    if message.text == "/admin" or message.text in ["➕ Anime qo'shish", "🎬 Qism qo'shish"]:
        return

    if not is_subscribed(message.from_user.id):
        send_sub_message(message.chat.id)
        return
    
    k = message.text
    if k in anime_db: show_anime(message.chat.id, k)
    else: bot.reply_to(message, "❌ Bunday kod mavjud emas.")

def show_anime(chat_id, k):
    a = anime_db[k]
    markup = types.InlineKeyboardMarkup(row_width=4)
    btns = [types.InlineKeyboardButton(f"{q}-qism", callback_data=f"p_{k}_{q}") for q in a['qismlar']]
    markup.add(*btns)
    bot.send_photo(chat_id, a['rasm'], caption=f"🎬 **{a['nomi']}**\n\n{a['tavsif']}", reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: True)
def callback_h(call):
    if call.data == "check_sub":
        if is_subscribed(call.from_user.id):
            bot.delete_message(call.message.chat.id, call.message.message_id)
            bot.send_message(call.message.chat.id, "✅ Rahmat! Endi kod yuboring.")
        else:
            bot.answer_callback_query(call.id, "❌ Hali a'zo bo'lmadingiz!", show_alert=True)
    
    elif call.data.startswith("p_"):
        _, k, q = call.data.split("_")
        bot.send_video(call.message.chat.id, anime_db[k]['qismlar'][q], caption=f"🎬 {anime_db[k]['nomi']} | {q}-qism")

# 6. RUN
if __name__ == "__main__":
    keep_alive()
    bot.infinity_polling(skip_pending=True)
