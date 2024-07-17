class Language:
    name = ''
    mapping = {}

    def __call__(self, action, *args, **kwargs):
        return self.mapping.get(action)

    def __repr__(self):
        return str(self.mapping)


class Eng(Language):
    name = 'ENG'
    mapping = {
        'exchange': 'exchange',
        'weather': 'weather',
        'quote': 'quote',
        'wish': 'wish',
        'news': 'news',
        'affirmation': 'affirmation',
        'events': 'events',
        'food': 'food',
        'poem': 'poem',
        'divination': 'divination',
        'movie': 'movie',
        'book': 'book',
        'update': 'update',
        'users': 'users',
        'hidden_functions': 'hidden_functions',
        'help': 'hidden_functions',
        'admins_help': 'admins_help',
        'send_other': 'send_other',
        'to_admin': 'to_admin',
        'send_all': 'send_all',
        'metaphorical_card': 'metaphorical_card',
        'russian_painting': 'russian_painting',
        'ip': 'ip',
        'statistic': 'statistic',
        'phone': 'phone',
        'camera': 'camera',
        'ngrok': 'ngrok',
        'serveo_ssh': 'serveo_ssh',
        'ngrok_db': 'ngrok_db',
        'restart_bot': 'restart_bot',
        'restart_system': 'restart_system',
        'systemctl': 'systemctl',
        'allow_connection': 'allow_connection'
    }


class Rus(Language):
    def __init__(self):
        super().__init__()
        self.name = 'RUS'
        self.mapping = {
            'курс': 'exchange',
            'погода': 'weather',
            'цитата': 'quote',
            'пожелание': 'wish',
            'новости': 'news',
            'аффирмация': 'affirmation',
            'события': 'events',
            'еда': 'food',
            'стих': 'poem',
            'гадание': 'divination',
            'фильм': 'movie',
            'книга': 'book',
            'пользователи': 'users',
            'помощь': 'hidden_functions',
            'админу': 'to_admin',
            'карта': 'metaphorical_card',
            'картина': 'russian_painting',
            'statistic': 'statistic',
            'телефон': 'phone',
            'камера': 'camera'
        }


class Localization:
    __instance = None
    languages = [
        Eng(),
        Rus()
    ]

    def __new__(cls, *args, **kwargs):
        if cls.__instance is None:
            cls.__instance = super().__new__(cls)
        return cls.__instance

    def __init__(self):
        self.mapping = {}

    def get(self, val):
        for language in self.languages:
            action = language(val)
            if action:
                return action

    def __repr__(self):
        text = []
        for language in self.languages:
            text.append(f'{language.name}: {language}')
        return '\n'.join(text)


localization = Localization()
