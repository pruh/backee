from dataclasses import dataclass
from typing import Dict


@dataclass
class DbConnector(object):
    port: int


@dataclass
class RemoteConnector(DbConnector):
    hostname: str


@dataclass
class DockerConnector(DbConnector):
    container: str
