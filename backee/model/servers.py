from dataclasses import dataclass
from backee.model.rotation_strategy import RotationStrategy


@dataclass
class BackupServer(object):
    name: str
    rotation_strategy: RotationStrategy


@dataclass
class SshBackupServer(BackupServer):
    location: str
    hostname: str
    port: int
    username: str
    key_path: str
