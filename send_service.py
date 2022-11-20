import requests
import traceback

from loaders.loader import Loader
import config
from loggers import get_logger
from exceptions import TBotException

logger = get_logger(__name__)


def send_dev_message(data: dict, by: str = 'mail') -> dict:
    """
    Send message to admin
    :param data: {'to': name or email, 'subject': 'subject' (unnecessary), 'text': 'text'}
    :param by: by what (mail or telegram)
    """
    resp = {}
    try:
        if by not in ('mail', 'telegram'):
            Loader.error_resp(f'Wrong parameter by ({by}) in send_dev_message')
            logger.error(resp['descr'])
            return resp
        if by == 'mail':
            data.update({'to': config.MAIL.get('address')})
        else:
            data.update({'to': config.USERS.get('root_id').get('chat_id')})
        current_try = 0
        while current_try < config.MAX_TRY:
            current_try += 1
            try:
                res = requests.post(config.MAIL.get('message_server_address') + '/' + by, data=data,
                                    headers={'Connection': 'close'})
            except Exception as e:
                raise TBotException(code=1, message=f'Error during send message to developer\n{e}')
            else:
                logger.info('Send successful')
                resp['res'] = res.text
                return resp
        logger.error('Max try exceeded')
    except TBotException as e:
        logger.exception(e.context)
