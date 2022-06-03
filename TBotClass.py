import configparser
import logging
import traceback
import datetime
import asyncio
import requests
import inspect
from functools import wraps

import config

from loaders.loader import Loader, check_permission
from loaders.internet_loader import InternetLoader
from loaders.file_loader import FileLoader
from loaders.db_loader import DBLoader

logger = logging.getLogger(__name__)
handler = logging.FileHandler('run.log')
handler.setLevel(logging.INFO)
handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)


def benchmark(func):
    """
    Count duration
    """
    @wraps(func)
    def wrap(*args, **kwargs):
        start = datetime.datetime.now()
        res = func(*args, **kwargs)
        duration = datetime.datetime.now() - start
        dur = float(str(duration.seconds) + '.' + str(duration.microseconds)[:3])
        logger.info(f'Duration: {dur} sec')
        return res

    return wrap


class TBotClass:
    permission = False

    def __init__(self):
        logger.info('TBotClass init')
        self.internet_loader = InternetLoader('ILoader')
        self.db_loader = DBLoader('DBLoader')
        self.file_loader = FileLoader('FLoader')
        self.get_config()
        self.is_prod = config.MAIN.get('PROD')
        if self.is_prod:
            logger.info(f'Send start message to root users')
            self.send_dev_message({'text': 'TBot is started'}, 'telegram')
        self.mapping = {
            'exchange': self.internet_loader.get_exchange,
            'weather': self.internet_loader.get_weather,
            'quote': self.internet_loader.get_quote,
            'wish': self.internet_loader.get_wish,
            'news': self.internet_loader.get_news,
            'affirmation': self.internet_loader.get_affirmation,
            'events': self.internet_loader.async_events,
            'food': self.internet_loader.get_restaurant,
            'poem': self.db_loader.get_poem if self.internet_loader.use_db else self.file_loader.get_poem,
            'movie': self.internet_loader.get_random_movie,
            'book': self.internet_loader.get_book,
            'update': self.db_loader.update_user_privileges,
            'users': self.db_loader.show_users,
            'hidden_functions': self.get_help,
            'admins_help': self.get_admins_help,
            'send_other': self.send_other,
            'metaphorical_card': self.file_loader.get_metaphorical_card,
            'russian_painting': self.internet_loader.get_russian_painting,
            'ip': self.file_loader.get_server_ip,
            'statistic': self.db_loader.get_statistic,
            'phone': self.internet_loader.get_phone_number_info,
            'camera': self.file_loader.get_camera_capture,
            'default': self.get_hello
        }

    def __del__(self):
        logger.error(f'Traceback: {traceback.format_exc()}')
        logger.info('TBotClass deleted')

    @benchmark
    def replace(self, message) -> dict:
        """
        Send result message to chat
        :param message: message from user
        :return: replace dict
        """
        resp = {}
        self.get_config()
        chat_id = str(message.json['chat']['id'])
        if self.internet_loader.use_db:
            login = message.json['chat'].get('username', None)
            first_name = message.json['chat'].get('first_name', None)
            if chat_id not in Loader.users.keys():
                privileges = Loader.privileges_levels['regular']
                self.db_loader.add_user(chat_id=chat_id,
                                        privileges=privileges,
                                        login=login,
                                        first_name=first_name)
                send_data = dict()
                send_data['subject'] = 'TBot NEW USER'
                send_data['text'] = f'New user added. Chat_id: {chat_id}, login: {login}, first_name: {first_name}'
                mail_resp = self.send_dev_message(send_data, 'mail')
                telegram_resp = self.send_dev_message(send_data, 'telegram')
                if mail_resp['res'] == 'ERROR' or telegram_resp['res'] == 'ERROR':
                    logger.warning(f'Message do not received. MAIL = {mail_resp}, Telegram = {telegram_resp}')
            else:
                if Loader.users[chat_id]['login'] != login or \
                   Loader.users[chat_id]['first_name'] != first_name:
                    self.db_loader.update_user(chat_id, login, first_name)
        privileges = Loader.users[chat_id]['value']
        if self.internet_loader.use_db:
            self.db_loader.log_request(chat_id)

        if message.content_type == 'text':
            resp['status'] = 'OK'
            form_text = message.text.lower().strip()
            sptext = form_text.split()
            default_func = self.mapping.get('default')
            func = self.mapping.get(sptext[0], default_func)
            if not inspect.iscoroutinefunction(func.__wrapped__):
                return func(privileges=privileges, text=form_text)
            else:
                return asyncio.run(func(privileges=privileges, text=form_text))

    @check_permission()
    def get_help(self, privileges: int, **kwargs) -> dict:
        """
        Get bot functions
        :param privileges: user privileges
        :return: {'res': 'OK or ERROR', 'text': 'message'}
        """
        resp = dict()
        resp['text'] = ''
        if Loader.privileges_levels['regular'] <= privileges:
            resp['text'] += str(f'Ты можешь написать "новости", "стих" и "фильм" с параметром\n'
                                f'Новости "количество новостей"\n'
                                f'Стих "имя автора или название"\n'
                                f'Фильм "год выпуска" или "промежуток", например "фильм 2001-2005"\n'
                                f'Так же, ты можешь написать phone и номер телефона, что бы узнать информацию о нем\n')
        if Loader.privileges_levels['trusted'] <= privileges:
            pass
        if Loader.privileges_levels['root'] <= privileges:
            pass
        return resp

    @check_permission()
    def get_hello(self, privileges: int, **kwargs) -> dict:
        """
        Get hello from bot
        :param privileges: user privileges
        :return: {'res': 'OK or ERROR', 'text': 'message'}
        """
        resp = dict()
        if Loader.privileges_levels['regular'] <= privileges:
            resp['text'] = f'Привет! Меня зовут InfoBot\n'
        if Loader.privileges_levels['trusted'] <= privileges:
            pass
        if Loader.privileges_levels['root'] <= privileges:
            resp['text'] = f'You are a root user'
        resp['markup'] = Loader.main_markup(privileges)
        return resp

    @check_permission(needed_level='root')
    def get_admins_help(self, **kwargs) -> dict:
        """
        Get bot functions for admin
        :param :
        :return:
        """
        resp = dict()
        resp['text'] = str(f'Update "chat_id" "privileges"\n'
                           f'Send_other "chat_id" "text"\n')
        return resp

    def get_config(self):
        self.config = configparser.ConfigParser()
        self.config.read('TBot.ini', encoding='windows-1251')

    @check_permission(needed_level='root')
    def send_other(self, text: str, **kwargs):
        """
        Send message to other user
        :param text: string "command chat_id message"
        :return: dict {'chat_id': 1234567, 'text': 'some'}
        """
        resp = {}
        lst = text.split()
        if len(lst) < 3:
            Loader.error_resp('Format is not valid')
        chat_id = 0
        try:
            chat_id = int(lst[1])
        except ValueError as e:
            Loader.error_resp('Chat_id format is not valid')
        if str(chat_id) not in Loader.users.keys():
            return Loader.error_resp('User not found')
        resp['chat_id'] = chat_id
        resp['text'] = ' '.join(lst[2:])
        return resp

    def send_dev_message(self, data: dict, by: str = 'mail') -> dict:
        """
        Send message to admin
        :param data: {'to': name or email, 'subject': 'subject' (unnecessary), 'text': 'text'}
        :param by: by what (mail or telegram)
        """
        resp = {}
        if by not in ('mail', 'telegram'):
            Loader.error_resp(f'Wrong parameter by ({by}) in send_dev_message')
            logger.error(resp['descr'])
            return resp
        if by == 'mail':
            data.update({'to': config.MAIL.get('address')})
        else:
            data.update({'to': config.DB.get('login')})
        current_try = 0
        while current_try < config.CONSTANTS.get('MAX_TRY'):
            current_try += 1
            try:
                res = requests.post(self.config.get('MAIL', 'message_server_address') + '/' + by, data=data,
                                    headers={'Connection': 'close'})
            except Exception as _ex:
                logger.exception(_ex)
            else:
                logger.info('Send successful')
                resp['res'] = res.text
                return resp
        logger.error('Max try exceeded')
