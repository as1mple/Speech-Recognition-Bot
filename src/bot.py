import os
import sys
from io import BytesIO
from datetime import datetime

import telebot
from telebot import types
from loguru import logger

from modules.convert import get_text_with_speech
from modules.request_to_server import save_to_database

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

HOST = os.getenv("HOST")
PORT = os.getenv("PORT")
TOKEN = os.getenv("TOKEN", "YOUR-TOKEN")

CFG = {"language": "uk-UA"}
utcnow = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ")

bot = telebot.TeleBot(TOKEN)
logger.info("Bot successfully launched")


@bot.message_handler(commands=["start", "help"])
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


def is_help(message: telebot.types.Message):
    """Check if message is help command"""
    if not message == "/help":
        bot.register_next_step_handler(message, say_hello)


@bot.message_handler(content_types=["voice"])
def voice_processing(message: telebot.types.Message):
    """Processing voice message"""
    logger.info(f"User [{message.chat.id}]  =>  Sent audio message")

    file_info = bot.get_file(message.voice.file_id)
    downloaded_file = bot.download_file(file_info.file_path)

    try:
        text = get_text_with_speech(BytesIO(downloaded_file), CFG["language"], logger, message)
    except Exception as e:
        bot.send_message(
            message.chat.id,
            "На етапі розпізнавання аудіозапису сталася помилка - сповістіть про це розробників",
        )
        logger.error(f"User [{message.chat.id}] ~ Recognition-Error  =>  {e}")

    else:
        if not text:
            bot.send_message(
                message.chat.id,
                "Текст невдалося розпізнати, спробуйте записати аудіозапис у менш шумному місці.",
            )
        else:
            bot.send_message(message.chat.id, text)
            utcnow = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ")

            logger.info(f"User [{message.chat.id}] => Recognition text => {text}")
            try:
                status = save_to_database(
                    HOST,
                    PORT,
                    message.chat.id,
                    utcnow,
                    text,
                    CFG["language"],
                    downloaded_file
                )

                logger.info(f"User [{message.chat.id}] ~ Request-Status  => {status}")
            except Exception as e:
                logger.error(f"User [{message.chat.id}] ~ Save-Error=>  {e}")
                bot.send_message(
                    message.chat.id,
                    "На етапі збереження даних сталася помилка - сповістіть про це розробників",
                )
            bot.send_message(
                message.chat.id,
                "Для повторного розпізаванная надішліть голосове повідомлення або файл формату wav.",
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
            "Доброго часу доби, вас вітає бот для перетворення аудіозапису на текст.",
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
    save_config("language", LANGUAGES_MAP.get(message.text, "uk-UA"), message)

    bot.send_message(
        message.chat.id,
        f"Мова розпізнавання - {message.text}.",
        reply_markup=telebot.types.ReplyKeyboardRemove(),
    )
    bot.send_message(
        message.chat.id, "Запишіть голосове повідомлення або надішліть файл формату wav."
    )


def save_config(key: str, value: str, message: telebot.types.Message) -> None:
    """Save data to config"""
    CFG.update({key: value})
    logger.info(f"User [{message.chat.id}]  => Updated settings => {CFG}")


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
