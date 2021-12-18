# -*- coding: utf-8 -*-
import configparser
import telebot
import logging
import requests
import datetime
import os
import string
import random

from TBotClass import TBotClass

def TBot():
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
        try:
            _save_file(message)
            if message.json['from']['id'] != int(config['MAIN']['chat_id']):
               bot.send_message(message.chat.id, "I know nothing. Go away!")
            else:
                bot.send_message(message.chat.id, tb.replace(message))
        except Exception as ex:
            logging.exception(f'Exception: {ex}')

    def _save_file(message) -> None:
        '''
        Save file

        :param downloaded_file: info about file
        :param file_type: audio, voice, photo etc
        :param file_extention: .mp3, .jpg etc

        :return:
        '''
        file_info = None
        file_extention = None
        if message.content_type == 'text':
            return
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
        downloaded_file = bot.download_file(file_info.file_path)
        curdir = os.curdir
        if not os.path.exists(os.path.join(curdir, message.content_type)):
            os.mkdir(os.path.join(curdir, message.content_type))
        with open(os.path.join(curdir, message.content_type, f'{_get_hash_name()}{file_extention}'), 'wb') as new_file:
            new_file.write(downloaded_file)

    def _get_hash_name() -> str:
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

    bot.infinity_polling()

if __name__ == '__main__':
    logging.basicConfig(filename='run.log',
                        level=logging.INFO,
                        format='%(asctime)s - %(levelname)s - %(message)s')
    start = datetime.datetime.now()
    TBot()