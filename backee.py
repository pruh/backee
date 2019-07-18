#!/usr/bin/env python3

import logging

from backee.parser.config_parser import parse_config
from backee.logger.std_logger import setup_std_logger


log = logging.getLogger(__name__)


def main():
    setup_std_logger()

    config = parse_config('backee/config.yml')


if __name__ == '__main__':
    main()
