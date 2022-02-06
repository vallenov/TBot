import logging
import random
import os
import pandas as pd

from loaders.loader import Loader

logger = logging.getLogger(__name__)
handler = logging.FileHandler('run.log')
handler.setLevel(logging.INFO)
handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)


class FileLoader(Loader):
    def __init__(self, name):
        super().__init__(name)
        self.files_list = ['poems.xlsx']
        self._check_file_db()

    def _check_file_db(self):
        self.fife_db = {}
        for file in self.files_list:
            file_path = os.path.join('file_db', file)
            if os.path.exists(file_path):
                self.fife_db[file] = file_path
                self.poems = self._load_poems()

    def _load_poems(self) -> list:
        file_path = self.fife_db.get('poems.xlsx', False)
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
                poems.append(poem)
            logger.info(f'{file_path} download. len = {len(poems)}')
            return poems

    def get_poem(self, text: str) -> dict:
        """
        Get respoesy from file
        :param:
        :return: poesy string
        """
        logger.info('get_poesy')
        lst = text.split()
        resp = {}
        random_poem = {}
        if self.poems:
            if len(lst) == 1:
                random_poem = random.choice(self.poems)
                resp['res'] = 'OK'
            else:
                search_string = ' '.join(lst[1:])
                print(search_string)
                authors_poems_list = []
                for poem in self.poems:
                    if search_string.lower() in poem['author'].lower() or search_string.lower() in poem['name'].lower():
                        authors_poems_list.append(poem)
                if authors_poems_list:
                    random_poem = random.choice(authors_poems_list)
                else:
                    resp['res'] = 'ERROR'
                    resp['descr'] = 'Author not found'
                    return resp
                resp['res'] = 'OK'
        else:
            logger.error('File poems.xlsx not found')
            resp['res'] = 'ERROR'
            resp['descr'] = 'ERROR "FL". Please, contact the administrator'
        author = random_poem['author']
        name = random_poem['name']
        text = random_poem['text']
        str_poem = f"{author}\n\n{name}\n\n{text}"
        resp.update({1: str_poem})
        return resp
