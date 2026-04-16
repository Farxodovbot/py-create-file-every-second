import json
import os
import time
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
# Bu qism Render botni o'chirib qo'ymasligi uchun kerak
flask_app = Flask('')

@flask_app.route('/')
def home():
    return "Bot ishlamoqda!"

def run_flask():
    flask_app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run_flask)
    t.start()

# ================= CONFIG =================
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

# ================= DB =================
def load():
    if not os.path.exists(DB_FILE):
        return {}
    try:
        with open(DB_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=4)

db = load()

def get_user(uid):
    uid = str(uid)
    if uid not in db:
        db[uid] = {
            "balance": 0,
            "step": None,
            "selected_uc": None,
            "last_bonus": 0
        }
        save(db)
    return db[uid]

# ================= HANDLERS =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 UC SHOP BOTga xush kelibsiz!\n\n"
        "💰 /balance - Balansni tekshirish\n"
        "🛒 /shop - UC sotib olish\n"
        "🎁 /bonus - Haftalik bonus"
    )

async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if uid == ADMIN_ID:
        await update.message.reply_text("💰 Balans: ∞ (Admin)")
        return
    u = get_user(uid)
    await update.message.reply_text(f"💰 Balans: {u['balance']} so'm")

async def bonus(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if uid == ADMIN_ID:
        await update.message.reply_text("👮 Admin bonus ishlatmaydi")
        return
    u = get_user(uid)
    now = time.time()
    wait = 7 * 24 * 60 * 60
    if now - u["last_bonus"] < wait:
        left = int(wait - (now - u["last_bonus"]))
        await update.message.reply_text(f"⏳ Bonus uchun hali {left//86400} kun bor.")
        return
    u["balance"] += 10
    u["last_bonus"] = now
    save(db)
    await update.message.reply_text(f"🎁 +10 bonus berildi!\n💰 Balans: {u['balance']}")

async def shop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton(f"{uc} UC - {price} so'm", callback_data=uc)] for uc, price in PACKAGES.items()]
    await update.message.reply_text("🛒 Paket tanlang:", reply_markup=InlineKeyboardMarkup(keyboard))

async def select(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id
    u = get_user(uid)
    uc = q.data
    price = PACKAGES.get(uc)
    if uid != ADMIN_ID and u["balance"] < price:
        await q.message.reply_text("❌ Balans yetarli emas!")
        return
    u["selected_uc"] = uc
    u["step"] = "wait_id"
    save(db)
    await q.message.reply_text(f"✅ {uc} UC tanlandi.\n🆔 Game ID yuboring:")

async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text: return
    uid = update.message.from_user.id
    u = get_user(uid)
    if u["step"] == "wait_id":
        game_id = update.message.text
        uc = u["selected_uc"]
        price = PACKAGES.get(uc, 0)
        if uid != ADMIN_ID:
            u["balance"] -= price
        u["step"] = None
        save(db)
        await context.bot.send_message(chat_id=ADMIN_ID, text=f"🆕 BUYURTMA\nUser: {uid}\nUC: {uc}\nID: {game_id}")
        await update.message.reply_text("✅ Buyurtma qabul qilindi!
Tez orada hisobingizga yuboriladi")

async def addbal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    try:
        target_id, amount = context.args[0], int(context.args[1])
        u = get_user(target_id)
        u["balance"] += amount
        save(db)
        await update.message.reply_text("✅ Bajarildi")
        await context.bot.send_message(chat_id=int(target_id), text=f"💰 Balansingizga {amount} so'm qo'shildi")
    except:
        await update.message.reply_text("Xato! /addbal ID MIQDOR")

# ================= MAIN =================
if __name__ == '__main__':
    keep_alive() # Veb-serverni ishga tushirish
    print("Bot ishga tushdi...")
    
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("balance", balance))
    app.add_handler(CommandHandler("shop", shop))
    app.add_handler(CommandHandler("bonus", bonus))
    app.add_handler(CommandHandler("addbal", addbal))
    app.add_handler(CallbackQueryHandler(select))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))
    
    app.run_polling()
