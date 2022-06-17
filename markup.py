from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from loaders.loader import Loader


def custom_markup(command, category, smile='🔹', row_width=1):
    markup = InlineKeyboardMarkup()
    markup.row_width = row_width
    item = None
    if isinstance(category, dict):
        item = category.keys()
    if isinstance(category, list):
        item = category
    if not item:
        raise ValueError
    for cat in item:
        short_cat = cat.split()[0]
        short_cat = short_cat.replace(',', '')
        short_cat = short_cat.lower()
        markup.add(InlineKeyboardButton(f'{smile} {cat}', callback_data=f'{command} {short_cat}'))
    return markup


def main_markup(privileges: int):
    markup = InlineKeyboardMarkup()
    markup.row_width = 1
    if Loader.privileges_levels['untrusted'] <= privileges:
        pass
    if Loader.privileges_levels['test'] <= privileges:
        pass
    if Loader.privileges_levels['regular'] <= privileges:
        markup.add(InlineKeyboardButton("📜 Hidden functions/Скрытые функции", callback_data="hidden_functions"),
                   InlineKeyboardButton("💵 Exchange/Курс валют", callback_data="exchange"),
                   InlineKeyboardButton("⛅️Weather/Погода", callback_data="weather"),
                   InlineKeyboardButton("💭 Quote/Цитата", callback_data="quote"),
                   InlineKeyboardButton("🤗 Wish/Пожелание", callback_data="wish"),
                   InlineKeyboardButton("📰 News/Новости", callback_data="news"),
                   InlineKeyboardButton("🧘‍♀️Affirmation/Аффирмация", callback_data="affirmation"),
                   InlineKeyboardButton("🎭 Events/Мероприятия", callback_data="events"),
                   InlineKeyboardButton("🍲 Food/Еда", callback_data="food"),
                   InlineKeyboardButton("🪶 Poem/Стих", callback_data="poem"),
                   InlineKeyboardButton("🎞 Movie/Фильм", callback_data="movie"),
                   InlineKeyboardButton("📖 Book/Книга", callback_data="book"),
                   InlineKeyboardButton("🎑 Metaphorical card/Метафорическая карта",
                                        callback_data="metaphorical_card"),
                   InlineKeyboardButton("🏞 Russian painting/Русская картина", callback_data="russian_painting"))
    if Loader.privileges_levels['trusted'] <= privileges:
        pass
    if Loader.privileges_levels['root'] <= privileges:
        markup.add(InlineKeyboardButton("🛠 Admins help/Руководство админу", callback_data="admins_help"),
                   InlineKeyboardButton("🖥 Ngrok", callback_data="ngrok"),
                   InlineKeyboardButton("📦 Ngrok DB", callback_data="ngrok_db"),
                   InlineKeyboardButton("📷 Camera/Камера", callback_data="camera"),
                   InlineKeyboardButton("👥 Users/Пользователи", callback_data="users"),
                   InlineKeyboardButton("🌐 Server IP/IP-адрес сервера", callback_data="ip"),
                   InlineKeyboardButton("📊 Statistic/Статистика", callback_data="statistic"))
    return markup
