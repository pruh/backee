import abc

from dataclasses import dataclass
from typing import Dict


@dataclass
class DbConnector(abc.ABC):
    port: int


@dataclass
class RemoteConnector(DbConnector):
    hostname: str


@dataclass
class DockerConnector(DbConnector):
    container: str
