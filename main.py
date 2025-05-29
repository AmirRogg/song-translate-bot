import os
import telebot
import lyricsgenius
from googletrans import Translator
import yt_dlp
from io import BytesIO
from PIL import Image

# گرفتن توکن امن از Environment Variable
BOT_TOKEN = os.getenv(7810040326:AAHjNWmwxHCfNDh_bK4fkB_cx8C7mh3xYuc)
GENIUS_TOKEN = os.getenv('GENIUS_TOKEN')  # اگر بعداً نیاز شد
if not BOT_TOKEN:
    raise ValueError("🔴 BOT_TOKEN در Env Vars تنظیم نشده!")

bot = telebot.TeleBot(BOT_TOKEN)
genius = lyricsgenius.Genius(GENIUS_TOKEN) if GENIUS_TOKEN else None
translator = Translator()

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "سلام! اسم آهنگ رو بفرست تا متن+ترجمه+خود آهنگ رو برات بفرستم.")

@bot.message_handler(func=lambda m: True)
def handle_song(message):
    song_name = message.text
    chat_id = message.chat.id
    bot.send_message(chat_id, f"⏳ دارم آهنگ «{song_name}» رو آماده می‌کنم…")
    # … (بقیه‌ی منطق همون‌جوری که قبل بود) …

bot.infinity_polling()
