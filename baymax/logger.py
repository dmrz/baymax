import logging

import colorlog


def get_logger(name, level=logging.DEBUG):
    handler = colorlog.StreamHandler()
    handler.setFormatter(colorlog.ColoredFormatter(
        '%(log_color)s%(asctime)s %(levelname)s:'
        '%(name)s: %(white)s%(message)s',
        datefmt=None,
        reset=True))
    logger = colorlog.getLogger(name)
    logger.addHandler(handler)
    logger.setLevel(level)
    return logger
