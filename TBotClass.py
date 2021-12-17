import os
import string
import random
import requests
from bs4 import BeautifulSoup
import configparser

class TBotClass:
    def __init__(self):
        self.__get_config()

    def replace(self, message) -> str:
        '''
        Send result message to chat

        :param bot: object TeleBot()
        :param message: message from user

        :return:
        '''
        if message.content_type == 'text':
            if message.text.lower() == 'help':
                return 'Hello! My name is DevInfoBot\nMy functions ->\n' + self.__dict_to_str(self.__get_help(False))
                #return f" "
            elif message.text.lower() == 'ex':
                return self.__dict_to_str(self._get_exchange())
            elif message.text.lower() == 'weather':
                return self.__dict_to_str(self._get_weather())
            else:
                return "I do not understand"

    def __dict_to_str(self, di: dict) -> str:
        fin_str = ''
        for key, value in di.items():
            fin_str += f'{key} = {value}\n'
        return fin_str

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
        return docs_str

    def __get_config(self):
        self.config = configparser.ConfigParser()
        self.config.read('TBot.ini', encoding='windows-1251')

    def _get_exchange(self) -> dict:
        '''
        Get exchange from internet

        :param:

        :return resp: string like {'USD': '73,6059', 'EUR':'83,1158'}
        '''
        ex = ['USD', 'EUR']
        soup = BeautifulSoup(requests.get(self.config['URL']['exchange_url']).text, 'lxml')
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
        '''
        Get weather from internet

        :param:

        :return resp: dict like {'Сегодня': '10°/15°', 'ср 12': '11°/18°'}
        '''

        soup = BeautifulSoup(requests.get(self.config['URL']['weather_url']).text, 'lxml')
        parse = soup.find_all('div', class_='DetailsSummary--DetailsSummary--2HluQ DetailsSummary--fadeOnOpen--vFCc_')
        resp = {}
        for i in parse:
            h2 = i.find('h2')
            div = i.find('div')
            span = div.find_all('span')
            span = list(map(lambda x: x.text, span))
            resp[h2.text] = ''.join(span[:-1])
        return resp