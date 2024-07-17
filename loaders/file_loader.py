import random
import os
import time
import traceback

import pandas as pd
import datetime

import config
from loaders.loader import Loader, check_permission, LoaderResponse, LoaderRequest
from markup import main_markup
from loggers import get_logger
from markup import custom_markup
from users import tbot_users
from localization import Rus

from exceptions import TBotException

logger = get_logger(__name__)


class FileLoader(Loader):
    """
    Work with files
    """

    def __init__(self):
        self.files_list = ['poems.xlsx']
        self._check_file_db()
        self.poems = []
        if not config.USE_DB:
            self.load_poems()

    def _check_file_db(self) -> None:
        """
        Check available files in directories
        """
        self.fife_db = {}
        for file in self.files_list:
            file_path = os.path.join('file_db', file)
            if os.path.exists(file_path):
                self.fife_db[file] = file_path

    def load_poems(self) -> None:
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
                    raise TBotException(code=2, message='Файл poems.xlsx не найден', send=True)
            except TBotException as e:
                logger.exception(e.context)
                e.send_error(traceback.format_exc())

    @check_permission()
    def get_poem(self, request: LoaderRequest) -> LoaderResponse:
        """
        Get poem from file
        :param:
        :return: poesy string
        """
        lst = request.text.split()
        resp = LoaderResponse()
        try:
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
                    raise TBotException(code=3, return_message='Стих не найден')
            author = random_poem['author']
            name = random_poem['name']
            text = random_poem['text']
            str_poem = f"{author}\n\n{name}\n\n{text}"
            resp.text = str_poem
            return resp
        except TBotException as e:
            logger.exception(e.context)
            e.send_error(traceback.format_exc())
            return e.return_message()

    @check_permission()
    def poem_divination(self, request: LoaderRequest) -> LoaderResponse:
        """
        Poem divination
        """
        resp = LoaderResponse()
        try:
            cmd = request.text.split()
            if request.chat_id not in tbot_users:
                raise TBotException(code=3, chat_id=f"{request.chat_id}")
            if not tbot_users(request.chat_id).cache:
                tbot_users(request.chat_id).cache = dict()
            if len(cmd) == 1:
                if 'poem' in tbot_users(request.chat_id).cache:
                    tbot_users(request.chat_id).cache.pop('poem')
                if not tbot_users(request.chat_id).cache.get('poem'):
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
                    tbot_users(request.chat_id).cache['poem'] = poem
                    resp.text = 'Выберите четверостишие'
                    resp.markup = custom_markup(
                        command='divination',
                        category=[str(i) for i in range(1, count_of_quatrains+1)],
                        smile='🔮'
                    )
                    resp.is_extra_log = False
                    return resp
            else:
                poem = tbot_users(request.chat_id).cache.get('poem')
                if not poem:
                    raise TBotException(code=7,
                                        return_message=f'Отсутствует сохраненный стих. Нажми на гадание еще разок',
                                        chat_id=request.chat_id,
                                        cache_field='poem')
                quatrains = poem['text'].split('\n\n')
                cmd = request.text.split()
                try:
                    number_of_quatrain = int(cmd[1])
                    resp.text = quatrains[number_of_quatrain - 1]
                except ValueError:
                    raise TBotException(code=6,
                                        return_message='Неправильный тип параметра',
                                        parameter=cmd[1],
                                        type=type(cmd[1]))
                except IndexError:
                    raise TBotException(code=7,
                                        return_message=f'Отсутствует сохраненный стих. Нажми на гадание еще разок',
                                        chat_id=request.chat_id,
                                        cache_field='poem')
                return resp
        except TBotException as e:
            logger.exception(e.context)
            e.send_error(traceback.format_exc())
            return e.return_message()

    @check_permission()
    def get_metaphorical_card(self, request: LoaderRequest) -> LoaderResponse:
        """
        Get metaphorical card from file
        :param:
        :return: metaphorical card photo
        """
        resp = LoaderResponse()
        met_cards_path = os.path.join('file_db', 'metaphorical_cards')
        random_card = random.choice(os.listdir(met_cards_path))
        resp.photo = os.path.join(met_cards_path, random_card)
        return resp

    @check_permission(needed_level='root')
    def get_camera_capture(self, request: LoaderRequest) -> LoaderResponse:
        """
        Get photo from camera
        :param:
        :return: dict with path to file
        """
        resp = LoaderResponse()
        unique_name = 'camera_' + str(datetime.datetime.now()).replace(':', '').replace(' ', '')[:16]
        path = os.path.join('tmp', unique_name)
        cmd = f"raspistill -o {path} -rot 180 -w 640 -h 480"
        os.system(cmd)
        i = 0
        try:
            while i < config.MAX_TRY:
                if os.path.exists(path):
                    resp.photo = path
                    return resp
                time.sleep(1)
                i += 1
            raise TBotException(code=2)
        except TBotException as e:
            logger.exception(e.context)
            e.send_error(traceback.format_exc())
            return e.return_message()

    @check_permission()
    def get_help(self, request: LoaderRequest) -> LoaderResponse:
        """
        Get bot functions
        :return: {'res': 'OK or ERROR', 'text': 'message'}
        """
        resp = LoaderResponse()
        resp.text = ''
        if Loader.privileges_levels['regular'] <= request.privileges:
            resp.text += str(
                f'Руководство пользователя:\n\n'
                f'✅ Новости "количество новостей". Например: новости 10\n\n'
                f'✅ Стих "имя автора или название или содержимое". Пример: стих о рыжей дворняге\n'
                f'Если будет найдено несколько стихов, придут несколько кнопок с именем ввтора и названием\n\n'
                f'✅ Фильм "год выпуска" или "промежуток". Пример: фильм 2001-2005"\n\n'
                f'✅ Так же, ты можешь написать "телефон" и номер телефона, что бы узнать информацию о нем\n\n'
                f'✅ По команде "мероприятия" можно получить интересные события (пока только в Москве)\n\n'
                f'✅ Что бы отправить сообщение админу, напиши "админу" и все что угодно после после пробела\n\n'
                f'❗️ Не все функции могут работать корректно, но я стараюсь отслеживать это'
            )
            resp.markup = custom_markup(
                command='commands',
                category=['Список команд'],
                smile='🔹'
            )
        if Loader.privileges_levels['trusted'] <= request.privileges:
            pass
        if Loader.privileges_levels['root'] <= request.privileges:
            pass
        return resp

    @check_permission()
    def commands_list(self, request: LoaderRequest) -> LoaderResponse:
        resp = LoaderResponse()
        msg = Rus()
        resp.text = msg.to_message()
        return resp

    @check_permission()
    def get_hello(self, request: LoaderRequest) -> LoaderResponse:
        """
        Get hello from bot
        :return:
        """
        resp = LoaderResponse()
        if Loader.privileges_levels['regular'] <= request.privileges:
            resp.text = f'Привет! Меня зовут InfoBot\n'
        if Loader.privileges_levels['trusted'] <= request.privileges:
            pass
        if Loader.privileges_levels['root'] <= request.privileges:
            resp.text = f'Вы root-пользователь'
        resp.markup = main_markup(request.privileges)
        resp.is_extra_log = False
        return resp

    @check_permission(needed_level='root')
    def get_admins_help(self, request: LoaderRequest) -> LoaderResponse:
        """
        Get bot functions for admin
        :param :
        :return:
        """
        resp = LoaderResponse()
        resp.text = str(
            f'Изменение привилегий пользователя - update privileges "chat_id" "privileges" 10-50\n'
            f'Изменение описания пользователя - update description "chat_id" "description"\n'
            f'Изменение активности пользователя (вместо удаления) - update description "chat_id" "active" 1 или 0\n'
            f'Отправить сообщение другому пользователю - send_other "chat_id" "text"\n'
            f'Массовая рассылка текста - send_all "text"\n'
            f'  - Последовательность #%usеr_name%# (не копировать!) будет заменена на имя пользователя\n'
            f'Управление сервисами на сервере - systemctl "action" "service"\n')
        return resp
