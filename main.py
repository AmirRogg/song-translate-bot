import os
import telebot
import lyricsgenius
from googletrans import Translator
import yt_dlp
from flask import Flask, request
from telebot import types

# ---------- Config ----------
BOT_TOKEN = os.getenv('BOT_TOKEN')
GENIUS_TOKEN = os.getenv('GENIUS_TOKEN')
WEBHOOK_BASE_URL = os.getenv('WEBHOOK_URL')
CHANNEL_USERNAME = '@hiphopthe90s'  # کانالی که کاربر باید عضو باشه

if not BOT_TOKEN:
    raise ValueError("🔴 BOT_TOKEN در متغیرهای محیطی (Env Vars) ست نشده!")
if not WEBHOOK_BASE_URL:
    raise ValueError("🔴 WEBHOOK_URL در متغیرهای محیطی (Env Vars) ست نشده!")

bot = telebot.TeleBot(BOT_TOKEN)
translator = Translator()
genius = lyricsgenius.Genius(GENIUS_TOKEN) if GENIUS_TOKEN else None

# ---------- Helper: چک کردن عضویت در کانال ----------
def check_channel_membership(user_id):
    try:
        member = bot.get_chat_member(CHANNEL_USERNAME, user_id)
        # عضو اگر نبودند یا وضعیت Left یا Kicked بود، False می‌شه
        if member.status in ['left', 'kicked']:
            return False
        return True
    except Exception as e:
        print(f"Error checking membership: {e}")
        # به هر دلیل اگه نتونستیم چک کنیم، فرض می‌کنیم نیست
        return False

# ---------- Start & Welcome + Button for Search ----------
@bot.message_handler(commands=['start'])
def send_welcome(message):
    chat_id = message.chat.id
    user_id = message.from_user.id

    if not check_channel_membership(user_id):
        markup = types.InlineKeyboardMarkup()
        join_btn = types.InlineKeyboardButton(text="عضویت در کانال", url=f"https://t.me/{CHANNEL_USERNAME.strip('@')}")
        markup.add(join_btn)
        bot.send_message(chat_id, f"👋 سلام!\nبرای استفاده از ربات باید اول عضو کانال ما بشی:\n{CHANNEL_USERNAME}", reply_markup=markup)
        return

    # دکمه سرچ به عنوان کیبورد
    markup = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    btn_search = types.KeyboardButton("🔎 جستجوی آهنگ")
    markup.add(btn_search)

    bot.send_message(chat_id,
                     "👋 سلام! اسم آهنگ رو بفرست تا متن + ترجمه + آهنگ + کاور رو برات بفرستم.",
                     reply_markup=markup)

# ---------- Handle Text & Search ----------
@bot.message_handler(func=lambda m: True)
def handle_song(message):
    chat_id = message.chat.id
    user_id = message.from_user.id

    # چک عضویت
    if not check_channel_membership(user_id):
        markup = types.InlineKeyboardMarkup()
        join_btn = types.InlineKeyboardButton(text="عضویت در کانال", url=f"https://t.me/{CHANNEL_USERNAME.strip('@')}")
        markup.add(join_btn)
        bot.send_message(chat_id, f"❗ برای استفاده از ربات باید عضو کانال بشی:\n{CHANNEL_USERNAME}", reply_markup=markup)
        return

    # اگر کاربر دکمه "جستجوی آهنگ" زد، بگو اسمشو بفرسته
    if message.text == "🔎 جستجوی آهنگ":
        bot.send_message(chat_id, "لطفا اسم آهنگ رو بفرست تا جستجو کنم.")
        return

    song_name = message.text.strip()
    bot.send_message(chat_id, f"⏳ در حال پردازش آهنگ: «{song_name}»...")

    try:
        # جستجوی آهنگ
        song = genius.search_song(song_name) if genius else None
        if not song:
            bot.send_message(chat_id, "⚠️ آهنگ پیدا نشد، لطفا اسم دقیق‌تر یا متفاوتی بفرست.")
            return

        lyrics = song.lyrics or "متن در دسترس نیست."
        # ترجمه
        translation = translator.translate(lyrics, src='en', dest='fa').text

        # دانلود آهنگ از یوتیوب
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

        # ارسال کاور
        if song.song_art_image_url:
            bot.send_photo(chat_id, song.song_art_image_url)

        # ارسال متن + ترجمه
        bot.send_message(chat_id,
                         f"🎵 *{song.title}* توسط *{song.artist}*\n\n📝 متن انگلیسی:\n{lyrics}\n\n🔁 ترجمه فارسی:\n{translation}",
                         parse_mode='Markdown')

        # ارسال آهنگ
        with open(file_path, 'rb') as audio:
            bot.send_audio(chat_id, audio, title=song.title)

        # حذف فایل دانلود شده (اختیاری)
        os.remove(file_path)

    except Exception as e:
        print(f"🚨 Error: {e}")
        bot.send_message(chat_id, "❌ یه مشکلی پیش اومد، دوباره تلاش کن.")

# ---------- Flask App برای webhook ----------
app = Flask(__name__)

@app.route('/')
def home():
    return '🤖 Bot is alive!'

@app.route('/' + BOT_TOKEN, methods=['POST'])
def webhook():
    update = telebot.types.Update.de_json(request.stream.read().decode("utf-8"))
    bot.process_new_updates([update])
    return 'OK', 200

# ---------- Start Server & Set Webhook ----------
if __name__ == '__main__':
    import time
    time.sleep(3)  # صبر کن سرور کامل بالا بیاد

    bot.remove_webhook()
    full_webhook_url = f"{WEBHOOK_BASE_URL.rstrip('/')}/{BOT_TOKEN}"
    bot.set_webhook(url=full_webhook_url)
    print(f"✅ Webhook set: {full_webhook_url}")

    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
