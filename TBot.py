# -*- coding: utf-8 -*-
import configparser
import time
import traceback
import telebot
import logging
import os
import string
import random
import datetime
import requests
import urllib3.exceptions
import math

from TBotClass import TBotClass

MAX_TRY = 5
MAX_LEN = 4000

DOWNLOADS = 'downloads'


class Msg:
    def __init__(self, text: str, chat: dict, content_type: str = 'text'):
        self.content_type = content_type
        self.json = {'chat': chat}
        self.text = text


def check_bot_connection(bot_obj) -> None:
    """
    Check bot connection
    """
    is_bot = None
    try:
        is_bot = bot_obj.get_me()
    except telebot.apihelper.ApiException as taa:
        logger.exception(f'{taa}')
    if not hasattr(is_bot, 'id'):
        logger.exception('Bot not found')
    else:
        logger.info(f'Connection to bot success')


def tbot():
    """
    Main func
    """
    config = configparser.ConfigParser()
    config.read('TBot.ini', encoding='windows-1251')
    token = config['MAIN']['token']
    bot = telebot.TeleBot(token)
    check_bot_connection(bot)

    content_types = ['audio', 'photo', 'voice', 'video', 'document', 'text', 'location', 'contact', 'sticker']

    conversation_logger = logging.getLogger('conversation')
    conversation_logger.setLevel(logging.INFO)
    curdir = os.curdir
    if not os.path.exists(os.path.join(curdir, DOWNLOADS)):
        os.mkdir(os.path.join(curdir, DOWNLOADS))
        os.chown(os.path.join(curdir, DOWNLOADS), 1000, 1000)
    if not os.path.exists(os.path.join(DOWNLOADS, 'text')):
        os.mkdir(os.path.join(DOWNLOADS, 'text'))
        os.chown(os.path.join(DOWNLOADS, 'text'), 1000, 1000)
    conv_handler = logging.FileHandler(os.path.join(DOWNLOADS, 'text', 'run_conv.log'))
    conv_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    conversation_logger.addHandler(conv_handler)

    tb = TBotClass()

    def safe_send(chat_id: int, replace: dict, reply_markup=None):
        """
        Send message with several tries
        :param chat_id: id of users chat
        :param replace: replace dict
        :param reply_markup: markup or None
        :return:
        """
        is_send = False
        current_try = 0
        start = 0
        text = replace.get('text', None)
        cnt_message = math.ceil(len(replace) / MAX_LEN) if text is not None else 1
        photo = replace.get('photo', None)
        for cnt in range(cnt_message):
            while current_try < MAX_TRY:
                current_try += 1
                try:
                    if photo is not None:
                        if 'http' not in photo:
                            photo = open(photo, 'rb')
                        bot.send_photo(chat_id, photo=photo, caption=text)
                    elif text is not None:
                        if start + MAX_LEN >= len(replace):
                            bot.send_message(chat_id, text[start:], reply_markup=reply_markup)
                        else:
                            bot.send_message(chat_id, text[start:start + MAX_LEN], reply_markup=reply_markup)
                        start += MAX_LEN
                except ConnectionResetError as cre:
                    logger.exception(f'ConnectionResetError exception: {cre}')
                except requests.exceptions.ConnectionError as rec:
                    logger.exception(f'requests.exceptions.ConnectionError exception: {rec}')
                except urllib3.exceptions.ProtocolError as uep:
                    logger.exception(f'urllib3.exceptions.ProtocolError exception: {uep}')
                except TypeError as te:
                    logger.exception(f'file not ready yet: {te}')
                    time.sleep(1)
                except Exception as _ex:
                    logger.exception(f'Unrecognized exception: {traceback.format_exc()}')
                    if not is_send:
                        tb.send_dev_message({'subject': 'TBot EXCEPTION', 'text': f'{traceback.format_exc()}'})
                        is_send = True
                else:
                    if text is not None:
                        conversation_logger.info('Response: ' + text.replace('\n', ' '))
                    else:
                        conversation_logger.info(f'Response: {photo}')
                    logger.info(f'Number of attempts: {current_try}')
                    logger.info(f'Send successful')
                    break

    @bot.callback_query_handler(func=lambda call: True)
    def callback_query(call):
        """
        Callback reaction
        """
        save_file(call.message)
        call.message.text = call.data
        replace = tb.replace(call.message)
        safe_send(call.message.json['chat']['id'], replace, reply_markup=replace.get('markup', None))

    @bot.message_handler(func=lambda message: True, content_types=content_types)
    def send_text(message):
        """
        Text reaction
        """
        save_file(message)
        replace = tb.replace(message)
        chat_id = replace.get('chat_id', None)
        if chat_id is not None:
            message.chat.id = chat_id
        if replace:
            safe_send(message.chat.id, replace, reply_markup=replace.get('markup', None))

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
            logger.info(f'Request: '
                        f'ID - {message.chat.id}, '
                        f'Login - {message.chat.username}, '
                        f'FirstName - {message.chat.first_name}')
            conversation_logger.info(f'Request: '
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
        if not os.path.exists(os.path.join(curdir, DOWNLOADS, message.content_type)):
            os.mkdir(os.path.join(curdir, DOWNLOADS, message.content_type))
            os.chown(os.path.join(curdir, DOWNLOADS, message.content_type), 1000, 1000)
        file_name = os.path.join(curdir, DOWNLOADS, message.content_type,
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
