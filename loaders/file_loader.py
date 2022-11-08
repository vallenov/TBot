import random
import os
import time

import pandas as pd
import datetime

import config
from loaders.loader import Loader, check_permission
from markup import main_markup
from loggers import get_logger
from markup import custom_markup

from exceptions import (
    WrongParameterTypeError,
    FileDBNotFoundError,
    UserNotFoundError,
    EmptyCacheError,
)

logger = get_logger(__name__)


class FileLoader(Loader):
    """
    Work with files
    """

    def __init__(self, name):
        super().__init__(name)
        self.files_list = ['poems.xlsx']
        self._check_file_db()
        self.poems = []

    def _check_file_db(self):
        """
        Check available files in directories
        """
        self.fife_db = {}
        for file in self.files_list:
            file_path = os.path.join('file_db', file)
            if os.path.exists(file_path):
                self.fife_db[file] = file_path

    def load_poems(self):
        """
        Load poems from file to memory
        """
        if not len(self.poems):
            try:
                file_path = self.fife_db.get('poems.xlsx', False)
                if file_path:
                    file_raw = pd.read_excel(file_path)
                    file = pd.DataFrame(file_raw, columns=['Author', 'Name', 'Poem'])
                    dict_file = file.to_dict()
                    for author, name, text in zip(dict_file['Author'].values(),
                                                  dict_file['Name'].values(),
                                                  dict_file['Poem'].values()):
                        try:
                            text = text.replace('<strong>', '\t')
                            text = text.replace('</strong>', '')
                            text = text.replace('<em>', '')
                            text = text.replace('</em>', '')
                        except AttributeError:
                            continue
                        poem = dict()
                        poem['author'] = author
                        poem['name'] = name
                        poem['text'] = text
                        self.poems.append(poem)
                    logger.info(f'{file_path} download. len = {len(self.poems)}')
                else:
                    raise FileDBNotFoundError('poems.xlsx')
            except FileDBNotFoundError:
                logger.exception('File not found')

    @check_permission()
    def get_poem(self, text: str, **kwargs) -> dict:
        """
        Get poem from file
        :param:
        :return: poesy string
        """
        lst = text.split()
        resp = {}
        if len(lst) == 1:
            random_poem = random.choice(self.poems)
        else:
            search_string = ' '.join(lst[1:])
            authors_poems_list = []
            for poem in self.poems:
                if search_string.lower() in poem['author'].lower() or search_string.lower() in poem['name'].lower():
                    authors_poems_list.append(poem)
            if authors_poems_list:
                random_poem = random.choice(authors_poems_list)
            else:
                return Loader.error_resp('Poem not found')
        author = random_poem['author']
        name = random_poem['name']
        text = random_poem['text']
        str_poem = f"{author}\n\n{name}\n\n{text}"
        resp['text'] = str_poem
        return resp

    @check_permission()
    def poem_divination(self, text: str, **kwargs):
        """
        Poem divination
        """
        resp = {}
        try:
            cmd = text.split()
            if kwargs['chat_id'] not in Loader.users.keys():
                raise UserNotFoundError(kwargs['chat_id'])
            if not Loader.users[kwargs['chat_id']].get('cache'):
                Loader.users[kwargs['chat_id']]['cache'] = dict()
            if len(cmd) == 1:
                if 'poem' in Loader.users[kwargs['chat_id']]['cache']:
                    Loader.users[kwargs['chat_id']]['cache'].pop('poem')
                if not Loader.users[kwargs['chat_id']]['cache'].get('poem'):
                    while True:
                        poem = random.choice(self.poems)
                        count_of_quatrains = poem['text'].count('\n\n')
                        if count_of_quatrains == 1:
                            lines = poem['text'].split('\n')
                            buf = ''
                            quatrains = []
                            for line in lines:
                                buf += line
                                if buf.count('\n') == 4:
                                    quatrains.append(buf)
                                buf = ''
                            count_of_quatrains = len(quatrains)
                        if count_of_quatrains:
                            break
                    Loader.users[kwargs['chat_id']]['cache']['poem'] = poem
                    resp['text'] = 'Выберите четверостишие'
                    resp['markup'] = custom_markup('divination', [str(i) for i in range(1, count_of_quatrains+1)], '🔮')
                    return resp
            else:
                poem = Loader.users[kwargs['chat_id']]['cache'].get('poem')
                if not poem:
                    raise EmptyCacheError('poem')
                quatrains = poem['text'].split('\n\n')
                cmd = text.split()
                try:
                    number_of_quatrain = int(cmd[1])
                    resp['text'] = quatrains[number_of_quatrain - 1]
                except ValueError:
                    raise WrongParameterTypeError(cmd[1])
                except IndexError:
                    raise EmptyCacheError('poem')
                return resp
        except UserNotFoundError as e:
            logger.exception(f'Chat {e.chat_id} not found')
            return Loader.error_resp(f'Chat {e.chat_id} not found')
        except WrongParameterTypeError as e:
            logger.exception(f'Chat {e.param} not found')
            return Loader.error_resp(f'Type of param {e.param} is not valid')
        except EmptyCacheError as e:
            logger.exception(f'Empty param: {e.param}')
            return Loader.error_resp(f'Отсутствует сохраненный стих. Нажми на гадание еще разок')

    @check_permission()
    def get_metaphorical_card(self, **kwargs) -> dict:
        """
        Get metaphorical card from file
        :param:
        :return: metaphorical card photo
        """
        resp = {}
        met_cards_path = os.path.join('file_db', 'metaphorical_cards')
        random_card = random.choice(os.listdir(met_cards_path))
        resp['photo'] = os.path.join(met_cards_path, random_card)
        return resp

    @check_permission(needed_level='root')
    def get_camera_capture(self, **kwargs) -> dict:
        """
        Get photo from camera
        :param:
        :return: dict with path to file
        """
        resp = {}
        unique_name = 'camera_' + str(datetime.datetime.now()).replace(':', '').replace(' ', '')[:16]
        path = os.path.join('tmp', unique_name)
        cmd = f"raspistill -o {path} -rot 180 -w 640 -h 480"
        os.system(cmd)
        i = 0
        while i < config.MAX_TRY:
            if os.path.exists(path):
                resp['photo'] = path
                return resp
            time.sleep(1)
            i += 1
        return Loader.error_resp('Something wrong')

    @check_permission()
    def get_help(self, **kwargs) -> dict:
        """
        Get bot functions
        :return: {'res': 'OK or ERROR', 'text': 'message'}
        """
        resp = dict()
        resp['text'] = ''
        if Loader.privileges_levels['regular'] <= kwargs['privileges']:
            resp['text'] += str(f'Ты можешь написать "новости", "стих" и "фильм" с параметром\n'
                                f'Новости "количество новостей"\n'
                                f'Стих "имя автора или название"\n'
                                f'Фильм "год выпуска" или "промежуток", например "фильм 2001-2005"\n'
                                f'Так же, ты можешь написать phone и номер телефона, что бы узнать информацию о нем\n')
        if Loader.privileges_levels['trusted'] <= kwargs['privileges']:
            pass
        if Loader.privileges_levels['root'] <= kwargs['privileges']:
            pass
        return resp

    @check_permission()
    def get_hello(self, **kwargs) -> dict:
        """
        Get hello from bot
        :return: {'res': 'OK or ERROR', 'text': 'message'}
        """
        resp = dict()
        if Loader.privileges_levels['regular'] <= kwargs['privileges']:
            resp['text'] = f'Привет! Меня зовут InfoBot\n'
        if Loader.privileges_levels['trusted'] <= kwargs['privileges']:
            pass
        if Loader.privileges_levels['root'] <= kwargs['privileges']:
            resp['text'] = f'You are a root user'
        resp['markup'] = main_markup(kwargs['privileges'])
        return resp

    @check_permission(needed_level='root')
    def get_admins_help(self, **kwargs) -> dict:
        """
        Get bot functions for admin
        :param :
        :return:
        """
        resp = dict()
        resp['text'] = str(f'Изменение привилегий пользователя - update privileges "chat_id" "privileges"\n'
                           f'Изменение описания пользователя - update description "chat_id" "description"\n'
                           f'Отправить сообщение другому пользователю - send_other "chat_id" "text"\n'
                           f'Массовая рассылка текста - send_all "text"\n'
                           f'Управление сервисами на сервере - systemctl "action" "service"\n')
        return resp
