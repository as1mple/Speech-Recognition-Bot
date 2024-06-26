import base64
import os
import sys
from datetime import datetime
from io import BytesIO

import telebot
from telebot import types
from loguru import logger

from modules.audio_handler import AudioProcessor
from modules.database_manager import get_files_by_chat_id, get_save_data, save_to_database
from setting import SERVER_HOST, SERVER_PORT, MAX_CAPTION_LENGTH, TOKEN

logger.configure(
    handlers=[
        {"sink": sys.stderr, "level": "DEBUG"},
        dict(
            sink="logs/debug.log",
            format="{time} {level} {message}",
            level="DEBUG",
            rotation="1 weeks",
        ),
    ]
)

LANGUAGES_MAP = {
    "українська": "uk-UA",
    "російська": "ru-RU",
    "англійська": "en-US",
    "німецька": "de-DE",
}

CFG = {"language": "uk-UA"}
utcnow = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ")

bot = telebot.TeleBot(TOKEN)
audio_processor = AudioProcessor()
logger.info("Bot successfully launched")


@bot.message_handler(commands=["start", "help", "search"])
def handle_start_help(message: telebot.types.Message):
    """Handle start and help commands"""
    logger.info(f"User [{message.chat.username} ~ {message.chat.id}] => asked for help")

    if message.text == "/start":
        bot.send_message(message.chat.id, "Щоб розпочати роботу бота привітайтесь з ним :=)")
        bot.send_message(message.chat.id, "Для ознайомлення з функіоналом напишіть /help")

    elif message.text == "/help":
        bot.send_message(
            message.chat.id, "Даний бот був розрозроблений для розпізнавання голосових повідомлен."
        )

        bot.send_message(
            message.chat.id,
            "Для того, щоб скористатися функціоналом \n"
            "=> Вам потрiбно  привітатись з ботом "
            "на українською, англійською чи російською мовою \n=> Вибрати мову для розпізнавання.\n"
            "=> Для зміни мови розпізнавання потрібно повторно привітатись.",
        )

    elif message.text == "/search":
        bot.send_message(
            message.chat.id,
            "Надішліть часовий проміжок за який потрібно знайти записи. Слід зауважити час збережений за Coordinated Universal Time (UTC). Приклад формату:",
        )

        bot.send_message(
            message.chat.id, "2021-12-18T12:41:05.488441Z 2021-12-18T12:41:05.488441Z"
        )
        bot.send_message(message.chat.id, "Введіть часовий проміжок (або chat id):")

        bot.register_next_step_handler(message, search_files)

    elif word_search(message.text):
        say_hello(message)

    else:
        bot.send_message(
            message.chat.id,
            "Для того, щоб скористатися функціоналом \n"
            "=> Вам потрiбно  привітатись з ботом "
            "на українською, англійською чи російською мовою \n=> Вибрати мову для розпізнавання.\n"
            "=> Для зміни мови розпізнавання потрібно повторно привітатись.",
        )


def search_files(message: telebot.types.Message):
    """Handle search files command"""
    logger.info(
        f"User [{message.chat.username} ~ {message.chat.id}] => search files by time interval or chat_id => {message.text}"
    )

    chat_id, time_from, time_to = None, None, None
    try:
        if len(message.text.split()) == 1:
            chat_id = int(message.text)
        else:
            time_from, time_to = message.text.split()
    except Exception:
        bot.send_message(
            message.chat.id,
            "Неправильний формат часу. Слід зауважити час збережений за "
            "Coordinated Universal Time (UTC). Приклад формату:",
        )
        bot.send_message(
            message.chat.id, "2021-12-18T12:41:05.488441Z 2021-12-18T12:41:05.488441Z"
        )
        bot.send_message(message.chat.id, "Введіть часовий проміжок ще раз:")

        logger.error(f"User [{message.chat.username} ~ {message.chat.id}] => Invalid time format => {message.text}")
        bot.register_next_step_handler(message, search_files)

    else:
        markup = types.ReplyKeyboardMarkup()

        markup.row("Так", "Ні")
        bot.send_message(
            message.chat.id,
            "Виконувати пошук серед користувачів, які надали анотацію до аудіозапису?",
            reply_markup=markup,
        )

        bot.register_next_step_handler(message, run_search_files, chat_id, time_from, time_to)


