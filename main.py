import telebot

BOT_TOKEN = "توکن_ربات_تو"
bot = telebot.TeleBot(BOT_TOKEN)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "سلام! اسم آهنگ رو بفرست تا ترجمشو + خود آهنگ بفرستم برات.")

@bot.message_handler(func=lambda m: True)
def process_song_request(message):
    song_name = message.text
    bot.reply_to(message, f"آهنگ «{song_name}» رو دریافت کردم. دارم روش کار می‌کنم…")
    # اینجا بعداً منطق دانلود + ترجمه اضافه می‌شه

bot.infinity_polling()
