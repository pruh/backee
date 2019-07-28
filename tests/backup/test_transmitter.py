import unittest
import subprocess

from backee.model.items import FilesBackupItem
from backee.model.servers import SshBackupServer
from backee.model.rotation_strategy import RotationStrategy

from backee.backup.transmitter import SshTransmitter


class SshTransmitterTestCase(unittest.TestCase):

    @unittest.mock.patch('subprocess.Popen')
    def test_backup_verified(self, subprocess):
        item = FilesBackupItem(
            includes=(('/a/b/c'),),
            excludes=(('/a/b/c/d'),),
            rotation_strategy=None)
        server = SshBackupServer(
            name='name',
            rotation_strategy=RotationStrategy(0, 0, 0),
            location='/location',
            hostname='hostname',
            port=22,
            username='username',
            key_path=None
        )

        subprocess.return_value = self.__get_subprocess_mock(
            stdout=('abc',))

        transmitter = SshTransmitter(server)
        self.assertTrue(transmitter.verify_backup(item, '/remote_path'))
        self.assertTrue(subprocess.called)

    @unittest.mock.patch('subprocess.Popen')
    def test_backup_verified_warning(self, subprocess):
        item = FilesBackupItem(
            includes=(('/a/b/c'),),
            excludes=(('/a/b/c/d'),),
            rotation_strategy=None)
        server = SshBackupServer(
            name='name',
            rotation_strategy=RotationStrategy(0, 0, 0),
            location='/location',
            hostname='hostname',
            port=22,
            username='username',
            key_path=None
        )

        subprocess.return_value = self.__get_subprocess_mock(
            stdout=('>Xcstpoguax',))

        transmitter = SshTransmitter(server)
        self.assertFalse(transmitter.verify_backup(item, '/remote_path'))
        self.assertTrue(subprocess.called)

    @unittest.mock.patch('subprocess.Popen')
    def test_backup_verified_error(self, subprocess):
        item = FilesBackupItem(
            includes=(('/a/b/c'),),
            excludes=(('/a/b/c/d'),),
            rotation_strategy=None)
        server = SshBackupServer(
            name='name',
            rotation_strategy=RotationStrategy(0, 0, 0),
            location='/location',
            hostname='hostname',
            port=22,
            username='username',
            key_path=None
        )

        subprocess.return_value = self.__get_subprocess_mock(
            stdout=('.Xcstpoguax',))

        transmitter = SshTransmitter(server)
        self.assertFalse(transmitter.verify_backup(item, '/remote_path'))
        self.assertTrue(subprocess.called)

    def __get_subprocess_mock(self, stdout: str, stderr: str = '') -> unittest.mock.Mock:
        process_mock = unittest.mock.Mock()
        attrs = {
            '__enter__': unittest.mock.Mock(return_value=process_mock),
            '__exit__': unittest.mock.Mock(return_value=None),
            'stdout': stdout,
            'stderr': '',
            'wait.return_value': 0,
        }
        process_mock.configure_mock(**attrs)
        return process_mock


if __name__ == '__main__':
    unittest.main()
