from dataclasses import dataclass
from typing import Tuple, Dict

from backee.model.db_connectors import DbConnector
from backee.model.rotation_strategy import RotationStrategy


@dataclass
class BackupItem(object):
    rotation_strategy: RotationStrategy


@dataclass
class FilesBackupItem(BackupItem):
    includes: Tuple[str]
    excludes: Tuple[str]


@dataclass
class DatabaseBackupItem(BackupItem):
    name: str
    connector: DbConnector


@dataclass
class MysqlBackupItem(DatabaseBackupItem):
    username: str
    password: str
    database: str


@dataclass
class DockerDataVolumesBackupItem(BackupItem):
    volumes: Tuple[str]
