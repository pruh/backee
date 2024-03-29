import unittest
import subprocess
from io import TextIOWrapper, BytesIO

from unittest import mock
from unittest.mock import Mock

from backee.model.items import FilesBackupItem
from backee.model.servers import SshBackupServer
from backee.model.rotation_strategy import RotationStrategy

from backee.backup.transmitter import SshTransmitter

from backee.backup import constants


class SshTransmitterTestCase(unittest.TestCase):
    @mock.patch("subprocess.Popen")
    def test_backup_verified(self, subprocess):
        item = FilesBackupItem(
            includes=(("/a/b/c"),), excludes=(("/a/b/c/d"),), rotation_strategy=None
        )
        server = SshBackupServer(
            name="name",
            rotation_strategy=RotationStrategy(0, 0, 0),
            location="/location",
            hostname="hostname",
            port=22,
            username="username",
            key_path=None,
        )

        subprocess.return_value = self.__get_subprocess_mock(stdout="abc")

        transmitter = SshTransmitter(server)
        self.assertTrue(transmitter.verify_backup(item, "/remote_path"))
        self.assertTrue(subprocess.called)

    @mock.patch("subprocess.Popen")
    def test_wildcards_backup_verified(self, subprocess):
        item = FilesBackupItem(
            includes=(("/a/b/*.db"),),
            excludes=(("/a/b/*.log"),),
            rotation_strategy=None,
        )
        server = SshBackupServer(
            name="name",
            rotation_strategy=RotationStrategy(0, 0, 0),
            location="/location",
            hostname="hostname",
            port=22,
            username="username",
            key_path=None,
        )

        subprocess.return_value = self.__get_subprocess_mock(
            stdout="abc",
        )

        transmitter = SshTransmitter(server)
        self.assertTrue(transmitter.verify_backup(item, "/remote_path"))
        self.assertTrue(subprocess.called)

    @mock.patch("subprocess.Popen")
    def test_backup_verified_warning(self, subprocess):
        item = FilesBackupItem(
            includes=(("/a/b/c"),), excludes=(("/a/b/c/d"),), rotation_strategy=None
        )
        server = SshBackupServer(
            name="name",
            rotation_strategy=RotationStrategy(0, 0, 0),
            location="/location",
            hostname="hostname",
            port=22,
            username="username",
            key_path=None,
        )

        subprocess.return_value = self.__get_subprocess_mock(
            stdout=">Xcstpoguax",
        )

        transmitter = SshTransmitter(server)
        self.assertFalse(transmitter.verify_backup(item, "/remote_path"))
        self.assertTrue(subprocess.called)

    @mock.patch("subprocess.Popen")
    def test_backup_verified_error(self, subprocess):
        item = FilesBackupItem(
            includes=(("/a/b/c"),), excludes=(("/a/b/c/d"),), rotation_strategy=None
        )
        server = SshBackupServer(
            name="name",
            rotation_strategy=RotationStrategy(0, 0, 0),
            location="/location",
            hostname="hostname",
            port=22,
            username="username",
            key_path=None,
        )

        subprocess.return_value = self.__get_subprocess_mock(
            stdout=".Xcstpoguax",
        )

        transmitter = SshTransmitter(server)
        self.assertFalse(transmitter.verify_backup(item, "/remote_path"))
        self.assertTrue(subprocess.called)

    def test_get_backup_names_sorted(self):
        ssh = Mock()
        stdout = Mock()
        stdout.readlines.return_value = ["a\nb\nc"]
        stderr = Mock()
        stderr.readlines.return_value = []
        ssh.exec_command.return_value = tuple([None, stdout, stderr])

        transmitter = SshTransmitter(server=Mock(), ssh_client=ssh)
        self.assertEqual(
            tuple(["a", "b", "c"]), transmitter.get_backup_names_sorted("/remote_path")
        )

    @mock.patch("subprocess.Popen")
    def test_backup_skipped_for_vanished_items(self, subprocess):
        item = FilesBackupItem(
            includes=(("/a/b/c"),), excludes=(("/a/b/c/d"),), rotation_strategy=None
        )
        server = SshBackupServer(
            name="name",
            rotation_strategy=RotationStrategy(0, 0, 0),
            location="/location",
            hostname="hostname",
            port=22,
            username="username",
            key_path=None,
        )

        subprocess.return_value = self.__get_subprocess_mock(
            stdout="abc", exit_code=constants.RSYNC_STATUS_SOURCE_VANISHED
        )

        transmitter = SshTransmitter(server, deps=())
        self.assertTrue(transmitter.verify_backup(item, "/remote_path"))
        self.assertTrue(subprocess.called)

    def __get_subprocess_mock(
        self,
        stdout: str,
        stderr: str = "",
        exit_code: int = 0,
    ) -> Mock:
        process_mock = Mock()
        attrs = {
            "__enter__": Mock(return_value=process_mock),
            "__exit__": Mock(return_value=None),
            "stdout": TextIOWrapper(BytesIO(stdout.encode("utf-8")), "utf8"),
            "stderr": TextIOWrapper(BytesIO(stderr.encode("utf-8")), "utf8"),
            "wait.return_value": exit_code,
        }
        process_mock.configure_mock(**attrs)
        return process_mock


if __name__ == "__main__":
    unittest.main()
