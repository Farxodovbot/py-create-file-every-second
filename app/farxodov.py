import json
import os
import time

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters
)

# ================= CONFIG =================
# DIQQAT: os.getenv ichiga tokenni emas, o'zgaruvchi nomini yozish kerak.
# Hozircha ishlashi uchun tokenni to'g'ridan-to'g'ri o'zgaruvchiga ulaymiz.
BOT_TOKEN = "8733154492:AAFW0VGswCOf-nhsf6FlCfU8i1KSaEfGYxA"
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

# ================= START =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 UC SHOP BOT\n\n"
        "💰 /balance - Balansni tekshirish\n"
        "🛒 /shop - UC sotib olish\n"
        "🎁 /bonus - Bonus olish"
    )

# ================= BALANCE =================
async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if uid == ADMIN_ID:
        await update.message.reply_text("💰 Balans: ∞ (Admin)")
        return
    u = get_user(uid)
    await update.message.reply_text(f"💰 Balans: {u['balance']} so'm")

# ================= BONUS =================
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
        await update.message.reply_text(f"⏳ Kuting: {left//86400} kun")
        return
    u["balance"] += 10
    u["last_bonus"] = now
    save(db)
    await update.message.reply_text(f"🎁 +10 bonus!\n💰 Balans: {u['balance']}")

# ================= SHOP =================
async def shop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = []
    for uc, price in PACKAGES.items():
        keyboard.append([InlineKeyboardButton(f"{uc} UC - {price} so'm", callback_data=uc)])
    await update.message.reply_text("🛒 Paket tanlang:", reply_markup=InlineKeyboardMarkup(keyboard))

# ================= SELECT PACKAGE =================
async def select(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id
    u = get_user(uid)
    uc = q.data
    price = PACKAGES[uc]
    if uid != ADMIN_ID:
        if u["balance"] < price:
            await q.message.reply_text("❌ Balans yetarli emas")
            return
    u["selected_uc"] = uc
    u["step"] = "wait_id"
    save(db)
    await q.message.reply_text("🆔 Game ID yuboring (faqat raqam):")

# ================= HANDLE ID =================
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    uid = msg.from_user.id
    u = get_user(uid)
    if u.get("step") == "wait_id":
        if not msg.text.isdigit():
            await msg.reply_text("❌ Faqat raqam kiriting!")
            return
        game_id = msg.text
        uc = u["selected_uc"]
        price = PACKAGES[uc]
        if uid != ADMIN_ID:
            u["balance"] -= price
        u["step"] = None
        u["selected_uc"] = None
        save(db)
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"🆕 BUYURTMA\nUser ID: {uid}\nUC: {uc}\nGame ID: {game_id}"
        )
        await msg.reply_text("✅ Qabul qilindi!\n⏳ 1-3 kun ichida tushadi.")

# ================= ADMIN BALANCE =================
async def addbal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    try:
        uid = context.args[0]
        amount = int(context.args[1])
        u = get_user(uid)
        u["balance"] += amount
        save(db)
        await update.message.reply_text("✅ Balans qo‘shildi")
        await context.bot.send_message(chat_id=int(uid), text=f"💰 +{amount} so'm berildi")
    except:
        await update.message.reply_text("To'g'ri format: /addbal user_id miqdor")

# ================= MAIN =================
if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("balance", balance))
    app.add_handler(CommandHandler("shop", shop))
    app.add_handler(CommandHandler("bonus", bonus))
    app.add_handler(CommandHandler("addbal", addbal))
    app.add_handler(CallbackQueryHandler(select))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))

    print("Bot muvaffaqiyatli ishga tushdi...")
    app.run_polling()
