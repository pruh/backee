import os
import logging
from datetime import datetime, date
from dateutil.relativedelta import relativedelta

from typing import Tuple, List, Optional

from backee.model.items import BackupItem, FilesBackupItem
from backee.model.servers import BackupServer, SshBackupServer
from backee.backup.transmitter import Transmitter, SshTransmitter
from backee.model.rotation_strategy import RotationStrategy

log = logging.getLogger(__name__)


def backup(items: Tuple[BackupItem], servers: Tuple[BackupServer]) -> None:
    """
    Start backup process.
    """
    for item in items:
        _check_item(item)

    for server in servers:
        __backup_to_server(items, server)


def __backup_to_server(items: Tuple[BackupItem], server: BackupServer) -> None:
    log.debug(f"backup to {server.name}")

    transmitter = __create_transmitter(server)

    for item in items:
        if isinstance(item, FilesBackupItem):
            __backup_files_to_server(transmitter, server, item)
        else:
            log.info(f"unsupported backup item: {item.name}")

    log.info(f"backup to {server.name} finished")


def __create_transmitter(server: BackupServer) -> Transmitter:
    if isinstance(server, SshBackupServer):
        return SshTransmitter(server)

    raise TypeError(f"unsupported server {server}")


def __backup_files_to_server(transmitter: SshTransmitter,
                             server: SshBackupServer,
                             item: FilesBackupItem) -> None:
    log.debug(f'backup {item.name}')

    server_root_dir_path = os.path.join(server.location, item.name, '')
    date_time_prefix = 'backup_'
    date_time_format = "%Y-%m-%d-%H-%M"
    backup_dir_name = date_time_prefix + \
        datetime.strftime(datetime.now(), date_time_format)
    backup_dir_path = os.path.join(
        server_root_dir_path, backup_dir_name, '')
    temp_dir_suffix = '-incomplete'
    temp_dir_name = backup_dir_name + temp_dir_suffix
    temp_dir_path = os.path.join(server_root_dir_path, temp_dir_name, '')
    links_dir_path = os.path.join(server_root_dir_path, 'current')

    if not transmitter.is_remote_dir_exist(server_root_dir_path):
        transmitter.create_dir(server_root_dir_path)
    else:
        transmitter.remove_remote_dir_if_exists(backup_dir_path)
        transmitter.remove_remote_dir_if_exists(temp_dir_path)

        transmitter.check_temp_dirs(server_root_dir_path, temp_dir_suffix)

        transmitter.check_links_dir(server_root_dir_path,
                                    item.name,
                                    links_dir_path,
                                    temp_dir_suffix)

    _check_remote_disk_space(
        transmitter, links_dir_path, item, temp_dir_path, server_root_dir_path)

    transmitter.transmit(links_dir_path, item, temp_dir_path)

    transmitter.rename_dir(temp_dir_path, backup_dir_path)

    transmitter.recreate_links_dir(backup_dir_path, links_dir_path)

    rs = _get_rotation_strategy(
        server.rotation_strategy, item.rotation_strategy)
    _remove_old_backups(
        transmitter,
        server_root_dir_path,
        rs,
        date_time_format,
        date_time_prefix)

    if transmitter.verify_backup(item, links_dir_path):
        log.debug(f"{item.name} backup finished")
    else:
        log.warning(f"{item.name} backup items differ from original items")


def _check_remote_disk_space(
        transmitter: SshTransmitter,
        links_dir_path: str,
        item: FilesBackupItem,
        remote_path: str,
        server_root_dir_path: str) -> None:
    log.debug('checking available space')
    transfer_size = transmitter.get_transfer_file_size(
        links_dir_path=links_dir_path,
        item=item,
        remote_path=remote_path)
    space_avail = transmitter.get_disk_space_available(server_root_dir_path)
    if space_avail < transfer_size:
        raise OSError(
            f"not enoght space to backup {item.name},"
            f" need {transfer_size - space_avail} bytes more")
    log.debug(f"{space_avail} bytes available for {transfer_size} bytes backup")


def _remove_old_backups(transmitter: SshTransmitter,
                        server_root_dir_path: str,
                        rotation_strategy: RotationStrategy,
                        date_time_format: str,
                        date_time_prefix: str) -> None:
    log.debug('looking for outdated backups')

    backups = transmitter.get_backup_names_sorted(server_root_dir_path)

    # backups to keep
    daily_backups = []
    monthly_backups = []
    yearly_backups = []
    now = date.today()
    for backup in backups:
        backup_date = __get_date_time(
            backup, date_time_format, date_time_prefix)
        if rotation_strategy.daily > 0 and \
                __is_in_timeframe(backup_date, now, now + relativedelta(days=-rotation_strategy.daily + 1)):
            daily_backups.append(backup)
        if rotation_strategy.monthly > 0 and \
                len(monthly_backups) < rotation_strategy.monthly and \
                __is_monthly_backup(backup_date) and \
                __is_in_timeframe(backup_date, now, now + relativedelta(months=-rotation_strategy.monthly + 1, day=1)) and \
                not __is_same_backup(monthly_backups, backup_date, date_time_format, date_time_prefix):
            monthly_backups.append(backup)
        if rotation_strategy.yearly > 0 and \
                len(yearly_backups) < rotation_strategy.yearly and \
                __is_yearly_backup(backup_date) and \
                __is_in_timeframe(backup_date, now, now + relativedelta(years=-rotation_strategy.yearly + 1, day=1, month=1)) and \
                not __is_same_backup(yearly_backups, backup_date, date_time_format, date_time_prefix):
            yearly_backups.append(backup)
    exclude = set(daily_backups)
    exclude.update(monthly_backups)
    exclude.update(yearly_backups)

    to_delete = tuple([x for x in backups if x not in exclude])
    if len(to_delete) == 0:
        log.debug("no outdated backups")
        return

    log.debug(f"removing outdated backup(s) {to_delete}")

    transmitter.remove_remote_dirs(to_delete)


def __is_in_timeframe(backup_date: date,
                      now: date,
                      last_eligible_date_time: date) -> bool:
    return last_eligible_date_time <= backup_date <= now


def __get_date_time(backup: str,
                    date_time_format: str,
                    date_time_prefix: str) -> date:
    date_time_str = backup.split(date_time_prefix)[-1] if \
        date_time_prefix and date_time_prefix in backup else \
        backup

    return datetime.strptime(date_time_str, date_time_format).date()


def __is_monthly_backup(date_time: date) -> bool:
    return date_time.day == 1


def __is_yearly_backup(date_time: date) -> bool:
    return date_time.day == 1 and date_time.month == 1


def __is_same_backup(already_added: List[str],
                     existing_date: date,
                     date_time_format: str,
                     date_time_prefix: str) -> bool:
    if len(already_added) == 0:
        return False
    previous_date_time = __get_date_time(
        already_added[-1], date_time_format, date_time_prefix)
    return existing_date == previous_date_time


def _get_rotation_strategy(server_strategy: RotationStrategy,
                           item_strategy: Optional[RotationStrategy]):
    return item_strategy if item_strategy else server_strategy


def _check_item(item: BackupItem):
    if isinstance(item, FilesBackupItem):
        for path in [*item.includes, *item.excludes]:
            if not os.path.exists(path):
                raise OSError(f"file does not exist: {path}")
    else:
        log.info(f"unsupported backup item to check: {item.name}")
