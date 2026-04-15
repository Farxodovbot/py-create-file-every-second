import json
import os
import time
import requests
import threading
from flask import Flask
from threading import Thread
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters
)

# ================= WEB SERVER (RENDER UCHUN) =================
server = Flask('')

@server.route('/')
def home():
    return "Bot faol! Render va UptimeRobot ulandi."

def run():
    # Render portni o'zi tayinlaydi, biz uni qabul qilamiz
    port = int(os.environ.get("PORT", 8080))
    server.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.start()

# ================= CONFIG (YANGI TOKEN) =================
BOT_TOKEN = "8733154492:AAEVRt0EF8FDGj3TnnfL6-NpmLLPxUdI4V8" 
ADMIN_ID = 7253593181
DB_FILE = "db.json"

# ================= PACKAGES =================
PACKAGES = {
    "60": 50,
    "120": 90,
    "360": 180,
    "720": 300
}

# ================= DATABASE FUNKSIYALARI =================
def load():
    if not os.path.exists(DB_FILE):
        with open(DB_FILE, "w") as f: json.dump({}, f)
        return {}
    try:
        with open(DB_FILE, "r") as f: return json.load(f)
    except: return {}

def save(data):
    with open(DB_FILE, "w") as f: json.dump(data, f, indent=4)

db = load()

def get_user(uid):
    uid = str(uid)
    if uid not in db:
        db[uid] = {"balance": 0, "step": None, "selected_uc": None, "last_bonus": 0}
        save(db)
    return db[uid]

# ================= COMMAND HANDLERS =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🤖 UC SHOP BOTGA XUSH KELIBSIZ!\n\n💰 /balance - Balansni tekshirish\n🛒 /shop - UC sotib olish\n🎁 /bonus - Haftalik bonus")

async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if uid == ADMIN_ID:
        await update.message.reply_text("💰 Balans: Cheksiz (Admin)")
        return
    u = get_user(uid)
    await update.message.reply_text(f"💰 Sizning balansingiz: {u['balance']} so'm")

async def bonus(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if uid == ADMIN_ID: return
    u = get_user(uid)
    now = time.time()
    wait = 7 * 24 * 60 * 60 # 7 kun
    if now - u["last_bonus"] < wait:
        left = int(wait - (now - u["last_bonus"]))
        await update.message.reply_text(f"⏳ Bonus olish uchun yana {left//86400} kun kuting.")
        return
    u["balance"] += 10
    u["last_bonus"] = now
    save(db)
    await update.message.reply_text(f"🎁 Tabriklaymiz! +10 so'm bonus berildi.\n💰 Balans: {u['balance']}")

async def shop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton(f"{uc} UC - {price} so'm", callback_data=uc)] for uc, price in PACKAGES.items()]
    await update.message.reply_text("🛒 Sotib olmoqchi bo'lgan paketni tanlang:", reply_markup=InlineKeyboardMarkup(keyboard))

async def select(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id
    u = get_user(uid)
    uc = q.data
    price = PACKAGES.get(uc)
    
    if uid != ADMIN_ID and u["balance"] < price:
        await q.message.reply_text(f"❌ Xatolik! Balansingiz yetarli emas.\nKerak: {price} so'm")
        return
    
    u["selected_uc"] = uc
    u["step"] = "wait_id"
    save(db)
    await q.message.reply_text(f"✅ {uc} UC tanlandi.\n🆔 Iltimos, Game ID raqamingizni yuboring:")

async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text: return
    uid = update.effective_user.id
    u = get_user(uid)
    
    if u["step"] == "wait_id":
        game_id = update.message.text
        uc = u["selected_uc"]
        price = PACKAGES.get(uc, 0)
        
        if uid != ADMIN_ID: u["balance"] -= price
        u["step"] = None
        u["selected_uc"] = None
        save(db)
        
        # Adminga xabar yuborish
        await context.bot.send_message(
            chat_id=ADMIN_ID, 
            text=f"🆕 YANGI BUYURTMA!\n👤 User ID: {uid}\n📦 Paket: {uc} UC\n🎮 Game ID: {game_id}"
        )
        await update.message.reply_text("✅ Buyurtmangiz qabul qilindi! Tez orada UC yuboriladi.")

async def addbal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    try:
        target_id, amount = context.args[0], int(context.args[1])
        u = get_user(target_id)
        u["balance"] += amount
        save(db)
        await update.message.reply_text(f"✅ Foydalanuvchi {target_id} balansiga {amount} so'm qo'shildi.")
        await context.bot.send_message(chat_id=int(target_id), text=f"💰 Balansingiz {amount} so'mga to'ldirildi!")
    except:
        await update.message.reply_text("Xato! Foydalanish: /addbal [ID] [miqdor]")

# ================= ASOSIY QISM =================
if __name__ == '__main__':
    # 1. Flask serverni yoqish (UptimeRobot uchun)
    keep_alive()
    print("Web-server ishga tushdi...")
    
    # 2. Telegram Botni yoqish
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    
    # Handlerlarni ro'yxatga olish
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("balance", balance))
    app.add_handler(CommandHandler("shop", shop))
    app.add_handler(CommandHandler("bonus", bonus))
    app.add_handler(CommandHandler("addbal", addbal))
    app.add_handler(CallbackQueryHandler(select))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))
    
    print("Bot pollingni boshladi...")
    app.run_polling()
