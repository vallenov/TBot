# -*- coding: utf-8 -*-
import configparser
import traceback
import telebot
import logging
import os
import string
import random
import datetime
import requests
from requests import exceptions
import math

from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

from TBotClass import TBotClass

MAX_TRY = 15
MAX_LEN = 4000


def tbot():
    config = configparser.ConfigParser()
    config.read('TBot.ini', encoding='windows-1251')
    token = config['MAIN']['token']
    bot = telebot.TeleBot(token)
    tb = TBotClass()
    content_types = ['audio', 'photo', 'voice', 'video', 'document', 'text', 'location', 'contact', 'sticker']

    conversation_logger = logging.getLogger('conversation')
    conversation_logger.setLevel(logging.INFO)
    conv_handler = logging.FileHandler('text/run_conv.log')
    conv_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    conversation_logger.addHandler(conv_handler)

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
                   InlineKeyboardButton("🪶 Poem/Стих", callback_data="poem"))
        return markup

    def safe_send(chat_id: int, replace: str, reply_markup=None):
        is_send = False
        current_try = 0
        while current_try < MAX_TRY:
            current_try += 1
            try:
                bot.send_message(chat_id, replace, reply_markup=reply_markup)
            except ConnectionResetError:
                logger.exception(f'ConnectionResetError exception: {traceback.format_exc()}')
            except Exception as _ex:
                logger.exception(f'Unrecognized exception: {traceback.format_exc()}')
                if not is_send:
                    send_dev_message({'subject': 'TBot EXCEPTION', 'text': f'{traceback.format_exc()}'})
                    is_send = True
            else:
                conversation_logger.info('Response: ' + replace.replace('\n', ' '))
                logger.info('Send successful')
                break

    @bot.callback_query_handler(func=lambda call: True)
    def callback_query(call):
        call.message.text = call.data
        replace = tb.replace(call.message)
        #bot.answer_callback_query(call.id, replace)
        conversation_logger.info(f'Request: ' 
                                 f'ID - {call.message.chat.id}, ' 
                                 f'Login - {call.message.chat.username}, '
                                 f'FirstName - {call.message.chat.first_name}, '
                                 f'Callback - {call.message.text}, '
                                 f'RAW - {call.message.chat}')
        cnt_message = math.ceil(len(replace['res']) / MAX_LEN)
        start = 0
        for cnt in range(cnt_message):
            if start + MAX_LEN >= len(replace['res']):
                safe_send(call.message.json['chat']['id'], replace['res'][start:])
            else:
                safe_send(call.message.json['chat']['id'], replace['res'][start:start + MAX_LEN])
            start += MAX_LEN

    @bot.message_handler(commands=['start'])
    def start_message(message):
        bot.send_message(message.chat.id, 'Welcome, my friend!')

    @bot.message_handler(func=lambda message: True, content_types=content_types)
    def send_text(message):
        save_file(message)
        replace = tb.replace(message)
        if replace.get('is_help', 0):
            safe_send(message.chat.id, replace['res'], reply_markup=gen_markup())
        else:
            cnt_message = math.ceil(len(replace['res']) / MAX_LEN)
            start = 0
            for cnt in range(cnt_message):
                if start + MAX_LEN >= len(replace['res']):
                    safe_send(message.chat.id, replace['res'][start:])
                else:
                    safe_send(message.chat.id, replace['res'][start:start+MAX_LEN])
                start += MAX_LEN

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
            conversation_logger.info(f'Response: '
                                     f'ID - {message.chat.id}, '
                                     f'Login - {message.chat.username}, '
                                     f'FirstName - {message.chat.first_name}, '
                                     f'Text - {message.text}, '
                                     f'RAW - {message.chat}')
            return
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
        file_name = os.path.join(curdir, message.content_type,
                                 f'{now_time()}{_get_hash_name()}{file_extention}')
        downloaded_info = bot.download_file(file_info.file_path)
        with open(file_name, 'wb') as new_file:
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

    def send_dev_message(data: dict):
        """
        Отправка сообщения админу

        """
        data.update({'to': config.get('MAIL', 'address')})
        current_try = 0
        while current_try < MAX_TRY:
            current_try += 1
            try:
                requests.post(config.get('MAIL', 'message_server_address'), data=data, headers={'Connection': 'close'})
            except Exception as _ex:
                logger.exception(_ex)
            else:
                logger.info('Send successful')
                break
        logger.error('Max try exceeded')

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
