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
        # self._get_config()
        self.internet_loader = InternetLoader('ILoader')
        self.file_loader = FileLoader('FLoader')
        self.db_loader = DBLoader('DBLoader')

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
        if chat_id not in Loader.users.keys():
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
            # elif form_text == 'events':
            #     resp['res'] = self._dict_to_str(self._get_events(), '\n')
            #     return resp
            elif form_text == 'events' or form_text == 'мероприятия':
                resp['res'] = self._dict_to_str(asyncio.run(self.internet_loader.async_events(privileges=privileges)),
                                                '\n')
            elif form_text == 'food' or form_text == 'еда':
                resp['res'] = self._dict_to_str(self.internet_loader.get_restaurant(privileges=privileges), ' ')
            elif form_text.startswith('poem') or form_text.startswith('стих'):
                resp['res'] = self._dict_to_str(self.file_loader.get_poem(form_text, privileges=privileges), '\n')
                # resp['res'] = self._dict_to_str(self.internet_loader.get_poem(), '')
            elif form_text.startswith('movie') or form_text.startswith('фильм'):
                resp['res'] = self._dict_to_str(
                    self.internet_loader.get_random_movie(form_text, privileges=privileges), ' ')
            elif form_text.startswith('update') or form_text.startswith('обновить'):
                resp['res'] = self._dict_to_str(self.db_loader.update_user(form_text, privileges=privileges), ' ')
            elif form_text == 'users' or form_text == 'пользователи':
                resp['res'] = self._dict_to_str(self.db_loader.show_users(privileges=privileges), ' ')
            elif TBotClass._is_phone_number(form_text) is not None:
                phone_number = TBotClass._is_phone_number(form_text)
                resp['res'] = self._dict_to_str(
                    self.internet_loader.get_phone_number_info(phone_number, privileges=privileges), ': '
                )
            else:
                resp['res'] = self._dict_to_str(self._get_help(privileges=privileges), ' ')
                resp['markup'] = self._gen_markup(privileges)
            return resp

    @staticmethod
    def _gen_markup(privileges: int):
        markup = InlineKeyboardMarkup()
        markup.row_width = 1
        if Loader.privileges_levels['untrusted'] <= privileges < Loader.privileges_levels['test']:
            pass
        if Loader.privileges_levels['test'] <= privileges < Loader.privileges_levels['regular']:
            pass
        if Loader.privileges_levels['regular'] <= privileges < Loader.privileges_levels['trusted']:
            pass
        markup.add(InlineKeyboardButton("💵 Exchange/Курс валют", callback_data="exchange"),
                   InlineKeyboardButton("⛅️Weather/Погода", callback_data="weather"),
                   InlineKeyboardButton("💭 Quote/Цитата", callback_data="quote"),
                   InlineKeyboardButton("🤗 Wish/Пожелание", callback_data="wish"),
                   InlineKeyboardButton("📰 News/Новости", callback_data="news"),
                   InlineKeyboardButton("🧘‍♀️Affirmation/Аффирмация", callback_data="affirmation"),
                   InlineKeyboardButton("🎭 Events/Мероприятия", callback_data="events"),
                   InlineKeyboardButton("🍲 Food/Еда", callback_data="food"),
                   InlineKeyboardButton("🪶 Poem/Стих", callback_data="poem"),
                   InlineKeyboardButton("🎞 Movie/Фильм", callback_data="movie"))
        if Loader.privileges_levels['trusted'] <= privileges < Loader.privileges_levels['root']:
            pass
        if privileges >= Loader.privileges_levels['root']:
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
            elif key.lower() == 'res' or key.lower() == 'len':
                continue
            else:
                fin_str += f'{key}{delimiter}{value}\n'
        return fin_str

    @check_permission()
    def _get_help(self, **kwargs) -> dict:
        """
        Get bot function
        :param dev: change view of help
        :return: {'func': 'description', ...}
        """
        logger.info('get_help')
        resp = {}
        resp['res'] = 'OK'
        resp['(RU)'] = str(f'Привет! Меня зовут InfoBot\n'
                           f'Ты можешь написать "новости", "стих" и "фильм" с параметром\n'
                           f'Новости "количество новостей"\n'
                           f'Стих "имя автора"\n'
                           f'Фильм "год выпуска"\n'
                           f'Так же, ты можешь написать номер телефона, что бы узнать информацию о нем\n'
                           f'Или используй следующие кнопки без параметров\n')
        resp['(ENG)'] = str(f'Hello! My name is InfoBot\n'
                            f'You may write "news", "poem" and "movie" with parameter\n'
                            f'News "count of news"\n'
                            f'Poem "author name"\n'
                            f'Movie "release year"\n'
                            f'Also you can write phone number to find out information about it\n'
                            f'Or use the next buttons without parameters\n')
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
