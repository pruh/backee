import os
import unittest
from unittest import mock
from unittest.mock import ANY
import logging
from logging import handlers, LogRecord
from typing import Tuple, Optional, Dict

from tests.util.config_mixin import ConfigMixin

from backee.model.web_handler import WebHandler
from backee.model.max_level_filter import MaxLevelFilter
from backee.parser.config_parser import parse_config


class LoggersParserTestCase(ConfigMixin, unittest.TestCase):
    """
    Tests for `backee/parser/logger_parser.py`.
    """

    @unittest.mock.patch('os.mkdir')
    def test_file_logger_all_values_parsed(self, mkdir):
        """
        All possible values for file logger are set and parsed correctly.
        """
        expected_file_logger = self.__create_file_logger(filename="/folder/log_file1",
                                                         format="('%(asctime)s [%(threadName)18s][%(levelname)8s] %(message)s')",
                                                         max_bytes=1024,
                                                         backup_count=1,
                                                         min_level=logging.INFO,
                                                         max_level=logging.ERROR)

        # parse config and get first logger
        parsed_config = self._get_parsed_config('file_loggers_config.yml')
        parsed_file_logger = parsed_config.loggers[0]

        # make sure file was opened
        mkdir.assert_called_with('/folder')

        result, msg = self.__compare_file_loggers(
            expected_file_logger, parsed_file_logger)
        self.assertTrue(
            result, msg=f"Full config is not as expected, following comparison failed: {msg}")

    @unittest.mock.patch('os.mkdir')
    def test_file_logger_default_values(self, mkdir):
        """
        Only required values are set and others are default.
        """
        expected_file_logger = self.__create_file_logger(filename="/folder/log_file2",
                                                         format="('%(asctime)s %(levelname)s %(message)s')",
                                                         max_bytes=1 * 1024 * 1024,
                                                         backup_count=0,
                                                         min_level=logging.DEBUG,
                                                         max_level=logging.CRITICAL)

        # parse config and get logger
        parsed_config = self._get_parsed_config('file_loggers_config.yml')
        parsed_file_logger = parsed_config.loggers[1]

        # make sure file was opened
        mkdir.assert_called_with('/folder')

        result, msg = self.__compare_file_loggers(
            expected_file_logger, parsed_file_logger)
        self.assertTrue(
            result, msg=f"Default config is not as expected, following comparison failed: {msg}")

    def test_web_logger_all_values_parsed(self):
        """
        All possible values for web logger are set and parsed correctly.
        """
        expected_web_logger = self.__create_web_handler(method='POST',
                                                        url='https://some/url1',
                                                        headers={
                                                            'Content-Type': 'application/json', 'TestHeader1': 'Value1'},
                                                        body='{"message":"message 1"}',
                                                        auth={
                                                            'type': 'basic', 'username': 'admin', 'password': '${WEB_LOGGER_PASSWORD}'},
                                                        min_level=logging.INFO,
                                                        max_level=logging.ERROR)

        # parse config and get logger
        parsed_config = self._get_parsed_config('full_config.yml')
        parsed_web_logger = parsed_config.loggers[0]

        self.assertEqual(expected_web_logger, parsed_web_logger,
                         msg='full web logger is parsed incorrectly')

    def test_web_logger_default_values(self):
        """
        Only required values are set and others are default.
        """
        expected_web_logger = self.__create_web_handler(method='POST',
                                                        url='https://some/url2',
                                                        body='{"message":"message 2"}')

        # parse config and get logger
        parsed_config = self._get_parsed_config('default_config.yml')
        parsed_web_logger = parsed_config.loggers[0]

        self.assertEqual(expected_web_logger, parsed_web_logger,
                         msg='default web logger is parsed incorrectly')

    @unittest.mock.patch('requests.post')
    def test_web_logger_wildcard_replacements_in_post(self, mock_post):
        """
        Test that {{ message }} and {{ name }} are replaced in url, headers and body for POST.
        """
        parsed_config = self._get_parsed_config('full_config.yml')
        parsed_web_logger = parsed_config.loggers[1]

        message = 'test'
        name = parsed_config.name

        parsed_web_logger.emit(LogRecord(
            name=None,
            level=logging.ERROR,
            pathname=None,
            lineno=None,
            msg=message,
            args=None,
            exc_info=None))

        # headers, data and URL are updated
        mock_post.assert_called_once_with(auth=ANY,
                                          data=f"{{\"message\":\"{message}\",\"name\":\"{name}\"}}",
                                          headers={
                                              'Content-Type': 'application/json', 'TestHeader2': f"{name} {message}"},
                                          url=f"https://some/url2?name={name}&message={message}")

    @unittest.mock.patch('requests.get')
    def test_web_logger_wildcard_replacements_in_get(self, mock_get):
        """
        Test that {{ message }} and {{ name }} are replaced in url, headers and body for GET.
        """
        parsed_config = self._get_parsed_config('full_config.yml')
        parsed_web_logger = parsed_config.loggers[2]

        message = 'test'
        name = parsed_config.name

        parsed_web_logger.emit(LogRecord(
            name=None,
            level=logging.ERROR,
            pathname=None,
            lineno=None,
            msg=message,
            args=None,
            exc_info=None))

        # headers, data and URL are updated
        mock_get.assert_called_once_with(auth=ANY,
                                         headers={
                                             'Content-Type': 'application/json', 'TestHeader3': f"{name} {message}"},
                                         url=f"https://some/url3?name={name}&message={message}")

    def __compare_file_loggers(self, first: handlers.RotatingFileHandler, second: handlers.RotatingFileHandler) -> Tuple[bool, str]:
        """
        Helper function to compare two handlers.RotatingFileHandler instances.
        """
        if not isinstance(first, handlers.RotatingFileHandler) or not (second, handlers.RotatingFileHandler):
            return False, "class instance"
        if first.baseFilename != second.baseFilename:
            return False, "filename"
        if first.maxBytes != second.maxBytes:
            return False, "maxBytes"
        if first.backupCount != second.backupCount:
            return False, "backupCount"
        if first.formatter._fmt != second.formatter._fmt:
            return False, "formatter"
        if first.level != second.level:
            return False, "level"
        if len(first.filters) != len(second.filters):
            return False, "filters"
        for x, y in zip(first.filters, second.filters):
            if x != y:
                return False, "filters items"

        return True, None

    def __create_file_logger(self,
                             filename: str,
                             format: str,
                             max_bytes: int = 1048576,
                             backup_count: int = 0,
                             min_level: int = logging.DEBUG,
                             max_level: int = logging.CRITICAL) -> handlers.RotatingFileHandler:
        with mock.patch('builtins.open', create=True):
            handler = handlers.RotatingFileHandler(
                filename=filename,
                maxBytes=max_bytes,
                backupCount=backup_count)
            handler.setFormatter(logging.Formatter(fmt=format))
            handler.setLevel(min_level)
            handler.addFilter(MaxLevelFilter(max_level))

        return handler

    def __create_web_handler(self, method: str,
                             url: str,
                             headers: Optional[Dict[str, str]] = None,
                             body: Optional[str] = None,
                             auth: Optional[Dict[str, str]] = None,
                             min_level: int = logging.DEBUG,
                             max_level: int = logging.CRITICAL,
                             name: str = '') -> WebHandler:

        web = WebHandler(method, url, headers, body, auth, name)
        web.setLevel(min_level)
        web.addFilter(MaxLevelFilter(max_level))

        return web


if __name__ == '__main__':
    unittest.main()
