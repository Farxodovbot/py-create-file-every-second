import logging
import os
from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher.handler import CancelHandler
from aiogram.dispatcher.middlewares import BaseMiddleware
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# --- SOZLAMALAR ---
API_TOKEN = '8635058894:AAHGygl5VARXfsNjvvbsRMFDQh1pbmGGFnM'
ADMIN_ID = 7253593181
CHANNEL_ID = "@AnimeFonuzbaza"
PORT = 8080  # Pydroid uchun standart port

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN, parse_mode="HTML")
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# Ma'lumotlarni vaqtincha saqlash (Lug'at)
anime_db = {}

# --- ADMIN HOLATLARI ---
class AnimeAdd(StatesGroup):
    photo = State()
    title = State()
    genre = State()
    episodes = State()
    quality = State()
    code = State()
    description = State()

# --- TEZKOR TEKSHIRUV (MIDDLEWARE) ---
class ForceSub(BaseMiddleware):
    async def on_pre_process_message(self, message: types.Message, data: dict):
        if message.from_user.id == ADMIN_ID or message.text == "/start":
            return
        
        status = await self.check_sub(message.from_user.id)
        if not status:
            await self.send_alert(message)
            raise CancelHandler()

    async def on_pre_process_callback_query(self, query: types.CallbackQuery, data: dict):
        if query.from_user.id == ADMIN_ID or query.data == "recheck":
            return
        
        status = await self.check_sub(query.from_user.id)
        if not status:
            await query.answer("⚠️ Kanalga a'zo bo'ling!", show_alert=True)
            raise CancelHandler()

    async def check_sub(self, user_id):
        try:
            m = await bot.get_chat_member(CHANNEL_ID, user_id)
            return m.status in ['member', 'creator', 'administrator']
        except: 
            return False

    async def send_alert(self, message):
        btn = InlineKeyboardMarkup().add(InlineKeyboardButton("Kanalga a'zo bo'lish", url=f"https://t.me/AnimeFonuzbaza"))
        btn.add(InlineKeyboardButton("✅ Tekshirish", callback_data="recheck"))
        await message.answer(f"❗ Botdan foydalanish uchun {CHANNEL_ID} kanaliga a'zo bo'ling!", reply_markup=btn)

dp.middleware.setup(ForceSub())

# --- ADMIN PANEL ---
@dp.message_handler(commands=['admin'], user_id=ADMIN_ID)
@dp.message_handler(text="➕ Anime qo'shish", user_id=ADMIN_ID)
async def admin_start(message: types.Message):
    await AnimeAdd.photo.set()
    await message.answer("🖼 <b>Poster yuboring:</b>")

@dp.message_handler(content_types=['photo'], state=AnimeAdd.photo)
async def load_photo(message: types.Message, state: FSMContext):
    await state.update_data(photo=message.photo[-1].file_id)
    await AnimeAdd.next()
    await message.answer("🎬 <b>Anime nomi:</b>")

@dp.message_handler(state=AnimeAdd.title)
async def load_title(message: types.Message, state: FSMContext):
    await state.update_data(title=message.text)
    await AnimeAdd.next()
    await message.answer("🎭 <b>Janrlari (#janr):</b>")

@dp.message_handler(state=AnimeAdd.genre)
async def load_genre(message: types.Message, state: FSMContext):
    await state.update_data(genre=message.text)
    await AnimeAdd.next()
    await message.answer("🎞 <b>Qismlar soni (faqat raqam):</b>")

@dp.message_handler(state=AnimeAdd.episodes)
async def load_eps(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        return await message.answer("Faqat raqam kiriting!")
    await state.update_data(episodes=message.text)
    await AnimeAdd.next()
    await message.answer("💿 <b>Sifati (1080p):</b>")

@dp.message_handler(state=AnimeAdd.quality)
async def load_qual(message: types.Message, state: FSMContext):
    await state.update_data(quality=message.text)
    await AnimeAdd.next()
    await message.answer("🔢 <b>Kod bering (masalan: 733):</b>")

@dp.message_handler(state=AnimeAdd.code)
async def load_code(message: types.Message, state: FSMContext):
    await state.update_data(code=message.text)
    await AnimeAdd.next()
    await message.answer("📝 <b>Tavsif:</b>")

@dp.message_handler(state=AnimeAdd.description)
async def finish(message: types.Message, state: FSMContext):
    d = await state.get_data()
    code = d['code']
    anime_db[code] = {'photo': d['photo'], 'title': d['title'], 'eps': d['episodes']}
    
    caption = (f"🎬 <b>{d['title']}</b>\n\n"
               f"✒️ Janri : {d['genre']}\n"
               f"----------------------------------\n"
               f"📁 Qismlar : {d['episodes']}\n"
               f"📊 Holati : 🟢 Davom etmoqda\n"
               f"💿 Sifat : {d['quality']}\n"
               f"⚪️ Tili : O'zbek tilida\n"
               f"----------------------------------\n"
               f"🔢 Kod : {code}\n"
               f"📝 Tavsif: {message.text}")
    
    me = await bot.get_me()
    btn = InlineKeyboardMarkup().add(InlineKeyboardButton("📺 Tomosha qilish", url=f"https://t.me/{me.username}?start={code}"))
    
    await bot.send_photo(CHANNEL_ID, d['photo'], caption=caption, reply_markup=btn)
    await state.finish()
    await message.answer("✅ Post kanalga yuborildi!")

# --- FOYDALANUVCHILAR ---
@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    code = message.get_args()
    if code and code in anime_db:
        data = anime_db[code]
        markup = InlineKeyboardMarkup(row_width=4)
        count = int(data['eps'])
        btns = [InlineKeyboardButton(f"{i}", callback_data=f"ep_{i}") for i in range(1, count + 1)]
        markup.add(*btns)
        await message.answer_photo(data['photo'], caption=f"🍿 <b>{data['title']}</b>\n\nMarhamat, qismni tanlang:", reply_markup=markup)
    else:
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
        if message.from_user.id == ADMIN_ID: kb.add("➕ Anime qo'shish")
        await message.answer("<b>Xush kelibsiz!</b>\nAnime kodini yuboring yoki kanaldan 'Tomosha qilish'ni bosing.", reply_markup=kb)

@dp.callback_query_handler(text="recheck")
async def recheck(q: types.CallbackQuery):
    m = await bot.get_chat_member(CHANNEL_ID, q.from_user.id)
    if m.status in ['member', 'creator', 'administrator']:
        await q.message.delete()
        await q.message.answer("✅ Obuna tasdiqlandi! Endi botdan foydalanishingiz mumkin.")
    else:
        await q.answer("❌ Hali ham kanalga a'zo emassiz!", show_alert=True)

if __name__ == '__main__':
    # Pydroid 3-da ishlashi uchun executor
    executor.start_polling(dp, skip_updates=True)
