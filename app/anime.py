import os
import logging
import sqlite3
from flask import Flask
from threading import Thread
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters

# --- RENDER UCHUN WEB SERVER ---
# Render bot o'chib qolmasligi uchun portni eshitib turishi shart
web_app = Flask(__name__)

@web_app.route('/')
def home():
    return "Bot is running!"

def run_web():
    port = int(os.environ.get("PORT", 8080))
    web_app.run(host='0.0.0.0', port=port)

# --- BOT LOGIKASI ---
logging.basicConfig(level=logging.INFO)

TOKEN = "8635058894:AAHGygl5VARXfsNjvvbsRMFDQh1pbmGGFnM"
ADMIN_ID = 7253593181

# DB ulanishi
conn = sqlite3.connect("anime_baza.db", check_same_thread=False)
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS animelar (
    code TEXT PRIMARY KEY,
    title TEXT,
    photo TEXT,
    eps INTEGER
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS qismlar (
    code TEXT,
    ep_num INTEGER,
    link TEXT
)
""")
conn.commit()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Anime kod yuboring (masalan: 001)")

async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    text = "<b>Admin Panel</b>\n\n➕ Anime qo‘shish:\n/add kod|nomi|rasm|qism_soni\n\n🎬 Qism qo‘shish:\n/set kod|qism|link"
    await update.message.reply_text(text, parse_mode="HTML")

async def add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    try:
        # /add buyrug'idan keyingi matnni olish
        raw_data = update.message.text.split(" ", 1)
        if len(raw_data) < 2:
            await update.message.reply_text("❌ Format: /add kod|nomi|rasm|soni")
            return
            
        data = raw_data[1].split("|")
        if len(data) != 4:
            await update.message.reply_text("❌ Format xato!")
            return

        cur.execute("INSERT OR REPLACE INTO animelar VALUES (?, ?, ?, ?)", (data[0], data[1], data[2], int(data[3])))
        conn.commit()
        await update.message.reply_text("✅ Anime qo‘shildi!")
    except Exception as e:
        await update.message.reply_text(f"❌ Xato: {e}")

async def set_ep(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    try:
        raw_data = update.message.text.split(" ", 1)
        if len(raw_data) < 2:
            await update.message.reply_text("❌ Format: /set kod|qism|link")
            return

        data = raw_data[1].split("|")
        cur.execute("INSERT OR REPLACE INTO qismlar VALUES (?, ?, ?)", (data[0], int(data[1]), data[2]))
        conn.commit()
        await update.message.reply_text("✅ Qism qo‘shildi!")
    except Exception as e:
        await update.message.reply_text(f"❌ Xato: {e}")

async def search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        code = update.message.text.strip()
        if not code.isdigit():
            return

        cur.execute("SELECT * FROM animelar WHERE code=?", (code,))
        res = cur.fetchone()
        if not res:
            await update.message.reply_text("❌ Topilmadi")
            return

        buttons = []
        for i in range(1, res[3] + 1):
            buttons.append(InlineKeyboardButton(str(i), callback_data=f"{code}_{i}"))

        keyboard = [buttons[i:i+5] for i in range(0, len(buttons), 5)]

        await update.message.reply_photo(
            photo=res[2],
            caption=f"🎬 <b>{res[1]}</b>",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML"
        )
    except Exception as e:
        await update.message.reply_text(f"❌ Xato: {e}")

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    try:
        code, ep = query.data.split("_")
        cur.execute("SELECT link FROM qismlar WHERE code=? AND ep_num=?", (code, ep))
        res = cur.fetchone()

        if res:
            await query.message.reply_text(f"🎞 {ep}-qism:\n{res[0]}")
        else:
            await query.message.reply_text("⚠️ Hali yuklanmagan")
    except Exception as e:
        await query.message.reply_text(f"❌ Xato: {e}")

def main():
    # 1. Web serverni alohida oqimda ishga tushirish
    Thread(target=run_web, daemon=True).start()

    # 2. Botni ishga tushirish
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin))
    app.add_handler(CommandHandler("add", add))
    app.add_handler(CommandHandler("set", set_ep))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, search))
    app.add_handler(CallbackQueryHandler(button))

    print("Bot ishladi...")
    app.run_polling()

if __name__ == "__main__":
    main()
