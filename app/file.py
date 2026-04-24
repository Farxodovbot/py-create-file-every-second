import os
import sqlite3
import random
from flask import Flask, request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Bot
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters
)

# ================= CONFIG =================
BOT_TOKEN = 8735085300:AAG4of7ojBjVbCf0UzIowPu0YVaUmrRNbWU
ADMIN_ID = 7253593181

PORT = int(os.environ.get("PORT", 5000))

bot = Bot(token=BOT_TOKEN)

# ================= FLASK =================
app = Flask(__name__)

# ================= DATABASE =================
conn = sqlite3.connect("anime.db", check_same_thread=False)
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS anime (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    description TEXT,
    link TEXT,
    code INTEGER
)
""")
conn.commit()

def add_anime(name, desc, link):
    code = random.randint(100000, 999999999)

    cur.execute(
        "INSERT INTO anime (name, description, link, code) VALUES (?, ?, ?, ?)",
        (name, desc, link, code)
    )
    conn.commit()

    return code

def get_all():
    cur.execute("SELECT * FROM anime")
    return cur.fetchall()

def find_by_code(code):
    cur.execute("SELECT * FROM anime WHERE code=?", (code,))
    return cur.fetchall()

# ================= STATE =================
state = {}

# ================= INLINE MENU =================
def menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📺 Anime ro‘yxat", callback_data="list")],
        [InlineKeyboardButton("🔑 Kod kirish", callback_data="code")],
        [InlineKeyboardButton("🛠 Admin", callback_data="admin")],
        [InlineKeyboardButton("ℹ️ Info", callback_data="info")]
    ])

# ================= START =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 ANIME BOT PRO\n\nInline menu ishlat 👇",
        reply_markup=menu()
    )

# ================= CALLBACK =================
async def callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    data = q.data

    # 📺 LIST
    if data == "list":
        anime = get_all()

        if not anime:
            return await q.message.reply_text("❌ Anime yo‘q")

        for a in anime:
            await q.message.reply_text(
                f"🎬 {a[1]}\n📄 {a[2]}\n🔗 {a[3]}\n🔢 CODE: {a[4]}"
            )

    # 🔑 CODE INPUT
    elif data == "code":
        state[q.from_user.id] = {"step": "code"}
        await q.message.reply_text("🔢 Kodni kiriting:")

    # 🛠 ADMIN
    elif data == "admin":
        if q.from_user.id != ADMIN_ID:
            return await q.message.reply_text("❌ Admin emassiz")

        state[q.from_user.id] = {"step": "name"}
        await q.message.reply_text("🎬 Anime nomi:")

    # ℹ️ INFO
    elif data == "info":
        await q.message.reply_text("🤖 Anime bot + code system + admin panel")

# ================= TEXT HANDLER =================
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    text = update.message.text

    if uid not in state:
        return

    step = state[uid]

    # ================= USER CODE =================
    if step["step"] == "code":
        try:
            code = int(text)
        except:
            return await update.message.reply_text("❌ Faqat raqam")

        res = find_by_code(code)

        if not res:
            return await update.message.reply_text("❌ Kod topilmadi")

        for a in res:
            await update.message.reply_text(
                f"""
🔥 ANIME

🎬 {a[1]}
📄 {a[2]}
🔗 {a[3]}
🔢 {a[4]}
"""
            )

        del state[uid]

    # ================= ADMIN FLOW =================
    elif step["step"] == "name":
        state[uid]["name"] = text
        state[uid]["step"] = "desc"
        await update.message.reply_text("📄 Description:")

    elif step["step"] == "desc":
        state[uid]["desc"] = text
        state[uid]["step"] = "link"
        await update.message.reply_text("🔗 Link:")

    elif step["step"] == "link":
        data = state[uid]

        code = add_anime(data["name"], data["desc"], text)

        del state[uid]

        await update.message.reply_text(
            f"✅ Anime qo‘shildi!\n🔢 CODE: {code}"
        )

# ================= TELEGRAM APP =================
application = Application.builder().token(BOT_TOKEN).build()

application.add_handler(CommandHandler("start", start))
application.add_handler(CallbackQueryHandler(callback))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

# ================= WEBHOOK =================
@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    application.process_update(update)
    return "ok"

# ================= RUN SERVER =================
if __name__ == "__main__":
    print(f"🤖 BOT RUNNING ON PORT {PORT}")
    app.run(host="0.0.0.0", port=PORT)