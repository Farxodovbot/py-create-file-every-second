import os
import yt_dlp
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
from shazamio import Shazam

TOKEN = "8717890222:AAEb501qDuzVglFzEKM3wAF-YwbSq9-1jDc"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "🔥 Assalomu alaykum. @Mixsavedibot ga Xush kelibsiz.\n"
        "Havola yuboring yoki musiqa topish uchun ovozli xabar yuboring!"
    )
    await update.message.reply_text(text)

async def handle_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    if "http" not in url: return
    
    keyboard = [
        [InlineKeyboardButton("🎬 360p", callback_data=f"360|{url}"), 
         InlineKeyboardButton("🎬 720p", callback_data=f"720|{url}")],
        [InlineKeyboardButton("🎵 Audio (MP3)", callback_data=f"audio|{url}")]
    ]
    await update.message.reply_text("Sifatni tanlang:", reply_markup=InlineKeyboardMarkup(keyboard))

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    quality, url = query.data.split("|")
    await query.answer()
    
    msg = await query.message.reply_text("⏳ Yuklanmoqda...")

    try:
        # Render-da xato bermasligi uchun soddalashtirilgan sozlamalar
        ydl_opts = {
            'format': 'best' if quality != "audio" else 'bestaudio',
            'outtmpl': f'file_{query.from_user.id}.%(ext)s',
            'no_warnings': True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)

        if quality == "audio":
            await query.message.reply_audio(audio=open(filename, 'rb'), caption="@Mixsavedibot")
        else:
            await query.message.reply_video(video=open(filename, 'rb'), caption="@Mixsavedibot")
        
        await msg.delete()
        if os.path.exists(filename): os.remove(filename)
    except Exception:
        await msg.edit_text("❌ Xato: Fayl juda katta yoki Render bu formatni qo'llamaydi.")

async def handle_shazam(update: Update, context: ContextTypes.DEFAULT_TYPE):
    status = await update.message.reply_text("🔍 Qidirilmoqda...")
    try:
        file = await update.message.voice.get_file()
        path = "shazam.ogg"
        await file.download_to_drive(path)
        
        shazam = Shazam()
        out = await shazam.recognize_song(path)
        if out['matches']:
            t = out['track']
            await status.edit_text(f"✅ Topildi: {t['title']} - {t['subtitle']}")
        else:
            await status.edit_text("❌ Topilmadi.")
        os.remove(path)
    except:
        await status.edit_text("❌ Shazam xatosi.")

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler('start', start))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_link))
    app.add_handler(MessageHandler(filters.VOICE | filters.AUDIO, handle_shazam))
    app.add_handler(CallbackQueryHandler(button_callback))
    app.run_polling()
P