#!/usr/bin/env python3

import logging

from backee.parser.config_parser import parse_config
from backee.logger.loggers import setup_default_loggers, setup_config_loggers, setup_uncaught_exceptions_logger
from backee.backup.backup import backup


def main():
    setup_uncaught_exceptions_logger()

    setup_default_loggers()

    config = parse_config('backee/config.yml')

    setup_config_loggers(config.loggers)

    backup(config.backup_items, config.backup_servers)


if __name__ == '__main__':
    main()
