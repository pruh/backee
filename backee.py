#!/usr/bin/env python3
import argparse
import logging

from backee.parser.config_parser import parse_config
from backee.logger.loggers import (
    setup_default_loggers,
    setup_config_loggers,
    setup_uncaught_exceptions_logger,
)
from backee.backup.backup import backup


def main():
    setup_uncaught_exceptions_logger()

    setup_default_loggers()

    args = _get_args()

    config = parse_config(args.config)

    setup_config_loggers(config.loggers)

    backup(config.name, config.backup_items, config.backup_servers)


def _get_args():
    parser = argparse.ArgumentParser(
        description="backee is a script for backup directories, files, databases and docker data volumes."
    )
    config_default_path = "backee/config.yml"
    parser.add_argument(
        "-c",
        "--config",
        action="store",
        default=config_default_path,
        type=str,
        help=f"path to config file (default: {config_default_path})",
    )
    return parser.parse_args()


if __name__ == "__main__":
    main()
