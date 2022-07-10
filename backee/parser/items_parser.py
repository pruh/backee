import os
import logging
from typing import Dict, Tuple, List, Optional, Any

from backee.parser.db_connector_parser import parse_db_connector
from backee.model.items import (
    BackupItem,
    FilesBackupItem,
    MysqlBackupItem,
    DatabaseBackupItem,
    DockerDataVolumesBackupItem,
)
from backee.model.rotation_strategy import RotationStrategy

from backee.parser.rotation_strategy_parser import parse_rotation_strategy


log = logging.getLogger(__name__)


def __parse_files(item: Dict[str, Any]) -> FilesBackupItem:
    if "includes" in item:
        includes = tuple([os.path.expanduser(x)
                         for x in item.get("includes") if __path_exists(x)])
    else:
        includes = ()
    if "excludes" in item:
        excludes = tuple([os.path.expanduser(x)
                         for x in item.get("excludes") if __path_exists(x)])
    else:
        excludes = ()
    return FilesBackupItem(
        includes=includes,
        excludes=excludes,
        rotation_strategy=parse_rotation_strategy(item["rotation_strategy"])
        if "rotation_strategy" in item
        else None,
    )


def __path_exists(path: str) -> bool:
    if not os.path.exists(path):
        log.error("file backup item does not exist: %s", path)
        return False

    return True


def __parse_mysql_item(item: Dict[str, Any]) -> MysqlBackupItem:
    return MysqlBackupItem(
        username=item["username"],
        password=item["password"],
        database=item["database"],
        connector=parse_db_connector(item=item["connection"]),
        rotation_strategy=parse_rotation_strategy(item["rotation_strategy"])
        if "rotation_strategy" in item
        else None,
    )


def __parse_database_backup_item(item: Dict[str, str]) -> DatabaseBackupItem:
    supported_types = {"mysql": __parse_mysql_item}

    db_type = item["type"]
    if db_type not in supported_types:
        raise KeyError(f"Unkown databse type: '{db_type}'")

    return supported_types[db_type](item)


def __parse_databases(items: Dict[str, Any]) -> Tuple[DatabaseBackupItem]:
    return tuple(__parse_database_backup_item(item=x) for x in items)


def __parse_docker_volumes(
    item: Dict[str, List[str]]
) -> Tuple[DockerDataVolumesBackupItem]:
    result = []
    for volume in item.get("data_volumes"):
        result.append(
            DockerDataVolumesBackupItem(
                volume=volume,
                rotation_strategy=parse_rotation_strategy(
                    item["rotation_strategy"])
                if "rotation_strategy" in item
                else None,
            )
        )
    return tuple(result)


def parse_items(items: Optional[Dict[str, Any]]) -> Optional[Tuple[BackupItem]]:
    if items is None:
        return None

    result = ()
    if "files" in items:
        result += (__parse_files(items.get("files")),)
    if "databases" in items:
        result += __parse_databases(items.get("databases"))
    if "docker" in items:
        result += __parse_docker_volumes(items.get("docker"))

    return result if len(result) else None
