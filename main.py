import os
import telebot
import lyricsgenius
from googletrans import Translator
import yt_dlp
from flask import Flask
import threading

# ---------- Config ----------
BOT_TOKEN = os.getenv('BOT_TOKEN')
GENIUS_TOKEN = os.getenv('GENIUS_TOKEN')

if not BOT_TOKEN:
    raise ValueError("🔴 BOT_TOKEN در Env Vars روی Render ست نشده یا خالیه!")

bot = telebot.TeleBot(BOT_TOKEN)
translator = Translator()
genius = lyricsgenius.Genius(GENIUS_TOKEN) if GENIUS_TOKEN else None

# ---------- Bot Logic ----------
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "👋 سلام! اسم آهنگ رو بفرست تا متن+ترجمه+آهنگ+کاور رو برات بفرستم.")

@bot.message_handler(func=lambda m: True)
def handle_song(message):
    song_name = message.text.strip()
    chat_id = message.chat.id
    bot.send_message(chat_id, f"⏳ در حال پردازش «{song_name}» …")

    try:
        # متن آهنگ
        song = genius.search_song(song_name) if genius else None
        lyrics = song.lyrics if song else "متن در دسترس نیست."

        # ترجمه
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

        # ارسال متن و ترجمه
        bot.send_message(chat_id,
            f"🎵 *{song_name}*\n\n📝 متن انگلیسی:\n{lyrics}\n\n🔁 ترجمه فارسی:\n{translation}",
            parse_mode='Markdown'
        )

        # کاور
        if song:
            cover_url = song.song_art_image_url
            bot.send_photo(chat_id, cover_url)

        # فایل صوتی
        with open(file_path, 'rb') as audio:
            bot.send_audio(chat_id, audio=audio, title=song_name)

    except Exception as e:
        bot.send_message(chat_id, "❌ مشکلی پیش اومد، دوباره تلاش کن.")
        print("Error:", e)

# ---------- Flask Web Server for Render ----------
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running, king 👑"

def run_flask():
    port = int(os.environ.get('PORT', 10000))  # پورت پیش‌فرض
    app.run(host='0.0.0.0', port=port)

# ---------- Start Bot & Web ----------
if __name__ == '__main__':
    threading.Thread(target=run_flask).start()  # اجرای Flask تو ترد جدا
    bot.infinity_polling()  # اجرای ربات تلگرام
