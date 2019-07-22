from dataclasses import dataclass
from typing import Tuple, Dict
from abc import ABC, abstractmethod

from backee.model.db_connectors import DbConnector
from backee.model.rotation_strategy import RotationStrategy


@dataclass
class BackupItem(ABC):
    rotation_strategy: RotationStrategy

    @property
    @abstractmethod
    def name(self):
        pass


@dataclass
class FilesBackupItem(BackupItem):
    includes: Tuple[str]
    excludes: Tuple[str]

    @property
    def name(self):
        return 'files'


@dataclass
class DatabaseBackupItem(BackupItem):
    connector: DbConnector

    @property
    def name(self):
        return 'databases'


@dataclass
class MysqlBackupItem(DatabaseBackupItem):
    username: str
    password: str
    database: str


@dataclass
class DockerDataVolumesBackupItem(BackupItem):
    volumes: Tuple[str]

    @property
    def name(self):
        return 'docker'
