import logging

from baymax.logger import get_logger


def test_logger(caplog):
    logger = get_logger("baymax_test")

    logger.debug("debug")
    logger.info("info")
    logger.warning("warning")
    logger.error("error")
    logger.critical("critical")

    log_dict = {
        level: message
        for (name, level, message) in caplog.record_tuples
        if name == logger.name
    }

    assert log_dict[logging.DEBUG] == "debug"
    assert log_dict[logging.INFO] == "info"
    assert log_dict[logging.WARNING] == "warning"
    assert log_dict[logging.ERROR] == "error"
    assert log_dict[logging.CRITICAL] == "critical"
