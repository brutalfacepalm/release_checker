import sys
import logging
from logging.handlers import RotatingFileHandler


def get_logger(service='app'):
    """
    Log events to files and stdout.
    :return: logger
    """
    logger = logging.getLogger('logger')
    logger.setLevel(logging.INFO)

    formatter = logging.Formatter("%(asctime)s — %(name)s — %(levelname)s — %(message)s")

    stream_logging = logging.StreamHandler(sys.stdout)
    stream_logging.setFormatter(formatter)
    stream_logging.setLevel(logging.INFO)

    file_logging = RotatingFileHandler(f'logs/{service}.log', 'w',
                                       maxBytes=1024 * 5, backupCount=2, encoding='utf-8')
    file_logging.setFormatter(formatter)
    file_logging.setLevel(logging.INFO)

    file_logging_error = RotatingFileHandler(f'logs/{service}_error.log', 'w',
                                             maxBytes=1024 * 5, backupCount=2, encoding='utf-8')
    file_logging_error.setFormatter(formatter)
    file_logging_error.setLevel(logging.ERROR)

    logger.addHandler(stream_logging)
    logger.addHandler(file_logging)
    logger.addHandler(file_logging_error)

    return logger
