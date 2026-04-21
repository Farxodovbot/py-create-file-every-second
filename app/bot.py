from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters
)
import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

# 🔐 TOKENINGIZ
TOKEN = "8613487563:AAGvAzI8a-HMyV-XlkI6rH4ptuvCmY23hsI"
CHANNEL = "@ishchilarmarkazi_uz"

jobs = []

# --- 🌐 RENDER UCHUN PORT (HEALTH CHECK) QISMI ---
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(b"Bot is alive and running!")

def run_port_server():
    # Render avtomatik ravishda PORT o'zgaruvchisini beradi, bo'lmasa 10000 ni oladi
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
    print(f"Port server {port}-portda ishga tushdi...")
    server.serve_forever()

# --- 🤖 BOT FUNKSIYALARI ---
async def is_member(user_id, context):
    try:
        member = await context.bot.get_chat_member(CHANNEL, user_id)
        return member.status in ["member", "administrator", "creator"]
    except:
        return False

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not await is_member(user_id, context):
        keyboard = [
            [InlineKeyboardButton("📢 Kanalga kirish", url=f"https://t.me/{CHANNEL.replace('@','')}")],
            [InlineKeyboardButton("✅ Tekshirish", callback_data="check")]
        ]
        await update.message.reply_text("❗ Botdan foydalanish uchun kanalga a’zo bo‘ling:", reply_markup=InlineKeyboardMarkup(keyboard))
        return

    keyboard = [
        [InlineKeyboardButton("📋 Ishlar", callback_data="jobs")],
        [InlineKeyboardButton("📝 Ariza", callback_data="apply")]
    ]
    await update.message.reply_text("👷 Ishchilar Markaziga xush kelibsiz!", reply_markup=InlineKeyboardMarkup(keyboard))

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "check":
        if await is_member(query.from_user.id, context):
            await query.edit_message_text("✅ Tasdiqlandingiz! /start yozing.")
        else:
            await query.edit_message_text("❌ Siz hali kanalga a’zo emassiz.")

    elif query.data == "jobs":
        if not jobs:
            await query.edit_message_text("😔 Hozircha ish yo‘q")
        else:
            text = "📋 Ishlar:\n\n" + "\n".join([f"{i+1}. {j}" for i, j in enumerate(jobs)])
            await query.edit_message_text(text)

async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text.startswith("ish:"):
        job = update.message.text.replace("ish:", "").strip()
        jobs.append(job)
        await update.message.reply_text("✅ Ish qo‘shildi!")

# --- 🚀 ASOSIY ISHGA TUSHIRISH ---
def main():
    # 1. Render portni topishi uchun soxta serverni alohida oqimda yoqamiz
    threading.Thread(target=run_port_server, daemon=True).start()

    # 2. Telegram botni ishga tushiramiz
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))

    print("--- BOT VA PORT SERVER ISHLAMOQDA ---")
    app.run_polling()

if __name__ == "__main__":
    main()
