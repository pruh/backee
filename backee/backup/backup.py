import logging

from typing import Tuple

from backee.model.items import BackupItem, FilesBackupItem
from backee.model.servers import BackupServer, SshBackupServer

from backee.backup.transmitter import Transmitter, SshTransmitter


log = logging.getLogger(__name__)


def backup(items: Tuple[BackupItem], servers: Tuple[BackupServer]) -> None:
    """
    Start backup process.
    """
    for server in servers:
        __backup_to_server(items, server)


def __backup_to_server(items: Tuple[BackupItem], server: BackupServer) -> None:
    log.debug(f"starting backup to {server.name}")

    transmitter = __create_transmitter(server)

    [transmitter.transmit(item) for item in items]


def __create_transmitter(server: BackupServer) -> Transmitter:
    if isinstance(server, SshBackupServer):
        return SshTransmitter(server)

    raise TypeError(f"unsupported server {server}")
