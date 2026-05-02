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

# --- MA'LUMOTLARNI YUKLASH VA SAQLASH ---
def load_db(file):
    if os.path.exists(file):
        with open(file, 'r', encoding='utf-8') as f:
            try:
                return json.load(f)
            except:
                return {}
    return {}

def save_db(data, file):
    with open(file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

anime_db = load_db(DB_FILE)
users_db = load_db(USERS_FILE)

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
    # Tugmalarni alohida qatorda chiqarish
    btn1 = types.InlineKeyboardButton("1️⃣ Kanalga a'zo bo'lish ➕", url=CHANNEL_LINK)
    btn2 = types.InlineKeyboardButton("2️⃣ ✅ Tasdiqlash", callback_query_data="recheck")
    markup.row(btn1) # 1-qator
    markup.row(btn2) # 2-qator
    
    bot.send_message(
        chat_id, 
        "❌ **Kanalga a'zo bo'lmagansiz!**\n\nBotdan foydalanish uchun avval kanalga obuna bo'ling va tasdiqlash tugmasini bosing.", 
        reply_markup=markup, 
        parse_mode="Markdown"
    )

# --- ADMIN PANEL KLAVIATURASI ---
def admin_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("📊 Statistika", "📢 Xabar yuborish")
    markup.add("➕ Anime qo'shish", "🗑 Animeni o'chirish")
    return markup

# --- START BUYRUG'I ---
@bot.message_handler(commands=['start'])
def start_handler(message):
    uid = str(message.from_user.id)
    if uid not in users_db:
        users_db[uid] = {"name": message.from_user.first_name}
        save_db(users_db, USERS_FILE)
    
    if not is_subscribed(message.from_user.id):
        send_sub_msg(message.chat.id)
        return

    if message.from_user.id == ADMIN_ID:
        bot.send_message(message.chat.id, "🛠 **Admin panelga xush kelibsiz!**", reply_markup=admin_keyboard(), parse_mode="Markdown")
    else:
        bot.send_message(message.chat.id, "👋 Salom! Anime kodini yuboring.", reply_markup=types.ReplyKeyboardRemove())

# --- TASDIQLASH (CALLBACK) ---
@bot.callback_query_handler(func=lambda call: call.data == "recheck")
def recheck_handler(call):
    if is_subscribed(call.from_user.id):
        bot.delete_message(call.message.chat.id, call.message.message_id)
        bot.send_message(call.message.chat.id, "✅ Rahmat! Obuna tasdiqlandi. Endi anime kodini yuborishingiz mumkin.")
    else:
        bot.answer_callback_query(call.id, "⚠️ Siz hali ham kanalga a'zo emassiz!", show_alert=True)

# --- ADMIN: STATISTIKA ---
@bot.message_handler(func=lambda m: m.text == "📊 Statistika" and m.from_user.id == ADMIN_ID)
def stats(message):
    total_u = len(users_db)
    total_a = len(anime_db)
    bot.send_message(message.chat.id, f"📊 **Bot holati:**\n\n👤 Foydalanuvchilar: `{total_u}` ta\n🎬 Animelar soni: `{total_a}` ta", parse_mode="Markdown")

# --- ADMIN: XABAR YUBORISH (RASSILKA) ---
@bot.message_handler(func=lambda m: m.text == "📢 Xabar yuborish" and m.from_user.id == ADMIN_ID)
def start_broadcast(message):
    msg = bot.send_message(message.chat.id, "📢 Reklama xabarini yuboring (Rasm, Video yoki Matn):")
    bot.register_next_step_handler(msg, send_broadcast)

def send_broadcast(message):
    sent = 0
    fail = 0
    bot.send_message(message.chat.id, "🚀 Tarqatish boshlandi...")
    for user_id in users_db.keys():
        try:
            bot.copy_message(user_id, message.chat.id, message.message_id)
            sent += 1
        except:
            fail += 1
    bot.send_message(message.chat.id, f"✅ Tugatildi!\n✅ Yetkazildi: {sent}\n❌ Bloklaganlar: {fail}")

# --- ADMIN: ANIME QO'SHISH ---
@bot.message_handler(func=lambda m: m.text == "➕ Anime qo'shish" and m.from_user.id == ADMIN_ID)
def add_anime_start(message):
    msg = bot.send_message(message.chat.id, "Anime kodini kiriting:")
    bot.register_next_step_handler(msg, add_anime_code)

def add_anime_code(message):
    code = message.text
    msg = bot.send_message(message.chat.id, f"Kod: `{code}`\nEndi anime nomini kiriting:", parse_mode="Markdown")
    bot.register_next_step_handler(msg, lambda m: add_anime_final(m, code))

def add_anime_final(message, code):
    name = message.text
    anime_db[code] = {"nomi": name}
    save_db(anime_db, DB_FILE)
    bot.send_message(message.chat.id, f"✅ Anime qo'shildi!\n🆔 Kod: `{code}`\n🎬 Nomi: {name}", parse_mode="Markdown")

# --- ASOSIY QIDIRUV VA NAZORAT ---
@bot.message_handler(func=lambda m: True)
def handle_all(message):
    # Har bir xabarda obunani tekshirish
    if not is_subscribed(message.from_user.id):
        send_sub_msg(message.chat.id)
        return

    code = message.text
    if code in anime_db:
        info = anime_db[code]
        bot.send_message(message.chat.id, f"🎬 **Nomi:** {info['nomi']}\n\nKod muvaffaqiyatli topildi!", parse_mode="Markdown")
    else:
        # Agar bu admin buyruqlari bo'lmasa
        if message.text not in ["📊 Statistika", "📢 Xabar yuborish", "➕ Anime qo'shish", "🗑 Animeni o'chirish"]:
            bot.send_message(message.chat.id, "❌ Afsuski, bunday kodli anime topilmadi.")

# --- SERVER KEEP-ALIVE ---
@app.route('/')
def index(): return "Running..."

def run_server():
    app.run(host='0.0.0.0', port=8080)

if __name__ == "__main__":
    Thread(target=run_server).start()
    print("Bot muvaffaqiyatli ishga tushdi!")
    bot.infinity_polling(skip_pending=True)
