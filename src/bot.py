import os
import logging

import telebot
from telebot import types

from modules.convert import get_text_with_speech


logging.getLogger("requests").setLevel(logging.CRITICAL)
logging.basicConfig(
    format="[%(asctime)s] %(filename)s:%(lineno)d %(levelname)s - %(message)s",
    level=logging.INFO,
    datefmt="%d.%m.%Y %H:%M:%S",
)


LNG_MAP = {"українська": "uk-UA", "російська": "ru-RU", "англійська": "en-US", "німецька": "de-DE"}
CFG = {"language": "uk-UA"}
TOKEN = os.getenv("TOKEN", "YOUR-TOKEN")

logging.info(os.getenv("TOKEN"))

bot = telebot.TeleBot(TOKEN)
logging.info("Bot in wait status")


@bot.message_handler(commands=["start", "help"])
def handle_start_help(message):
    logging.info(f"Send command => {message.text}")

    if message.text == "/start":
        bot.send_message(message.chat.id, "Щоб розпочати роботу бота привітайтесь з ним :=)")
        bot.send_message(message.chat.id, "Для ознайомлення з функіоналом напишіть /help")

    elif message.text == "/help":
        bot.send_message(
            message.chat.id, "Даний бот був розрозроблений для розпізнавання голосових повідомлен."
        )

        bot.send_message(
            message.chat.id,
            "Для того, щоб розпочати пошук розкладу по вашим критерiям: \n"
            "=> Вам потрiбно  привітатись з ботом "
            "на українською, англійською чи російською мовою \n=> Вибрати мову для розпізнавання.\n"
            "=> Для зміни мови розпізнавання потрібно повторно привітатись.",
        )
    else:
        bot.register_next_step_handler(message, say_hello)


def is_help(message):
    if not message == "/help":
        bot.register_next_step_handler(message, say_hello)


@bot.message_handler(content_types=["voice"])
def voice_processing(message):
    path_to_save_voice = "tmp.wav"
    file_info = bot.get_file(message.voice.file_id)
    downloaded_file = bot.download_file(file_info.file_path)

    with open(path_to_save_voice, "wb") as audi_file:
        audi_file.write(downloaded_file)

    text = get_text_with_speech(path_to_save_voice, CFG["language"])

    if not text:
        bot.send_message(
            message.chat.id,
            "Текст невдалося розпізнати, спробуйте записати аудіозапис у менш шумному місці.",
        )
    else:
        bot.send_message(message.chat.id, text)
        bot.send_message(
            message.chat.id,
            "Для повторного розпізаванная надішліть голосове повідомлення або файл формату wav.",
        )
        logging.info(f"Recognition text => {text}")

    os.remove(path_to_save_voice)


@bot.message_handler(func=lambda message: True, content_types=["text"])
def event_handler(message):
    logging.info(f"User message => {message.text}")

    if word_search(message.text):
        say_hello(message)


def say_hello(message):
    if word_search(message.text):
        logging.info("User ~ hello")

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


def get_language(message):
    save_data("language", LNG_MAP.get(message.text))

    bot.send_message(
        message.chat.id,
        f"Мову розпізнавання - {message.text}.",
        reply_markup=telebot.types.ReplyKeyboardRemove(),
    )
    bot.send_message(
        message.chat.id, f"Запишіть голосове повідомлення або надішліть файл формату wav."
    )


def save_data(key: str, value: str):
    CFG.update({key: value})
    logging.info(f"Update params => {CFG}")


def word_search(text: str) -> bool:
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
