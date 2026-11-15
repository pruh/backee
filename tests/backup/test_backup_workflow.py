import unittest
from datetime import date, datetime
from unittest import mock

from backee.backup import backup
from backee.model.items import FilesBackupItem
from backee.model.rotation_strategy import RotationStrategy
from backee.model.servers import BackupServer, SshBackupServer


class BackupWorkflowTestCase(unittest.TestCase):
    def setUp(self):
        self.item = FilesBackupItem(
            includes=("/source",), excludes=(), rotation_strategy=None
        )
        self.server = SshBackupServer(
            name="destination",
            rotation_strategy=RotationStrategy(daily=2, monthly=0, yearly=0),
            location="/backups",
            hostname="backup.example",
            port=22,
            username="backup",
            key_path=None,
        )
        self.root = "/backups/files/"
        self.snapshot = self.root + "backup_2026-11-15-12-30/"
        self.incomplete = self.root + "backup_2026-11-15-12-30-incomplete/"
        self.current = self.root + "current"

        factory_patch = mock.patch.object(backup, "SshTransmitter", autospec=True)
        self.factory = factory_patch.start()
        self.addCleanup(factory_patch.stop)
        self.transmitter = self.factory.return_value
        self.transmitter.is_remote_dir_exist.return_value = False
        self.transmitter.get_transfer_file_size.return_value = 100
        self.transmitter.get_disk_space_available.return_value = 100
        self.transmitter.get_backup_names_sorted.return_value = ()
        self.transmitter.verify_backup.return_value = True

        datetime_patch = mock.patch.object(backup, "datetime", wraps=datetime)
        datetime_patch.start().now.return_value = datetime(2026, 11, 15, 12, 30)
        self.addCleanup(datetime_patch.stop)
        date_patch = mock.patch.object(backup, "date", wraps=date)
        date_patch.start().today.return_value = date(2026, 11, 15)
        self.addCleanup(date_patch.stop)

    def run_backup(self):
        backup.backup("example", (self.item,), (self.server,))

    def test_first_backup_publishes_snapshot_only_after_transfer(self):
        self.run_backup()

        self.factory.assert_called_once_with(self.server)
        self.transmitter.create_dir.assert_called_once_with(self.root)
        self.transmitter.get_transfer_file_size.assert_called_once_with(
            links_dir_path=self.current, item=self.item, remote_path=self.incomplete
        )
        self.transmitter.assert_has_calls(
            [
                mock.call.transmit(self.current, self.item, self.incomplete),
                mock.call.rename_dir(self.incomplete, self.snapshot),
                mock.call.recreate_links_dir(self.snapshot, self.current),
            ]
        )
        self.transmitter.verify_backup.assert_called_once_with(self.item, self.current)
        self.transmitter.remove_remote_dirs.assert_not_called()

    def test_existing_destination_recovers_links_before_transfer(self):
        self.transmitter.is_remote_dir_exist.return_value = True

        self.run_backup()

        self.transmitter.create_dir.assert_not_called()
        self.transmitter.assert_has_calls(
            [
                mock.call.remove_remote_dir_if_exists(self.snapshot),
                mock.call.remove_remote_dir_if_exists(self.incomplete),
                mock.call.check_temp_dirs(self.root, "-incomplete"),
                mock.call.check_links_dir(self.root, self.current, "-incomplete"),
            ]
        )
        calls = self.transmitter.mock_calls
        self.assertLess(
            calls.index(
                mock.call.check_links_dir(self.root, self.current, "-incomplete")
            ),
            calls.index(mock.call.transmit(self.current, self.item, self.incomplete)),
        )

    def test_retention_removes_expired_snapshots_but_keeps_recent_and_incomplete(self):
        old = self.root + "backup_2026-11-12-12-30"
        recent = self.root + "backup_2026-11-14-12-30"
        self.transmitter.get_backup_names_sorted.return_value = (
            old,
            recent,
            self.incomplete.rstrip("/"),
            self.snapshot.rstrip("/"),
        )

        self.run_backup()

        self.transmitter.remove_remote_dirs.assert_called_once_with((old,))

    def test_insufficient_space_stops_before_transfer(self):
        self.transmitter.get_disk_space_available.return_value = 99

        with self.assertRaisesRegex(OSError, "not enough space"):
            self.run_backup()

        self.transmitter.transmit.assert_not_called()
        self.transmitter.rename_dir.assert_not_called()
        self.transmitter.recreate_links_dir.assert_not_called()
        self.transmitter.remove_remote_dirs.assert_not_called()

    def test_failed_transfer_does_not_publish_snapshot_or_rotate_backups(self):
        self.transmitter.transmit.side_effect = OSError("transfer failed")

        with self.assertRaisesRegex(OSError, "transfer failed"):
            self.run_backup()

        self.transmitter.rename_dir.assert_not_called()
        self.transmitter.recreate_links_dir.assert_not_called()
        self.transmitter.get_backup_names_sorted.assert_not_called()
        self.transmitter.verify_backup.assert_not_called()

    def test_verification_difference_is_logged(self):
        self.transmitter.verify_backup.return_value = False

        with self.assertLogs(backup.log, level="WARNING") as logs:
            self.run_backup()

        self.assertIn("backup items differ from original items", logs.output[0])

    def test_unsupported_server_is_rejected_before_transfer(self):
        server = BackupServer("unsupported", self.server.rotation_strategy)

        with self.assertRaisesRegex(TypeError, "unsupported server"):
            backup.backup("example", (self.item,), (server,))

        self.factory.assert_not_called()


if __name__ == "__main__":
    unittest.main()
