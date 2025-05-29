import os
import telebot
import lyricsgenius
from googletrans import Translator
import yt_dlp
from flask import Flask, request
from telebot import types
import logging

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

# ---------- Setup logging ----------
logging.basicConfig(filename='bot_errors.log', level=logging.ERROR,
                    format='%(asctime)s %(levelname)s %(message)s')

# ---------- Helper: چک کردن عضویت در کانال ----------
def check_channel_membership(user_id):
    try:
        member = bot.get_chat_member(CHANNEL_USERNAME, user_id)
        if member.status in ['left', 'kicked']:
            return False
        return True
    except Exception as e:
        logging.error(f"Error checking membership for user {user_id}: {e}")
        return False

# ---------- دکمه عضویت با لینک واضح ----------
def send_join_channel_message(chat_id):
    join_url = f"https://t.me/{CHANNEL_USERNAME.strip('@')}"
    markup = types.InlineKeyboardMarkup()
    join_btn = types.InlineKeyboardButton(text="👉 عضو شدن در کانال", url=join_url)
    markup.add(join_btn)
    bot.send_message(chat_id,
                     f"❗ برای استفاده از ربات باید اول عضو کانال ما بشی:\n{join_url}",
                     reply_markup=markup)

# ---------- Start & Welcome + Button for Search ----------
@bot.message_handler(commands=['start'])
def send_welcome(message):
    chat_id = message.chat.id
    user_id = message.from_user.id

    if not check_channel_membership(user_id):
        send_join_channel_message(chat_id)
        return

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

    if not check_channel_membership(user_id):
        send_join_channel_message(chat_id)
        return

    if message.text == "🔎 جستجوی آهنگ":
        bot.send_message(chat_id, "لطفا اسم آهنگ رو بفرست تا جستجو کنم.")
        return

    song_name = message.text.strip()
    bot.send_message(chat_id, f"⏳ در حال پردازش آهنگ: «{song_name}»...")

    file_path = None
    try:
        # جستجوی آهنگ
        song = genius.search_song(song_name) if genius else None
        if not song:
            bot.send_message(chat_id, "⚠️ آهنگ پیدا نشد، لطفا اسم دقیق‌تر یا متفاوتی بفرست.")
            return

        lyrics = song.lyrics or "متن در دسترس نیست."
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
                         f"🎵 *{song.title}* توسط *{song.artist}*\n\n📝 متن انگلیسی:\n{lyrics}\n\n🔁 تر
