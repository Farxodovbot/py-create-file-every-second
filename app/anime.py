import logging
import os
import sqlite3
import asyncio
from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher.handler import CancelHandler
from aiogram.dispatcher.middlewares import BaseMiddleware
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiohttp import web

# --- SOZLAMALAR ---
API_TOKEN = '8635058894:AAHGygl5VARXfsNjvvbsRMFDQh1pbmGGFnM'
ADMIN_ID = 7253593181
CHANNEL_ID = "@AnimeFonuzbaza"

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN, parse_mode="HTML")
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# --- BAZA (SQLite) ---
conn = sqlite3.connect('anime_data.db', check_same_thread=False)
cur = conn.cursor()
cur.execute('CREATE TABLE IF NOT EXISTS animelar (code TEXT PRIMARY KEY, title TEXT, photo TEXT, eps_count INTEGER)')
cur.execute('CREATE TABLE IF NOT EXISTS qismlar (code TEXT, ep_num INTEGER, link TEXT)')
conn.commit()

# --- RENDER PORT SOZLAMASI (Web Server) ---
async def handle(request):
    return web.Response(text="Bot ishlamoqda!")

async def on_startup(dp):
    # Render uchun portni ochish
    app = web.Application()
    app.router.add_get("/", handle)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, "0.0.0.0", port)
    asyncio.create_task(site.start())
    logging.info(f"Web server {port}-portda ishga tushdi.")

# --- OBUNA MIDDLEWARE ---
class ForceSub(BaseMiddleware):
    async def on_pre_process_message(self, message: types.Message, data: dict):
        if message.from_user.id == ADMIN_ID or (message.text and message.text.startswith("/start")):
            return
        try:
            member = await bot.get_chat_member(CHANNEL_ID, message.from_user.id)
            if member.status not in ['member', 'creator', 'administrator']:
                btn = InlineKeyboardMarkup().add(InlineKeyboardButton("A'zo bo'lish", url=f"https://t.me/{CHANNEL_ID[1:]}"))
                btn.add(InlineKeyboardButton("✅ Tekshirish", callback_data="recheck"))
                await message.answer(f"⚠️ Botdan foydalanish uchun {CHANNEL_ID} kanaliga a'zo bo'ling!", reply_markup=btn)
                raise CancelHandler()
        except: pass

dp.middleware.setup(ForceSub())

# --- HOLATLAR ---
class AnimeAdd(StatesGroup):
    photo, title, eps_count, code, links = State(), State(), State(), State(), State()

class ChannelPost(StatesGroup):
    photo, info, code = State(), State(), State()

# --- ADMIN PANEL ---
@dp.message_handler(commands=['admin'], user_id=ADMIN_ID)
async def admin_panel(message: types.Message):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    kb.add("➕ Anime qo'shish", "📢 Kanalga xabar")
    await message.answer("<b>Admin panel!</b>", reply_markup=kb)

# --- KANALGA XABAR ---
@dp.message_handler(text="📢 Kanalga xabar", user_id=ADMIN_ID)
async def post_start(message: types.Message):
    await ChannelPost.photo.set()
    await message.answer("🖼 Xabar uchun rasm yuboring:")

@dp.message_handler(content_types=['photo'], state=ChannelPost.photo)
async def post_photo(message: types.Message, state: FSMContext):
    await state.update_data(photo=message.photo[-1].file_id)
    await ChannelPost.next()
    await message.answer("📝 Ma'lumotlarni yuboring:")

@dp.message_handler(state=ChannelPost.info)
async def post_info(message: types.Message, state: FSMContext):
    await state.update_data(info=message.text)
    await ChannelPost.next()
    await message.answer("🔢 Anime kodini yuboring:")

@dp.message_handler(state=ChannelPost.code)
async def post_finish(message: types.Message, state: FSMContext):
    data = await state.get_data()
    bot_info = await bot.get_me()
    btn = InlineKeyboardMarkup().add(InlineKeyboardButton("📺 Tomosha qilish", url=f"https://t.me/{bot_info.username}?start={message.text}"))
    await bot.send_photo(CHANNEL_ID, data['photo'], caption=f"{data['info']}\n\n🔢 <b>Kod:</b> <code>{message.text}</code>", reply_markup=btn)
    await state.finish()
    await message.answer("✅ Kanalga yuborildi!")

