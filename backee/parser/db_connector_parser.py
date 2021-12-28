from typing import Dict, Any

from backee.model.db_connectors import DbConnector, RemoteConnector, DockerConnector


def __parse_local(
    item: Dict[str, Any], default_host: str, def_port: int
) -> RemoteConnector:
    return RemoteConnector(hostname=default_host, port=item.get("port", def_port))


def __parse_remote(
    item: Dict[str, Any], default_host: str, def_port: int
) -> RemoteConnector:
    return RemoteConnector(
        hostname=item.get("host", default_host), port=item.get("port", def_port)
    )


def __parse_docker(
    item: Dict[str, Any], default_host: str, def_port: int
) -> DockerConnector:
    return DockerConnector(container=item["container"], port=item.get("port", def_port))


def parse_db_connector(item: Dict[str, Any]) -> DbConnector:
    supported_types = {
        "local": __parse_local,
        "remote": __parse_remote,
        "docker": __parse_docker,
    }

    default_host = "127.0.0.1"
    default_port = 3306
    conn_type = item["type"]
    if conn_type not in supported_types:
        raise KeyError(f"Unknown database type: '{conn_type}'")

    return supported_types[conn_type](item, default_host, default_port)
