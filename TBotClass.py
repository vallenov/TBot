import configparser
import logging
import traceback
import datetime
import asyncio

from loaders.internet_loader import InternetLoader
from loaders.file_loader import FileLoader
from loaders.db_loader import DBLoader

logger = logging.getLogger(__name__)
handler = logging.FileHandler('run.log')
handler.setLevel(logging.INFO)
handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)


def check_permission(func):
    """
    Check permission before execute func
    :param func: input func
    :return: wrapped func
    """
    def wrap(*args, **kwargs):
        resp = {}
        if not TBotClass.permission:
            logger.error('Permission denied')
            resp['res'] = "ERROR"
            resp['descr'] = 'Permission denied'
            res = resp
        else:
            res = func(*args, **kwargs)
        return res
    return wrap


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
        self.__get_config()
        self.internet_loader = InternetLoader('ILoader')
        self.file_loader = FileLoader('FLoader')
        #self.db_loader = DBLoader('DBLoader')

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
        trust_ids = []
        if ',' in self.config['MAIN']['trust_ids'].split(','):
            trust_ids = list(map(lambda x: int(x), self.config['MAIN']['trust_ids'].split(',')))
        else:
            trust_ids.append(int(self.config['MAIN']['trust_ids']))
        if message.json['chat']['id'] == int(self.config['MAIN']['root_id']):
            TBotClass.permission = True
        elif message.json['chat']['id'] in trust_ids:
            TBotClass.permission = False
        else:
            resp['status'] = 'ERROR'
            resp['res'] = 'Permission denied'
            return resp
        if message.content_type == 'text':
            resp['status'] = 'OK'
            form_text = message.text.lower().strip()
            if form_text == 'exchange' or form_text == 'валюта':
                resp['res'] = self.__dict_to_str(self.internet_loader.get_exchange())
                return resp
            elif form_text == 'weather' or form_text == 'погода':
                resp['res'] = self.__dict_to_str(self.internet_loader.get_weather())
                return resp
            elif form_text == 'quote' or form_text == 'цитата':
                resp['res'] = self.__dict_to_str(self.internet_loader.get_quote(), '\n')
                return resp
            elif form_text == 'wish' or form_text == 'пожелание':
                resp['res'] = self.__dict_to_str(self.internet_loader.get_wish())
                return resp
            elif form_text.startswith('news') or form_text.startswith('новости'):
                resp['res'] = self.__dict_to_str(self.internet_loader.get_news(form_text), '\n')
                return resp
            elif form_text == 'affirmation' or form_text == 'аффирмация':
                resp['res'] = self.__dict_to_str(self.internet_loader.get_affirmation())
                return resp
            # elif form_text == 'events':
            #     resp['res'] = self.__dict_to_str(self._get_events(), '\n')
            #     return resp
            elif form_text == 'events' or form_text == 'мероприятия':
                resp['res'] = self.__dict_to_str(asyncio.run(self.internet_loader.async_events()), '\n')
                return resp
            elif form_text == 'food' or form_text == 'еда':
                resp['res'] = self.__dict_to_str(self.internet_loader.get_restaurant(), ' ')
                return resp
            elif form_text.startswith('poem') or form_text.startswith('стих'):
                resp['res'] = self.__dict_to_str(self.file_loader.get_poem(form_text), '\n')
                #resp['res'] = self.__dict_to_str(self.internet_loader.get_poem(), '')
                return resp
            elif TBotClass._is_phone_number(form_text) is not None:
                phone_number = TBotClass._is_phone_number(form_text)
                resp['res'] = self.__dict_to_str(self.internet_loader.get_phone_number_info(phone_number), ': ')
                return resp
            else:
                resp['is_help'] = 1
                resp['res'] = str(f'Hello! My name is DevInfoBot\n'
                                  f'You may read "news" and "poem" with parameter\n'
                                  f'News "count of news"\n'
                                  f'Poem "author name"\n'
                                  f'Or use the next buttons without parameters\n')
                return resp

    @staticmethod
    def __dict_to_str(di: dict, delimiter: str = ' = ') -> str:
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

    def __get_help(self, dev: bool) -> dict:
        """
        Get bot function
        :param dev: change view of help
        :return: {'func': 'description', ...}
        """
        logger.info('get_help')
        docs_str = {}
        if dev:
            docs = list(filter(lambda x: '__' not in x and x.startswith('_'), dir(self)))
            for doc in docs:
                if str(eval(f'self.{doc}.__doc__')) is not None:
                    docs_str[doc] = str(eval(f'self.{doc}.__doc__')).split('\n')[1].strip()
        else:
            docs_str['ex'] = 'Получить курс доллара и евро'
            docs_str['weather'] = 'Получить прогноз погоды'
            docs_str['quote'] = 'Получить цитату'
            docs_str['wish'] = 'Получить пожелание на день'
            docs_str['news'] = 'Получить последние новости (после news можно указать число новостей)'
            docs_str['affirmation'] = 'Получить аффирмацию'
            docs_str['events'] = 'Получить мероприятия'
        docs_str['res'] = 'OK'
        return docs_str

    def __get_config(self):
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
