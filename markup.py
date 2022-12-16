from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

import config
from loaders.loader import Loader
from loggers import get_logger
from exceptions import TBotException

logger = get_logger(__name__)


def custom_markup(command, category, smile='🔹', row_width=1):
    """
    Make custom markup
    :param command: input command
    :param category: command level 2 list or dict
    :param: emoji
    :param row_width: width of markup
    :return: markup
    """
    markup = InlineKeyboardMarkup()
    markup.row_width = row_width
    item = None
    if isinstance(category, dict):
        item = category.keys()
    if isinstance(category, list):
        item = category
    if not item:
        logger.exception(f'Wrong item type: {type(item)}')
        raise TBotException(code=8, message=f'Wrong item type: {type(item)}')
    for cat in item:
        short_cat = cat.split()[0]
        short_cat = short_cat.replace(',', '')
        markup.add(InlineKeyboardButton(f'{smile} {cat}', callback_data=f'{command} {short_cat}'))
    return markup


def main_markup(privileges: int):
    """
    Main markup
    """
    markup = InlineKeyboardMarkup()
    markup.row_width = 2
    if Loader.privileges_levels['untrusted'] <= privileges:
        pass
    if Loader.privileges_levels['test'] <= privileges:
        pass
    if Loader.privileges_levels['regular'] <= privileges:
        markup.add(InlineKeyboardButton("📜 Скрытые функции", callback_data="hidden_functions"),
                   InlineKeyboardButton("💵 Курс валют", callback_data="exchange"),
                   InlineKeyboardButton("⛅️Погода", callback_data="weather"),
                   InlineKeyboardButton("💭 Цитата", callback_data="quote"),
                   InlineKeyboardButton("🤗 Пожелание", callback_data="wish"),
                   InlineKeyboardButton("📰 Новости", callback_data="news"),
                   InlineKeyboardButton("🧘‍♀️Аффирмация", callback_data="affirmation"),
                   InlineKeyboardButton("🎭 Мероприятия", callback_data="events"),
                   InlineKeyboardButton("🍲 Еда", callback_data="food"),
                   InlineKeyboardButton("🪶 Стих", callback_data="poem"),
                   InlineKeyboardButton("🔮 Гадание", callback_data="divination"),
                   InlineKeyboardButton("🎞 Фильм", callback_data="movie"),
                   InlineKeyboardButton("📖 Книга", callback_data="book"),
                   InlineKeyboardButton("🎑 Метафорическая карта",
                                        callback_data="metaphorical_card"),
                   InlineKeyboardButton("🏞 Русская картина", callback_data="russian_painting"))
    if Loader.privileges_levels['trusted'] <= privileges:
        pass
    if Loader.privileges_levels['root'] <= privileges:
        markup.add(InlineKeyboardButton("🛠 Руководство админу", callback_data="admins_help"),
                   InlineKeyboardButton("🔁 Перезагрузка бота", callback_data="restart_bot"),
                   InlineKeyboardButton("🔃 Перезагрузка системы", callback_data="restart_system"),
                   InlineKeyboardButton("🖥 Ngrok", callback_data="ngrok"),
                   InlineKeyboardButton("📦 Ngrok DB", callback_data="ngrok_db"),
                   InlineKeyboardButton("📷 Камера", callback_data="camera"),
                   InlineKeyboardButton("👥 Пользователи", callback_data="users"),
                   InlineKeyboardButton("🌐 IP-адрес сервера", callback_data="ip"),
                   InlineKeyboardButton("📊 Статистика", callback_data="statistic"))
    return markup
