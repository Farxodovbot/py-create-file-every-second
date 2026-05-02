import telebot
from telebot import types
import json
import os
from threading import Thread
from flask import Flask

# --- KONFIGURATSIYA ---
TOKEN = '8635058894:AAHt945xJp5f6emU5IDaG0qDHNBOhqiGzKs'
ADMIN_ID = 7253593181
CHANNEL_ID = -1003863245997
CHANNEL_LINK = "https://t.me/AnimeFonuzbaza"
DB_FILE = 'anime_data.json'
USERS_FILE = 'users.json'

bot = telebot.TeleBot(TOKEN)
app = Flask('')

# --- MA'LUMOTLARNI YUKLASH ---
def load_db(file):
    if os.path.exists(file):
        with open(file, 'r', encoding='utf-8') as f:
            try: return json.load(f)
            except: return {}
    return {}

def save_db(data, file):
    with open(file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

anime_db = load_db(DB_FILE)
users_db = load_db(USERS_FILE)

# --- MAJBURIY OBUNA NAZORATI ---
def is_subscribed(user_id):
    if int(user_id) == ADMIN_ID: return True
    try:
        status = bot.get_chat_member(CHANNEL_ID, user_id).status
        return status in ['member', 'administrator', 'creator']
    except: return False

def send_sub_msg(chat_id):
    markup = types.InlineKeyboardMarkup()
    markup.row(types.InlineKeyboardButton("1️⃣ Kanalga a'zo bo'lish ➕", url=CHANNEL_LINK))
    markup.row(types.InlineKeyboardButton("2️⃣ ✅ Tasdiqlash", callback_query_data="recheck"))
    bot.send_message(chat_id, "🛑 **DIQQAT!**\n\nBotdan foydalanish uchun kanalimizga obuna bo'lishingiz shart. Obuna bo'lib 'Tasdiqlash' tugmasini bosing.", reply_markup=markup, parse_mode="Markdown")

# --- ADMIN TO'LIQ INLINE PANEL ---
def admin_panel_markup():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("📊 Statistika", callback_query_data="admin_stats"),
        types.InlineKeyboardButton("📢 Xabar tarqatish", callback_query_data="admin_broadcast"),
        types.InlineKeyboardButton("➕ Yangi Anime", callback_query_data="admin_add"),
        types.InlineKeyboardButton("🎬 Qism qo'shish", callback_query_data="admin_add_part"),
        types.InlineKeyboardButton("🗑 O'chirish", callback_query_data="admin_del"),
        types.InlineKeyboardButton("🚀 Kanalga post", callback_query_data="admin_post")
    )
    return markup

# --- START ---
@bot.message_handler(commands=['start'])
def start_handler(message):
    uid = str(message.from_user.id)
    if uid not in users_db:
        users_db[uid] = {"name": message.from_user.first_name}
        save_db(users_db, USERS_FILE)

    if not is_subscribed(message.from_user.id):
        send_sub_msg(message.chat.id)
        return

    if int(uid) == ADMIN_ID:
        bot.send_message(message.chat.id, "🛠 **Admin boshqaruv paneli:**", reply_markup=admin_panel_markup(), parse_mode="Markdown")
    else:
        bot.send_message(message.chat.id, "✅ Xush kelibsiz! Anime kodini yuboring.")

# --- CALLBACK HANDLER ---
@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    uid = call.from_user.id
    chat_id = call.message.chat.id

    if call.data == "recheck":
        if is_subscribed(uid):
            bot.delete_message(chat_id, call.message.message_id)
            bot.send_message(chat_id, "🎉 Tasdiqlandi! Anime kodini yuboring.")
        else:
            bot.answer_callback_query(call.id, "❌ Hali a'zo bo'lmadingiz!", show_alert=True)

    if uid == ADMIN_ID:
        bot.answer_callback_query(call.id)
        if call.data == "admin_stats":
            bot.send_message(chat_id, f"📊 **Statistika:**\n\n👤 Foydalanuvchilar: {len(users_db)}\n🎬 Animelar: {len(anime_db)}", parse_mode="Markdown")
        
        elif call.data == "admin_broadcast":
            msg = bot.send_message(chat_id, "📢 Foydalanuvchilarga tarqatish uchun xabar yuboring:")
            bot.register_next_step_handler(msg, do_broadcast)
            
        elif call.data == "admin_add":
            msg = bot.send_message(chat_id, "➕ Yangi anime kodini kiriting:")
            bot.register_next_step_handler(msg, add_anime_code)

        elif call.data == "admin_add_part":
            msg = bot.send_message(chat_id, "🎬 Qaysi kodga qism qo'shmoqchisiz?")
            bot.register_next_step_handler(msg, get_code_for_part)

        elif call.data == "admin_del":
            msg = bot.send_message(chat_id, "🗑 O'chirmoqchi bo'lgan anime kodini kiriting:")
            bot.register_next_step_handler(msg, del_anime_code)

        elif call.data == "admin_post":
            msg = bot.send_message(chat_id, "🚀 Kanalga yuboriladigan postni yuboring:")
            bot.register_next_step_handler(msg, do_post_channel)

    # Foydalanuvchi qism tanlaganda
    if call.data.startswith("pv_"):
        _, code, idx = call.data.split("_")
        idx = int(idx)
        if code in anime_db:
            video_id = anime_db[code]['qismlar'][idx]
            bot.send_video(chat_id, video_id, caption=f"🎬 {anime_db[code]['nomi']}\n✅ {idx+1}-qism")
        bot.answer_callback_query(call.id)

