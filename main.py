import os
import telebot
import lyricsgenius
from googletrans import Translator
import yt_dlp
from io import BytesIO

# 1) گرفتن توکن امن از Env Var
BOT_TOKEN = os.getenv('BOT_TOKEN')
GENIUS_TOKEN = os.getenv('GENIUS_TOKEN')

if not BOT_TOKEN:
    raise ValueError("🔴 BOT_TOKEN در Env Vars روی Render ست نشده یا خالیه!")

# 2) راه‌اندازی بات و کلاینت Genius
bot = telebot.TeleBot(BOT_TOKEN)
translator = Translator()
genius = lyricsgenius.Genius(GENIUS_TOKEN) if GENIUS_TOKEN else None

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message,
        "👋 سلام! اسم آهنگ رو بفرست تا متن+ترجمه+آهنگ+کاور رو برات بفرستم."
    )

@bot.message_handler(func=lambda m: True)
def handle_song(message):
    song_name = message.text.strip()
    chat_id = message.chat.id
    bot.send_message(chat_id, f"⏳ در حال پردازش «{song_name}» …")

    try:
        # متن انگلیسی
        lyrics = genius.search_song(song_name).lyrics if genius else "متن در دسترس نیست."
        # ترجمه فارسی
        translation = translator.translate(lyrics, src='en', dest='fa').text

        # دانلود صوت
        ydl_opts = {
            'format': 'bestaudio/best',
            'quiet': True,
            'noplaylist': True,
            'outtmpl': '/tmp/audio.%(ext)s'
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"ytsearch:{song_name}", download=True)
            entry = info['entries'][0]
            file_path = ydl.prepare_filename(entry)

        # ارسال متن+ترجمه
        bot.send_message(chat_id,
            f"🎵 *{song_name}*\n\n📝 متن انگلیسی:\n{lyrics}\n\n🔁 ترجمه فارسی:\n{translation}",
            parse_mode='Markdown'
        )

        # ارسال کاور
        if genius:
            cover_url = genius.search_song(song_name).song_art_image_url
            bot.send_photo(chat_id, cover_url)

        # ارسال فایل صوتی
        with open(file_path, 'rb') as audio:
            bot.send_audio(chat_id, audio=audio, title=song_name)

    except Exception as e:
        bot.send_message(chat_id, "❌ مشکلی پیش اومد، دوباره تلاش کن.")
        print("Error:", e)

bot.infinity_polling()
