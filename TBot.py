# -*- coding: utf-8 -*-
import configparser
import traceback
import telebot
import logging
import os
import string
import random
import datetime

from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

from TBotClass import TBotClass

MAX_TRY = 15


def tbot():
    config = configparser.ConfigParser()
    config.read('TBot.ini', encoding='windows-1251')
    token = config['MAIN']['token']
    bot = telebot.TeleBot(token)
    tb = TBotClass()

    def gen_markup():
        markup = InlineKeyboardMarkup()
        markup.row_width = 1
        markup.add(InlineKeyboardButton("💵 Exchange/Курс валют", callback_data="ex"),
                   InlineKeyboardButton("⛅️Weather/Погода", callback_data="weather"),
                   InlineKeyboardButton("💭 Quote/Цитата", callback_data="quote"),
                   InlineKeyboardButton("🤗 Wish/Пожелание", callback_data="wish"),
                   InlineKeyboardButton("📰 News/Новости", callback_data="news"),
                   InlineKeyboardButton("🧘‍♀️Affirmation/Аффирмация", callback_data="affirmation"),
                   InlineKeyboardButton("🎭 Events/Мероприятия", callback_data="events"),
                   InlineKeyboardButton("🍲 Food/Еда", callback_data="food"),
                   InlineKeyboardButton("🪶 Poesy/Позия", callback_data="poesy"))
        return markup

    @bot.callback_query_handler(func=lambda call: True)
    def callback_query(call):
        call.message.text = call.data
        replace = tb.replace(call.message)
        #bot.answer_callback_query(call.id, replace)
        current_try = 0
        save_response(f'{str(call.message.chat)} Callback: {call.message.text}')
        while current_try < MAX_TRY:
            current_try += 1
            try:
                bot.send_message(call.message.json['chat']['id'], replace['res'])
            except Exception as _ex:
                logger.exception(f'Unrecognized exception: {_ex}')
            else:
                save_response(replace['res'])
                logger.info('Send successful')
                break

    @bot.message_handler(commands=['start'])
    def start_message(message):
        bot.send_message(message.chat.id, 'Welcome, my friend!')

    @bot.message_handler(func=lambda message: True, content_types=['audio', 'photo', 'voice', 'video', 'document',
                                                                   'text', 'location', 'contact', 'sticker'])
    def send_text(message):
        current_try = 0
        save_file(message)
        while current_try < MAX_TRY:
            current_try += 1
            replace = tb.replace(message)
            try:
                if replace.get('is_help', 0):
                    bot.send_message(message.chat.id, replace['res'], reply_markup=gen_markup())
                else:
                    bot.send_message(message.chat.id, replace['res'])
            except Exception as _ex:
                logger.exception(f'Unrecognized exception: {_ex}')
            else:
                save_response(replace['res'])
                logger.info('Send successful')
                break

    def save_response(text: str) -> None:
        """
        Save bot response text to the file
        :param text: text to save
        :return:
        """
        curdir = os.curdir
        file_name = os.path.join(curdir, 'text', f'{now_time()[:10]}.txt')
        with open(file_name, 'a') as file:
            text = text.replace('\n', ' ')
            file.write(f"{datetime.datetime.now()} {text}\n")
        os.chown(file_name, 1000, 1000)

    def save_file(message) -> None:
        """
        Save file
        :param message: input message
        :return:
        """
        file_info = None
        file_extention = None
        curdir = os.curdir
        if message.content_type == 'text':
            file_extention = '.txt'
            file_info = message.json
        if message.content_type == 'photo':
            file_extention = '.jpg'
            file_info = bot.get_file(message.photo[-1].file_id)
        if message.content_type == 'audio':
            file_extention = '.mp3'
            file_info = bot.get_file(message.audio.file_id)
        if message.content_type == 'voice':
            file_extention = '.mp3'
            file_info = bot.get_file(message.voice.file_id)
        if message.content_type == 'video':
            file_extention = '.mp4'
            file_info = bot.get_file(message.video.file_id)
        if not os.path.exists(os.path.join(curdir, message.content_type)):
            os.mkdir(os.path.join(curdir, message.content_type))
            os.chown(os.path.join(curdir, message.content_type), 1000, 1000)
        if file_extention == '.txt':
            write_type = 'a'
            file_name = os.path.join(curdir, message.content_type, f'{now_time()[:10]}{file_extention}')
            downloaded_info = str(file_info).replace('\n', ' ')
            downloaded_info = f"{datetime.datetime.now()} {downloaded_info}\n"
        else:
            write_type = 'wb'
            file_name = os.path.join(curdir, message.content_type,
                                     f'{now_time()}{_get_hash_name()}{file_extention}')
            downloaded_info = bot.download_file(file_info.file_path)
        with open(file_name, write_type) as new_file:
            new_file.write(downloaded_info)
        os.chown(file_name, 1000, 1000)

    def now_time() -> str:
        """
        Get nowtime like: 20222-01-18123458
        """
        return str(datetime.datetime.now()).replace(':', '').replace(' ', '')[:16]

    def _get_hash_name() -> str:
        """
        Generate hash name
        :param:
        :return name: name of file
        """
        simbols = string.ascii_lowercase + string.ascii_uppercase
        name = ''
        for _ in range(15):
            name += random.choice(simbols)
        return name

    try:
        bot.infinity_polling(none_stop=True)
    except Exception as ex:
        logger.exception(f'Infinity polling exception: {ex}\n{traceback.format_exc()}')


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)

    logger = logging.getLogger(__name__)
    handler = logging.FileHandler('run.log')
    handler.setLevel(logging.INFO)
    handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(handler)

    logger.info('TBot is started')
    tbot()
