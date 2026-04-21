
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)

# 🔐 TOKEN (o'zing qo'yasan)
TOKEN = 8613487563:AAGvAzI8a-HMyV-XlkI6rH4ptuvCmY23hsI

# 👑 ADMIN
ADMIN_ID = 6945660449

# 📋 ishlar bazasi
jobs = []

# ---------------- START ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👷 Ishchilar Markazi botiga xush kelibsiz!\n\n"
        "📌 Ishlar: /jobs\n"
        "📝 Ish qo‘shish (admin): ish: matn"
    )

# ---------------- JOBS LIST ----------------
async def jobs_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not jobs:
        await update.message.reply_text("😔 Hozircha ish yo‘q")
        return

    text = "📋 Ishlar ro‘yxati:\n\n"
    for i, j in enumerate(jobs, 1):
        text += f"{i}. {j}\n"

    await update.message.reply_text(text)

# ---------------- TEXT HANDLER ----------------
async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text

    # 🔥 ADMIN JOB ADD
    if text.startswith("ish:"):
        if user_id != ADMIN_ID:
            await update.message.reply_text("❌ Siz admin emassiz!")
            return

        job = text.replace("ish:", "").strip()
        jobs.append(job)

        await update.message.reply_text("✅ Ish qo‘shildi!")

# ---------------- MAIN ----------------
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("jobs", jobs_list))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))

    app.run_polling()

if __name__ == "__main__":
    main()