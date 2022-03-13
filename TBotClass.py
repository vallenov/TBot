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
    """
    Count duration
    """

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
        self._get_config()
        self.is_prod = int(self.config.get('MAIN', 'PROD'))
        if self.is_prod:
            logger.info(f'Send start message to root users')
            self.send_dev_message({'text': 'TBot is started'}, 'telegram')

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
        self._get_config()
        chat_id = str(message.json['chat']['id'])
        if self.internet_loader.use_db and chat_id not in Loader.users.keys():
            login = message.json['chat'].get('username', None)
            first_name = message.json['chat'].get('first_name', None)
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
            privileges = Loader.users[chat_id]['value']
        if self.internet_loader.use_db:
            self.db_loader.log_request(chat_id)
        if message.content_type == 'text':
            resp['status'] = 'OK'
            form_text = message.text.lower().strip()
            if form_text == 'exchange' or form_text == 'валюта':
                resp = self.internet_loader.get_exchange(privileges=privileges)
            elif form_text == 'weather' or form_text == 'погода':
                resp = self.internet_loader.get_weather(privileges=privileges)
            elif form_text == 'quote' or form_text == 'цитата':
                resp = self.internet_loader.get_quote(privileges=privileges)
            elif form_text == 'wish' or form_text == 'пожелание':
                resp = self.internet_loader.get_wish(privileges=privileges)
            elif form_text.startswith('news') or form_text.startswith('новости'):
                resp = self.internet_loader.get_news(form_text, privileges=privileges)
            elif form_text == 'affirmation' or form_text == 'аффирмация':
                resp = self.internet_loader.get_affirmation(privileges=privileges)
            elif form_text == 'events' or form_text == 'мероприятия':
                resp = asyncio.run(self.internet_loader.async_events(privileges=privileges))
            elif form_text == 'food' or form_text == 'еда':
                resp = self.internet_loader.get_restaurant(privileges=privileges)
            elif form_text.startswith('poem') or form_text.startswith('стих'):
                if self.db_loader.use_db:
                    resp = self.db_loader.get_poem(form_text, privileges=privileges)
                else:
                    if not hasattr(self.file_loader, 'poems'):
                        self.file_loader.load_poems()
                    resp = self.file_loader.get_poem(form_text, privileges=privileges)
            elif form_text.startswith('movie') or form_text.startswith('фильм'):
                resp = self.internet_loader.get_random_movie(form_text, privileges=privileges)
                if ' ' not in form_text and not resp['text'].startswith('Permission denied'):
                    resp['markup'] = self.gen_custom_markup('movie',
                                                            ['1950-1960', '1960-1970', '1970-1980',
                                                             '1980-1990', '1990-2000', '2000-2010', '2010-2020'],
                                                            '🎞')
            elif form_text.startswith('book') or form_text.startswith('книга'):
                resp = self.internet_loader.get_book(form_text, privileges=privileges)
                if ' ' not in form_text and not resp['text'].startswith('Permission denied'):
                    resp['markup'] = self.gen_custom_markup('book', self.internet_loader.book_genres, '📖')
            elif form_text.startswith('update') or form_text.startswith('обновить'):
                resp = self.db_loader.update_user(form_text, privileges=privileges)
            elif form_text.startswith('delete') or form_text.startswith('удалить'):
                resp = self.db_loader.delete_user(form_text, privileges=privileges)
            elif form_text == 'users' or form_text == 'пользователи':
                resp = self.db_loader.show_users(privileges=privileges)
            elif form_text == 'hidden_functions' or form_text == 'скрытые_функции':
                resp = self._get_help(privileges=privileges)
            elif form_text == 'admins_help' or form_text == 'руководство_админу':
                resp = self._get_admins_help(privileges=privileges)
            elif form_text.startswith('send_other') or form_text.startswith('отправить_другому'):
                resp = self.send_other(form_text, privileges=privileges)
            elif form_text == 'metaphorical_card' or form_text == 'метафорическая_карта':
                resp = self.file_loader.get_metaphorical_card(privileges=privileges)
            elif form_text == 'russian_painting' or form_text == 'русская_картина':
                resp = self.internet_loader.get_russian_painting(privileges=privileges)
            elif form_text == 'ip':
                resp = self.file_loader.get_server_ip(privileges=privileges)
            elif form_text.startswith('statistic') or form_text.startswith('статистика'):
                resp = self.db_loader.get_statistic(form_text, privileges=privileges)
                if ' ' not in form_text and not resp['text'].startswith('Permission denied'):
                    resp['markup'] = self.gen_custom_markup('statistic',
                                                            ['Today', 'Week', 'Month', 'All'],
                                                            '📋')
            elif TBotClass._is_phone_number(form_text) is not None:
                phone_number = TBotClass._is_phone_number(form_text)
                resp = self.internet_loader.get_phone_number_info(phone_number, privileges=privileges)
            else:
                resp = self._get_hello(privileges=privileges)
            return resp

    @staticmethod
    def gen_custom_markup(command,  category, smile='🔹', row_width=1):
        markup = InlineKeyboardMarkup()
        markup.row_width = row_width
        if isinstance(category, dict):
            item = category.keys()
        if isinstance(category, list):
            item = category
        for cat in item:
            short_cat = cat.split()[0]
            short_cat = short_cat.replace(',', '')
            short_cat = short_cat.lower()
            markup.add(InlineKeyboardButton(f'{smile} {cat}', callback_data=f'{command} {short_cat}'))
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
                       InlineKeyboardButton("🎞 Movie/Фильм", callback_data="movie"),
                       InlineKeyboardButton("📖 Book/Книга", callback_data="book"),
                       InlineKeyboardButton("🎑 Metaphorical card/Метафорическая карта",
                                            callback_data="metaphorical_card"),
                       InlineKeyboardButton("🏞 Russian painting/Русская картина", callback_data="russian_painting"))
        if Loader.privileges_levels['trusted'] <= privileges:
            pass
        if Loader.privileges_levels['root'] <= privileges:
            markup.add(InlineKeyboardButton("🛠 Admins help/Руководство админу", callback_data="admins_help"),
                       InlineKeyboardButton("👥 Users/Пользователи", callback_data="users"),
                       InlineKeyboardButton("🌐 Server IP/IP-адрес сервера", callback_data="ip"),
                       InlineKeyboardButton("📋 Statistic/Статистика", callback_data="statistic"))
        return markup

    @check_permission()
    def _get_help(self, privileges: int) -> dict:
        """
        Get bot functions
        :param privileges: user privileges
        :return: {'res': 'OK or ERROR', 'text': 'message'}
        """
        resp = dict()
        resp['text'] = ''
        # if Loader.privileges_levels['untrusted'] <= privileges:
        #     return Loader.error_resp('Permission denied')
        # if Loader.privileges_levels['test'] <= privileges:
        #     return Loader.error_resp('Permission denied')
        if Loader.privileges_levels['regular'] <= privileges:
            resp['text'] += str(f'Ты можешь написать "новости", "стих" и "фильм" с параметром\n'
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
        resp = dict()
        # if Loader.privileges_levels['untrusted'] <= privileges:
        #     resp[0] = f'Permission denied'
        # if Loader.privileges_levels['test'] <= privileges:
        #     resp[0] = f'Permission denied'
        if Loader.privileges_levels['regular'] <= privileges:
            resp['text'] = f'Привет! Меня зовут InfoBot\n'
        if Loader.privileges_levels['trusted'] <= privileges:
            pass
        if Loader.privileges_levels['root'] <= privileges:
            resp['text'] = f'You are a root user'
        resp['markup'] = self._gen_markup(privileges)
        return resp

    @check_permission(needed_level='root')
    def _get_admins_help(self, **kwargs) -> dict:
        """
        Get bot functions for admin
        :param :
        :return:
        """
        resp = dict()
        resp['text'] = str(f'Update "chat_id" "privileges"\n'
                           f'Delete "chat_id"\n'
                           f'Send_other "chat_id" "text"\n')
        return resp

    def _get_config(self):
        self.config = configparser.ConfigParser()
        self.config.read('TBot.ini', encoding='windows-1251')

    @staticmethod
    def _is_phone_number(number: str) -> str or None:
        """
        Check string. If non phone number, return None. Else return formatted phone number
        :param number: any format of phone number
        :return: formatted phone number
        """
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
            resp['res'] = 'ERROR'
            resp['descr'] = f'Wrong parameter by ({by}) in send_dev_message'
            logger.error(resp['descr'])
            return resp
        if by == 'mail':
            data.update({'to': self.config.get('MAIL', 'address')})
        else:
            data.update({'to': self.config.get('DB', 'login')})
        current_try = 0
        while current_try < MAX_TRY:
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
