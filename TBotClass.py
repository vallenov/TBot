import os
import string
import random
import requests
from bs4 import BeautifulSoup
import configparser

class TBotClass:
    def __init__(self):
        self._get_config()

    def replace(self, message) -> None:
        '''
        Send result message to chat

        :param bot: object TeleBot()
        :param message: message from user

        :return:
        '''
        if message.content_type == 'text':
            if message.text.lower() == 'qwe':
                return f"Maybe, you meant 'qwerty'?"
            elif message.text.lower() == 'ex':
                exchange = self._get_exchange()
                exchange_str = ''
                for ex in exchange.keys():
                    exchange_str += f'{ex} = {exchange[ex]}\n'
                return exchange_str
            elif message.text.lower() == 'weather':
                weather = self._get_weather()
                weather_str = ''
                for we in weather.keys():
                    weather_str += f'{we}: {weather[we]}\n'
                return weather_str
            else:
                return "I do not understand"

    def _get_config(self):
        self.config = configparser.ConfigParser()
        self.config.read('TBot.ini', encoding='windows-1251')

    def _get_exchange(self) -> dict:
        '''
        Get exchange from internet

        :param:

        :return resp: string like {'USD': '73,6059', 'EUR':'83,1158'}
        '''
        ex = ['USD', 'EUR']
        soup = BeautifulSoup(requests.get(self.config['MAIN']['exchange_url']).text, 'lxml')
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

        res = requests.get(self.config['MAIN']['weather_url']).text
        with open('res.html', 'w', encoding="utf-8") as file:
            file.write(res)
        soup = BeautifulSoup(requests.get(self.config['MAIN']['weather_url']).text, 'lxml')
        parse = soup.find_all('div', class_='DetailsSummary--DetailsSummary--2HluQ DetailsSummary--fadeOnOpen--vFCc_')
        resp = {}
        for i in parse:
            h2 = i.find('h2')
            div = i.find('div')
            span = div.find_all('span')
            span = list(map(lambda x: x.text, span))
            resp[h2.text] = ''.join(span[:-1])
        return resp