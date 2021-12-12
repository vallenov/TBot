import os
import string
import random
import requests
from bs4 import BeautifulSoup
import configparser

class TBotClass:
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
            else:
                return "I do not understand"

    def _get_exchange(self) -> dict:
        '''
        Get exchange from internet

        :param:

        :return resp: string like "USD = 73,6059\nEUR = 83,1158"
        '''
        ex = ['USD', 'EUR']
        config = configparser.ConfigParser()
        config.read('TBot.ini', encoding='windows-1251')
        soup = BeautifulSoup(requests.get(config['MAIN']['exchange_url']).text, 'lxml')
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
