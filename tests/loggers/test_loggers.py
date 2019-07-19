import unittest
from unittest import mock
import logging
import sys

from backee.logger.loggers import setup_default_loggers, setup_config_loggers


class ConfigParserTestCase(unittest.TestCase):
    """
    Test for `logger/loggers.py`
    """

    @unittest.mock.patch('logging.Logger.addHandler')
    def test_set_loggers_set(self, addHandler):
        """
        Test that stdout and stderr loggers are set.
        """
        setup_default_loggers()

        # assert that stdout and stderr added
        self.assertTrue(
            any(args[0][0].stream == sys.stdout for args in addHandler.call_args_list))
        self.assertTrue(
            any(args[0][0].stream == sys.stderr for args in addHandler.call_args_list))

    @unittest.mock.patch('logging.Logger.addHandler')
    def test_loggers_set(self, addHandler):
        """
        Test that loggers are set.
        """
        handlers = (
            logging.StreamHandler(),
            logging.NullHandler()
        )

        setup_config_loggers(handlers)

        calls = [unittest.mock.call(handlers[0]),
                 unittest.mock.call(handlers[1])]
        addHandler.assert_has_calls(calls, any_order=True)


if __name__ == '__main__':
    unittest.main()
