import logging
import random
import os
import pandas as pd
import subprocess as sb

from loaders.loader import Loader, check_permission

logger = logging.getLogger(__name__)
handler = logging.FileHandler('run.log')
handler.setLevel(logging.INFO)
handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)


class FileLoader(Loader):
    """
    Work with files
    """

    def __init__(self, name):
        super().__init__(name)
        self.files_list = ['poems.xlsx']
        self._check_file_db()

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
        try:
            file_path = self.fife_db.get('poems.xlsx', False)
        except Exception as e:
            return False
        self.poems = []
        if file_path:
            file_raw = pd.read_excel(file_path)
            file = pd.DataFrame(file_raw, columns=['Author', 'Name', 'Poem'])
            dict_file = file.to_dict()
            poems = []
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
            logger.info(f'{file_path} download. len = {len(poems)}')
            return True
        else:
            return False

    @check_permission()
    def get_poem(self, text: str, **kwargs) -> dict:
        """
        Get poem from file
        :param:
        :return: poesy string
        """
        lst = text.split()
        resp = {}
        is_load = False
        if not hasattr(self, 'poems'):
            is_load = self.load_poems()
        if is_load:
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
        else:
            logger.error('File poems.xlsx not found')
            return Loader.error_resp()
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
    def get_server_ip(self, **kwargs) -> dict:
        """
        Get server ip
        :param:
        :return: dict with ip
        """
        resp = {}
        output = sb.check_output("ifconfig | "
                                 "grep `ifconfig -s | "
                                 "grep '\<w.*' | "
                                 "awk '{print $1}'` -A 1 | "
                                 "grep inet | "
                                 "awk '{print $2}'", shell=True)
        resp['text'] = output.decode()
        return resp
