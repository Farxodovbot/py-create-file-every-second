
import os
from flask import Flask
from threading import Thread
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters

# --- RENDER UCHUN PORT VA WEBSERVER QISMI ---
app = Flask('')

@app.route('/')
def home():
    return "Bot yoniq!"

def run():
    # Render o'zi avtomatik port raqamini beradi, topolmasa 8080 ishlatadi
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()

# Serverni botdan oldin ishga tushiramiz
keep_alive()
# --------------------------------------------

# 🔒 TOKEN
part1 = "8790916522:AAEqGclWYmVO"
part2 = "qxA-NXvqiDrCjnZAF_-4Zgs"
TOKEN = part1 + part2

ADMIN_ID = 7253593181
CHANNEL_ID = -1003725403066
CHANNEL_LINK = "https://t.me/farxodovdasturchi"

PRICE_PER_ROBUX = 100
PENALTY = 10000

RULES_TEXT = (
    "📜 BOT QOIDALARI\n\n"
    "1. Kanalga obuna bo‘lish majburiy.\n"
    "2. Chiqsangiz balansdan 10 000 so‘m yechiladi.\n"
    "3. Qayta obuna bo‘lmaguncha bot ishlamaydi.\n"
    "4. Robuxni faqat bot orqali sotib olishingiz mumkin.\n"
    "5. Balans boshida 0, admin orqali to‘ldiriladi.\n"
    "6. Buyurtma 1–3 kunda amalga oshadi."
)

async def check_sub(context, user_id):
    try:
        member = await context.bot.get_chat_member(CHANNEL_ID, user_id)
        return member.status in ["member", "administrator", "creator"]
    except:
        return False

async def ensure_sub(update, context):
    user_id = update.effective_user.id
    if not await check_sub(context, user_id):
        balance = context.user_data.get("balance", 0)
        context.user_data["balance"] = max(0, balance - PENALTY)
        keyboard = [
            [InlineKeyboardButton("📢 Obuna bo‘lish", url=CHANNEL_LINK)],
            [InlineKeyboardButton("✅ Tekshirish", callback_data="check_sub")]
        ]
        await update.message.reply_text(
            f"❗ Obuna yo‘q!\n💸 Jarima: -{PENALTY} so‘m",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return False
    return True

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    username = user.username or "NoUsername"
    users = context.application.bot_data.get("users", {})
    users[user_id] = username
    context.application.bot_data["users"] = users
    context.user_data.setdefault("balance", 0)
    if not await ensure_sub(update, context):
        return
    keyboard = [[KeyboardButton("🛒 Robux sotib olish")], [KeyboardButton("💰 Balans")]]
    await update.message.reply_text(RULES_TEXT, reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))

async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await ensure_sub(update, context):
        return
    text = update.message.text
    if text == "🛒 Robux sotib olish":
        await update.message.reply_text("💰 Necha Robux kerak? (30-800)")
        context.user_data["step"] = "robux"
    elif text == "💰 Balans":
        bal = context.user_data.get("balance", 0)
        await update.message.reply_text(f"💳 Balans: {bal} so‘m")
    elif context.user_data.get("step") == "robux":
        try:
            amount = int(text)
            if amount < 30 or amount > 800:
                return await update.message.reply_text("❌ 30-800 oralig‘ida!")
            context.user_data["robux"] = amount
            context.user_data["step"] = "username"
            await update.message.reply_text("👤 Username kiriting:")
        except:
            await update.message.reply_text("❌ Son yoz!")
    elif context.user_data.get("step") == "username":
        username = text
        robux = context.user_data["robux"]
        price = robux * PRICE_PER_ROBUX
        balance = context.user_data.get("balance", 0)
        if balance < price:
            return await update.message.reply_text("❌ Balans yetarli emas!")
        context.user_data["balance"] -= price
        await update.message.reply_text(f"✅ Buyurtma qabul qilindi!\n👤 {username}\n💰 {robux} Robux\n⏳ 1–3 kunda")
        await context.bot.send_message(ADMIN_ID, f"🆕 Buyurtma!\nUser: {update.effective_user.id}\nUsername: {username}\nRobux: {robux}\n/done {update.effective_user.id}")

async def topup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    try:
        uid = int(context.args[0]); amount = int(context.args[1])
        user_data = context.application.user_data[uid]
        user_data["balance"] = user_data.get("balance", 0) + amount
        await context.bot.send_message(uid, f"💰 +{amount} so‘m qo‘shildi!")
        await update.message.reply_text("Qo‘shildi!")
    except:
        await update.message.reply_text("Format: /topup id summa")

async def done(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    try:
        uid = int(context.args[0])
        await context.bot.send_message(uid, "✅ Buyurtma bajarildi!")
        await update.message.reply_text("Yakunlandi!")
    except:
        await update.message.reply_text("Format: /done id")

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    users = context.application.bot_data.get("users", {})
    text = f"📊 Users: {len(users)}\n\n"
    for uid, uname in users.items(): text += f"{uname} ({uid})\n"
    await update.message.reply_text(text)

async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "check_sub":
        if await check_sub(context, query.from_user.id):
            await query.message.delete()
            await context.bot.send_message(query.from_user.id, "✅ Obuna OK")
        else:
            await query.answer("❌ Obuna yo‘q", show_alert=True)

def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("topup", topup))
    app.add_handler(CommandHandler("done", done))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, menu))
    app.add_handler(CallbackQueryHandler(buttons))
    print("Bot ishlayapti...")
    app.run_polling()

if __name__ == "__main__":
    main()
