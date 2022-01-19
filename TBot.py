# -*- coding: utf-8 -*-
import configparser
import traceback
import telebot
import logging
import requests
import os
import string
import random
import datetime

import urllib3.exceptions

from requests import Response
from TBotClass import TBotClass

telebot.apihelper.RETRY_ON_ERROR = 0

MAX_TRY = 15


def custom_request_sender(method, request_url, params=None, files=None,
                          timeout=(None, None), proxies=None) -> Response:
    headers = {'Connection': 'close'}
    s = requests.Session()
    current_try = 0
    while current_try < MAX_TRY:
        current_try += 1
        try:
            resp = s.request(method=method, url=request_url, params=params, headers=headers, files=files,
                             timeout=timeout, proxies=proxies)
        except requests.exceptions.ConnectionError as rec:
            logging.exception(f'Request exception: {rec}')
        except ConnectionResetError as cre:
            logging.exception(f'ConnectionResetError exception: {cre}')
        except urllib3.exceptions.ProtocolError as uep:
            logging.exception(f'urllib3 exception: {uep}')
        except telebot.apihelper.ApiException as taa:
            logging.exception(f'Telegram exception: {taa}')
        except Exception as e:
            logging.exception(f'Custom request exception: {e}')
        else:
            if resp:
                s.close()
                return resp
    logging.error(f'MAX_TRY exceeded')


def tbot():
    config = configparser.ConfigParser()
    config.read('TBot.ini', encoding='windows-1251')
    token = config['MAIN']['token']
    bot = telebot.TeleBot(token)
    tb = TBotClass()

    @bot.message_handler(commands=['start'])
    def start_message(message):
        bot.send_message(message.chat.id, 'Welcome, my friend!')

    @bot.message_handler(func=lambda message: True, content_types=['audio', 'photo', 'voice', 'video', 'document',
                                                                   'text', 'location', 'contact', 'sticker'])
    def send_text(message):
        current_try = 0
        save_file(message)
        while current_try < MAX_TRY:
            current_try += 1
            replace = tb.replace(message)
            try:
                trust_ids = []
                if ',' in config['MAIN']['trust_ids'].split(','):
                    trust_ids = list(map(lambda x: int(x), config['MAIN']['trust_ids'].split(',')))
                else:
                    trust_ids.append(int(config['MAIN']['trust_ids']))
                if message.json['from']['id'] == int(config['MAIN']['root_id']):
                    TBotClass._permission = True
                elif message.json['from']['id'] in trust_ids:
                    TBotClass._permission = False
                bot.send_message(message.chat.id, replace)
            except Exception as _ex:
                logging.exception(f'Unrecognized exception: {_ex}')
            else:
                save_response(replace)
                logging.info('Send successful')
                break

    def save_response(text: str) -> None:
        """
        Save bot response text to the file
        :param text: text to save
        :return:
        """
        curdir = os.curdir
        file_name = os.path.join(curdir, 'text', f'{now_time()[:10]}.txt')
        with open(file_name, 'a') as file:
            text = text.replace('\n', ' ')
            file.write(f"{datetime.datetime.now()} {text}\n")
        os.chown(file_name, 1000, 1000)

    def save_file(message) -> None:
        """
        Save file
        :param message: input message
        :return:
        """
        file_info = None
        file_extention = None
        curdir = os.curdir
        if message.content_type == 'text':
            file_extention = '.txt'
            file_info = message.json
        if message.content_type == 'photo':
            file_extention = '.jpg'
            file_info = bot.get_file(message.photo[-1].file_id)
        if message.content_type == 'audio':
            file_extention = '.mp3'
            file_info = bot.get_file(message.audio.file_id)
        if message.content_type == 'voice':
            file_extention = '.mp3'
            file_info = bot.get_file(message.voice.file_id)
        if message.content_type == 'video':
            file_extention = '.mp4'
            file_info = bot.get_file(message.video.file_id)
        if not os.path.exists(os.path.join(curdir, message.content_type)):
            os.mkdir(os.path.join(curdir, message.content_type))
            os.chown(os.path.join(curdir, message.content_type), 1000, 1000)
        if file_extention == '.txt':
            write_type = 'a'
            file_name = os.path.join(curdir, message.content_type, f'{now_time()[:10]}{file_extention}')
            downloaded_info = str(file_info).replace('\n', ' ')
            downloaded_info = f"{datetime.datetime.now()} {downloaded_info}\n"
        else:
            write_type = 'wb'
            file_name = os.path.join(curdir, message.content_type,
                                     f'{now_time()}{_get_hash_name()}{file_extention}')
            downloaded_info = bot.download_file(file_info.file_path)
        with open(file_name, write_type) as new_file:
            new_file.write(downloaded_info)
        os.chown(file_name, 1000, 1000)

    def now_time() -> str:
        """
        Get nowtime like: 20222-01-18123458
        """
        return str(datetime.datetime.now()).replace(':', '').replace(' ', '')[:16]

    def _get_hash_name() -> str:
        """
        Generate hash name
        :param:
        :return name: name of file
        """
        simbols = string.ascii_lowercase + string.ascii_uppercase
        name = ''
        for _ in range(15):
            name += random.choice(simbols)
        return name

    try:
        bot.infinity_polling()
    except Exception as ex:
        logging.exception(f'Infinity polling exception: {ex}\n{traceback.format_exc()}')


if __name__ == '__main__':
    logging.basicConfig(filename='run.log',
                        level=logging.INFO,
                        format='%(asctime)s - %(levelname)s - %(message)s')
    start = datetime.datetime.now()
    telebot.apihelper.CUSTOM_REQUEST_SENDER = custom_request_sender
    tbot()
