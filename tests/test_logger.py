import logging

from hypothesis import given, strategies as st

from baymax.logger import get_logger


def test_logger(caplog):
    @given(logger_name=st.text(), logger_message=st.text())
    def inner(logger_name, logger_message):

        logger = get_logger(logger_name)

        for level, _ in logging._levelToName.items():
            with caplog.at_level(level):
                logger.log(level, logger_message)
            assert caplog.messages[0] == logger_message
        caplog.clear()

    inner()