# --- ANIME QO'SHISH ---
@dp.message_handler(text="➕ Anime qo'shish", user_id=ADMIN_ID)
async def start_adding(message: types.Message):
    await AnimeAdd.photo.set()
    await message.answer("🖼 Anime posterini yuboring:")

@dp.message_handler(content_types=['photo'], state=AnimeAdd.photo)
async def load_photo(message: types.Message, state: FSMContext):
    await state.update_data(photo=message.photo[-1].file_id)
    await AnimeAdd.next(); await message.answer("🎬 Anime nomini kiriting:")

@dp.message_handler(state=AnimeAdd.title)
async def load_title(message: types.Message, state: FSMContext):
    await state.update_data(title=message.text)
    await AnimeAdd.next(); await message.answer("🎞 Qismlar sonini yozing:")

@dp.message_handler(state=AnimeAdd.eps_count)
async def load_eps(message: types.Message, state: FSMContext):
    await state.update_data(eps_count=int(message.text))
    await AnimeAdd.next(); await message.answer("🔢 Anime kodini bering:")

@dp.message_handler(state=AnimeAdd.code)
async def load_code(message: types.Message, state: FSMContext):
    await state.update_data(code=message.text, current_ep=1)
    await AnimeAdd.next(); await message.answer("🔗 1-qism linkini yuboring:")

@dp.message_handler(state=AnimeAdd.links)
async def load_links(message: types.Message, state: FSMContext):
    data = await state.get_data()
    cur.execute("INSERT INTO qismlar VALUES (?, ?, ?)", (data['code'], data['current_ep'], message.text))
    conn.commit()
    if data['current_ep'] < data['eps_count']:
        next_ep = data['current_ep'] + 1
        await state.update_data(current_ep=next_ep)
        await message.answer(f"🔗 {next_ep}-qism linkini yuboring:")
    else:
        cur.execute("INSERT INTO animelar VALUES (?, ?, ?, ?)", (data['code'], data['title'], data['photo'], data['eps_count']))
        conn.commit()
        await state.finish(); await message.answer("✅ Anime bazaga qo'shildi!")

# --- QIDIRUV VA START ---
@dp.message_handler(commands=['start'])
async def start_handler(message: types.Message):
    code = message.get_args()
    if code: await send_anime(message, code)
    else: await message.answer("👋 Salom! Anime kodini yuboring.")

@dp.message_handler(lambda m: m.text.isdigit())
async def code_search(message: types.Message):
    await send_anime(message, message.text)

async def send_anime(message, code):
    cur.execute("SELECT * FROM animelar WHERE code=?", (code,))
    res = cur.fetchone()
    if res:
        markup = InlineKeyboardMarkup(row_width=4)
        btns = [InlineKeyboardButton(f"{i}", callback_data=f"v_{code}_{i}") for i in range(1, res[3]+1)]
        markup.add(*btns)
        await message.answer_photo(res[2], caption=f"🎬 <b>{res[1]}</b>", reply_markup=markup)
    else: await message.answer("❌ Kod topilmadi.")

@dp.callback_query_handler(lambda c: c.data.startswith('v_'))
async def show_ep(callback: types.CallbackQuery):
    _, code, ep = callback.data.split('_')
    cur.execute("SELECT link FROM qismlar WHERE code=? AND ep_num=?", (code, ep))
    link = cur.fetchone()
    if link: await callback.message.answer(f"🎬 {ep}-qism:\n\n{link[0]}")
    await callback.answer()

@dp.callback_query_handler(text="recheck")
async def recheck(c: types.CallbackQuery):
    m = await bot.get_chat_member(CHANNEL_ID, c.from_user.id)
    if m.status in ['member', 'creator', 'administrator']:
        await c.message.delete(); await c.message.answer("✅ Tasdiqlandi!")
    else: await c.answer("❌ A'zo emassiz!", show_alert=True)

if __name__ == '__main__':
    executor.start_polling(dp, on_startup=on_startup, skip_updates=True)
