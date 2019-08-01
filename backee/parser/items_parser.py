from typing import Dict, Tuple, List, Optional, Any

from backee.parser.db_connector_parser import parse_db_connector
from backee.model.items import BackupItem, FilesBackupItem, MysqlBackupItem, DatabaseBackupItem, DockerDataVolumesBackupItem
from backee.model.rotation_strategy import RotationStrategy

from backee.parser.rotation_strategy_parser import parse_rotation_strategy


def __parse_files(item: Dict[str, Any]) -> FilesBackupItem:
    return FilesBackupItem(
        includes=tuple(item.get('includes')),
        excludes=tuple(item.get('excludes')),
        rotation_strategy=parse_rotation_strategy(
            item['rotation_strategy']) if 'rotation_strategy' in item else None
    )


def __parse_mysql_item(item: Dict[str, Any]) -> MysqlBackupItem:
    return MysqlBackupItem(
        username=item['username'],
        password=item['password'],
        database=item['database'],
        connector=parse_db_connector(item=item['connection']),
        rotation_strategy=parse_rotation_strategy(
            item['rotation_strategy']) if 'rotation_strategy' in item else None
    )


def __parse_database_backup_item(item: Dict[str, str]) -> DatabaseBackupItem:
    supported_types = {
        "mysql": __parse_mysql_item
    }

    db_type = item['type']
    if db_type not in supported_types:
        raise KeyError(f"Unkown databse type: '{db_type}'")

    return supported_types[db_type](item)


def __parse_databases(items: Dict[str, Any]) -> Tuple[DatabaseBackupItem]:
    return tuple(__parse_database_backup_item(item=x) for x in items)


def __parse_docker_volumes(item: Dict[str, List[str]]) -> DockerDataVolumesBackupItem:
    return DockerDataVolumesBackupItem(
        volumes=tuple(item.get('data_volumes')),
        rotation_strategy=parse_rotation_strategy(
            item['rotation_strategy']) if 'rotation_strategy' in item else None
    )


def parse_items(items: Optional[Dict[str, Any]]) -> Optional[Tuple[BackupItem]]:
    if items is None:
        return None

    result = ()
    if 'files' in items:
        result += (__parse_files(items.get('files')),)
    if 'databases' in items:
        result += __parse_databases(items.get('databases'))
    if 'docker' in items:
        result += (__parse_docker_volumes(items.get('docker')),)

    return result if len(result) else None
