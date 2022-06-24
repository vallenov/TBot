class TBotExeption(Exception):
    ...


class FileDBNotFound(TBotExeption):
    def __init__(self, file_name):
        self.file_name = file_name
        super().__init__(f'File {file_name} not found')


class ConfigAttributeNotFound(TBotExeption):
    def __init__(self, attr_name):
        self.attr_name = attr_name
        super().__init__(f'Attribute {attr_name} not found')
