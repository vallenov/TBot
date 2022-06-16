# -*- coding: utf-8 -*-
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
import socket

import config

from BotFunctions import BotFunctions
from send_service import send_dev_message


class Msg:
    def __init__(self, text: str, chat: dict, content_type: str = 'text'):
        self.content_type = content_type
        self.json = {'chat': chat}
        self.text = text


class TBot:
    """
    Main class
    """
    logger = None
    conversation_logger = None
    bot = None
    bot_func = None

    @staticmethod
    def init_loggers():
        logging.basicConfig(level=logging.INFO)
        TBot.logger = logging.getLogger(__name__)
        handler = logging.FileHandler('run.log')
        handler.setLevel(logging.INFO)
        handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        TBot.logger.addHandler(handler)

        TBot.conversation_logger = logging.getLogger('conversation')
        TBot.conversation_logger.setLevel(logging.INFO)
        conv_handler = logging.FileHandler(os.path.join('downloads', 'text', 'run_conv.log'))
        conv_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        TBot.conversation_logger.addHandler(conv_handler)

    @staticmethod
    def init_bot():
        TBot.bot = telebot.TeleBot(config.TOKEN)

        @TBot.bot.callback_query_handler(func=lambda call: True)
        def callback_query(call):
            """
            Callback reaction
            """
            TBot.save_file(call.message)
            call.message.text = call.data
            replace = TBot.bot_func.replace(call.message)
            TBot.safe_send(call.message.json['chat']['id'], replace, reply_markup=replace.get('markup', None))

        @TBot.bot.message_handler(func=lambda message: True, content_types=config.CONTENT_TYPES)
        def send_text(message):
            """
            Text reaction
            """
            TBot.save_file(message)
            replace = TBot.bot_func.replace(message)
            chat_id = replace.get('chat_id', None)
            if chat_id is not None:
                message.chat.id = chat_id
            if replace:
                TBot.safe_send(message.chat.id, replace, reply_markup=replace.get('markup', None))

        TBot.check_bot_connection(TBot.bot)
        TBot.logger.info('TBot is started')

    @staticmethod
    def init_dirs():
        curdir = os.curdir
        if not os.path.exists(os.path.join(curdir, 'downloads')):
            os.mkdir(os.path.join(curdir, 'downloads'))
            os.chown(os.path.join(curdir, 'downloads'), 1000, 1000)
        if not os.path.exists(os.path.join('downloads', 'text')):
            os.mkdir(os.path.join('downloads', 'text'))
            os.chown(os.path.join('downloads', 'text'), 1000, 1000)

    @staticmethod
    def check_bot_connection(bot_obj) -> None:
        """
        Check bot connection
        """
        is_bot = None
        try:
            is_bot = bot_obj.get_me()
        except telebot.apihelper.ApiException as taa:
            TBot.logger.exception(f'{taa}')
        if not hasattr(is_bot, 'id'):
            TBot.logger.exception('Bot not found')
            send_dev_message({'subject': 'Bot not found', 'text': f'{is_bot}'})
        else:
            TBot.logger.info(f'Connection to bot success')

    @staticmethod
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
        cnt_message = math.ceil(len(replace) / config.MESSAGE_MAX_LEN) if text is not None else 1
        photo = replace.get('photo', None)
        for cnt in range(cnt_message):
            while current_try < config.MAX_TRY:
                current_try += 1
                try:
                    if photo is not None:
                        if 'http' not in photo:
                            photo = open(photo, 'rb')
                        TBot.bot.send_photo(chat_id, photo=photo, caption=text)
                    elif text is not None:
                        if start + config.MESSAGE_MAX_LEN >= len(replace):
                            TBot.bot.send_message(chat_id, text[start:], reply_markup=reply_markup)
                        else:
                            TBot.bot.send_message(chat_id,
                                                  text[start:start + config.MESSAGE_MAX_LEN],
                                                  reply_markup=reply_markup)
                        start += config.MESSAGE_MAX_LEN
                except ConnectionResetError as cre:
                    TBot.logger.exception(f'ConnectionResetError exception: {cre}')
                except requests.exceptions.ConnectionError as rec:
                    TBot.logger.exception(f'requests.exceptions.ConnectionError exception: {rec}')
                except urllib3.exceptions.ProtocolError as uep:
                    TBot.logger.exception(f'urllib3.exceptions.ProtocolError exception: {uep}')
                except TypeError as te:
                    TBot.logger.exception(f'file not ready yet: {te}')
                    time.sleep(1)
                except Exception as ex:
                    TBot.logger.exception(f'Unrecognized exception during a send: {traceback.format_exc()}')
                    if not is_send:
                        send_dev_message({'subject': repr(ex)[:-2], 'text': f'{traceback.format_exc()}'})
                        TBot.init_bot()
                        is_send = True
                else:
                    if text is not None:
                        TBot.conversation_logger.info('Response: ' + text.replace('\n', ' '))
                    else:
                        TBot.conversation_logger.info(f'Response: {photo}')
                    TBot.logger.info(f'Number of attempts: {current_try}')
                    TBot.logger.info(f'Send successful')
                    break

    @staticmethod
    def save_file(message) -> None:
        """
        Save file
        :param message: input message
        :return:
        """
        file_info = None
        file_extension = None
        curdir = os.curdir
        if message.content_type == 'text':
            TBot.logger.info(f'Request: '
                             f'ID - {message.chat.id}, '
                             f'Login - {message.chat.username}, '
                             f'FirstName - {message.chat.first_name}')
            TBot.conversation_logger.info(f'Request: '
                                          f'ID - {message.chat.id}, '
                                          f'Login - {message.chat.username}, '
                                          f'FirstName - {message.chat.first_name}, '
                                          f'Text - {message.text}, '
                                          f'RAW - {message.chat}')
            return
        if message.content_type == 'photo':
            file_extension = '.jpg'
            file_info = TBot.bot.get_file(message.photo[-1].file_id)
        if message.content_type == 'audio':
            file_extension = '.mp3'
            file_info = TBot.bot.get_file(message.audio.file_id)
        if message.content_type == 'voice':
            file_extension = '.mp3'
            file_info = TBot.bot.get_file(message.voice.file_id)
        if message.content_type == 'video':
            file_extension = '.mp4'
            file_info = TBot.bot.get_file(message.video.file_id)
        if not os.path.exists(os.path.join(curdir, 'downloads', message.content_type)):
            os.mkdir(os.path.join(curdir, 'downloads', message.content_type))
            os.chown(os.path.join(curdir, 'downloads', message.content_type), 1000, 1000)
        file_name = os.path.join(curdir, 'downloads', message.content_type,
                                 f'{TBot.now_time()}{TBot._get_hash_name()}{file_extension}')
        downloaded_info = TBot.bot.download_file(file_info.file_path)
        with open(file_name, 'wb') as new_file:
            new_file.write(downloaded_info)
        os.chown(file_name, 1000, 1000)

    @staticmethod
    def now_time() -> str:
        """
        Get nowtime like: 20222-01-18123458
        """
        return str(datetime.datetime.now()).replace(':', '').replace(' ', '')[:16]

    @staticmethod
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

    @staticmethod
    def run():
        TBot.init_loggers()
        TBot.init_bot()
        TBot.init_dirs()

        TBot.bot_func = BotFunctions()
        try:
            TBot.bot.infinity_polling(none_stop=True)
        except (requests.exceptions.ReadTimeout,
                urllib3.exceptions.ReadTimeoutError,
                socket.timeout,
                Exception) as ex:
            TBot.logger.exception(f'Infinity polling exception: {ex}\n{traceback.format_exc()}\nTBot stop')
            send_dev_message({'subject': repr(ex)[:-2],
                              'text': f'Infinity polling exception: {traceback.format_exc()}\nTBot stop'})


if __name__ == '__main__':
    TBot.run()
