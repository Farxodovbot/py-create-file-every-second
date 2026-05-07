import logging
import sqlite3
import asyncio
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.exceptions import ChatNotFound, BotBlocked

# --- MA'LUMOTLAR ---
API_TOKEN = '8705927604:AAEjfrb7ZK2es-9tf2pu6csYuSUywMxrGxY'
ADMIN_ID = 7253593181
DATABASE = "anime_data.db"

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN, parse_mode="HTML")
dp = Dispatcher(bot)

# --- BAZA BILAN ISHLASH ---
def init_db():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY)')
    cursor.execute('CREATE TABLE IF NOT EXISTS animes (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT)')
    cursor.execute('CREATE TABLE IF NOT EXISTS episodes (anime_id INTEGER, part INTEGER, video_id TEXT)')
    cursor.execute('CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)')
    
    # Boshlang'ich sozlamalar
    cursor.execute("INSERT OR IGNORE INTO settings VALUES ('ch_id', '-100...')") # Kanal ID
    cursor.execute("INSERT OR IGNORE INTO settings VALUES ('ch_link', 'https://t.me/...')") # Kanal Link
    conn.commit()
    conn.close()

init_db()

# --- ADMIN PANEL ---
def get_admin_keyboard():
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("➕ Anime yaratish", callback_data="new_anime"),
        InlineKeyboardButton("🎬 Qism qo'shish", callback_data="add_part"),
        InlineKeyboardButton("📢 Reklama", callback_data="send_ads"),
        InlineKeyboardButton("📊 Statistika", callback_data="stats"),
        InlineKeyboardButton("🔗 Kanal sozlamalari", callback_data="chan_settings")
    )
    return markup

# --- OBUNANI TEKSHIRISH ---
async def is_subscribed(user_id):
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("SELECT value FROM settings WHERE key='ch_id'")
    ch_id = c.fetchone()[0]
    conn.close()
    try:
        member = await bot.get_chat_member(chat_id=ch_id, user_id=user_id)
        return member.status != 'left'
    except:
        return True

# --- START BUYRUG'I ---
@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    # Foydalanuvchini ro'yxatga olish
    conn = sqlite3.connect(DATABASE)
    conn.execute("INSERT OR IGNORE INTO users VALUES (?)", (message.from_user.id,))
    conn.commit()
    
    args = message.get_args()
    if args and args.startswith("vid"): # Masalan: vid_5_1 (animeID_qism)
        if not await is_subscribed(message.from_user.id):
            c = conn.cursor()
            c.execute("SELECT value FROM settings WHERE key='ch_link'")
            link = c.fetchone()[0]
            btn = InlineKeyboardMarkup().add(InlineKeyboardButton("Kanalga a'zo bo'lish", url=link))
            btn.add(InlineKeyboardButton("✅ Tekshirish", url=f"https://t.me/{(await bot.get_me()).username}?start={args}"))
            return await message.answer("⚠️ Videoni ko'rish uchun kanalga a'zo bo'lishingiz shart!", reply_markup=btn)

        _, a_id, part = args.split("_")
        c = conn.cursor()
        c.execute("SELECT video_id FROM episodes WHERE anime_id=? AND part=?", (a_id, part))
        res = c.fetchone()
        if res:
            await message.answer_video(res[0], caption=f"🎬 Qism: {part}")
        else:
            await message.answer("❌ Video topilmadi.")
    else:
        await message.answer("👋 Xush kelibsiz! Anime ko'rish uchun kanaldagi linklardan foydalaning.")
    conn.close()

# --- ADMIN BUYRUQLARI ---
@dp.message_handler(commands=['admin'], user_id=ADMIN_ID)
async def admin_main(message: types.Message):
    await message.answer("🛠 <b>Admin Panel</b>\nKerakli bo'limni tanlang:", reply_markup=get_admin_keyboard())

@dp.callback_query_handler(user_id=ADMIN_ID)
async def admin_calls(call: types.CallbackQuery):
    if call.data == "stats":
        conn = sqlite3.connect(DATABASE)
        res = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        conn.close()
        await call.message.answer(f"👤 Jami foydalanuvchilar: {res} ta")
    
    elif call.data == "new_anime":
        await call.message.answer("Yangi anime nomini yozing:\n(Namuna: `/anime Naruto`)", parse_mode="Markdown")

    elif call.data == "chan_settings":
        await call.message.answer("Kanal ID va Linkini sozlash:\n(Namuna: `/set -100123 https://t.me/link`)", parse_mode="Markdown")

# --- ADMIN MA'LUMOT KIRITISH ---
@dp.message_handler(commands=['anime'], user_id=ADMIN_ID)
async def add_anime_name(message: types.Message):
    name = message.get_args()
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("INSERT INTO animes (name) VALUES (?)", (name,))
    conn.commit()
    await message.answer(f"✅ Anime yaratildi. ID: <b>{c.lastrowid}</b>\nEndi videoni quyidagicha yuboring:\n`/qism {c.lastrowid} 1` (ID va Qism)")
    conn.close()

@dp.message_handler(content_types=['video'], user_id=ADMIN_ID)
async def save_video(message: types.Message):
    await message.answer(f"📹 Videoning File ID: <code>{message.video.file_id}</code>\nUni /qism buyrug'i bilan bazaga qo'shing.")

@dp.message_handler(commands=['qism'], user_id=ADMIN_ID)
async def add_episode(message: types.Message):
    args = message.get_args().split() # ID, Qism, VideoID
    a_id, part, v_id = args[0], args[1], args[2]
    conn = sqlite3.connect(DATABASE)
    conn.execute("INSERT INTO episodes VALUES (?, ?, ?)", (a_id, part, v_id))
    conn.commit()
    conn.close()
    
    bot_user = await bot.get_me()
    link = f"https://t.me/{bot_user.username}?start=vid_{a_id}_{part}"
    await message.answer(f"✅ Qism qo'shildi!\n\nKanal uchun tugma linki:\n<code>{link}</code>")

@dp.message_handler(commands=['set'], user_id=ADMIN_ID)
async def set_channel(message: types.Message):
    args = message.get_args().split()
    conn = sqlite3.connect(DATABASE)
    conn.execute("UPDATE settings SET value=? WHERE key='ch_id'", (args[0],))
    conn.execute("UPDATE settings SET value=? WHERE key='ch_link'", (args[1],))
    conn.commit()
    conn.close()
    await message.answer("✅ Kanal sozlamalari yangilandi!")

# --- REKLAMA ---
@dp.callback_query_handler(text="send_ads", user_id=ADMIN_ID)
async def ads_start(call: types.CallbackQuery):
    await call.message.answer("Reklama matnini yuboring (Hamma foydalanuvchilarga yuboriladi).")

@dp.message_handler(user_id=ADMIN_ID, is_reply=False)
async def broadcast(message: types.Message):
    if message.text.startswith("/") : return # Buyruqlarni o'tkazib yuboradi
    conn = sqlite3.connect(DATABASE)
    users = conn.execute("SELECT user_id FROM users").fetchall()
    conn.close()
    
    count = 0
    for user in users:
        try:
            await bot.send_message(user[0], message.text)
            count += 1
            await asyncio.sleep(0.05) # Spam blokirovkasidan qochish
        except: continue
    await message.answer(f"📢 Reklama {count} kishiga yuborildi.")

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
