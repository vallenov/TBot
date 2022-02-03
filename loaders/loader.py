import configparser


class Loader:
    loaders = []

    def __init__(self, name):
        self.name = name
        Loader.loaders.append(self.name)
        self.__get_config()

    def __get_config(self):
        self.config = configparser.ConfigParser()
        self.config.read('TBot.ini', encoding='windows-1251')

    @staticmethod
    def get_loaders():
        return Loader.loaders
