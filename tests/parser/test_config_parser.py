import os
import unittest
from unittest import mock

from tests.util.config_mixin import ConfigMixin

from backee.parser.config_parser import parse_config


class ConfigParserTestCase(ConfigMixin, unittest.TestCase):
    """
    Tests for `backee/parser/config_parser.py`.
    """

    @mock.patch.dict('os.environ', {'WEB_LOGGER_PASSWORD': 'ABC123qwe'})
    def test_env_variables_replaced(self):
        """
        Assert that env variables are replaced in parsed config.
        """
        password = 'ABC123qwe'
        parsed_config = self._get_parsed_config('full_config.yml')
        logger_with_replaced_password = parsed_config.loggers[0]

        # replaced if env variable is present
        self.assertEqual(password, logger_with_replaced_password._auth.password,
                         msg='password is not replaced')

        db_backup_item_with_unchaged_password = parsed_config.backup_items[3]

        # not replaced if there is no such env variable
        self.assertEqual('${MYSQL_PASSWORD}', db_backup_item_with_unchaged_password.password,
                         msg='password should not be replaced')


if __name__ == '__main__':
    unittest.main()
