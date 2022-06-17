import requests
from loaders.loader import Loader
import config
from loggers import get_logger

logger = get_logger(__name__)


def send_dev_message(data: dict, by: str = 'mail') -> dict:
    """
    Send message to admin
    :param data: {'to': name or email, 'subject': 'subject' (unnecessary), 'text': 'text'}
    :param by: by what (mail or telegram)
    """
    resp = {}
    if by not in ('mail', 'telegram'):
        Loader.error_resp(f'Wrong parameter by ({by}) in send_dev_message')
        logger.error(resp['descr'])
        return resp
    if by == 'mail':
        data.update({'to': config.MAIL.get('address')})
    else:
        data.update({'to': config.DB.get('login')})
    current_try = 0
    while current_try < config.MAX_TRY:
        current_try += 1
        try:
            res = requests.post(config.MAIL.get('message_server_address') + '/' + by, data=data,
                                headers={'Connection': 'close'})
        except Exception as _ex:
            logger.exception(_ex)
        else:
            logger.info('Send successful')
            resp['res'] = res.text
            return resp
    logger.error('Max try exceeded')
