import random
import requests
from bs4 import BeautifulSoup
import configparser


class TBotClass:
    def __init__(self):
        self.__get_config()

    def replace(self, message) -> str:
        """
        Send result message to chat
        :param message: message from user
        :return: replace string
        """
        if message.content_type == 'text':
            form_text = message.text.lower().strip()
            if form_text == 'help':
                return 'Hello! My name is DevInfoBot\nMy functions ->\n' + self.__dict_to_str(self.__get_help(False))
            elif form_text == 'ex':
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
                return "I do not understand"

    @staticmethod
    def __dict_to_str(di: dict, delimiter: str = ' = ') -> str:
        fin_str = ''
        for key, value in di.items():
            fin_str += f'{key}{delimiter}{value}\n'
        return fin_str

    @staticmethod
    def _site_to_lxml(url: str) -> BeautifulSoup:
        """
        Get site and convert it to the lxml

        :param url: https://site.com/
        :return: BeautifulSoup object
        """
        return BeautifulSoup(requests.get(url).text, 'lxml')

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

        ex = ['USD', 'EUR']
        soup = TBotClass._site_to_lxml(self.config['URL']['exchange_url'])
        parse = soup.find_all('tr')
        resp = {}
        for item in parse[1:]:
            inf = item.find_all('td')
            if inf[1].text not in ex: continue
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
        return resp

    def _get_weather(self) -> dict:
        """
        Get weather from internet
        :param:
        :return: dict like {'Сегодня': '10°/15°', 'ср 12': '11°/18°'}
        """

        soup = TBotClass._site_to_lxml(self.config['URL']['weather_url'])
        parse = soup.find_all('div', class_='DetailsSummary--DetailsSummary--2HluQ DetailsSummary--fadeOnOpen--vFCc_')
        resp = {}
        for i in parse:
            h2 = i.find('h2')
            div = i.find('div')
            span = div.find_all('span')
            span = list(map(lambda x: x.text, span))
            resp[h2.text] = ''.join(span[:-1])
        return resp

    def _get_quote(self) -> dict:
        """
        Get quote from internet
        :param:
        :return: dict like {'quote1': 'author1', 'quote2: 'author2'}
        """

        soup = TBotClass._site_to_lxml(self.config['URL']['quote_url'])
        quotes = soup.find_all('div', class_='quote')
        resp = {}
        for quote in quotes:
            author = quote.find('a')
            text = quote.find('div', class_='quote_name')
            resp[text.text] = author.text
        random_key = random.choice(list(resp.keys()))
        return {random_key: resp[random_key]}

    def _get_wish(self) -> str:
        """
        Get wish from internet
        :param:
        :return: wish string
        """

        soup = TBotClass._site_to_lxml(self.config['URL']['wish_url'])
        wishes = soup.find_all('ol')
        wish_list = wishes[0].find_all('li')
        return random.choice(wish_list).text

    def _get_news(self, count: int = 5) -> dict:
        """
        Get news from internet
        :param:
        :return: wish string
        """

        soup = TBotClass._site_to_lxml(self.config['URL']['news_url'])
        news = soup.find_all('div', class_='cell-list__item-info')
        resp = {}
        for n in news:
            time = n.find('span', class_='elem-info__date')
            text = n.find('span', class_='share')
            if time and text:
                resp[time.text] = text.get('data-title')
            if len(resp) == count:
                break
        return resp

