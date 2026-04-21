from flask import Flask
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
import threading

TOKEN = 8613487563:AAGvAzI8a-HMyV-XlkI6rH4ptuvCmY23hsI
ADMIN_ID = 6945660449

jobs = []

# ---------------- BOT ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👷 Bot ishlayapti")

async def jobs_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("\n".join(jobs) if jobs else "😔 Yo‘q")

async def handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    user_id = update.effective_user.id

    if text.startswith("ish:") and user_id == ADMIN_ID:
        jobs.append(text.replace("ish:", "").strip())

def run_bot():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("jobs", jobs_list))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handler))

    app.run_polling()

# ---------------- SERVER ----------------
app = Flask(__name__)

@app.route("/")
def home():
    return "Bot ishlayapti 🚀"

@app.route("/jobs")
def get_jobs():
    return {"jobs": jobs}

# ---------------- START ----------------
if __name__ == "__main__":
    threading.Thread(target=run_bot).start()
    app.run(host="0.0.0.0", port=5000)