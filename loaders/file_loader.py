import random
import os
import time

import pandas as pd
import datetime

import config
from loaders.loader import Loader, check_permission
from markup import main_markup
from loggers import get_logger

from exceptions import (
    FileDBNotFoundError,
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

    @check_permission()
    def get_poem(self, text: str, **kwargs) -> dict:
        """
        Get poem from file
        :param:
        :return: poesy string
        """
        lst = text.split()
        resp = {}
        if not len(self.poems):
            try:
                self.load_poems()
            except FileDBNotFoundError:
                logger.exception('File not found')
                return Loader.error_resp()
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
    def get_help(self, privileges: int, **kwargs) -> dict:
        """
        Get bot functions
        :param privileges: user privileges
        :return: {'res': 'OK or ERROR', 'text': 'message'}
        """
        resp = dict()
        resp['text'] = ''
        if Loader.privileges_levels['regular'] <= privileges:
            resp['text'] += str(f'???? ???????????? ???????????????? "??????????????", "????????" ?? "??????????" ?? ????????????????????\n'
                                f'?????????????? "???????????????????? ????????????????"\n'
                                f'???????? "?????? ???????????? ?????? ????????????????"\n'
                                f'?????????? "?????? ??????????????" ?????? "????????????????????", ???????????????? "?????????? 2001-2005"\n'
                                f'?????? ????, ???? ???????????? ???????????????? phone ?? ?????????? ????????????????, ?????? ???? ???????????? ???????????????????? ?? ??????\n')
        if Loader.privileges_levels['trusted'] <= privileges:
            pass
        if Loader.privileges_levels['root'] <= privileges:
            pass
        return resp

    @check_permission()
    def get_hello(self, privileges: int, **kwargs) -> dict:
        """
        Get hello from bot
        :param privileges: user privileges
        :return: {'res': 'OK or ERROR', 'text': 'message'}
        """
        resp = dict()
        if Loader.privileges_levels['regular'] <= privileges:
            resp['text'] = f'????????????! ???????? ?????????? InfoBot\n'
        if Loader.privileges_levels['trusted'] <= privileges:
            pass
        if Loader.privileges_levels['root'] <= privileges:
            resp['text'] = f'You are a root user'
        resp['markup'] = main_markup(privileges)
        return resp

    @check_permission(needed_level='root')
    def get_admins_help(self, **kwargs) -> dict:
        """
        Get bot functions for admin
        :param :
        :return:
        """
        resp = dict()
        resp['text'] = str(f'Update "chat_id" "privileges"\n'
                           f'Send_other "chat_id" "text"\n')
        return resp