def run_search_files(message: telebot.types.Message, chat_id, time_from, time_to):
    collection_name = "user" if message.text.lower() == "так" else "undefined_user"
    logger.info(f"User [{message.chat.username} ~ {message.chat.id}] => Asked search files with => {collection_name}")

    try:
        if chat_id:
            result = get_files_by_chat_id(SERVER_HOST, SERVER_PORT, collection_name, chat_id)[
                "result"
            ]
        else:
            result = get_save_data(SERVER_HOST, SERVER_PORT, collection_name, time_from, time_to)["result"]

        bot.send_message(
            message.chat.id,
            f"Знайдено записів: {len(result)}",
            reply_markup=telebot.types.ReplyKeyboardRemove(),
        )
        logger.info(f"User [{message.chat.username} ~ {message.chat.id}] => Find files => {len(result)}")

        for data in result:
            user_id = data["user_id"]
            time = data["timestamp"]["$date"]
            decode_bytes = base64.b64decode(data["speech_bytes"])
            caption = (
                f'description ~ {data["description"]} \n'
                f"time ~ {time} \nuser_id ~ {user_id} \n"
                f'language ~ {data["language"]} \n'
                f'text ~ {data["text"]}'
            )

            if len(caption) > MAX_CAPTION_LENGTH:
                preview_message = bot.send_voice(
                    message.chat.id,
                    decode_bytes,
                    caption=caption[:MAX_CAPTION_LENGTH],
                )

                remaining_caption = caption[MAX_CAPTION_LENGTH:]
                while len(remaining_caption) > 0:
                    part_caption = remaining_caption[:MAX_CAPTION_LENGTH]
                    bot.reply_to(preview_message, part_caption)
                    remaining_caption = remaining_caption[MAX_CAPTION_LENGTH:]

            else:
                bot.send_voice(
                    message.chat.id,
                    decode_bytes,
                    caption=caption,
                )

    except Exception as e:
        bot.send_message(
            message.chat.id,
            "Помилка з'єднання з сервером. Повідомте про це розробників.",
        )
        logger.error(f"User [{message.chat.username} ~ {message.chat.id}] => {e}")


def is_help(message: telebot.types.Message):
    """Check if message is help command"""
    if not message == "/help":
        bot.register_next_step_handler(message, say_hello)


@bot.message_handler(content_types=["voice"])
def voice_processing(message: telebot.types.Message):
    """Processing voice message"""
    logger.info(f"User [{message.chat.username} ~ {message.chat.id}] => Sent audio message")

    file_info = bot.get_file(message.voice.file_id)
    downloaded_file = bot.download_file(file_info.file_path)

    if ADMIN_CHAT_ID := os.getenv("ADMIN_CHAT_ID"):
        bot.send_audio(
            ADMIN_CHAT_ID,
            downloaded_file,
            caption=f"username ~ {message.chat.username} \nchat_id ~ {message.chat.id}",
        )

    try:
        # text = audio_processor.process_with_google_speech(BytesIO(downloaded_file), CFG["language"], logger, message)
        text = audio_processor.process_with_whisper(BytesIO(downloaded_file))
    except Exception as e:
        bot.send_message(
            message.chat.id,
            "На етапі розпізнавання аудіозапису сталася помилка - сповістіть про це розробників",
        )
        logger.error(f"User [{message.chat.username} ~ {message.chat.id}] ~ Recognition-Error => {e}")

    else:
        if not text:
            bot.send_message(
                message.chat.id,
                "Текст невдалося розпізнати, спробуйте записати аудіозапис у менш шумному місці.",
            )
        else:
            bot.send_message(message.chat.id, text)
            logger.info(f"User [{message.chat.username} ~ {message.chat.id}] => Recognition text => {text}")

            markup = types.ReplyKeyboardMarkup()

            markup.row("Так", "Ні")
            bot.send_message(
                message.chat.id,
                "Зберегти отримані дані до Бази Знань?",
                reply_markup=markup,
            )

            bot.register_next_step_handler(message, is_save_to_db, text, downloaded_file)


def is_save_to_db(message: telebot.types.Message, text, downloaded_file):
    logger.info(f"User [{message.chat.username} ~ {message.chat.id}] => Asked for save data => {message.text}")

    time_utc = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ")

    if message.text and message.text.lower() == "так":
        bot.send_message(
            message.chat.id,
            "Напишіть опис до файлу або його id",
            reply_markup=telebot.types.ReplyKeyboardRemove(),
        )

        bot.register_next_step_handler(message, input_description, text, downloaded_file, time_utc)

    else:
        save_to_db_without_description(message, text, downloaded_file, time_utc)

        bot.send_message(
            message.chat.id,
            "Запишіть голосове повідомлення або надішліть файл формату wav.",
            reply_markup=telebot.types.ReplyKeyboardRemove(),
        )


