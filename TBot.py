# -*- coding: utf-8 -*-
import configparser
import telebot
import logging
import requests
import datetime

from TBotClass import TBotClass

def TBot():
    config = configparser.ConfigParser()
    config.read('TBot.ini', encoding='windows-1251')
    token = config['MAIN']['token']
    bot = telebot.TeleBot(token)
    TB = TBotClass()
    # mess = 'I just want to say hello'
    # mess = mess.split()
    # for m in mess:
    #     bot.send_message(int(config['MAIN']['chat_id']), m)
    #     time.sleep(2)

    @bot.message_handler(commands=['start'])
    def start_message(message):
        bot.send_message(message.chat.id, 'Welcome, my friend!')

    @bot.message_handler(func=lambda message: True, content_types=['audio', 'photo', 'voice', 'video', 'document',
                                                                   'text', 'location', 'contact', 'sticker'])
    def send_text(message):
        try:
            if message.json['from']['id'] != int(config['MAIN']['chat_id']):
               bot.send_message(message.chat.id, "I know nothing. Go away!")
            else:
                print(TB._get_exchange())
                TB.replace(bot, message)
        except Exception as ex:
            logging.exception(f'Exception: {ex}')

    bot.infinity_polling()

if __name__ == '__main__':
    logging.basicConfig(filename='run.log',
                        level=logging.INFO,
                        format='%(asctime)s - %(levelname)s - %(message)s')
    start = datetime.datetime.now()
    TBot()