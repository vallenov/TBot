import os
import string
import random
import requests
from bs4 import BeautifulSoup
import configparser

class TBotClass:
    def replace(self, bot, message):
        print(message)
        if message.content_type == 'text':
            if message.text.lower() == 'qwe':
                return  bot.send_message(message.chat.id, f"Maybe, you meant 'qwerty'?")
            elif message.text.lower() == 'ex':
                exchange = self._get_exchange()
                tmp = ''
                for e in exchange:
                    tmp += f"{e['name']} = {e['exchange']}\n"
                bot.send_message(message.chat.id, tmp)
            else:
                return bot.send_message(message.chat.id, "I do not understand")
        elif message.content_type == 'photo':
            file_info = bot.get_file(message.photo[-1].file_id)
            downloaded_file = bot.download_file(file_info.file_path)
            self.save_file(downloaded_file, 'img', '.jpg')

            return bot.send_message(message.chat.id, 'Very beautiful!')

        elif message.content_type == 'audio':
            file_info = bot.get_file(message.audio.file_id)
            downloaded_file = bot.download_file(file_info.file_path)
            self.save_file(downloaded_file, 'audio', '.mp3')

        elif message.content_type == 'voice':
            file_info = bot.get_file(message.voice.file_id)
            downloaded_file = bot.download_file(file_info.file_path)
            self.save_file(downloaded_file, 'voice', '.mp3')

    def save_file(self, downloaded_file, file_type: str, file_extention: str) -> None:
        curdir = os.curdir
        if not os.path.exists(os.path.join(curdir, file_type)):
            os.mkdir(os.path.join(curdir, file_type))
        with open(os.path.join(curdir, file_type, f'{self.get_hash_name()}{file_extention}'), 'wb') as new_file:
            new_file.write(downloaded_file)

    def get_hash_name(self) -> str:
        simbols = string.ascii_lowercase + string.ascii_uppercase
        name = ''
        for _ in range(15):
            name += random.choice(simbols)
        return name

    def _get_exchange(self) -> float:
        ex = ['USD', 'EUR']
        config = configparser.ConfigParser()
        config.read('TBot.ini', encoding='windows-1251')
        soup = BeautifulSoup(requests.get(config['MAIN']['exchange_url']).text, 'lxml')
        parse = soup.find_all('tr')
        resp = []
        for item in parse[1:]:
            inf = item.find_all('td')
            if inf[1].text not in ex: continue
            tmp = {}
            tmp['id'] = inf[0].text
            tmp['name'] = inf[1].text
            tmp['e'] = inf[2].text
            tmp['descr'] = inf[3].text
            tmp['exchange'] = inf[4].text
            resp.append(tmp)
            print(tmp)
        return resp