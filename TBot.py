# -*- coding: utf-8 -*-
import time
import traceback
import telebot
import os
import datetime
import requests
import urllib3.exceptions
import math
import socket
import inspect
import asyncio

import config

from loaders.loader import Loader
from loaders.internet_loader import InternetLoader
from loaders.file_loader import FileLoader
from loaders.db_loader import DBLoader
from send_service import send_dev_message
from helpers import now_time, get_hash_name
from loggers import get_logger, get_conversation_logger

logger = get_logger(__name__)
conversation_logger = get_conversation_logger()


class Msg:
    def __init__(self, text: str, chat: dict, content_type: str = 'text'):
        self.content_type = content_type
        self.json = {'chat': chat}
        self.text = text


class TBot:
    """
    Main class
    """
    bot = None
    internet_loader = None
    file_loader = None
    db_loader = None
    mapping = None

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
            replace = TBot.replace(call.message)
            TBot.safe_send(call.message.json['chat']['id'], replace, reply_markup=replace.get('markup', None))

        @TBot.bot.message_handler(func=lambda message: True, content_types=config.CONTENT_TYPES)
        def send_text(message):
            """
            Text reaction
            """
            TBot.save_file(message)
            replace = TBot.replace(message)
            chat_id = replace.get('chat_id', None)
            if chat_id is not None:
                message.chat.id = chat_id
            if replace:
                TBot.safe_send(message.chat.id, replace, reply_markup=replace.get('markup', None))

        TBot.check_bot_connection(TBot.bot)
        logger.info('TBot is started')

    @staticmethod
    def init_loaders():
        TBot.internet_loader = InternetLoader('ILoader')
        TBot.db_loader = DBLoader('DBLoader')
        TBot.file_loader = FileLoader('FLoader')

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
            logger.exception(f'{taa}')
        if not hasattr(is_bot, 'id'):
            logger.exception('Bot not found')
            send_dev_message({'subject': 'Bot not found', 'text': f'{is_bot}'})
        else:
            logger.info(f'Connection to bot success')

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
                    logger.exception(f'ConnectionResetError exception: {cre}')
                except requests.exceptions.ConnectionError as rec:
                    logger.exception(f'requests.exceptions.ConnectionError exception: {rec}')
                except urllib3.exceptions.ProtocolError as uep:
                    logger.exception(f'urllib3.exceptions.ProtocolError exception: {uep}')
                except TypeError as te:
                    logger.exception(f'file not ready yet: {te}')
                    time.sleep(1)
                except Exception as ex:
                    logger.exception(f'Unrecognized exception during a send: {traceback.format_exc()}')
                    if not is_send:
                        send_dev_message({'subject': repr(ex)[:-2], 'text': f'{traceback.format_exc()}'})
                        TBot.init_bot()
                        is_send = True
                else:
                    if text is not None:
                        conversation_logger.info('Response: ' + text.replace('\n', ' '))
                    else:
                        conversation_logger.info(f'Response: {photo}')
                    logger.info(f'Number of attempts: {current_try}')
                    logger.info(f'Send successful')
                    break

    @staticmethod
    def replace(message) -> dict:
        """
        Send result message to chat
        :param message: message from user
        :return: replace dict
        """
        start = datetime.datetime.now()
        res = {}
        chat_id = str(message.json['chat']['id'])
        if config.USE_DB:
            login = message.json['chat'].get('username', None)
            first_name = message.json['chat'].get('first_name', None)
            if chat_id not in Loader.users.keys():
                privileges = Loader.privileges_levels['regular']
                TBot.db_loader.add_user(chat_id=chat_id,
                                        privileges=privileges,
                                        login=login,
                                        first_name=first_name)
                send_data = dict()
                send_data['subject'] = 'TBot NEW USER'
                send_data['text'] = f'New user added. Chat_id: {chat_id}, login: {login}, first_name: {first_name}'
                mail_resp = send_dev_message(send_data, 'mail')
                telegram_resp = send_dev_message(send_data, 'telegram')
                if mail_resp['res'] == 'ERROR' or telegram_resp['res'] == 'ERROR':
                    logger.warning(f'Message do not received. MAIL = {mail_resp}, Telegram = {telegram_resp}')
            else:
                if Loader.users[chat_id]['login'] != login or \
                        Loader.users[chat_id]['first_name'] != first_name:
                    DBLoader.update_user(chat_id, login, first_name)
        privileges = Loader.users[chat_id]['value']
        if config.USE_DB:
            TBot.db_loader.log_request(chat_id)

        if message.content_type == 'text':
            form_text = message.text.lower().strip()
            sptext = form_text.split()
            default_func = TBot.mapping.get('default')
            func = TBot.mapping.get(sptext[0], default_func)
            if not inspect.iscoroutinefunction(func.__wrapped__):
                res = func(privileges=privileges, text=form_text)
            else:
                res = asyncio.run(func(privileges=privileges, text=form_text))
        duration = datetime.datetime.now() - start
        dur = float(str(duration.seconds) + '.' + str(duration.microseconds)[:3])
        logger.info(f'Duration: {dur} sec')
        return res

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
                                 f'{now_time()}{get_hash_name()}{file_extension}')
        downloaded_info = TBot.bot.download_file(file_info.file_path)
        with open(file_name, 'wb') as new_file:
            new_file.write(downloaded_info)
        os.chown(file_name, 1000, 1000)

    @staticmethod
    def run():
        TBot.init_bot()
        TBot.init_dirs()
        TBot.init_loaders()
        TBot.mapping = {
            'exchange': TBot.internet_loader.get_exchange,
            'weather': TBot.internet_loader.get_weather,
            'quote': TBot.internet_loader.get_quote,
            'wish': TBot.internet_loader.get_wish,
            'news': TBot.internet_loader.get_news,
            'affirmation': TBot.internet_loader.get_affirmation,
            'events': TBot.internet_loader.async_events,
            'food': TBot.internet_loader.get_restaurant,
            'poem': TBot.db_loader.get_poem if config.USE_DB else TBot.file_loader.get_poem,
            'movie': TBot.internet_loader.get_random_movie,
            'book': TBot.internet_loader.get_book,
            'update': TBot.db_loader.update_user_privileges,
            'users': TBot.db_loader.show_users,
            'hidden_functions': TBot.file_loader.get_help,
            'admins_help': TBot.file_loader.get_admins_help,
            'send_other': TBot.db_loader.send_other,
            'metaphorical_card': TBot.file_loader.get_metaphorical_card,
            'russian_painting': TBot.internet_loader.get_russian_painting,
            'ip': TBot.file_loader.get_server_ip,
            'statistic': TBot.db_loader.get_statistic,
            'phone': TBot.internet_loader.get_phone_number_info,
            'camera': TBot.file_loader.get_camera_capture,
            'ngrok': TBot.internet_loader.ngrok,
            'ngrok_db': TBot.internet_loader.ngrok_db,
            'default': TBot.file_loader.get_hello
        }
        if config.PROD:
            logger.info(f'Send start message to root users')
            send_dev_message({'text': 'TBot is started'}, 'telegram')
        try:
            TBot.bot.infinity_polling(none_stop=True)
        except (requests.exceptions.ReadTimeout,
                urllib3.exceptions.ReadTimeoutError,
                socket.timeout,
                Exception) as ex:
            logger.exception(f'Infinity polling exception: {ex}\n{traceback.format_exc()}\nTBot stop')
            send_dev_message({'subject': repr(ex)[:-2],
                              'text': f'Infinity polling exception: {traceback.format_exc()}\nTBot stop'})


if __name__ == '__main__':
    TBot.run()
