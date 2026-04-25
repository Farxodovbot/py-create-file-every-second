import os
import subprocess
from yt_dlp import YoutubeDL
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters

BOT_TOKEN = 8600136141:AAFwARoMN1tPQeF-ndFrdv3MX0UUIHF1gHk

# ---------------- START ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎧 MUSIC BOT READY\n\n"
        "📌 Qo'shiq yoz → video chiqadi\n"
        "📌 Video bos → menu chiqadi"
    )

# ---------------- YOUTUBE SEARCH ----------------
def search_youtube(query):
    ydl_opts = {"quiet": True, "default_search": "ytsearch5"}
    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(query, download=False)
        return info["entries"]

# ---------------- DOWNLOAD VIDEO ----------------
def download_video(url):
    ydl_opts = {"format": "best", "outtmpl": "video.%(ext)s"}
    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        return ydl.prepare_filename(info)

# ---------------- AUDIO EXTRACT ----------------
def extract_audio(video_path):
    audio_path = "music.mp3"
    subprocess.run([
        "ffmpeg", "-y",
        "-i", video_path,
        "-q:a", "0",
        "-map", "a",
        audio_path
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return audio_path

# ---------------- VIDEO MENU ----------------
def menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📄 Qo'shiq so'zlari", callback_data="lyrics")],
        [InlineKeyboardButton("🎬 Video", callback_data="video")],
        [InlineKeyboardButton("🎧 Audio", callback_data="audio")]
    ])

# ---------------- TEXT HANDLER ----------------
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.message.text

    results = search_youtube(query)

    buttons = []
    context.user_data["videos"] = {}
    context.user_data["last_query"] = query

    for i, r in enumerate(results):
        context.user_data["videos"][str(i)] = r["webpage_url"]

        buttons.append([
            InlineKeyboardButton(f"🎬 {r['title'][:30]}", callback_data=f"vid_{i}")
        ])

    await update.message.reply_text(
        "🎵 Video tanlang:",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

# ---------------- CALLBACK ----------------
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    data = q.data

    # 🎬 VIDEO TANLASH
    if data.startswith("vid_"):
        i = data.split("_")[1]
        url = context.user_data["videos"][i]

        video = download_video(url)

        context.user_data["last_video"] = video
        context.user_data["last_title"] = context.user_data["last_query"]

        await q.message.reply_video(
            video=open(video, "rb"),
            reply_markup=menu()
        )

    # 📄 LYRICS
    elif data == "lyrics":
        title = context.user_data["last_title"]
        await q.message.reply_text(f"📄 Lyrics topilmadi: {title}")

    # 🎬 VIDEO
    elif data == "video":
        video = context.user_data["last_video"]
        await q.message.reply_video(video=open(video, "rb"))

    # 🎧 AUDIO
    elif data == "audio":
        title = context.user_data["last_title"]

        search = title + " official audio"
        results = search_youtube(search)

        url = results[0]["webpage_url"]

        video = download_video(url)
        audio = extract_audio(video)

        await q.message.reply_audio(audio=open(audio, "rb"))

# ---------------- MAIN ----------------
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(CallbackQueryHandler(button))

    print("Bot ishladi...")
    app.run_polling()

if __name__ == "__main__":
    main()