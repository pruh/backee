import unittest
from unittest import mock
from datetime import datetime, date
from dateutil.relativedelta import relativedelta

from backee.backup import backup
from backee.backup.transmitter import SshTransmitter, Transmitter
from backee.model.rotation_strategy import RotationStrategy
from backee.model.items import FilesBackupItem


class BackupTestCase(unittest.TestCase):
    @unittest.mock.patch("backee.backup.transmitter.SshTransmitter")
    def test_old_daily_backups_remove(self, transmitter):
        date_time_format = "%Y-%m-%d-%H-%M"
        now = datetime.now().replace(minute=1)
        today = now.strftime(date_time_format)
        one_day_ago_1 = (now + relativedelta(days=-1)).strftime(date_time_format)
        one_day_ago_2 = (now + relativedelta(days=-1, minute=2)).strftime(
            date_time_format
        )
        two_days_ago = (now + relativedelta(days=-2)).strftime(date_time_format)
        three_days_ago = (now + relativedelta(days=-3)).strftime(date_time_format)
        four_days_ago = (now + relativedelta(days=-4)).strftime(date_time_format)
        tomorrow = (now + relativedelta(days=+1)).strftime(date_time_format)
        sorted_dates = sorted(
            (
                today,
                one_day_ago_1,
                one_day_ago_2,
                two_days_ago,
                three_days_ago,
                four_days_ago,
                tomorrow,
            )
        )
        transmitter.get_backup_names_sorted.return_value = sorted_dates
        rs = RotationStrategy(daily=2, monthly=0, yearly=0)
        backup._remove_old_backups(
            transmitter=transmitter,
            server_root_dir_path="",
            rotation_strategy=rs,
            date_time_format=date_time_format,
            date_time_prefix="",
        )

        to_delete = tuple(
            sorted((two_days_ago, three_days_ago, four_days_ago, tomorrow))
        )
        self.assertCountEqual(
            to_delete,
            transmitter.remove_remote_dirs.call_args_list[0][0][0],
            msg="wrong daily backups to delete",
        )

    @unittest.mock.patch("backee.backup.transmitter.SshTransmitter")
    def test_old_monthly_backups_remove(self, transmitter):
        prefix = "abc_"
        date_time_format = "%Y-%m-%d-%H-%M"
        now = date.today()
        first_day_of_month = date(day=1, month=now.month, year=now.year)
        today = prefix + first_day_of_month.strftime(date_time_format)
        future_monthly = prefix + (
            first_day_of_month + relativedelta(months=+1)
        ).strftime(date_time_format)
        non_monthly = prefix + (first_day_of_month + relativedelta(days=+1)).strftime(
            date_time_format
        )
        one_month_ago_1 = prefix + (
            first_day_of_month + relativedelta(months=-1)
        ).strftime(date_time_format)
        one_month_ago_2 = prefix + (
            first_day_of_month + relativedelta(months=-1, minutes=+1)
        ).strftime(date_time_format)
        two_months_ago = prefix + (
            first_day_of_month + relativedelta(months=-2)
        ).strftime(date_time_format)
        three_months_ago = prefix + (
            first_day_of_month + relativedelta(months=-3)
        ).strftime(date_time_format)
        sorted_dates = tuple(
            sorted(
                (
                    today,
                    future_monthly,
                    non_monthly,
                    one_month_ago_1,
                    one_month_ago_2,
                    two_months_ago,
                    three_months_ago,
                )
            )
        )
        transmitter.get_backup_names_sorted.return_value = sorted_dates
        rs = RotationStrategy(daily=0, monthly=2, yearly=0)
        backup._remove_old_backups(
            transmitter=transmitter,
            server_root_dir_path="",
            rotation_strategy=rs,
            date_time_format=date_time_format,
            date_time_prefix=prefix,
        )

        to_delete = tuple(
            sorted(
                (
                    future_monthly,
                    non_monthly,
                    one_month_ago_2,
                    two_months_ago,
                    three_months_ago,
                )
            )
        )
        self.assertCountEqual(
            to_delete,
            transmitter.remove_remote_dirs.call_args_list[0][0][0],
            msg="wrong monthly backups to delete",
        )

    @unittest.mock.patch("backee.backup.transmitter.SshTransmitter")
    def test_old_yearly_backups_remove(self, transmitter):
        date_time_format = "%Y-%m-%d-%H-%M"
        now = date.today()
        first_day_of_year = date(day=1, month=1, year=now.year)
        today = first_day_of_year.strftime(date_time_format)
        future_year = (first_day_of_year + relativedelta(years=+1)).strftime(
            date_time_format
        )
        non_yearly = (first_day_of_year + relativedelta(days=+1)).strftime(
            date_time_format
        )
        one_year_ago_1 = (first_day_of_year + relativedelta(years=-1)).strftime(
            date_time_format
        )
        one_year_ago_2 = (
            first_day_of_year + relativedelta(years=-1, minutes=+1)
        ).strftime(date_time_format)
        two_years_ago = (first_day_of_year + relativedelta(years=-2)).strftime(
            date_time_format
        )
        three_years_ago = (first_day_of_year + relativedelta(years=-3)).strftime(
            date_time_format
        )
        sorted_dates = tuple(
            sorted(
                (
                    today,
                    future_year,
                    non_yearly,
                    one_year_ago_1,
                    one_year_ago_2,
                    two_years_ago,
                    three_years_ago,
                )
            )
        )
        transmitter.get_backup_names_sorted.return_value = sorted_dates
        rs = RotationStrategy(daily=0, monthly=0, yearly=2)
        backup._remove_old_backups(
            transmitter=transmitter,
            server_root_dir_path="",
            rotation_strategy=rs,
            date_time_format=date_time_format,
            date_time_prefix="",
        )

        to_delete = tuple(
            sorted(
                (
                    future_year,
                    non_yearly,
                    one_year_ago_2,
                    two_years_ago,
                    three_years_ago,
                )
            )
        )
        self.assertCountEqual(
            to_delete,
            transmitter.remove_remote_dirs.call_args_list[0][0][0],
            msg="wrong yearly backups to delete",
        )

    @unittest.mock.patch("backee.backup.transmitter.SshTransmitter")
    def test_many_old_backups(self, transmitter):
        date_time_format = "%Y-%m-%d-%H-%M"
        prefix = "prefix-"
        today = date.today()
        sorted_dates = []
        for day in range(366, -1, -1):
            sorted_dates.append(
                prefix + (today + relativedelta(days=-day)).strftime(date_time_format)
            )

        transmitter.get_backup_names_sorted.return_value = sorted_dates
        rs = RotationStrategy(daily=1, monthly=1, yearly=1)
        backup._remove_old_backups(
            transmitter=transmitter,
            server_root_dir_path="",
            rotation_strategy=rs,
            date_time_format=date_time_format,
            date_time_prefix=prefix,
        )

        to_delete = sorted_dates.copy()
        daily = prefix + today.strftime(date_time_format)
        monthly = prefix + date(day=1, month=today.month, year=today.year).strftime(
            date_time_format
        )
        yearly = prefix + date(day=1, month=1, year=today.year).strftime(
            date_time_format
        )
        to_delete.remove(daily)
        to_delete.remove(monthly)
        to_delete.remove(yearly)

        self.assertListEqual(
            to_delete,
            list(transmitter.remove_remote_dirs.call_args_list[0][0][0]),
            msg="wrong number of backups to delete",
        )

    @unittest.mock.patch("backee.backup.transmitter.SshTransmitter")
    def test_zero_rotation_strategy(self, transmitter):
        """
        Test if rotation strategy has 0, than that backups will be removed.
        """
        date_time_format = "%Y-%m-%d-%H-%M"
        now = date.today()
        first_day_of_year = date(day=1, month=1, year=now.year)
        today = first_day_of_year.strftime(date_time_format)

        sorted_dates = ((today),)
        transmitter.get_backup_names_sorted.return_value = sorted_dates
        rs = RotationStrategy(daily=0, monthly=0, yearly=0)
        backup._remove_old_backups(
            transmitter=transmitter,
            server_root_dir_path="",
            rotation_strategy=rs,
            date_time_format=date_time_format,
            date_time_prefix="",
        )

        self.assertCountEqual(
            ((today),),
            transmitter.remove_remote_dirs.call_args_list[0][0][0],
            msg="wrong yearly backups to delete",
        )

    def test_proper_rotation_strategy(self):
        """
        Test that item rotation strategy is used if any, server otherwise.
        """
        server_strategy = RotationStrategy(10, 10, 10)
        item_strategy = RotationStrategy(20, 20, 20)
        self.assertEqual(
            item_strategy,
            backup._get_rotation_strategy(
                server_strategy=server_strategy, item_strategy=item_strategy
            ),
            msg="wrong rotation strategy is used",
        )

        item_strategy = None
        self.assertEqual(
            server_strategy,
            backup._get_rotation_strategy(
                server_strategy=server_strategy, item_strategy=item_strategy
            ),
            msg="wrong rotation strategy is used",
        )

    @unittest.mock.patch("backee.backup.transmitter.SshTransmitter")
    def test_remote_disk_space(self, transmitter):
        """
        Test error is raised when there is no enough disk space.
        """
        transmitter.get_transfer_file_size.return_value = 2
        transmitter.get_disk_space_available.return_value = 1

        self.assertRaises(
            OSError,
            backup._check_remote_disk_space,
            transmitter,
            "",
            FilesBackupItem(includes=(), excludes=(), rotation_strategy=None),
            "",
            "",
        )


if __name__ == "__main__":
    unittest.main()
