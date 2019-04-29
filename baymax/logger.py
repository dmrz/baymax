import logging

import colorlog


LOG_COLORS = {
    "DEBUG": "blue",
    "INFO": "green",
    "WARNING": "yellow",
    "ERROR": "red",
    "CRITICAL": "bold_red",
}


def get_logger(name, level=logging.DEBUG):
    handler = colorlog.StreamHandler()
    handler.setFormatter(
        colorlog.ColoredFormatter(
            "%(log_color)s%(asctime)s %(levelname)s:"
            "%(name)s: %(message_log_color)s%(message)s",
            datefmt=None,
            reset=True,
            log_colors=LOG_COLORS,
            secondary_log_colors={
                "message": {
                    "DEBUG": "cyan",
                    "INFO": "cyan",
                    "WARNING": "yellow",
                    "ERROR": "red",
                    "CRITICAL": "red",
                }
            },
        )
    )
    logger = colorlog.getLogger(name)
    logger.addHandler(handler)
    logger.setLevel(level)
    return logger
