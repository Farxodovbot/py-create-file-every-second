import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from flask import Flask

TOKEN = 8702330862:AAGOVFONokhO8pWGgvUlxLqhquTa2BcM4uQ
ADMIN_ID = 7253593181
CHANNEL = "@hororkinolar"
BOT_USERNAME = "YourBotUsername"

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

kino_baza = {}
qismlar = {}

# ================== MAJBURIY OBUNA ==================

def check_sub(user_id):
    try:
        member = bot.get_chat_member(CHANNEL, user_id)
        return member.status in ["member", "administrator", "creator"]
    except:
        return False

def sub_keyboard():
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("📢 Kanalga o'tish", url="https://t.me/hororkinolar"))
    kb.add(InlineKeyboardButton("✅ Tekshirish", callback_data="check_sub"))
    return kb

# ================== START ==================

@bot.message_handler(commands=['start'])
def start(msg):
    if not check_sub(msg.from_user.id):
        bot.send_message(msg.chat.id, "❌ Kanalga obuna bo‘ling!", reply_markup=sub_keyboard())
        return

    args = msg.text.split()

    if len(args) > 1:
        code = args[1]
        kino = kino_baza.get(code)

        if kino:
            kb = InlineKeyboardMarkup()
            kb.add(InlineKeyboardButton("📺 Qismlar", callback_data=f"parts_{code}"))

            bot.send_photo(
                msg.chat.id,
                kino["photo"],
                f"🎬 {kino['name']}\n\n📝 {kino['desc']}",
                reply_markup=kb
            )
            return

    bot.send_message(msg.chat.id, "🎬 Kod yuboring")

# ================== ADMIN KINO QO‘SHISH ==================

user_step = {}

@bot.message_handler(commands=['kino_qoshish'])
def kino_add(msg):
    if msg.from_user.id == ADMIN_ID:
        user_step[msg.from_user.id] = {"step": "name"}
        bot.send_message(msg.chat.id, "🎬 Kino nomi:")
    else:
        bot.send_message(msg.chat.id, "❌ Ruxsat yo‘q")

# ================== PROCESS ==================

@bot.message_handler(content_types=['text', 'photo'])
def process(msg):
    user_id = msg.from_user.id

    if not check_sub(user_id):
        bot.send_message(msg.chat.id, "❌ Obuna bo‘ling!", reply_markup=sub_keyboard())
        return

    step = user_step.get(user_id)

    # NOM
    if step and step["step"] == "name":
        step["name"] = msg.text
        step["step"] = "desc"
        bot.send_message(msg.chat.id, "📝 Tavsif:")

    # TAVSIF
    elif step and step["step"] == "desc":
        step["desc"] = msg.text
        step["step"] = "code"
        bot.send_message(msg.chat.id, "🔑 Kod:")

    # KOD
    elif step and step["step"] == "code":
        step["code"] = msg.text
        step["step"] = "photo"
        bot.send_message(msg.chat.id, "📷 Rasm yubor:")

    # RASM
    elif step and step["step"] == "photo" and msg.content_type == "photo":
        step["photo"] = msg.photo[-1].file_id

        kino_baza[step["code"]] = step

        # 🔘 KANAL POST
        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton(
            "🎬 Tomosha qilish",
            url=f"https://t.me/{BOT_USERNAME}?start={step['code']}"
        ))

        bot.send_photo(
            CHANNEL,
            step["photo"],
            f"🎬 <b>{step['name']}</b>\n\n📝 {step['desc']}\n\n🔑 Kod: <code>{step['code']}</code>",
            reply_markup=kb
        )

        bot.send_message(msg.chat.id, "✅ Joylandi!")
        user_step[user_id] = None

    # KOD QIDIRISH
    elif msg.content_type == "text":
        kino = kino_baza.get(msg.text)

        if kino:
            kb = InlineKeyboardMarkup()
            kb.add(InlineKeyboardButton("📺 Qismlar", callback_data=f"parts_{msg.text}"))

            bot.send_photo(
                msg.chat.id,
                kino["photo"],
                f"🎬 {kino['name']}\n\n📝 {kino['desc']}",
                reply_markup=kb
            )

# ================== QISMLAR ==================

@bot.callback_query_handler(func=lambda call: call.data.startswith("parts_"))
def parts(call):
    code = call.data.split("_")[1]
    parts = qismlar.get(code, [])

    if not parts:
        bot.answer_callback_query(call.id, "Qismlar yo‘q")
        return

    kb = InlineKeyboardMarkup()
    for i, link in enumerate(parts, 1):
        kb.add(InlineKeyboardButton(f"🎬 {i}-qism", url=link))

    bot.send_message(call.message.chat.id, "📺 Qismlar:", reply_markup=kb)

# ================== ADMIN QISM QO‘SHISH ==================

@bot.message_handler(commands=['qism_qoshish'])
def qism(msg):
    if msg.from_user.id == ADMIN_ID:
        user_step[msg.from_user.id] = {"step": "qcode"}
        bot.send_message(msg.chat.id, "🔑 Kino kodi:")

@bot.message_handler(func=lambda m: True)
def qism_process(msg):
    step = user_step.get(msg.from_user.id)

    if step and step.get("step") == "qcode":
        step["code"] = msg.text
        step["step"] = "qlink"
        bot.send_message(msg.chat.id, "🔗 Link:")

    elif step and step.get("step") == "qlink":
        code = step["code"]

        if code not in qismlar:
            qismlar[code] = []

        qismlar[code].append(msg.text)

        bot.send_message(msg.chat.id, "✅ Qism qo‘shildi")
        user_step[msg.from_user.id] = None

# ================== OBUNA TEKSHIRISH ==================

@bot.callback_query_handler(func=lambda call: call.data == "check_sub")
def check(call):
    if check_sub(call.from_user.id):
        bot.send_message(call.message.chat.id, "✅ Obuna tasdiqlandi!")
    else:
        bot.answer_callback_query(call.id, "❌ Obuna yo‘q", show_alert=True)

# ================== FLASK (GUNICORN UCHUN) ==================

@app.route('/')
def home():
    return "Bot ishlayapti"

# ================== RUN ==================

def run():
    bot.polling()

if __name__ == "__main__":
    from threading import Thread

    Thread(target=run).start()
    app.run(host="0.0.0.0", port=5000)