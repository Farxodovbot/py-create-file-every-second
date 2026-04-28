import logging
import os
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

anime_db = {}

# --- RENDER UCHUN WEB SERVER (O'CHIB QOLMASLIGI UCHUN) ---
async def handle(request):
    return web.Response(text="Bot ishlamoqda...")

# --- TEZKOR OBUNA MIDDLEWARE ---
class ForceSub(BaseMiddleware):
    async def on_pre_process_message(self, message: types.Message, data: dict):
        if message.from_user.id == ADMIN_ID or message.text == "/start":
            return
        status = await self.check_sub(message.from_user.id)
        if not status:
            btn = InlineKeyboardMarkup().add(InlineKeyboardButton("A'zo bo'lish", url="https://t.me/AnimeFonuzbaza"))
            btn.add(InlineKeyboardButton("✅ Tekshirish", callback_data="recheck"))
            await message.answer(f"⚠️ Botdan foydalanish uchun {CHANNEL_ID} kanaliga a'zo bo'ling!", reply_markup=btn)
            raise CancelHandler()

    async def check_sub(self, user_id):
        try:
            m = await bot.get_chat_member(CHANNEL_ID, user_id)
            return m.status in ['member', 'creator', 'administrator']
        except: return False

dp.middleware.setup(ForceSub())

# --- ADMIN PANEL ---
class AnimeAdd(StatesGroup):
    photo = State()
    title = State()
    genre = State()
    episodes = State()
    quality = State()
    code = State()
    description = State()

@dp.message_handler(commands=['admin'], user_id=ADMIN_ID)
@dp.message_handler(text="➕ Anime qo'shish", user_id=ADMIN_ID)
async def admin_start(message: types.Message):
    await AnimeAdd.photo.set()
    await message.answer("🖼 Anime posterini yuboring:")

@dp.message_handler(content_types=['photo'], state=AnimeAdd.photo)
async def load_photo(message: types.Message, state: FSMContext):
    await state.update_data(photo=message.photo[-1].file_id)
    await AnimeAdd.next(); await message.answer("🎬 Anime nomi:")

@dp.message_handler(state=AnimeAdd.title)
async def load_title(message: types.Message, state: FSMContext):
    await state.update_data(title=message.text)
    await AnimeAdd.next(); await message.answer("🎭 Janrlar (#janr):")

@dp.message_handler(state=AnimeAdd.genre)
async def load_genre(message: types.Message, state: FSMContext):
    await state.update_data(genre=message.text)
    await AnimeAdd.next(); await message.answer("🎞 Qismlar soni:")

@dp.message_handler(state=AnimeAdd.episodes)
async def load_eps(message: types.Message, state: FSMContext):
    await state.update_data(episodes=message.text)
    await AnimeAdd.next(); await message.answer("💿 Sifati:")

@dp.message_handler(state=AnimeAdd.quality)
async def load_qual(message: types.Message, state: FSMContext):
    await state.update_data(quality=message.text)
    await AnimeAdd.next(); await message.answer("🔢 Kod bering:")

@dp.message_handler(state=AnimeAdd.code)
async def load_code(message: types.Message, state: FSMContext):
    await state.update_data(code=message.text)
    await AnimeAdd.next(); await message.answer("📝 Tavsif:")

@dp.message_handler(state=AnimeAdd.description)
async def finish_add(message: types.Message, state: FSMContext):
    d = await state.get_data()
    anime_db[d['code']] = d
    caption = f"🎬 <b>{d['title']}</b>\n\n✒️ Janri: {d['genre']}\n📁 Qismlar: {d['episodes']}\n💿 Sifat: {d['quality']}\n🔢 Kod: {d['code']}\n📝 Tavsif: {message.text}"
    me = await bot.get_me()
    btn = InlineKeyboardMarkup().add(InlineKeyboardButton("📺 Tomosha qilish", url=f"https://t.me/{me.username}?start={d['code']}"))
    await bot.send_photo(CHANNEL_ID, d['photo'], caption=caption, reply_markup=btn)
    await state.finish()
    await message.answer("✅ Kanalga yuborildi!")

# --- START ---
@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    code = message.get_args()
    if code and code in anime_db:
        data = anime_db[code]
        markup = InlineKeyboardMarkup(row_width=4)
        btns = [InlineKeyboardButton(f"{i}", callback_data=f"ep_{i}") for i in range(1, int(data['episodes'])+1)]
        markup.add(*btns)
        await message.answer_photo(data['photo'], caption=f"🍿 <b>{data['title']}</b>\nQismlar:", reply_markup=markup)
    else:
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True).add("➕ Anime qo'shish")
        await message.answer("Xush kelibsiz! Anime kodini yuboring.", reply_markup=kb)

@dp.callback_query_handler(text="recheck")
async def recheck(q: types.CallbackQuery):
    m = await bot.get_chat_member(CHANNEL_ID, q.from_user.id)
    if m.status in ['member', 'creator', 'administrator']:
        await q.message.delete(); await q.message.answer("✅ Rahmat! Bot tayyor.")
    else:
        await q.answer("❌ A'zo emassiz!", show_alert=True)

async def on_startup(dp):
    await bot.set_my_commands([types.BotCommand("start", "Yangilash"), types.BotCommand("admin", "Admin")])

if __name__ == '__main__':
    # Render uchun port sozlamasi
    port = int(os.environ.get("PORT", 8080))
    # Web serverni fonda yurgizish
    app = web.Application()
    app.router.add_get('/', handle)
    # Botni ishga tushirish
    executor.start_polling(dp, on_startup=on_startup, skip_updates=True)
