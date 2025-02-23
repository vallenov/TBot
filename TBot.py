# -*- coding: utf-8 -*-
import time
import traceback
import telebot
import os
import datetime
import requests
import urllib3.exceptions as url_lib_exceptions
import math
import inspect
import asyncio
import aiohttp
import config

from mysql.connector.errors import OperationalError
from sqlalchemy import exc

from loaders.loader import Loader, LoaderResponse, LoaderRequest
from loaders.internet_loader import InternetLoader
from loaders.file_loader import FileLoader
from loaders.db_loader import DBLoader
from send_service import send_dev_message
from helpers import now_time, get_hash_name
from loggers import get_logger, get_conversation_logger, init_dirs
from exceptions import TBotException
from users import tbot_users
from localization import localization

init_dirs()

logger = get_logger(__name__)
conversation_logger = get_conversation_logger()


class TBot:
    """
    Main class
    """
    bot = None
    internet_loader: InternetLoader = None
    file_loader: FileLoader = None
    db_loader: DBLoader = None
    mapping = None

    @staticmethod
    def init_bot():
        TBot.bot = telebot.TeleBot(config.TOKEN)
        TBot.check_bot_connection(TBot.bot)
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
            'divination': TBot.db_loader.poem_divination if config.USE_DB else TBot.file_loader.poem_divination,
            'movie': TBot.internet_loader.get_random_movie,
            'book': TBot.internet_loader.get_book,
            'update': TBot.db_loader.update_user_data,
            'users': TBot.db_loader.show_users,
            'hidden_functions': TBot.file_loader.get_help,
            'commands': TBot.file_loader.commands_list,
            'admins_help': TBot.file_loader.get_admins_help,
            'send_other': TBot.db_loader.send_other,
            'to_admin': TBot.db_loader.send_to_admin,
            'send_all': TBot.db_loader.send_to_all_users,
            'metaphorical_card': TBot.file_loader.get_metaphorical_card,
            'russian_painting': TBot.internet_loader.get_russian_painting,
            'ip': TBot.internet_loader.get_server_ip,
            'statistic': TBot.db_loader.get_statistic,
            'phone': TBot.internet_loader.get_phone_number_info,
            'camera': TBot.file_loader.get_camera_capture,
            'ngrok': TBot.internet_loader.ngrok,
            'serveo_ssh': TBot.internet_loader.serveo_ssh,
            'ngrok_db': TBot.internet_loader.ngrok_db,
            'restart_bot': TBot.internet_loader.tbot_restart,
            'restart_system': TBot.internet_loader.system_restart,
            'systemctl': TBot.internet_loader.systemctl,
            'allow_connection': TBot.internet_loader.allow_connection
        }

        @TBot.bot.callback_query_handler(func=lambda call: True)
        def callback_query(call):
            """
            Callback reaction
            """
            call.message.text = call.data
            TBot.log_request(call.message)
            chat_id = call.message.json['chat']['id']
            replace = TBot.replace(call.message)
            try:
                TBot.safe_send(call.message.json['chat']['id'], replace)
            except TBotException:
                logger.exception(f'Message to {chat_id} is not send')
                TBot.safe_send(chat_id, LoaderResponse(text=f"Something is wrong"))

        @TBot.bot.message_handler(func=lambda message: True, content_types=config.CONTENT_TYPES)
        def send_text(message):
            """
            Text reaction
            """
            if message.content_type == 'text':
                TBot.log_request(message)
                replace = TBot.replace(message)
                chat_id = replace.chat_id
                if not chat_id:
                    chat_id = message.chat.id
                if chat_id and isinstance(chat_id, int):
                    try:
                        TBot.safe_send(chat_id, replace)
                    except TBotException:
                        logger.exception(f'Message to {chat_id} is not send')
                        TBot.safe_send(message.chat.id, LoaderResponse(text=f"Something is wrong"))
                    else:
                        if chat_id != message.chat.id:
                            TBot.safe_send(
                                message.chat.id, LoaderResponse(text=f"Сообщение отправлено пользователю {chat_id}")
                            )
                elif chat_id and isinstance(chat_id, list):
                    is_send = []
                    is_not_send = []
                    for user_chat_id in replace.chat_id:
                        try:
                            TBot.safe_send(user_chat_id, replace)
                        except TBotException:
                            is_not_send.append(str(user_chat_id))
                        else:
                            is_send.append(str(user_chat_id))
                    if is_send:
                        chat_ids = ', '.join(is_send)
                        TBot.safe_send(
                            message.chat.id, LoaderResponse(
                                text=f"Сообщения доставлены пользователям: {chat_ids}"
                            )
                        )
                    if is_not_send:
                        chat_ids = ', '.join(is_send)
                        TBot.safe_send(
                            message.chat.id, LoaderResponse(
                                text=f"Сообщения не доставлены пользователям: {chat_ids}"
                            )
                        )
            else:
                try:
                    TBot.save_file(message)
                except TBotException as e:
                    logger.exception(e.context)
                    e.send_error(traceback.format_exc())
                    TBot.safe_send(message.chat.id, e.return_message())

        logger.info('TBot is started')

    @staticmethod
    def log_request(message):
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

    @staticmethod
    def init_loaders():
        TBot.internet_loader = InternetLoader()
        TBot.db_loader = DBLoader()
        TBot.file_loader = FileLoader()



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
    def safe_send(chat_id: int, replace: LoaderResponse):
        """
        Send message with several tries
        :param chat_id: id of users chat
        :param replace: replace dict
        :return:
        """
        text = replace.text
        photo = replace.photo
        if not text and not photo:
            TBotException(code=6, message='Replace is empty')
        if text:
            user = tbot_users(str(chat_id))
            text = text.replace('#%user_name%#', user.first_name or 'участник моего мини-клуба')
        is_send = False
        current_try = 0
        start = 0
        cnt_message = math.ceil(len(replace.text) / config.MESSAGE_MAX_LEN) if text else 1
        parse_mode = replace.parse_mode
        for cnt in range(cnt_message):
            while current_try < config.MAX_TRY:
                current_try += 1
                try:
                    if photo is not None:
                        if 'http' not in photo:
                            photo = open(photo, 'rb')
                        TBot.bot.send_photo(chat_id, photo=photo, caption=text)
                    elif text is not None:
                        if start + config.MESSAGE_MAX_LEN >= len(replace.text):
                            TBot.bot.send_message(chat_id, text[start:],
                                                  reply_markup=replace.markup,
                                                  parse_mode=parse_mode)
                        else:
                            TBot.bot.send_message(chat_id,
                                                  text[start:start + config.MESSAGE_MAX_LEN],
                                                  reply_markup=replace.markup,
                                                  parse_mode=parse_mode)
                        start += config.MESSAGE_MAX_LEN
                except ConnectionResetError as cre:
                    logger.exception(f'ConnectionResetError exception: {cre}')
                except requests.exceptions.ConnectionError as rec:
                    logger.exception(f'requests.exceptions.ConnectionError exception: {rec}')
                except url_lib_exceptions.ProtocolError as uep:
                    logger.exception(f'ProtocolError exception: {uep}')
                except TypeError as te:
                    logger.exception(f'File not ready yet: {te}')
                    time.sleep(1)
                except telebot.apihelper.ApiException as e:
                    logger.exception(f'Message to {chat_id} is not send')
                    raise TBotException(code=1)
                except Exception as ex:
                    logger.exception(f'Unrecognized exception during a send: {traceback.format_exc()}')
                    if not is_send:
                        send_dev_message({'subject': repr(ex)[:-2], 'text': f'{traceback.format_exc()}'})
                        is_send = True
                else:
                    if text:
                        conversation_logger.info('Response: ' + text.replace('\n', ' '))
                    if photo:
                        conversation_logger.info(f'Response: {photo}')
                    logger.info(f'Number of attempts: {current_try}')
                    logger.info(f'Send successful')
                    break

    @staticmethod
    def replace(message) -> LoaderResponse:
        """
        Send result message to chat
        :param message: message from user
        :return:
        """
        start = datetime.datetime.now()
        res = LoaderResponse()
        chat_id = str(message.json['chat']['id'])
        if config.USE_DB:
            login = message.json['chat'].get('username', None)
            first_name = message.json['chat'].get('first_name', None)
            if chat_id not in tbot_users:
                privileges = Loader.privileges_levels['regular']
                try:
                    TBot.db_loader.add_user(
                        chat_id=chat_id,
                        privileges=privileges,
                        login=login,
                        first_name=first_name
                    )
                except (OperationalError, exc.OperationalError) as e:
                    send_data = dict(
                        subject=f'TBot DB connection error',
                        text=f'{e}'
                    )
                    send_dev_message(data=send_data, by='telegram')
                    TBot.internet_loader.tbot_restart(privileges=privileges)  
                send_data = dict(
                    subject='TBot NEW USER',
                    text=f'New user added. Chat_id: {chat_id}, login: {login}, first_name: {first_name}'
                )
                mail_resp = send_dev_message(send_data, 'mail')
                if mail_resp and mail_resp['res'] == 'ERROR':
                    logger.warning(f'Message do not received. MAIL = {mail_resp}')
                telegram_resp = send_dev_message(send_data, 'telegram')
                if telegram_resp and telegram_resp['res'] == 'ERROR':
                    logger.warning(f'Message do not received. Telegram = {telegram_resp}')
            else:
                if tbot_users(chat_id).login != login or \
                        tbot_users(chat_id).first_name != first_name:
                    DBLoader.update_user(chat_id, login, first_name)
        privileges = tbot_users(chat_id).privileges
        if message.content_type == 'text':
            form_text = message.text.strip().rstrip()
            action = form_text.split()[0].lower()
            action = localization.get(action)
            func = TBot.mapping.get(action, TBot.file_loader.get_hello)
            request = LoaderRequest(
                text=form_text,
                privileges=privileges,
                chat_id=chat_id
            )
            log_request = None
            if config.USE_DB:
                try:
                    log_request = TBot.db_loader.log_request(
                        chat_id=chat_id
                    )
                except (OperationalError, exc.OperationalError) as e:
                    send_data = dict(subject=f'TBot DB connection error', text=f'{e}')
                    send_dev_message(data=send_data, by='telegram')
                    TBot.internet_loader.tbot_restart(request=request)
            try:
                res = asyncio.run(func(request=request)) \
                    if inspect.iscoroutinefunction(func.__wrapped__) \
                    else func(request=request)
            except (
                aiohttp.client_exceptions.ClientConnectionError,
                aiohttp.client_exceptions.ClientConnectorCertificateError,
                RuntimeError
            ):
                pass
            if config.USE_DB and action in TBot.mapping.keys() and res.is_extra_log:
                res.extra_log(request_id=log_request.lr_id, action=action)
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
        curdir = os.curdir
        if message.content_type == 'photo':
            file_extension = '.jpg'
            file_info = TBot.bot.get_file(message.photo[-1].file_id)
        elif message.content_type == 'audio':
            file_extension = '.mp3'
            file_info = TBot.bot.get_file(message.audio.file_id)
        elif message.content_type == 'voice':
            file_extension = '.mp3'
            file_info = TBot.bot.get_file(message.voice.file_id)
        elif message.content_type == 'video':
            file_extension = '.mp4'
            file_info = TBot.bot.get_file(message.video.file_id)
        else:
            raise TBotException(code=2, return_message='Я пока не умею обрабатывать этот тип данных')
        if not os.path.exists(
            os.path.join(curdir, 'downloads', message.content_type)
        ):
            os.mkdir(
                os.path.join(curdir, 'downloads', message.content_type)
            )
            os.chown(
                os.path.join(curdir, 'downloads', message.content_type),
                1000,
                1000
            )
        file_name = os.path.join(
            curdir, 'downloads', message.content_type, f'{now_time()}{get_hash_name()}{file_extension}'
        )
        downloaded_info = TBot.bot.download_file(file_info.file_path)
        with open(file_name, 'wb') as new_file:
            new_file.write(downloaded_info)
        os.chown(file_name, 1000, 1000)

    @staticmethod
    def run():
        """
        Main method
        """
        TBot.init_bot()
        # отправка сообщения о начале работы только с прода
        if config.PROD:
            logger.info(f'Send start message to root users')
            send_dev_message({'text': 'TBot is started'}, 'telegram')
        while True:
            try:
                TBot.bot.infinity_polling(none_stop=True)
            except (
                url_lib_exceptions.NewConnectionError,
                url_lib_exceptions.MaxRetryError,
                url_lib_exceptions.ConnectionError,
            ) as url_lib_ex:
                logger.exception(url_lib_ex)



if __name__ == '__main__':
    TBot.run()
