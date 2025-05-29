import os
import telebot
import lyricsgenius
from googletrans import Translator
import yt_dlp
from flask import Flask, request

# ---------- Config ----------
BOT_TOKEN = os.getenv('BOT_TOKEN')
GENIUS_TOKEN = os.getenv('GENIUS_TOKEN')
WEBHOOK_BASE_URL = os.getenv('WEBHOOK_URL')

if not BOT_TOKEN:
    raise ValueError("🔴 BOT_TOKEN در متغیرهای محیطی (Env Vars) ست نشده!")

if not WEBHOOK_BASE_URL:
    raise ValueError("🔴 WEBHOOK_URL در متغیرهای محیطی (Env Vars) ست نشده!")

bot = telebot.TeleBot(BOT_TOKEN)
translator = Translator()
genius = lyricsgenius.Genius(GENIUS_TOKEN) if GENIUS_TOKEN else None

# ---------- Bot Logic ----------
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "👋 سلام! اسم آهنگ رو بفرست تا متن + ترجمه + آهنگ + کاور رو برات بفرستم.")

@bot.message_handler(func=lambda m: True)
def handle_song(message):
    song_name = message.text.strip()
    chat_id = message.chat.id
    bot.send_message(chat_id, f"⏳ در حال پردازش «{song_name}»...")

    try:
        song = genius.search_song(song_name) if genius else None
        lyrics = song.lyrics if song else "متن در دسترس نیست."
        translation = translator.translate(lyrics, src='en', dest='fa').text

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

        bot.send_message(chat_id,
            f"🎵 *{song_name}*\n\n📝 متن انگلیسی:\n{lyrics}\n\n🔁 ترجمه فارسی:\n{translation}",
            parse_mode='Markdown'
        )

        if song:
            cover_url = song.song_art_image_url
            bot.send_photo(chat_id, cover_url)

        with open(file_path, 'rb') as audio:
            bot.send_audio(chat_id, audio=audio, title=song_name)

    except Exception as e:
        bot.send_message(chat_id, "❌ یه مشکلی پیش اومد، دوباره تلاش کن.")
        print("🚨 Error:", e)

# ---------- Flask App ----------
app = Flask(__name__)

@app.route('/')
def home():
    return '🤖 Bot is alive!'

@app.route('/' + BOT_TOKEN, methods=['POST'])
def webhook():
    update = telebot.types.Update.de_json(request.stream.read().decode("utf-8"))
    bot.process_new_updates([update])
    return 'OK', 200

# ---------- Start ----------
if __name__ == '__main__':
    import time
    time.sleep(3)

    bot.remove_webhook()
    full_webhook_url = f"{WEBHOOK_BASE_URL.rstrip('/')}/{BOT_TOKEN}"
    bot.set_webhook(url=full_webhook_url)
    print(f"✅ Webhook set: {full_webhook_url}")

    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
