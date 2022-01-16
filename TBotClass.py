import random
import requests
from bs4 import BeautifulSoup
import configparser
import logging
import traceback
import datetime


def check_permission(func):
    def wrap(*args, **kwargs):
        resp = {}
        if not TBotClass.permission:
            resp['res'] = "ERROR"
            res = resp
        else:
            res = func(*args, **kwargs)
        return res
    return wrap


class TBotClass:
    permission = False

    def __init__(self):
        logging.info('TBot is started')
        self.__get_config()

    def __del__(self):
        logging.error(f'Traceback: {traceback.format_exc()}')
        logging.info('TBot is stopped')

    def replace(self, message) -> str:
        """
        Send result message to chat
        :param message: message from user
        :return: replace string
        """
        if message.content_type == 'text':
            form_text = message.text.lower().strip()
            if form_text == 'ex':
                return self.__dict_to_str(self._get_exchange())
            elif form_text == 'weather':
                return self.__dict_to_str(self._get_weather())
            elif form_text == 'quote':
                return self.__dict_to_str(self._get_quote(), '\n')
            elif form_text == 'wish':
                return self._get_wish()
            elif form_text.startswith('news'):
                text_split = form_text.split()
                if len(text_split) > 1:
                    return self.__dict_to_str(self._get_news(int(text_split[1])), '\n')
                else:
                    return self.__dict_to_str(self._get_news(), '\n')
            else:
                return 'Hello! My name is DevInfoBot\nMy functions ->\n' + self.__dict_to_str(self.__get_help(False))

    @staticmethod
    def __dict_to_str(di: dict, delimiter: str = ' = ') -> str:
        fin_str = ''
        if di.get('res').upper() == 'ERROR':
            return 'Operation not permitted'
        for key, value in di.items():
            if key.lower() == 'res':
                continue
            fin_str += f'{key}{delimiter}{value}\n'
        return fin_str

    @staticmethod
    def _site_to_lxml(url: str) -> BeautifulSoup or None:
        """
        Get site and convert it to the lxml

        :param url: https://site.com/
        :return: BeautifulSoup object
        """
        try:
            soup = BeautifulSoup(requests.get(url).text, 'lxml')
        except Exception as _ex:
            logging.exception(f'Exception in {__name__}:\n{_ex}')
            return None
        else:
            logging.info(f'Get successful ({url})')
        return soup

    @staticmethod
    def get_logfile_name() -> str:
        """
        Get filename like: '2022-01-16'
        :return: filename
        """
        return str(datetime.datetime.now()).replace(':', '').replace(' ', '')[:10]

    def __get_help(self, dev: bool) -> dict:
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
        docs_str['res'] = 'OK'
        return docs_str

    def __get_config(self):
        self.config = configparser.ConfigParser()
        self.config.read('TBot.ini', encoding='windows-1251')

    def _get_exchange(self) -> dict:
        """
        Get exchange from internet
        :param:
        :return: string like {'USD': '73,6059', 'EUR':'83,1158'}
        """
        resp = {}
        ex = ['USD', 'EUR']
        soup = TBotClass._site_to_lxml(self.config['URL']['exchange_url'])
        if soup is None:
            resp['res'] = 'ERROR'
            return resp
        parse = soup.find_all('tr')
        for item in parse[1:]:
            inf = item.find_all('td')
            if inf[1].text not in ex:
                continue
            '''
            Structure of inf:
            tmp = {}
            tmp['id'] = inf[0].text
            tmp['name'] = inf[1].text
            tmp['e'] = inf[2].text
            tmp['descr'] = inf[3].text
            tmp['exchange'] = inf[4].text
            '''
            resp[inf[1].text] = inf[4].text
        resp['res'] = 'OK'
        return resp

    def _get_weather(self) -> dict:
        """
        Get weather from internet
        :param:
        :return: dict like {'Сегодня': '10°/15°', 'ср 12': '11°/18°'}
        """
        resp = {}
        soup = TBotClass._site_to_lxml(self.config['URL']['weather_url'])
        if soup is None:
            resp['res'] = 'ERROR'
            return resp
        parse = soup.find_all('div', class_='DetailsSummary--DetailsSummary--2HluQ DetailsSummary--fadeOnOpen--vFCc_')
        for i in parse:
            h2 = i.find('h2')
            div = i.find('div')
            span = div.find_all('span')
            span = list(map(lambda x: x.text, span))
            resp[h2.text] = ''.join(span[:-1])
        resp['res'] = 'OK'
        return resp

    def _get_quote(self) -> dict:
        """
        Get quote from internet
        :param:
        :return: dict like {'quote1': 'author1', 'quote2: 'author2'}
        """
        resp = {}
        soup = TBotClass._site_to_lxml(self.config['URL']['quote_url'])
        if soup is None:
            resp['res'] = 'ERROR'
            return resp
        quotes = soup.find_all('div', class_='quote')
        for quote in quotes:
            author = quote.find('a')
            text = quote.find('div', class_='quote_name')
            resp[text.text] = author.text
        random_key = random.choice(list(resp.keys()))
        return {'res': 'OK', random_key: resp[random_key]}

    def _get_wish(self) -> str:
        """
        Get wish from internet
        :param:
        :return: wish string
        """
        soup = TBotClass._site_to_lxml(self.config['URL']['wish_url'])
        if soup is None:
            return 'Something is wrong!'
        wishes = soup.find_all('ol')
        wish_list = wishes[0].find_all('li')
        return random.choice(wish_list).text

    def _get_news(self, count: int = 5) -> dict:
        """
        Get news from internet
        :param:
        :return: wish string
        """
        resp = {}
        soup = TBotClass._site_to_lxml(self.config['URL']['news_url'])
        if soup is None:
            resp['res'] = 'ERROR'
            return resp
        news = soup.find_all('div', class_='cell-list__item-info')
        for n in news:
            time = n.find('span', class_='elem-info__date')
            text = n.find('span', class_='share')
            if time and text:
                resp[time.text] = text.get('data-title')
            if len(resp) == count:
                break
        resp['res'] = 'OK'
        return resp