def save_to_db_without_description(
    message: telebot.types.Message, text, downloaded_file, time_utc
) -> None:
    """Save to database without description"""

    logger.info(f"User [{message.chat.username} ~ {message.chat.id}] => Input description => None")

    try:
        status = save_to_database(
            SERVER_HOST,
            SERVER_PORT,
            "undefined_user",
            message.chat.id,
            time_utc,
            text,
            CFG["language"],
            downloaded_file,
            message.text,
        )

        logger.info(f"User [{message.chat.username} ~ {message.chat.id}] ~ Request-Status => {status}")
    except Exception as e:
        logger.error(f"User [{message.chat.username} ~ {message.chat.id}] ~ Save-Error => {e}")


def input_description(message: telebot.types.Message, text, downloaded_file, time_utc):
    """Input description for file and save to db"""
    logger.info(f"User [{message.chat.username} ~ {message.chat.id}] => Input description => {message.text}")
    save_config("description", message.text, message)

    try:
        status = save_to_database(
            SERVER_HOST,
            SERVER_PORT,
            "user",
            message.chat.id,
            time_utc,
            text,
            CFG["language"],
            downloaded_file,
            message.text,
        )

        bot.send_message(
            message.chat.id,
            "✅ Інформація успішно збережена до Бази Знань.",
        )
        logger.info(f"User [{message.chat.username} ~ {message.chat.id}] ~ Request-Status => {status}")
    except Exception as e:
        logger.error(f"User [{message.chat.username} ~ {message.chat.id}] ~ Save-Error => {e}")
        bot.send_message(
            message.chat.id,
            "❌ На етапі збереження даних сталася помилка - сповістіть про це розробників",
        )

    bot.send_message(
        message.chat.id,
        "Запишіть голосове повідомлення або надішліть файл формату wav.",
        reply_markup=telebot.types.ReplyKeyboardRemove(),
    )


@bot.message_handler(func=lambda message: True, content_types=["text"])
def event_handler(message: telebot.types.Message):
    """Handle all messages"""
    logger.info(f"User [{message.chat.username} ~ {message.chat.id}] => sent a message => {message.text}")
    if word_search(message.text):
        say_hello(message)


def say_hello(message: telebot.types.Message):
    """Say hello to user and ask for language"""
    if word_search(message.text):
        bot.send_message(
            message.chat.id,
            f"Доброго часу доби, вас вітає бот для перетворення аудіозапису на текст. "
            f"Ваш унікальний ідентифікатор чату => {message.chat.username} ~ {message.chat.id}.",
        )
        markup = types.ReplyKeyboardMarkup()

        markup.row("українська", "російська")
        markup.row("англійська", "німецька")
        bot.send_message(
            message.chat.id,
            "Виберіть мову, яку буде містити аудіозапис",
            reply_markup=markup,
        )

        bot.register_next_step_handler(message, get_language)


def get_language(message: telebot.types.Message):
    """Get language from user"""
    change_language = LANGUAGES_MAP.get(message.text, "uk-UA")
    save_config("language", change_language, message)

    bot.send_message(
        message.chat.id,
        f"Мова розпізнавання - {change_language}.",
        reply_markup=telebot.types.ReplyKeyboardRemove(),
    )
    bot.send_message(
        message.chat.id,
        "Запишіть голосове повідомлення або надішліть файл формату wav.",
    )


def save_config(key: str, value: str, message: telebot.types.Message) -> None:
    """Save data to config"""
    CFG.update({key: value})
    logger.info(f"User [{message.chat.username} ~ {message.chat.id}] => Updated settings => {CFG}")


def word_search(text: str) -> bool:
    """Check if text contains hello words"""
    key_word = [
        "hello",
        "привет",
        "hi",
        "ку",
        "вітаю",
        "привіт",
        "доброго",
    ]

    array = list(map(lambda el: el.lower(), text.split()))
    result = True in list(map(lambda el: el in array, key_word))

    return result


if __name__ == "__main__":
    bot.polling(none_stop=True, interval=0)
