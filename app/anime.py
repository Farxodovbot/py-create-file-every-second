import os
import asyncio
import sqlite3
import logging
from flask import Flask
from threading import Thread
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

# --- RENDER UCHUN WEB SERVER ---
web_app = Flask(__name__)

@web_app.route('/')
def home():
    return "Bot is live!"

def run_web():
    port = int(os.environ.get("PORT", 8080))
    web_app.run(host='0.0.0.0', port=port)

# --- BOT LOGIKASI ---
TOKEN = "8635058894:AAHGygl5VARXfsNjvvbsRMFDQh1pbmGGFnM"
ADMIN_ID = 7253593181

# DB ulanishi
conn = sqlite3.connect("anime_baza.db", check_same_thread=False)
cur = conn.cursor()
cur.execute("CREATE TABLE IF NOT EXISTS animelar (code TEXT PRIMARY KEY, title TEXT, photo TEXT, eps INTEGER)")
cur.execute("CREATE TABLE IF NOT EXISTS qismlar (code TEXT, ep_num INTEGER, link TEXT)")
conn.commit()

bot = Bot(token=TOKEN)
dp = Dispatcher()

# START
@dp.message(Command("start"))
async def start_handler(message: types.Message):
    await message.answer("👋 Anime kodini yuboring (masalan: 001)")

# ADMIN PANEL
@dp.message(Command("admin"))
async def admin_handler(message: types.Message):
    if message.from_user.id != ADMIN_ID: return
    text = "<b>Admin Panel</b>\n\n➕ /add kod|nomi|rasm|soni\n🎬 /set kod|qism|link"
    await message.answer(text, parse_mode="HTML")

# ANIME QO'SHISH
@dp.message(Command("add"))
async def add_anime(message: types.Message):
    if message.from_user.id != ADMIN_ID: return
    try:
        data = message.text.replace("/add ", "").split("|")
        cur.execute("INSERT OR REPLACE INTO animelar VALUES (?, ?, ?, ?)", (data[0], data[1], data[2], int(data[3])))
        conn.commit()
        await message.answer("✅ Anime qo'shildi!")
    except:
        await message.answer("❌ Xato! Format: /add 001|Nomi|Rasm|12")

# QISM QO'SHISH
@dp.message(Command("set"))
async def set_ep(message: types.Message):
    if message.from_user.id != ADMIN_ID: return
    try:
        data = message.text.replace("/set ", "").split("|")
        cur.execute("INSERT OR REPLACE INTO qismlar VALUES (?, ?, ?)", (data[0], int(data[1]), data[2]))
        conn.commit()
        await message.answer("✅ Qism qo'shildi!")
    except:
        await message.answer("❌ Xato! Format: /set 001|1|link")

# QIDIRUV
@dp.message(F.text.regexp(r'^\d+$'))
async def search_handler(message: types.Message):
    code = message.text
    cur.execute("SELECT * FROM animelar WHERE code=?", (code,))
    res = cur.fetchone()
    if res:
        builder = InlineKeyboardBuilder()
        for i in range(1, res[3] + 1):
            builder.button(text=str(i), callback_data=f"ep_{code}_{i}")
        builder.adjust(5)
        await message.answer_photo(photo=res[2], caption=f"🎬 <b>{res[1]}</b>", reply_markup=builder.as_markup(), parse_mode="HTML")
    else:
        await message.answer("❌ Topilmadi")

# TUGMA BOSILGANDA
@dp.callback_query(F.data.startswith("ep_"))
async def callback_handler(callback: types.CallbackQuery):
    _, code, ep = callback.data.split("_")
    cur.execute("SELECT link FROM qismlar WHERE code=? AND ep_num=?", (code, ep))
    res = cur.fetchone()
    if res:
        await callback.message.answer(f"🎞 {ep}-qism:\n{res[0]}")
    else:
        await callback.message.answer("⚠️ Hali yuklanmagan")
    await callback.answer()

async def main():
    Thread(target=run_web, daemon=True).start()
    logging.basicConfig(level=logging.INFO)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
