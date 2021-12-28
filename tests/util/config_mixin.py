import os
import logging
from unittest import mock

from backee.parser.config_parser import parse_config


class ConfigMixin:
    def __get_config_file_contents(self, filename: str):
        config_file = os.path.join(
            os.path.dirname(__file__), os.pardir, "resources", filename
        )
        with open(config_file) as f:
            return f.read()

    def _get_parsed_config(self, filename: str):
        mock_config = mock.mock_open(
            read_data=self.__get_config_file_contents(filename)
        )
        with mock.patch("builtins.open", mock_config, create=True):
            parsed_config = parse_config(filename=None)
        return parsed_config