# --- ADMIN FUNKSIYALARI ---
def do_broadcast(message):
    for uid in users_db.keys():
        try: bot.copy_message(uid, message.chat.id, message.message_id)
        except: continue
    bot.send_message(message.chat.id, "✅ Xabar hamma a'zolarga tarqatildi.")

def add_anime_code(message):
    code = message.text
    msg = bot.send_message(message.chat.id, f"Kod: `{code}`. Endi nomini yuboring:", parse_mode="Markdown")
    bot.register_next_step_handler(msg, lambda m: add_anime_name(m, code))

def add_anime_name(message, code):
    anime_db[code] = {"nomi": message.text, "qismlar": []}
    save_db(anime_db, DB_FILE)
    bot.send_message(message.chat.id, f"✅ Anime yaratildi: {message.text}")

def get_code_for_part(message):
    code = message.text
    if code in anime_db:
        msg = bot.send_message(message.chat.id, f"🎬 {anime_db[code]['nomi']}\nEndi videoni yuboring:")
        bot.register_next_step_handler(msg, lambda m: save_part(m, code))
    else: bot.send_message(message.chat.id, "❌ Kod topilmadi.")

def save_part(message, code):
    if message.content_type == 'video':
        anime_db[code]['qismlar'].append(message.video.file_id)
        save_db(anime_db, DB_FILE)
        bot.send_message(message.chat.id, f"✅ {len(anime_db[code]['qismlar'])}-qism saqlandi.")
    else: bot.send_message(message.chat.id, "❌ Faqat video yuboring!")

def del_anime_code(message):
    if message.text in anime_db:
        del anime_db[message.text]
        save_db(anime_db, DB_FILE)
        bot.send_message(message.chat.id, "🗑 O'chirildi.")
    else: bot.send_message(message.chat.id, "❌ Topilmadi.")

def do_post_channel(message):
    try:
        bot.copy_message(CHANNEL_ID, message.chat.id, message.message_id)
        bot.send_message(message.chat.id, "✅ Kanalga yuborildi.")
    except Exception as e: bot.send_message(message.chat.id, f"❌ Xatolik: {e}")

# --- ASOSIY QIDIRUV ---
@bot.message_handler(func=lambda m: True)
def main_search(message):
    if not is_subscribed(message.from_user.id):
        send_sub_msg(message.chat.id)
        return

    code = message.text
    if code in anime_db:
        anime = anime_db[code]
        parts = anime.get('qismlar', [])
        if not parts:
            bot.send_message(message.chat.id, f"🎬 **{anime['nomi']}**\n⚠️ Qismlar hali yuklanmagan.")
            return
        
        markup = types.InlineKeyboardMarkup(row_width=5)
        btns = [types.InlineKeyboardButton(f"{i+1}", callback_query_data=f"pv_{code}_{i}") for i in range(len(parts))]
        markup.add(*btns)
        bot.send_message(message.chat.id, f"🎬 **{anime['nomi']}**\n\nQismni tanlang:", reply_markup=markup, parse_mode="Markdown")
    elif message.from_user.id != ADMIN_ID:
        bot.send_message(message.chat.id, "❌ Bunday kodli anime topilmadi.")

# --- SERVER ---
@app.route('/')
def home(): return "OK"

if __name__ == "__main__":
    Thread(target=lambda: app.run(host='0.0.0.0', port=8080)).start()
    bot.infinity_polling(skip_pending=True)
