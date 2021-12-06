import os
import string
import random

class TBotClass:
    def replace(self, bot, message):
        print(message)
        if message.content_type == 'text':
            if message.text.lower() == 'qwe':
                return  bot.send_message(message.chat.id, f"Maybe, you meant 'qwerty'?")
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