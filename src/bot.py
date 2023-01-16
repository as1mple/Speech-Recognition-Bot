import base64
import os
import sys
from io import BytesIO
from datetime import datetime

import telebot
from telebot import types
from loguru import logger

from modules.convert import get_text_with_speech, size_b64_string
from modules.request_to_server import save_to_database, get_save_data, get_files_by_chat_id

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

SERVER_HOST = os.getenv("SERVER_HOST")
SERVER_PORT = os.getenv("SERVER_PORT")
TOKEN = os.getenv("TOKEN")

CFG = {"language": "uk-UA"}
utcnow = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ")

bot = telebot.TeleBot(TOKEN)
logger.info("Bot successfully launched")


@bot.message_handler(commands=["start", "help", "search"])
def handle_start_help(message: telebot.types.Message):
    """Handle start and help commands"""
    logger.info(f"User [{message.chat.id}] => asked for help")

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
    logger.info(f"User [{message.chat.id}] => search files by time interval or chat_id => {message.text}")

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

        logger.error(f"User [{message.chat.id}] => Invalid time format => {message.text}")
        bot.register_next_step_handler(message, search_files)

    else:
        try:
            if chat_id:
                result = get_files_by_chat_id(SERVER_HOST, SERVER_PORT, chat_id)["result"]
            else:
                result = get_save_data(SERVER_HOST, SERVER_PORT, time_from, time_to)["result"]

            bot.send_message(message.chat.id, f"Знайдено записів: {len(result)}")
            logger.info(f"User [{message.chat.id}] => Find files => {len(result)}")

            for data in result:
                user_id = data["user_id"]
                time = data["timestamp"]["$date"]
                decode_bytes = base64.b64decode(data["speech_bytes"])
                caption = f'description ~ {data["description"]} \n' \
                          f"time ~ {time} \nuser_id ~ {user_id} \n" \
                          f'language ~ {data["language"]} \n' \
                          f'text ~ {data["text"]}'

                # logger.info(
                #     f"User [{message.chat.id}] => Send file => {size_b64_string(data['speech_bytes']) / 1024} kb")
                # logger.info(f"User [{message.chat.id}] => Length caption => {len(caption)} characters")

                if len(caption) > 1024:
                    preview_message = bot.send_voice(
                        message.chat.id,
                        decode_bytes,
                        caption=caption[:1024],
                    )

                    bot.reply_to(preview_message, caption[1024:])

                else:
                    bot.send_voice(
                        message.chat.id,
                        decode_bytes,
                        caption=caption,
                    )

        except Exception as e:
            bot.send_message(
                message.chat.id, "Помилка з'єднання з сервером. Повідомте про це розробників."
            )
            logger.error(f"User [{message.chat.id}] => {e}")


def is_help(message: telebot.types.Message):
    """Check if message is help command"""
    if not message == "/help":
        bot.register_next_step_handler(message, say_hello)


@bot.message_handler(content_types=["voice"])
def voice_processing(message: telebot.types.Message):
    """Processing voice message"""
    logger.info(f"User [{message.chat.id}] => Sent audio message")

    file_info = bot.get_file(message.voice.file_id)
    downloaded_file = bot.download_file(file_info.file_path)

    try:
        text = get_text_with_speech(BytesIO(downloaded_file), CFG["language"], logger, message)
    except Exception as e:
        bot.send_message(
            message.chat.id,
            "На етапі розпізнавання аудіозапису сталася помилка - сповістіть про це розробників",
        )
        logger.error(f"User [{message.chat.id}] ~ Recognition-Error => {e}")

    else:
        if not text:
            bot.send_message(
                message.chat.id,
                "Текст невдалося розпізнати, спробуйте записати аудіозапис у менш шумному місці.",
            )
        else:
            bot.send_message(message.chat.id, text)
            logger.info(f"User [{message.chat.id}] => Recognition text => {text}")

            markup = types.ReplyKeyboardMarkup()

            markup.row("Так", "Ні")
            bot.send_message(
                message.chat.id, "Зберегти отримані дані до Бази Знань?", reply_markup=markup
            )

            bot.register_next_step_handler(message, is_save_to_db, text, downloaded_file)


def is_save_to_db(message: telebot.types.Message, text, downloaded_file):
    logger.info(f"User [{message.chat.id}] => Asked for save data => {message.text}")

    if message.text.lower() == "так":
        bot.send_message(
            message.chat.id,
            "Напишіть опис до файлу або його id",
            reply_markup=telebot.types.ReplyKeyboardRemove(),
        )

        bot.register_next_step_handler(message, input_description, text, downloaded_file)

    else:
        bot.send_message(
            message.chat.id,
            "Запишіть голосове повідомлення або надішліть файл формату wav.",
            reply_markup=telebot.types.ReplyKeyboardRemove(),
        )


def input_description(message: telebot.types.Message, text, downloaded_file):
    """Input description for file and save to db"""
    logger.info(f"User [{message.chat.id}] => Input description => {message.text}")
    save_config("description", message.text, message)

    utcnow = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    try:
        status = save_to_database(
            SERVER_HOST,
            SERVER_PORT,
            message.chat.id,
            utcnow,
            text,
            CFG["language"],
            downloaded_file,
            message.text,
        )

        bot.send_message(
            message.chat.id,
            "✅ Інформація успішно збережена до Бази Знань.",
        )
        logger.info(f"User [{message.chat.id}] ~ Request-Status => {status}")
    except Exception as e:
        logger.error(f"User [{message.chat.id}] ~ Save-Error => {e}")
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
    logger.info(f"User [{message.chat.id}] => sent a message => {message.text}")
    if word_search(message.text):
        say_hello(message)


def say_hello(message: telebot.types.Message):
    """Say hello to user and ask for language"""
    if word_search(message.text):
        bot.send_message(
            message.chat.id,
            f"Доброго часу доби, вас вітає бот для перетворення аудіозапису на текст. "
            f"Ваш унікальний ідентифікатор чату => {message.chat.id}.",
        )
        markup = types.ReplyKeyboardMarkup()

        markup.row("українська", "російська")
        markup.row("англійська", "німецька")
        bot.send_message(
            message.chat.id, "Виберіть мову, яку буде містити аудіозапис", reply_markup=markup
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
        message.chat.id, "Запишіть голосове повідомлення або надішліть файл формату wav."
    )


def save_config(key: str, value: str, message: telebot.types.Message) -> None:
    """Save data to config"""
    CFG.update({key: value})
    logger.info(f"User [{message.chat.id}] => Updated settings => {CFG}")


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
