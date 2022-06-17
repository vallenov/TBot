import logging
import os

logging.basicConfig(level=logging.INFO)


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
