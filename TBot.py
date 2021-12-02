import configparser
import telebot


def TBot():
    config = configparser.ConfigParser()
    config.read('TBot.ini', encoding='windows-1251')
    token = config['MAIN']['token']
    bot = telebot.TeleBot(token)

    @bot.message_handler(commands=['start'])
    def start_message(message):
        bot.send_message(message.chat.id, 'Welcome, my friend!')

    @bot.message_handler(content_types=['text'])
    def send_text(message):
        if message.json['from']['username'] != config['MAIN']['master']:
            bot.send_message(message.chat.id, "Who are you???")
        else:
            if message.text.lower() == 'qwe':
                bot.send_message(message.chat.id, "Maybe, you meant 'qwerty'?")
            else:
                bot.send_message(message.chat.id, "I do not understand")

    bot.polling()

if __name__ == '__main__':
    TBot()