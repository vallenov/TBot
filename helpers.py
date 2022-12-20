import random
import datetime
import string
import config

from loggers import get_logger
from exceptions import TBotException

logger = get_logger(__name__)


def now_time() -> str:
    """
    Get nowtime like: 20222-01-18123458
    """
    return str(datetime.datetime.now()).replace(':', '').replace(' ', '')[:16]


def get_hash_name() -> str:
    """
    Generate hash name
    :param:
    :return name: name of file
    """
    simbols = string.ascii_lowercase + string.ascii_uppercase
    name = ''
    for _ in range(15):
        name += random.choice(simbols)
    return name


def dict_to_str(di: dict, delimiter: str = ' = ') -> str:
    """
    Turn dict to str
    Digit not use
    Keys "res" and "chat_id" is skipping
    Example:
         {1: 'text'} => 'text'
         {'key': 'value'}, '=' => 'key = value'
         {'key1': 'value1', 'key2': 'value2'}, ': ' => key1: value1\nkey2: value2
    :param di: input dict
    :param delimiter: delimiter string
    :return: string
    """
    fin_str = ''
    for key, value in di.items():
        if isinstance(key, int):
            fin_str += f'{value}\n'
        else:
            fin_str += f'{key}{delimiter}{value}\n'
    return fin_str


def is_phone_number(number: str) -> str or None:
    """
    Check string. If non phone number, return None. Else return formatted phone number
    :param number: any format of phone number
    :return: formatted phone number
    """
    resp = {}
    if len(number) < 10 or len(number) > 18:
        return None
    allowed_simbols = '0123456789+()- '
    for num in number:
        if num not in allowed_simbols:
            return None
    raw_num = number
    raw_num = raw_num.strip()
    raw_num = raw_num.replace(' ', '')
    raw_num = raw_num.replace('+', '')
    raw_num = raw_num.replace('(', '')
    raw_num = raw_num.replace(')', '')
    raw_num = raw_num.replace('-', '')
    if len(raw_num) < 11:
        raw_num = '8' + raw_num
    if raw_num.startswith('7'):
        raw_num = '8' + raw_num[1:]
    if not raw_num.startswith('89'):
        resp['res'] = 'ERROR'
        resp['descr'] = 'Number format is not valid'
        return None
    return raw_num


def check_config_attribute(attr: str) -> str or Exception:
    if config.LINKS.get(attr, None):
        return config.LINKS[attr]
    else:
        raise TBotException(code=4, return_message="I can't do this yet😔", message=f'Attribute {attr} not found')


def cut_commands(text: str, count_of_commands):
    while '  ' in text:
        text = text.replace('  ', ' ')
    for _ in range(count_of_commands):
        text = text[text.find(' ')+1:]
    return text
