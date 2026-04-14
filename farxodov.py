import time
import json
import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes
)

# ================= CONFIG =================
BOT_TOKEN = 8637820333:AAFkZ6NO2rz-uFOFGde2KPim33k25RkFzYY
ADMIN_ID = 7253593181

DB_FILE = "db.json"

# ================= WEB SERVER (UPTIME) =================
class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is alive")

def run_web():
    server = HTTPServer(("0.0.0.0", 10000), Handler)
    server.serve_forever()

threading.Thread(target=run_web).start()

# ================= DATABASE =================
def load():
    if not os.path.exists(DB_FILE):
        return {}
    with open(DB_FILE, "r") as f:
        return json.load(f)

def save(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f)

users = load()

def get_user(uid):
    uid = str(uid)

    if uid not in users:
        users[uid] = {
            "balance": 0,
            "premium_until": 0
        }
        save(users)

    return users[uid]

# ================= PREMIUM =================
def is_premium(uid):
    return get_user(uid)["premium_until"] > time.time()

# ================= PREMIUM BUY =================
def buy_premium(uid, days, price):
    u = get_user(uid)

    if u["balance"] < price:
        return False

    u["balance"] -= price

    now = time.time()

    if u["premium_until"] > now:
        u["premium_until"] += days * 86400
    else:
        u["premium_until"] = now + days * 86400

    save(users)
    return True

# ================= STATUS =================
def premium_left(uid):
    left = int(get_user(uid)["premium_until"] - time.time())

    if left <= 0:
        return "❌ Yo‘q"

    return f"{left // 86400} kun"

# ================= START =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    u = get_user(uid)

    save(users)

    await update.message.reply_text(
        f"👋 Xush kelibsiz!\n\n"
        f"💰 Balans: {u['balance']}\n"
        f"💎 Premium: {premium_left(uid)}\n\n"
        f"🆓 /buy7 /buy30 /buy60 /buy90\n"
        f"💎 /premium"
    )

# ================= FREE COMMANDS =================
async def buy7(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    ok = buy_premium(uid, 7, 20)
    save(users)
    await update.message.reply_text("✅ 7 kun aktiv" if ok else "❌ Balans yetarli emas")

async def buy30(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    ok = buy_premium(uid, 30, 120)
    save(users)
    await update.message.reply_text("✅ 30 kun aktiv" if ok else "❌ Balans yetarli emas")

async def buy60(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    ok = buy_premium(uid, 60, 200)
    save(users)
    await update.message.reply_text("✅ 60 kun aktiv" if ok else "❌ Balans yetarli emas")

async def buy90(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    ok = buy_premium(uid, 90, 270)
    save(users)
    await update.message.reply_text("✅ 90 kun aktiv" if ok else "❌ Balans yetarli emas")

# ================= PREMIUM MENU =================
def premium_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💎 7 kun - 20", callback_data="p7")],
        [InlineKeyboardButton("💎 30 kun - 120", callback_data="p30")],
        [InlineKeyboardButton("💎 60 kun - 200", callback_data="p60")],
        [InlineKeyboardButton("💎 90 kun - 270", callback_data="p90")]
    ])

async def premium(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("💎 Premium:", reply_markup=premium_menu())

async def premium_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    uid = q.from_user.id

    if q.data == "p7":
        ok = buy_premium(uid, 7, 20)
    elif q.data == "p30":
        ok = buy_premium(uid, 30, 120)
    elif q.data == "p60":
        ok = buy_premium(uid, 60, 200)
    elif q.data == "p90":
        ok = buy_premium(uid, 90, 270)
    else:
        ok = False

    save(users)

    text = "✅ Sotib olindi!" if ok else "❌ Balans yetarli emas"

    await q.edit_message_text(text, reply_markup=premium_menu())

# ================= ADMIN ADD BALANCE =================
async def add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Admin emassiz")
        return

    try:
        uid = context.args[0]
        amount = int(context.args[1])

        u = get_user(uid)
        u["balance"] += amount

        save(users)

        await update.message.reply_text(f"✅ {uid} ga +{amount}")

        await context.bot.send_message(
            uid,
            f"💰 Balansingizga +{amount} qo‘shildi"
        )

    except:
        await update.message.reply_text("❌ /add user_id amount")

# ================= APP =================
app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("buy7", buy7))
app.add_handler(CommandHandler("buy30", buy30))
app.add_handler(CommandHandler("buy60", buy60))
app.add_handler(CommandHandler("buy90", buy90))
app.add_handler(CommandHandler("premium", premium))
app.add_handler(CommandHandler("add", add))
app.add_handler(CallbackQueryHandler(premium_click))

print("Bot ishlayapti...")
app.run_polling()