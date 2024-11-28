import telebot
from telebot.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
import yt_dlp
import os

# Создаем бота с вашим API токеном
bot = telebot.TeleBot("7569838293:AAG7QpGaESSwsQD84DJHcAYWV5KrQ3w8f-Y")

# Приветственное сообщение
@bot.message_handler(commands=['start'])
def send_welcome(message: Message):
    bot.reply_to(message, "👋 Привет! Отправь мне ссылку на видео из TikTok или YouTube, и я помогу тебе скачать его.\n")

# Обработка сообщений с TikTok или YouTube ссылками
@bot.message_handler(
    func=lambda message: "tiktok.com" in message.text or "youtube.com" in message.text or "youtu.be" in message.text)
def handle_video_request(message: Message):
    url = message.text.strip()
    bot.send_message(message.chat.id, "Выберите формат загрузки:", reply_markup=create_format_buttons(url))

# Создание кнопок для выбора формата
def create_format_buttons(url):
    markup = InlineKeyboardMarkup()
    markup.row_width = 2
    markup.add(InlineKeyboardButton("🎥 Видео", callback_data=f"video|{url}"),
               InlineKeyboardButton("🎶 Аудио", callback_data=f"audio|{url}"))
    return markup

# Обработка нажатия кнопок
@bot.callback_query_handler(func=lambda call: True)
def handle_format_selection(call):
    action, url = call.data.split('|')
    bot.answer_callback_query(call.id)  # Подтверждаем нажатие кнопки сразу

    if action == "video":
        bot.send_message(call.message.chat.id, "⏳ Начинаю загрузку видео...")
        download_and_send_media(call.message.chat.id, url, media_type='video')
    elif action == "audio":
        bot.send_message(call.message.chat.id, "⏳ Начинаю загрузку аудио...")
        download_and_send_media(call.message.chat.id, url, media_type='audio')

# Загрузка и отправка медиа с обработкой ошибок и повторными попытками
def download_and_send_media(chat_id, url, media_type='video', retries=3):
    if media_type == 'video':
        ydl_opts = {
            'format': 'best[ext=mp4]/best[ext=webm]',  # Выбираем одиночный видеофайл в mp4, если доступен
            'outtmpl': 'downloads/%(title)s.%(ext)s',
            'socket_timeout': 60  # Увеличиваем тайм-аут
        }
    else:  # media_type == 'audio'
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': 'downloads/%(title)s.%(ext)s',
            'socket_timeout': 60  # Увеличиваем тайм-аут
        }

    for attempt in range(retries):
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)

                # Отправляем файл в чат
                with open(filename, 'rb') as file:
                    if media_type == 'video':
                        bot.send_video(chat_id, file, caption="🎥 Вот твое видео!")
                    else:
                        bot.send_audio(chat_id, file, caption="🎶 Вот твое аудио!")

                # Удаляем скачанный файл
                os.remove(filename)
                return  # Успешно завершили, выходим из функции

        except Exception as e:
            if attempt < retries - 1:
                bot.send_message(chat_id, f"❌ Ошибка при загрузке, пробую снова... ({attempt + 1}/{retries})")
            else:
                bot.send_message(chat_id, f"❌ Произошла ошибка: {str(e)}")

# Запуск бота
if __name__ == "__main__":
    if not os.path.exists('downloads'):
        os.makedirs('downloads')

    print("Бот запущен")
    bot.infinity_polling()
