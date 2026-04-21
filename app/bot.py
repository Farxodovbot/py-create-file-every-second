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

# 🔐 TOKEN
TOKEN = "8613487563:AAGvAzI8a-HMyV-XlkI6rH4ptuvCmY23hsI"
CHANNEL = "@ishchilarmarkazi_uz"

jobs = []
verified_users = set()

# ---------------- CHECK MEMBER ----------------
async def is_member(user_id, context):
    try:
        member = await context.bot.get_chat_member(CHANNEL, user_id)
        return member.status in ["member", "administrator", "creator"]
    except Exception:
        return False

# ---------------- START ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if not await is_member(user_id, context):
        keyboard = [
            [InlineKeyboardButton("📢 Kanalga kirish", url=f"https://t.me/{CHANNEL.replace('@','')}")],
            [InlineKeyboardButton("✅ Tekshirish", callback_data="check")]
        ]

        await update.message.reply_text(
            "❗ Botdan foydalanish uchun kanalga a’zo bo‘ling:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    verified_users.add(user_id)
    keyboard = [
        [InlineKeyboardButton("📋 Ishlar", callback_data="jobs")],
        [InlineKeyboardButton("📝 Ariza", callback_data="apply")]
    ]

    await update.message.reply_text(
        "👷 Ishchilar Markaziga xush kelibsiz!",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ---------------- BUTTONS ----------------
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "check":
        if await is_member(query.from_user.id, context):
            await query.edit_message_text("✅ Tasdiqlandingiz! Endi /start deb yozing.")
        else:
            await query.edit_message_text("❌ Siz hali kanalga a’zo emassiz.")

    elif query.data == "jobs":
        if not jobs:
            await query.edit_message_text("😔 Hozircha ish yo‘q")
        else:
            text = "📋 Ishlar ro'yxati:\n\n" + "\n".join([f"{i+1}. {j}" for i, j in enumerate(jobs)])
            await query.edit_message_text(text)

    elif query.data == "apply":
        await query.edit_message_text("📝 Arizangiz qabul qilindi!")

# ---------------- ADMIN ADD JOB ----------------
async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text.startswith("ish:"):
        job = text.replace("ish:", "").strip()
        jobs.append(job)
        await update.message.reply_text("✅ Yangi ish qo‘shildi!")

# ---------------- MAIN ----------------
def main():
    # Render uchun portni ochib qo'yamiz (kerak bo'lsa)
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))

    print("--- BOT ISHGA TUSHDI ---")
    app.run_polling()

if __name__ == "__main__":
    main()
