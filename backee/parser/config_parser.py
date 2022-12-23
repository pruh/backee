import os
import yaml

from typing import Dict, Any

from backee.parser.loggers_parser import parse_loggers
from backee.parser.servers_parser import parse_servers
from backee.parser.items_parser import parse_items
from backee.parser.rotation_strategy_parser import parse_rotation_strategy

from backee.model.config import Config


def parse_config(filename: str) -> Config:
    """
    Parse config file and expand all environment variables.
    """
    with open(filename, mode="r", encoding="utf-8") as f:
        return parse_contents(f.read())


def parse_contents(contents: str) -> Config:
    contents = os.path.expandvars(contents)
    yml_config = yaml.full_load(contents)

    name = yml_config["settings"]["name"]

    __replace_global_patters(config=yml_config, patterns={"{{ name }}": name})

    rotation_strategy = parse_rotation_strategy(
        data=yml_config.get("rotation_strategy")
    )

    return Config(
        name=name,
        loggers=parse_loggers(loggers=yml_config.get("loggers")),
        backup_servers=parse_servers(
            servers=yml_config.get("servers"), default_rs=rotation_strategy
        ),
        backup_items=parse_items(items=yml_config.get("backup_items")),
    )


def __replace_global_patters(
    config: Dict[str, Any], patterns: Dict[str, str]
) -> Dict[str, Any]:
    for k, v in config.items():
        if isinstance(v, dict):
            __replace_global_patters(config=v, patterns=patterns)
            continue
        elif isinstance(v, list):
            config[k] = [
                __replace_str_global_patters(config=item, patterns=patterns)
                if isinstance(item, str)
                else __replace_global_patters(config=item, patterns=patterns)
                for item in v
            ]
            continue
        elif isinstance(v, str):
            config[k] = __replace_str_global_patters(config=v, patterns=patterns)

    return config


def __replace_str_global_patters(config: str, patterns: Dict[str, str]) -> str:
    for k, v in patterns.items():
        if k in config:
            return config.replace(k, v)

    return config
