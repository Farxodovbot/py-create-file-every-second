
import telebot
from telebot import types

# --- SOZLAMALAR ---
TOKEN = ""8635058894:AAHnof_upa_bWpcL3b6SNVt7wNO-t74zBxg
ADMIN_ID = 7253593181
CHANNEL_ID = "@AnimeFonuzbaza" # Majburiy obuna va post yuborish uchun
bot = telebot.TeleBot(TOKEN)
# Vaqtincha ma'lumot saqlash
user_data = {}

# --- MAJBURIY OBUNA TEKSHIRISH ---
def check_sub(user_id):
    try:
        member = bot.get_chat_member(CHANNEL_ID, user_id)
        if member.status in ['member', 'administrator', 'creator']:
            return True
        return False
    except:
        return False

# --- START BUYRUG'I ---
@bot.message_handler(commands=['start'])
def start_cmd(message):
    if not check_sub(message.from_user.id):
        markup = types.InlineKeyboardMarkup()
        btn_sub = types.InlineKeyboardButton("Obuna bo'lish ➕", url=f"https://t.me/{CHANNEL_ID[1:]}")
        btn_done = types.InlineKeyboardButton("Tekshirish ✅", callback_data="check_sub")
        markup.add(btn_sub)
        markup.add(btn_done)
        bot.send_message(message.chat.id, f"⚠️ Kechirasiz, botdan foydalanish uchun kanalimizga obuna bo'lishingiz kerak!", reply_markup=markup)
        return
    
    bot.send_message(message.chat.id, "👋 Xush kelibsiz! Anime kodini yuboring.")

# --- ADMIN PANEL ---
@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if message.from_user.id == ADMIN_ID:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add("Post yaratish 📝", "Anime qo'shish ➕")
        bot.send_message(message.chat.id, "🎛 Admin panelga xush kelibsiz!", reply_markup=markup)

# --- ANIME QO'SHISH (ID OLISH) ---
@bot.message_handler(func=lambda message: message.text == "Anime qo'shish ➕")
def add_anime(message):
    if message.from_user.id == ADMIN_ID:
        bot.send_message(message.chat.id, "📹 Menga videoni yuboring (file_id olish uchun):")

@bot.message_handler(content_types=['video'])
def save_video(message):
    if message.from_user.id == ADMIN_ID:
        v_id = message.video.file_id
        bot.send_message(message.chat.id, f"✅ Video ID olindi:\n\n`{v_id}`", parse_mode="Markdown")

# --- KANALGA POST YARATISH ---
@bot.message_handler(func=lambda message: message.text == "Post yaratish 📝")
def start_post(message):
    if message.from_user.id == ADMIN_ID:
        bot.send_message(message.chat.id, "1️⃣ Anime uchun rasm yuboring:")
        bot.register_next_step_handler(message, get_photo)

def get_photo(message):
    if message.content_type != 'photo':
        bot.send_message(message.chat.id, "❌ Xato! Rasm yuboring.")
        return
    user_data['photo'] = message.photo[-1].file_id
    bot.send_message(message.chat.id, "2️⃣ Anime nomini yozing:")
    bot.register_next_step_handler(message, get_name)

def get_name(message):
    user_data['name'] = message.text
    bot.send_message(message.chat.id, "3️⃣ Janrini yozing (#Jangovar #Horror):")
    bot.register_next_step_handler(message, get_genre)

def get_genre(message):
    user_data['genre'] = message.text
    bot.send_message(message.chat.id, "4️⃣ Jami qismlar soni (Kino bo'lsa 'Kino' deb yozing):")
    bot.register_next_step_handler(message, get_parts)

def get_parts(message):
    user_data['parts'] = message.text
    bot.send_message(message.chat.id, "5️⃣ Anime kodini yozing:")
    bot.register_next_step_handler(message, get_code)

def get_code(message):
    code = message.text
    b_name = bot.get_me().username
    
    caption = (
        f"📺 **{user_data['name']}**\n\n"
        f"📽 Qismlarni tanlang:\n"
        f"📀 Jami: {user_data['parts']}\n"
        f"🌟 Reyting: 0.0/10\n"
        f"🎭 Janr: {user_data['genre']}\n\n"
        f"🔢 Kod: {code}"
    )
    
    markup = types.InlineKeyboardMarkup(row_width=3)
    if user_data['parts'].isdigit():
        total = int(user_data['parts'])
        btns = [types.InlineKeyboardButton(f"{i}-qism", url=f"https://t.me/{b_name}?start={code}_{i}") for i in range(1, total+1)]
        markup.add(*btns)
    else:
        markup.add(types.InlineKeyboardButton("🎬 Tomosha qilish", url=f"https://t.me/{b_name}?start={code}"))
    
    markup.row(types.InlineKeyboardButton("🏠 Bosh menyu", url=f"https://t.me/{b_name}"))
    
    try:
        bot.send_photo(CHANNEL_ID, user_data['photo'], caption=caption, reply_markup=markup, parse_mode="Markdown")
        bot.send_message(message.chat.id, "✅ Post kanalga yuborildi!")
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Xato: {e}")

# --- CALLBACK (OBUNA TEKSHIRISH) ---
@bot.callback_query_handler(func=lambda call: call.data == "check_sub")
def check_callback(call):
    if check_sub(call.from_user.id):
        bot.edit_message_text("✅ Rahmat! Endi botdan foydalanishingiz mumkin. /start bosing.", call.message.chat.id, call.message.message_id)
    else:
        bot.answer_callback_query(call.id, "❌ Siz hali ham kanalga a'zo emassiz!", show_alert=True)

# --- BOTNI RUN QILISH ---
bot.infinity_polling()
