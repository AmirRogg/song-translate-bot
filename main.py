import os
import telebot
import lyricsgenius
from googletrans import Translator
import yt_dlp
from io import BytesIO

# ——————————————
# 1) گرفتن توکن از Environment Variable
# ——————————————
BOT_TOKEN = os.getenv('BOT_TOKEN')
GENIUS_TOKEN = os.getenv('GENIUS_TOKEN')  # در صورت استفاده از Genius API

if not BOT_TOKEN:
    raise ValueError("🔴 لطفاً BOT_TOKEN را در Env Vars روی Render ست کنید!")

# ——————————————
# 2) راه‌اندازی بات و کلاینت‌ها
# ——————————————
bot = telebot.TeleBot(BOT_TOKEN)
translator = Translator()
genius = lyricsgenius.Genius(GENIUS_TOKEN) if GENIUS_TOKEN else None

# ——————————————
# 3) هندلر دستور /start
# ——————————————
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(
        message,
        "👋 سلام! اسم آهنگ مورد نظرت رو بفرست تا:\n"
        "1️⃣ متن انگلیسی\n"
        "2️⃣ ترجمه فارسی\n"
        "3️⃣ فایل صوتی + کاور\n\n"
        "رو برات بفرستم!"
    )

# ——————————————
# 4) هندلر دریافت نام آهنگ
# ——————————————
@bot.message_handler(func=lambda m: True)
def handle_song(message):
    song_name = message.text.strip()
    chat_id = message.chat.id

    bot.send_message(chat_id, f"⏳ دارم آهنگ «{song_name}» رو آماده می‌کنم…")

    try:
        # ——————————————
        # 4.1) گرفتن متن آهنگ
        # ——————————————
        if genius:
            song = genius.search_song(song_name)
            lyrics = song.lyrics
        else:
            lyrics = "⚠️ Genius API ست نشده؛ متن آهنگ در دسترس نیست."

        # ——————————————
        # 4.2) ترجمه فارسی
        # ——————————————
        translation = translator.translate(lyrics, src='en', dest='fa').text

        # ——————————————
        # 4.3) دانلود فایل صوتی از یوتیوب
        # ——————————————
        ydl_opts = {
            'format': 'bestaudio/best',
            'quiet': True,
            'noplaylist': True,
            'outtmpl': '/tmp/audio.%(ext)s'
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"ytsearch:{song_name}", download=True)
            # فایل اول سرچ
            entry = info['entries'][0]
            file_path = ydl.prepare_filename(entry)

        # ——————————————
        # 4.4) دانلود کاور (اگر لینک موجود باشد)
        # ——————————————
        if genius and song.song_art_image_url:
            # ساده‌ترین حالت: فقط ارسال URL کاور به کاربر
            cover_url = song.song_art_image_url
        else:
            cover_url = None

        # ——————————————
        # 4.5) ارسال متن + ترجمه
        # ——————————————
        text = (
            f"🎵 *{song.title if genius else song_name}*\n\n"
            f"📝 _Lyrics:_\n{lyrics}\n\n"
            f"🔁 _Translation:_\n{translation}"
        )
        bot.send_message(chat_id, text, parse_mode='Markdown')

        # ——————————————
        # 4.6) ارسال کاور (در صورت وجود) و فایل صوتی
        # ——————————————
        if cover_url:
            bot.send_photo(chat_id, cover_url)

        with open(file_path, 'rb') as audio:
            bot.send_audio(
                chat_id,
                audio=audio,
                title=song.title if genius else song_name,
                performer=song.artist if genius else None
            )

    except Exception as e:
        bot.send_message(chat_id, "❌ اوه! مشکلی پیش اومد. دوباره تلاش کن.")
        print(f"Error in handle_song: {e}")

# ——————————————
# 5) شروع Polling
# ——————————————
bot.infinity_polling()
