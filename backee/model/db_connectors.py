from dataclasses import dataclass


@dataclass
class DbConnector(object):
    port: int


@dataclass
class RemoteConnector(DbConnector):
    hostname: str


@dataclass
class DockerConnector(DbConnector):
    container: str
