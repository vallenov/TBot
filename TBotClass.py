import configparser
import logging
import traceback
import datetime
import asyncio
import requests

from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

from loaders.loader import Loader, check_permission
from loaders.internet_loader import InternetLoader
from loaders.file_loader import FileLoader
from loaders.db_loader import DBLoader

MAX_TRY = 15

logger = logging.getLogger(__name__)
handler = logging.FileHandler('run.log')
handler.setLevel(logging.INFO)
handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)


def benchmark(func):
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
        if not self.db_loader.use_db:
            self.file_loader = FileLoader('FLoader')

    def __del__(self):
        logger.error(f'Traceback: {traceback.format_exc()}')
        logger.info('TBotClass deleted')

    @benchmark
    def replace(self, message) -> dict:
        """
        Send result message to chat
        :param message: message from user
        :return: replace string
        """
        resp = {}
        self._get_config()
        chat_id = str(message.json['chat']['id'])
        if self.internet_loader.use_db and chat_id not in Loader.users.keys():
            login = message.json['chat'].get('username', None)
            first_name = message.json['chat'].get('first_name', None)
            privileges = Loader.privileges_levels['regular']
            self.db_loader.add_user(user_id=chat_id,
                                    privileges=privileges,
                                    login=login,
                                    first_name=first_name)
            send_data = dict()
            send_data['subject'] = 'TBot NEW USER'
            send_data['text'] = f'New user added. Chat_id: {chat_id}, login: {login}, first_name: {first_name}'
            self.send_dev_message(send_data)
        else:
            privileges = Loader.users[chat_id]['value']
        if message.content_type == 'text':
            resp['status'] = 'OK'
            form_text = message.text.lower().strip()
            if form_text == 'exchange' or form_text == 'валюта':
                resp['res'] = self._dict_to_str(self.internet_loader.get_exchange(privileges=privileges))
            elif form_text == 'weather' or form_text == 'погода':
                resp['res'] = self._dict_to_str(self.internet_loader.get_weather(privileges=privileges))
            elif form_text == 'quote' or form_text == 'цитата':
                resp['res'] = self._dict_to_str(self.internet_loader.get_quote(privileges=privileges), '\n')
            elif form_text == 'wish' or form_text == 'пожелание':
                resp['res'] = self._dict_to_str(self.internet_loader.get_wish(privileges=privileges))
            elif form_text.startswith('news') or form_text.startswith('новости'):
                resp['res'] = self._dict_to_str(self.internet_loader.get_news(form_text, privileges=privileges), '\n')
            elif form_text == 'affirmation' or form_text == 'аффирмация':
                resp['res'] = self._dict_to_str(self.internet_loader.get_affirmation(privileges=privileges))
            elif form_text == 'events' or form_text == 'мероприятия':
                resp['res'] = self._dict_to_str(asyncio.run(self.internet_loader.async_events(privileges=privileges)),
                                                '\n')
            elif form_text == 'food' or form_text == 'еда':
                resp['res'] = self._dict_to_str(self.internet_loader.get_restaurant(privileges=privileges), ' ')
            elif form_text.startswith('poem') or form_text.startswith('стих'):
                if self.db_loader.use_db:
                    resp['res'] = self._dict_to_str(self.db_loader.get_poem(form_text, privileges=privileges), '\n')
                else:
                    resp['res'] = self._dict_to_str(self.file_loader.get_poem(form_text, privileges=privileges), '\n')
            elif form_text.startswith('movie') or form_text.startswith('фильм'):
                resp['res'] = self._dict_to_str(
                    self.internet_loader.get_random_movie(form_text, privileges=privileges), ' ')
                if ' ' not in form_text:
                    resp['markup'] = self._gen_movie_markup(privileges=privileges)
            elif form_text.startswith('update') or form_text.startswith('обновить'):
                resp['res'] = self._dict_to_str(self.db_loader.update_user(form_text, privileges=privileges), ' ')
            elif form_text.startswith('delete') or form_text.startswith('удалить'):
                resp['res'] = self._dict_to_str(self.db_loader.delete_user(form_text, privileges=privileges), ' ')
            elif form_text == 'users' or form_text == 'пользователи':
                resp['res'] = self._dict_to_str(self.db_loader.show_users(privileges=privileges), ' ')
            elif form_text == 'hidden_functions' or form_text == 'скрытые_функции':
                resp['res'] = self._dict_to_str(self._get_help(privileges=privileges), ' ')
            elif form_text == 'admins_help' or form_text == 'руководство_админу':
                resp['res'] = self._dict_to_str(self._get_admins_help(privileges=privileges), ' ')
            elif form_text.startswith('send_other') or form_text.startswith('отправить_другому'):
                resp = self.send_other(form_text, privileges=privileges)
                if resp['res'] == 'ERROR':
                    resp['res'] = self._dict_to_str(resp)
            elif TBotClass._is_phone_number(form_text) is not None:
                phone_number = TBotClass._is_phone_number(form_text)
                resp['res'] = self._dict_to_str(
                    self.internet_loader.get_phone_number_info(phone_number, privileges=privileges), ': '
                )
            else:
                resp['res'] = self._dict_to_str(self._get_hello(privileges=privileges))
                resp['markup'] = self._gen_markup(privileges=privileges)
            return resp

    @staticmethod
    def _gen_movie_markup(privileges: int):
        markup = InlineKeyboardMarkup()
        markup.row_width = 1
        if Loader.privileges_levels['untrusted'] <= privileges:
            pass
        if Loader.privileges_levels['test'] <= privileges:
            pass
        if Loader.privileges_levels['regular'] <= privileges:
            markup.add(InlineKeyboardButton("🎞 1950-1960", callback_data="movie 1950 1960"),
                       InlineKeyboardButton("🎞 1960-1970", callback_data="movie 1960 1970"),
                       InlineKeyboardButton("🎞 1970-1980", callback_data="movie 1970 1980"),
                       InlineKeyboardButton("🎞 1980-1990", callback_data="movie 1980 1990"),
                       InlineKeyboardButton("🎞 1990-2000", callback_data="movie 1990 2000"),
                       InlineKeyboardButton("🎞 2000-2010", callback_data="movie 2000 2010"),
                       InlineKeyboardButton("🎞 2010-2020", callback_data="movie 2010 2020"))
        if Loader.privileges_levels['trusted'] <= privileges:
            pass
        if Loader.privileges_levels['root'] <= privileges:
            pass
        return markup

    @staticmethod
    def _gen_markup(privileges: int):
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
                       InlineKeyboardButton("🎞 Movie/Фильм", callback_data="movie"))
        if Loader.privileges_levels['trusted'] <= privileges:
            pass
        if Loader.privileges_levels['root'] <= privileges:
            markup.add(InlineKeyboardButton("🛠 Admins help/Руководство админу", callback_data="admins_help"))
            markup.add(InlineKeyboardButton("👥 Users/Пользователи", callback_data="users"))
        return markup

    @staticmethod
    def _dict_to_str(di: dict, delimiter: str = ' = ') -> str:
        fin_str = ''
        if di.get('res').upper() == 'ERROR':
            descr = di.get('descr', None)
            if descr is not None:
                logger.error(f'Description: {descr}')
                return descr
            return 'Something is wrong'
        for key, value in di.items():
            if isinstance(key, int):
                fin_str += f'{value}\n'
            elif key.lower() == 'res' or key.lower() == 'len' or key.lower() == 'chat_id':
                continue
            else:
                fin_str += f'{key}{delimiter}{value}\n'
        return fin_str

    @check_permission()
    def _get_help(self, privileges: int) -> dict:
        """
        Get bot functions
        :param privileges: user privileges
        :return: {'res': 'OK or ERROR', 'text': 'message'}
        """
        logger.info('get_help')
        resp = dict()
        resp['res'] = 'OK'
        # if Loader.privileges_levels['untrusted'] <= privileges:
        #     return Loader.error_resp('Permission denied')
        # if Loader.privileges_levels['test'] <= privileges:
        #     return Loader.error_resp('Permission denied')
        if Loader.privileges_levels['regular'] <= privileges:
            resp[0] = str(f'Ты можешь написать "новости", "стих" и "фильм" с параметром\n'
                          f'Новости "количество новостей"\n'
                          f'Стих "имя автора или название"\n'
                          f'Фильм "год выпуска"\n'
                          f'Так же, ты можешь написать номер телефона, что бы узнать информацию о нем\n')
        if Loader.privileges_levels['trusted'] <= privileges:
            pass
        if Loader.privileges_levels['root'] <= privileges:
            pass
        return resp

    @check_permission()
    def _get_hello(self, privileges: int) -> dict:
        """
        Get hello from bot
        :param privileges: user privileges
        :return: {'res': 'OK or ERROR', 'text': 'message'}
        """
        logger.info('get_help')
        resp = dict()
        resp['res'] = 'OK'
        # if Loader.privileges_levels['untrusted'] <= privileges:
        #     resp[0] = f'Permission denied'
        # if Loader.privileges_levels['test'] <= privileges:
        #     resp[0] = f'Permission denied'
        if Loader.privileges_levels['regular'] <= privileges:
            resp[0] = f'Привет! Меня зовут InfoBot\n'
        if Loader.privileges_levels['trusted'] <= privileges:
            pass
        if Loader.privileges_levels['root'] <= privileges:
            resp[0] = f'You are a root user'
        return resp

    @check_permission(needed_level='root')
    def _get_admins_help(self, **kwargs) -> dict:
        """
        Get bot functions for admin
        :param :
        :return:
        """
        logger.info('get_admins_help')
        resp = dict()
        resp['res'] = 'OK'
        resp[0] = str(f'Update "chat_id" "privileges"\n'
                      f'Delete "chat_id"\n'
                      f'Send_other "chat_id" "text"\n')
        return resp

    def _get_config(self):
        self.config = configparser.ConfigParser()
        self.config.read('TBot.ini', encoding='windows-1251')

    @staticmethod
    def _is_phone_number(number: str) -> str or None:
        resp = {}
        if len(number) < 10 or len(number) > 18:
            return None
        allowed_simbols = '0123456789+()- '
        for num in number:
            if num not in allowed_simbols:
                return None
        raw_num = number
        raw_num = raw_num.strip()
        raw_num = raw_num.replace(' ', '')
        raw_num = raw_num.replace('+', '')
        raw_num = raw_num.replace('(', '')
        raw_num = raw_num.replace(')', '')
        raw_num = raw_num.replace('-', '')
        if len(raw_num) < 11:
            raw_num = '8' + raw_num
        if raw_num.startswith('7'):
            raw_num = '8' + raw_num[1:]
        if not raw_num.startswith('89'):
            resp['res'] = 'ERROR'
            resp['descr'] = 'Number format is not valid'
            return None
        return raw_num

    @check_permission(needed_level='root')
    def send_other(self, text: str, **kwargs):
        """
        Get respoesy from DB
        :param:
        :return: poesy string
        """
        logger.info('send_other')
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
        resp['res'] = ' '.join(lst[2:])
        return resp

    def send_dev_message(self, data: dict):
        """
        Отправка сообщения админу
        :param data: {'to': name or email, 'subject': 'subject' (unnecessary), 'text': 'text'}
        """
        data.update({'to': self.config.get('MAIL', 'address')})
        current_try = 0
        while current_try < MAX_TRY:
            current_try += 1
            try:
                requests.post(self.config.get('MAIL', 'message_server_address'), data=data,
                              headers={'Connection': 'close'})
            except Exception as _ex:
                logger.exception(_ex)
            else:
                logger.info('Send successful')
                break
        logger.error('Max try exceeded')
