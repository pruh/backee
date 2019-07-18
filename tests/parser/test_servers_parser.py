import unittest
from unittest import mock

from tests.util.config_mixin import ConfigMixin

from backee.parser.config_parser import parse_config
from backee.model.servers import SshBackupServer
from backee.model.rotation_strategy import RotationStrategy


class LoggersParserTestCase(ConfigMixin, unittest.TestCase):
    """
    Tests for `backee/parser/servers_parser.py`.
    """

    def test_servers_all_values_parsed(self):
        """
        All possible values are set and parsed correctly.
        """
        expected_server = self.__create_ssh_backup_server(name='server 1',
                                                          location='/some/path1',
                                                          hostname='hostname1',
                                                          port=2222,
                                                          username='username1',
                                                          key_path='/path/to/id_rsa1',
                                                          rotation_strategy=RotationStrategy(daily=10, monthly=5, yearly=1))

        # parse config and get server
        parsed_config = self._get_parsed_config('full_config.yml')
        parsed_server = parsed_config.backup_servers[0]

        self.assertEqual(expected_server, parsed_server,
                         msg='full server is not correct')

    def test_servers_default_values_parsed(self):
        """
        Only default values are set and parsed correctly.
        """
        expected_server = self.__create_ssh_backup_server(name='server 2',
                                                          location='/some/path2',
                                                          hostname='hostname2')

        # parse config and get server
        parsed_config = self._get_parsed_config('default_config.yml')
        parsed_server = parsed_config.backup_servers[0]

        self.assertEqual(expected_server, parsed_server,
                         msg='full server is not correct')

    def test_rotation_strategy_overwrites(self):
        """
        Test global rotation strategy is overwritten by server one.
        """
        expected_server = self.__create_ssh_backup_server(name='server 2',
                                                          location='/some/path2',
                                                          hostname='hostname2',
                                                          port=2223,
                                                          username='username2',
                                                          key_path='/path/to/id_rsa2',
                                                          rotation_strategy=RotationStrategy(daily=20, monthly=10, yearly=2))

        # parse config and get server
        parsed_config = self._get_parsed_config('full_config.yml')
        parsed_server = parsed_config.backup_servers[1]

        self.assertEqual(expected_server, parsed_server,
                         msg='server with overwritten rotation strategy is not correct')

    def __create_ssh_backup_server(self, name: str,
                                   location: str,
                                   hostname: str,
                                   port: int = 22,
                                   username: str = None,
                                   key_path: str = None,
                                   rotation_strategy: RotationStrategy = RotationStrategy(daily=1, monthly=0, yearly=0)) -> SshBackupServer:

        return SshBackupServer(
            name=name,
            location=location,
            hostname=hostname,
            port=port,
            username=username,
            key_path=key_path,
            rotation_strategy=rotation_strategy)
