import telebot
from telebot import types

# --- SOZLAMALAR ---
# Yangi tokenni shu yerga joyladim
TOKEN = "8635058894:AAHnof_upa_bWpcL3b6SNVt7wNO-t74zBxg" 
ADMIN_ID = 7253593181
CHANNEL_ID = "@AnimeFonuzbaza"
bot = telebot.TeleBot(TOKEN)

# Bazani vaqtincha saqlash
anime_database = {} 

# --- MAJBURIY OBUNA ---
def check_sub(user_id):
    try:
        status = bot.get_chat_member(CHANNEL_ID, user_id).status
        return status in ['member', 'administrator', 'creator']
    except:
        return False

# --- START ---
@bot.message_handler(commands=['start'])
def start(message):
    if not check_sub(message.from_user.id):
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("Obuna bo'lish ➕", url=f"https://t.me/{CHANNEL_ID[1:]}"))
        markup.add(types.InlineKeyboardButton("Tekshirish ✅", callback_data="check"))
        bot.send_message(message.chat.id, "❌ Botdan foydalanish uchun kanalga a'zo bo'ling!", reply_markup=markup)
        return

    # Tugma bosilganda kod kelsa
    text = message.text.split()
    if len(text) > 1:
        code = text[1]
        if code in anime_database:
            bot.send_video(message.chat.id, anime_database[code], caption=f"🍿 Mana siz so'ragan anime! (Kod: {code})")
        else:
            bot.send_message(message.chat.id, "😔 Bu kod bo'yicha anime topilmadi.")
    else:
        bot.send_message(message.chat.id, "👋 Salom! Anime kodini yuboring yoki kanaldagi tugmani bosing.")

# --- ADMIN PANEL ---
@bot.message_handler(commands=['admin'])
def admin(message):
    if message.from_user.id == ADMIN_ID:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add("Anime qo'shish ➕", "Post yaratish 📝")
        bot.send_message(message.chat.id, "Xush kelibsiz, Admin!", reply_markup=markup)

# --- 1. ANIME QO'SHISH (ADMIN O'ZI KOD BERADI) ---
@bot.message_handler(func=lambda m: m.text == "Anime qo'shish ➕")
def add_anime_start(message):
    if message.from_user.id == ADMIN_ID:
        bot.send_message(message.chat.id, "📹 Anime videosini yoki faylini yuboring:")
        bot.register_next_step_handler(message, get_anime_file)

def get_anime_file(message):
    if message.content_type not in ['video', 'document']:
        bot.send_message(message.chat.id, "❌ Video yoki fayl yuboring!")
        return
    
    file_id = message.video.file_id if message.content_type == 'video' else message.document.file_id
    bot.send_message(message.chat.id, "🔢 Ushbu anime uchun **maxsus kod** bering (masalan: 77):")
    bot.register_next_step_handler(message, save_anime, file_id)

def save_anime(message, file_id):
    custom_code = message.text
    anime_database[custom_code] = file_id
    bot.send_message(message.chat.id, f"✅ Saqlandi! Kod: {custom_code}")

# --- 2. POST YARATISH ---
@bot.message_handler(func=lambda m: m.text == "Post yaratish 📝")
def create_post_start(message):
    if message.from_user.id == ADMIN_ID:
        bot.send_message(message.chat.id, "🖼 Rasm yuboring (tagiga barcha janr, qism ma'lumotlarini yozib):")
        bot.register_next_step_handler(message, process_post)

def process_post(message):
    if message.content_type != 'photo':
        bot.send_message(message.chat.id, "⚠️ Rasm va matnni birga yuboring!")
        return
    
    photo_id = message.photo[-1].file_id
    caption = message.caption
    bot.send_message(message.chat.id, "🔢 Ushbu post qaysi kodni ochsin? (Maxsus kodni yozing):")
    bot.register_next_step_handler(message, send_to_channel, photo_id, caption)

def send_to_channel(message, photo_id, caption):
    code = message.text
    b_name = bot.get_me().username
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🎬 Tomosha qilish", url=f"https://t.me/{b_name}?start={code}"))
    
    bot.send_photo(CHANNEL_ID, photo_id, caption=caption, reply_markup=markup, parse_mode="Markdown")
    bot.send_message(message.chat.id, "✅ Post kanalga yuborildi!")

# --- CALLBACK ---
@bot.callback_query_handler(func=lambda call: call.data == "check")
def check_call(call):
    if check_sub(call.from_user.id):
        bot.delete_message(call.message.chat.id, call.message.message_id)
        bot.send_message(call.message.chat.id, "✅ Rahmat! /start bosing.")
    else:
        bot.answer_callback_query(call.id, "❌ Obuna bo'lmadingiz!", show_alert=True)

bot.infinity_polling()
