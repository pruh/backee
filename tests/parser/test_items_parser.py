import unittest
from unittest import mock

from typing import Tuple, Optional

from backee.model.items import (
    BackupItem,
    FilesBackupItem,
    MysqlBackupItem,
    DatabaseBackupItem,
    DockerDataVolumesBackupItem,
)
from backee.model.db_connectors import DbConnector, RemoteConnector, DockerConnector
from backee.model.rotation_strategy import RotationStrategy
from backee.parser.config_parser import parse_config
from backee.parser.items_parser import parse_items

from tests.util.config_mixin import ConfigMixin


class ItemsParserTestCase(ConfigMixin, unittest.TestCase):
    """
    Tests for `backee/parser/items_parser.py`.
    """

    @unittest.mock.patch("os.path.exists")
    def test_file_items_all_values_parsed(self, exists):
        """
        All possible values are set and parsed correctly.
        """

        def exists_side_effect(path):
            return True

        exists.side_effect = exists_side_effect

        expected_file_item = self.__create_file_item(
            includes=(
                "/path/to/include1",
                "/path/to/include2",
            ),
            excludes=("/path/to/include/exclude",),
            rotation_strategy=None,
        )

        # parse config and get file items
        parsed_config = self._get_parsed_config("full_config.yml")
        parsed_file_item = parsed_config.backup_items[0]

        self.assertEqual(
            expected_file_item,
            parsed_file_item,
            msg="full file item is parsed incorrectly",
        )

    def test_no_backup_items_parsed(self):
        """
        Only default values are set and parsed correctly.
        """
        self.assertIsNone(parse_items(None), msg="backup items should be empty")

    def test_empty_backup_items_parsed(self):
        """
        Only default values are set and parsed correctly.
        """
        self.assertIsNone(parse_items({}), msg="backup items should be None")

    def test_local_database_values_parsed(self):
        """
        All possible values are set and parsed correctly.
        """
        expected_database = self.__create_database_item(
            username="username1",
            password="password1",
            database="database1",
            connector=self.__create_db_remote_connector(
                hostname="127.0.0.1", port=3360
            ),
            rotation_strategy=RotationStrategy(daily=30, monthly=15, yearly=3),
        )

        parsed_config = self._get_parsed_config("full_config.yml")
        parsed_database_items = parsed_config.backup_items[1]

        self.assertEqual(
            expected_database,
            parsed_database_items,
            msg="full database items are parsed incorrectly",
        )

    def test_remote_database_values_parsed(self):
        """
        All possible values are set and parsed correctly.
        """
        expected_database = self.__create_database_item(
            username="username2",
            password="password2",
            database="database2",
            connector=self.__create_db_remote_connector(
                hostname="192.168.1.1", port=3365
            ),
            rotation_strategy=None,
        )

        parsed_config = self._get_parsed_config("full_config.yml")
        parsed_database_items = parsed_config.backup_items[2]

        self.assertEqual(
            expected_database,
            parsed_database_items,
            msg="full database items are parsed incorrectly",
        )

    def test_docker_database_values_parsed(self):
        """
        All possible values are set and parsed correctly.
        """
        expected_database = self.__create_database_item(
            username="username3",
            password="${MYSQL_PASSWORD}",
            database="database3",
            connector=self.__create_db_docker_connector(
                container="container3", port=3370
            ),
            rotation_strategy=None,
        )

        parsed_config = self._get_parsed_config("full_config.yml")
        parsed_database_items = parsed_config.backup_items[3]

        self.assertEqual(
            expected_database,
            parsed_database_items,
            msg="full database items are parsed incorrectly",
        )

    def test_docker_items_all_values_parsed(self):
        """
        All possible values are set and parsed correctly.
        """
        expected_docker_item_1 = self.__create_docker_backup_item(
            volume="data_container_1",
            rotation_strategy=RotationStrategy(daily=40, monthly=20, yearly=4),
        )
        expected_docker_item_2 = self.__create_docker_backup_item(
            volume="data_container_2",
            rotation_strategy=RotationStrategy(daily=40, monthly=20, yearly=4),
        )

        parsed_config = self._get_parsed_config("full_config.yml")

        self.assertEqual(
            expected_docker_item_1,
            parsed_config.backup_items[4],
            msg="full docker item is parsed incorrectly",
        )
        self.assertEqual(
            expected_docker_item_2,
            parsed_config.backup_items[5],
            msg="full docker item is parsed incorrectly",
        )

    def test_excludes_file_item_optional(self):
        parsed_config = self._get_parsed_config("default_config.yml")
        item = parsed_config.backup_items[0]

        self.assertEqual((), item.excludes, msg="excludes parsed incirrectly")

    @unittest.mock.patch("os.path.expanduser")
    @unittest.mock.patch("os.path.exists")
    def test_paths_expanded(self, exists, expanduser):
        """
        Test that ~ in path to local file items is expanded
        """

        def expanduser_side_effect(path: str):
            if "~" in path:
                return path.replace("~", "/a")
            else:
                return path

        expanduser.side_effect = expanduser_side_effect

        def exists_side_effect(path):
            return True

        exists.side_effect = exists_side_effect

        item = {"files": {"includes": ["~/b/c", "/d/e/f"], "excludes": ["~/y/z"]}}
        parsed = parse_items(item)
        self.assertEqual(parsed[0].includes, tuple(["/a/b/c", "/d/e/f"]))
        self.assertEqual(parsed[0].excludes, tuple(["/a/y/z"]))

    @unittest.mock.patch("os.path.exists")
    def test_nonexistent_items_skipped(self, exists):
        """
        Test when file backup item does not exists it is removed from the results.
        """
        exists1 = "/a/b/c"
        exists2 = "/d/e/f"
        nonexistent1 = "/g/h/i"
        nonexistent2 = "/j/k/l"

        def side_effect(path):
            if path == exists1 or path == exists2:
                return True
            else:
                return False

        exists.side_effect = side_effect

        item = {
            "files": {
                "includes": [exists1, nonexistent1],
                "excludes": [exists2, nonexistent2],
            }
        }
        parsed = parse_items(item)
        self.assertEqual(parsed[0].includes, tuple(["/a/b/c"]))
        self.assertEqual(parsed[0].excludes, tuple(["/d/e/f"]))

    def __create_file_item(
        self,
        includes: Tuple[str] = ((),),
        excludes: Tuple[str] = ((),),
        rotation_strategy: RotationStrategy = None,
    ) -> FilesBackupItem:
        return FilesBackupItem(
            includes=includes, excludes=excludes, rotation_strategy=rotation_strategy
        )

    def __create_database_item(
        self,
        username: str,
        password: str,
        database: str,
        connector: DbConnector,
        rotation_strategy: RotationStrategy = None,
    ) -> MysqlBackupItem:
        return MysqlBackupItem(
            username=username,
            password=password,
            database=database,
            connector=connector,
            rotation_strategy=rotation_strategy,
        )

    def __create_docker_backup_item(
        self, volume: str, rotation_strategy: RotationStrategy = None
    ) -> DockerDataVolumesBackupItem:
        return DockerDataVolumesBackupItem(
            volume=volume, rotation_strategy=rotation_strategy
        )

    def __create_db_remote_connector(self, hostname: str, port: int) -> RemoteConnector:
        return RemoteConnector(hostname=hostname, port=port)

    def __create_db_docker_connector(
        self, container: str, port: int
    ) -> DockerConnector:
        return DockerConnector(container=container, port=port)


if __name__ == "__main__":
    unittest.main()
