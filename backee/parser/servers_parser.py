from typing import Tuple, Dict, Any

from backee.model.servers import BackupServer, SshBackupServer
from backee.model.rotation_strategy import RotationStrategy

from backee.parser.rotation_strategy_parser import parse_rotation_strategy


def __parse_ssh_server(server: Dict[str, Any], rotation_strategy: RotationStrategy) -> BackupServer:
    return SshBackupServer(
        name=server['name'],
        location=server['location'],
        hostname=server['connection']['host'],
        port=server['connection'].get('port', 22),
        username=server['connection'].get('username', None),
        key_path=server['connection'].get('key', None),
        rotation_strategy=rotation_strategy
    )


def __parse_server(server: Dict[str, Any], rotation_strategy: RotationStrategy) -> BackupServer:
    supported_servers = {
        "ssh": __parse_ssh_server
    }

    server_type = server['type']
    if server_type not in supported_servers:
        raise KeyError(f"Unkown server type: '{server_type}'")

    if 'rotation_strategy' in server:
        rotation_strategy = parse_rotation_strategy(
            server['rotation_strategy'])

    return supported_servers[server_type](server, rotation_strategy)


def parse_servers(servers: Tuple[Dict[str, Any]], rotation_strategy: RotationStrategy) -> Tuple[BackupServer]:
    if servers is None:
        return ((),)

    return tuple(__parse_server(x, rotation_strategy) for x in servers)
