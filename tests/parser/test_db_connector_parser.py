import unittest

from backee.model.db_connectors import RemoteConnector, DockerConnector

from tests.util.config_mixin import ConfigMixin


class ItemsParserTestCase(ConfigMixin, unittest.TestCase):
    """
    Tests for `backee/parser/db_connector_parser.py`.
    """

    def test_local_db_parser(self):
        expected_db_connector = RemoteConnector(hostname="127.0.0.1", port=3360)

        parsed_config = self._get_parsed_config("full_config.yml")
        parsed_connector = parsed_config.backup_items[1].connector

        self.assertEqual(
            expected_db_connector,
            parsed_connector,
            msg="local connector is parsed incorrectly",
        )

    def test_remote_db_parser(self):
        expected_db_connector = RemoteConnector(hostname="192.168.1.1", port=3365)

        parsed_config = self._get_parsed_config("full_config.yml")
        parsed_connector = parsed_config.backup_items[2].connector

        self.assertEqual(
            expected_db_connector,
            parsed_connector,
            msg="local connector is parsed incorrectly",
        )

    def test_docker_db_parser(self):
        expected_db_connector = DockerConnector(container="container3", port=3370)

        parsed_config = self._get_parsed_config("full_config.yml")
        parsed_connector = parsed_config.backup_items[3].connector

        self.assertEqual(
            expected_db_connector,
            parsed_connector,
            msg="local connector is parsed incorrectly",
        )


if __name__ == "__main__":
    unittest.main()
