import os
import re
import yaml
import logging

from typing import List, Dict

from backee.parser.loggers_parser import parse_loggers
from backee.parser.servers_parser import parse_servers
from backee.parser.items_parser import parse_items
from backee.parser.rotation_strategy_parser import parse_rotation_strategy

from backee.model.servers import BackupServer
from backee.model.items import BackupItem
from backee.model.config import Config
from backee.model.rotation_strategy import RotationStrategy


def parse_config(filename: str) -> Config:
    """
    Parse config file and expand all environment variables.
    """
    with open(filename) as f:
        return parse_contents(f.read())


def parse_contents(contents: str) -> Config:
    contents = os.path.expandvars(contents)
    yml_config = yaml.full_load(contents)

    name = yml_config['settings']['name']

    rotation_strategy = parse_rotation_strategy(
        data=yml_config.get('rotation_strategy'))
    return Config(
        name=name,
        loggers=parse_loggers(loggers=yml_config.get('loggers'), name=name),
        backup_servers=parse_servers(servers=yml_config.get('servers'),
                                     rotation_strategy=rotation_strategy),
        backup_items=parse_items(items=yml_config.get('backup_items'),
                                 rotation_strategy=rotation_strategy))
