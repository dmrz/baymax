import logging

from hypothesis import given, strategies as st

from baymax.logger import get_logger


@given(logger_name=st.text(), logger_message=st.text())
def test_logger(caplog, logger_name, logger_message):
    logger = get_logger(logger_name)

    logger.debug(logger_message)
    logger.info(logger_message)
    logger.warning(logger_message)
    logger.error(logger_message)
    logger.critical(logger_message)

    log_dict = {
        level: message
        for (name, level, message) in caplog.record_tuples
        if name == logger.name
    }

    for level in [
        logging.DEBUG,
        logging.INFO,
        logging.WARNING,
        logging.ERROR,
        logging.CRITICAL,
    ]:
        assert log_dict[level] == logger_message
