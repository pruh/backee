import logging
from dataclasses import dataclass

from typing import Tuple

from backee.model.servers import BackupServer
from backee.model.items import BackupItem
from backee.model.rotation_strategy import RotationStrategy


@dataclass
class Config(object):
    name: str
    loggers: Tuple[logging.Handler]
    backup_servers: Tuple[BackupServer]
    backup_items: Tuple[BackupItem]
