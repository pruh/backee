#!/usr/bin/env python3
import argparse
import socket
import logging

from backee.parser.config_parser import parse_config
from backee.logger.loggers import (
    setup_default_loggers,
    setup_config_loggers,
    setup_uncaught_exceptions_logger,
)
from backee.backup.backup import backup


log = logging.getLogger(__name__)


def main():
    setup_uncaught_exceptions_logger()

    setup_default_loggers()

    _get_lock("backee")

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


def _get_lock(process_name: str):
    """
    A technique that is handy on a Linux system is using domain sockets.

    It is atomic and avoids the problem of having lock files
    lying around if your process gets sent a SIGKILL.
    """
    # Without holding a reference to our socket somewhere it gets garbage
    # collected when the function exits
    _get_lock._lock_socket = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)

    try:
        # The null byte (\0) means the socket is created
        # in the abstract namespace instead of being created
        # on the file system itself.
        _get_lock._lock_socket.bind("\0" + process_name)
        log.debug("lock acquired")
    except socket.error as socker_error:
        raise OSError("failed to acquire lock") from socker_error


if __name__ == "__main__":
    main()
