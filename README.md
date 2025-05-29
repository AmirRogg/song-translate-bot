# song-translate-bot
import telebot

BOT_TOKEN = "توکن رباتت اینجاست"
bot = telebot.TeleBot(BOT_TOKEN)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "سلام! اسم آهنگ رو بفرست تا ترجمشو + خود آهنگ بفرستم برات.")

@bot.message_handler(func=lambda m: True)
def echo_all(message):
    bot.reply_to(message, f"آهنگ '{message.text}' رو دریافت کردم. در حال پردازش...")

bot.infinity_polling()
