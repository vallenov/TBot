import os
import string
import random
import requests
from bs4 import BeautifulSoup
import configparser

class TBotClass:
    def replace(self, bot, message) -> None:
        '''
        Send result message to chat

        :param bot: object TeleBot()
        :param message: message from user

        :return:
        '''
        if message.content_type == 'text':
            if message.text.lower() == 'qwe':
                return bot.send_message(message.chat.id, f"Maybe, you meant 'qwerty'?")
            elif message.text.lower() == 'ex':
                exchange = self._get_exchange()
                exchange_str = ''
                for ex in exchange.keys():
                    exchange_str += f'{ex} = {exchange[ex]}\n'
                bot.send_message(message.chat.id, exchange_str)
            else:
                return bot.send_message(message.chat.id, "I do not understand")
        elif message.content_type == 'photo':
            file_info = bot.get_file(message.photo[-1].file_id)
            downloaded_file = bot.download_file(file_info.file_path)
            self._save_file(downloaded_file, 'img', '.jpg')
            return bot.send_message(message.chat.id, 'Very beautiful!')

        elif message.content_type == 'audio':
            file_info = bot.get_file(message.audio.file_id)
            downloaded_file = bot.download_file(file_info.file_path)
            self._save_file(downloaded_file, 'audio', '.mp3')

        elif message.content_type == 'voice':
            file_info = bot.get_file(message.voice.file_id)
            downloaded_file = bot.download_file(file_info.file_path)
            self._save_file(downloaded_file, 'voice', '.mp3')

        elif message.content_type == 'video':
            file_info = bot.get_file(message.video.file_id)
            downloaded_file = bot.download_file(file_info.file_path)
            self._save_file(downloaded_file, 'video', '.mp4')

    def _save_file(self, downloaded_file, file_type: str, file_extention: str) -> None:
        '''
        Save file

        :param downloaded_file: info about file
        :param file_type: audio, voice, photo etc
        :param file_extention: .mp3, .jpg etc

        :return:
        '''
        curdir = os.curdir
        if not os.path.exists(os.path.join(curdir, file_type)):
            os.mkdir(os.path.join(curdir, file_type))
        with open(os.path.join(curdir, file_type, f'{self._get_hash_name()}{file_extention}'), 'wb') as new_file:
            new_file.write(downloaded_file)

    def _get_hash_name(self) -> str:
        '''
        Generate hash name

        :param:

        :return name: name of file
        '''
        simbols = string.ascii_lowercase + string.ascii_uppercase
        name = ''
        for _ in range(15):
            name += random.choice(simbols)
        return name

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
