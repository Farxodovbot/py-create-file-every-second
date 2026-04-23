import json
import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

TOKEN = 8790916522:AAEqGclWYmVOqxA-NXvqiDrCjnZAF_-4Zgs
ADMIN_ID = 7253593181
CHANNEL = "@farxodovdasturchi"

DB = "db.json"

# ---------- DB ----------
def load():
    if not os.path.exists(DB):
        return {}
    return json.load(open(DB))

def save(data):
    json.dump(data, open(DB, "w"), indent=4)

def user(uid):
    data = load()
    uid = str(uid)
    if uid not in data:
        data[uid] = {"balance": 0}
        save(data)
    return data

# ---------- SUB CHECK ----------
async def is_subscribed(bot, user_id):
    try:
        member = await bot.get_chat_member(CHANNEL, user_id)
        return member.status in ["member", "administrator", "creator"]
    except:
        return False

# ---------- START ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_subscribed(context.bot, update.effective_user.id):
        await update.message.reply_text(f"❗ Avval kanalga obuna bo‘ling: {CHANNEL}")
        return

    user(update.effective_user.id)
    await update.message.reply_text(
        "🎮 Robux Shop Bot\n\n"
        "/balance - balans\n"
        "/shop - narxlar\n"
        "/convert - robux sotish\n"
        "/withdraw - yechish"
    )

# ---------- BALANCE ----------
async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load()
    uid = str(update.effective_user.id)

    bal = data.get(uid, {}).get("balance", 0)
    await update.message.reply_text(f"💰 Balans: {bal} so'm")

# ---------- SHOP ----------
async def shop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🛒 Robux narxlar:\n"
        "1️⃣ 100 Robux = 100 000 so'm\n"
        "2️⃣ 700 Robux = 700 000 so'm"
    )

# ---------- CONVERT ----------
async def convert(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🎮 Necha Robux sotmoqchisiz?")
    context.user_data["step"] = "convert"

async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    uid = str(update.effective_user.id)
    data = load()

    # ---------- CONVERT STEP ----------
    if context.user_data.get("step") == "convert":
        try:
            robux = int(text)
            price = robux * 100

            await context.bot.send_message(
                ADMIN_ID,
                f"🆕 Robux sotish:\nUser: {uid}\nRobux: {robux}\nSumma: {price}"
            )

            await update.message.reply_text("✅ So‘rov yuborildi")
        except:
            await update.message.reply_text("❌ Raqam yoz")
        context.user_data["step"] = None
        return

    # ---------- WITHDRAW ----------
    if context.user_data.get("step") == "withdraw":
        choice = text

        prices = {"1": 100000, "2": 700000}
        robux = {"1": 100, "2": 700}

        if choice not in prices:
            await update.message.reply_text("❌ 1 yoki 2 tanla")
            return

        if data[uid]["balance"] < prices[choice]:
            await update.message.reply_text("❌ Balans yetarli emas")
            return

        data[uid]["balance"] -= prices[choice]
        save(data)

        await context.bot.send_message(
            ADMIN_ID,
            f"💸 Robux yechish:\nUser: {uid}\nRobux: {robux[choice]}"
        )

        await update.message.reply_text("✅ Yuborildi")
        context.user_data["step"] = None
        return

# ---------- WITHDRAW ----------
async def withdraw(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "💸 Tanla:\n1️⃣ 100 Robux\n2️⃣ 700 Robux"
    )
    context.user_data["step"] = "withdraw"

# ---------- ADMIN ADD ----------
async def add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    try:
        _, uid, amount = update.message.text.split()
        data = load()

        uid = str(uid)
        amount = int(amount)

        if uid not in data:
            data[uid] = {"balance": 0}

        data[uid]["balance"] += amount
        save(data)

        await update.message.reply_text("✅ Qo‘shildi")
    except:
        await update.message.reply_text("/add user_id amount")

# ---------- MAIN ----------
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("balance", balance))
app.add_handler(CommandHandler("shop", shop))
app.add_handler(CommandHandler("convert", convert))
app.add_handler(CommandHandler("withdraw", withdraw))
app.add_handler(CommandHandler("add", add))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))

app.run_polling()