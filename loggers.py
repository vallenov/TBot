import logging
import os

logging.basicConfig(level=logging.INFO)


def init_dirs():
    """
    Init downloads dir
    """
    curdir = os.curdir
    if not os.path.exists(os.path.join(curdir, 'downloads')):
        os.mkdir(os.path.join(curdir, 'downloads'))
        os.chown(os.path.join(curdir, 'downloads'), 1000, 1000)
    if not os.path.exists(os.path.join('downloads', 'text')):
        os.mkdir(os.path.join('downloads', 'text'))
        os.chown(os.path.join('downloads', 'text'), 1000, 1000)
    print(os.path.join(curdir, 'tests', 'downloads'))
    if not os.path.exists(os.path.join(curdir, 'tests', 'downloads')):
        os.mkdir(os.path.join(curdir, 'tests', 'downloads'))
        os.chown(os.path.join(curdir, 'tests', 'downloads'), 1000, 1000)
    if not os.path.exists(os.path.join('tests', 'downloads', 'text')):
        os.mkdir(os.path.join('tests', 'downloads', 'text'))
        os.chown(os.path.join('tests', 'downloads', 'text'), 1000, 1000)


def get_logger(name: str):
    logger = logging.getLogger(name)
    handler = logging.FileHandler('run.log')
    handler.setLevel(logging.INFO)
    handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(handler)
    return logger


def get_conversation_logger():

    conversation_logger = logging.getLogger('conversation')
    conversation_logger.setLevel(logging.INFO)
    conv_handler = logging.FileHandler(os.path.join('downloads', 'text', 'run_conv.log'))
    conv_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    conversation_logger.addHandler(conv_handler)
    return conversation_logger
