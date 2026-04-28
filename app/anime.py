import logging
import os
import sqlite3
from threading import Thread
from flask import Flask
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes, ConversationType

# --- SOZLAMALAR ---
TOKEN = '8635058894:AAHGygl5VARXfsNjvvbsRMFDQh1pbmGGFnM'
ADMIN_ID = 7253593181
CHANNEL_ID = "@AnimeFonuzbaza"

# --- FLASK (Render Porti uchun) ---
server = Flask(__name__)
@server.route('/')
def index(): return "Bot is Online!"

def run_server():
    port = int(os.environ.get("PORT", 8080))
    server.run(host='0.0.0.0', port=port)

# --- BAZA ---
conn = sqlite3.connect('anime_data.db', check_same_thread=False)
cur = conn.cursor()
cur.execute('CREATE TABLE IF NOT EXISTS animelar (code TEXT PRIMARY KEY, title TEXT, photo TEXT, eps INTEGER)')
cur.execute('CREATE TABLE IF NOT EXISTS qismlar (code TEXT, ep_num INTEGER, link TEXT)')
conn.commit()

# --- LOGGING ---
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# --- BOT FUNKSIYALARI ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    # Agar start bilan kod kelsa (masalan /start 001)
    if context.args:
        await send_anime(update, context, context.args[0])
    else:
        await update.message.reply_text(f"👋 Salom! Anime kodini yuboring.\nAdmin bo'lsangiz: /admin")

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    await update.message.reply_text("<b>Admin panel!</b>\n\nMarhamat, anime qo'shish uchun kodlardan foydalaning.", parse_mode="HTML")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text.isdigit():
        await send_anime(update, context, text)
    else:
        await update.message.reply_text("🔢 Iltimos, faqat raqamli kod yuboring.")

async def send_anime(update: Update, context: ContextTypes.DEFAULT_TYPE, code: str):
    cur.execute("SELECT * FROM animelar WHERE code=?", (code,))
    res = cur.fetchone()
    if res:
        keyboard = []
        for i in range(1, res[3] + 1):
            keyboard.append(InlineKeyboardButton(str(i), callback_data=f"v_{code}_{i}"))
        
        # Tugmalarni 5 tadan qatorga tizish
        reply_markup = InlineKeyboardMarkup([keyboard[i:i + 5] for i in range(0, len(keyboard), 5)])
        await update.message.reply_photo(res[2], caption=f"🎬 <b>{res[1]}</b>\n🔢 Kod: <code>{res[0]}</code>", reply_markup=reply_markup, parse_mode="HTML")
    else:
        await update.message.reply_text("❌ Bunday kodli anime topilmadi.")

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data.split('_')
    
    code, ep = data[1], data[2]
    cur.execute("SELECT link FROM qismlar WHERE code=? AND ep_num=?", (code, ep))
    link = cur.fetchone()
    if link:
        await query.message.reply_text(f"🎞 <b>{ep}-qism:</b>\n\n{link[0]}", parse_mode="HTML")

# --- ASOSIY ---
def main():
    # Render portini ushlab turish uchun Flaskni alohida oqimda yoqamiz
    Thread(target=run_server).start()

    # PTB Application yaratish
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin_panel))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(button_click))

    print("Bot PTB kutubxonasida ishga tushdi...")
    app.run_polling()

if __name__ == '__main__':
    main()
