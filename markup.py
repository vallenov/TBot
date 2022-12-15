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
    markup.row_width = 1
    buttons_w = config.BUTTON_WIDTH
    if Loader.privileges_levels['untrusted'] <= privileges:
        pass
    if Loader.privileges_levels['test'] <= privileges:
        pass
    if Loader.privileges_levels['regular'] <= privileges:
        markup.add(InlineKeyboardButton("📜 Скрытые функции".center(buttons_w), callback_data="hidden_functions"),
                   InlineKeyboardButton("💵 Курс валют".center(buttons_w), callback_data="exchange"),
                   InlineKeyboardButton("⛅️Погода".center(buttons_w), callback_data="weather"),
                   InlineKeyboardButton("💭 Цитата".center(buttons_w), callback_data="quote"),
                   InlineKeyboardButton("🤗 Пожелание".center(buttons_w), callback_data="wish"),
                   InlineKeyboardButton("📰 Новости".center(buttons_w), callback_data="news"),
                   InlineKeyboardButton("🧘‍♀️Аффирмация".center(buttons_w), callback_data="affirmation"),
                   InlineKeyboardButton("🎭 Мероприятия".center(buttons_w), callback_data="events"),
                   InlineKeyboardButton("🍲 Еда".center(buttons_w), callback_data="food"),
                   InlineKeyboardButton("🪶 Стих".center(buttons_w), callback_data="poem"),
                   InlineKeyboardButton("🔮 Гадание".center(buttons_w), callback_data="divination"),
                   InlineKeyboardButton("🎞 Фильм".center(buttons_w), callback_data="movie"),
                   InlineKeyboardButton("📖 Книга".center(buttons_w), callback_data="book"),
                   InlineKeyboardButton("🎑 Метафорическая карта".center(buttons_w),
                                        callback_data="metaphorical_card"),
                   InlineKeyboardButton("🏞 Русская картина".center(buttons_w), callback_data="russian_painting"))
    if Loader.privileges_levels['trusted'] <= privileges:
        pass
    if Loader.privileges_levels['root'] <= privileges:
        markup.add(InlineKeyboardButton("🛠 Руководство админу".center(buttons_w), callback_data="admins_help"),
                   InlineKeyboardButton("🔁 Перезагрузка бота".center(buttons_w), callback_data="restart_bot"),
                   InlineKeyboardButton("🔃 Перезагрузка системы".center(buttons_w), callback_data="restart_system"),
                   InlineKeyboardButton("🖥 Ngrok".center(buttons_w), callback_data="ngrok"),
                   InlineKeyboardButton("📦 Ngrok DB".center(buttons_w), callback_data="ngrok_db"),
                   InlineKeyboardButton("📷 Камера".center(buttons_w), callback_data="camera"),
                   InlineKeyboardButton("👥 Пользователи".center(buttons_w), callback_data="users"),
                   InlineKeyboardButton("🌐 IP-адрес сервера".center(buttons_w), callback_data="ip"),
                   InlineKeyboardButton("📊 Статистика".center(buttons_w), callback_data="statistic"))
    return markup
