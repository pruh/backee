import logging
import sys

from typing import Tuple

from backee.model.max_level_filter import MaxLevelFilter


def setup_default_loggers() -> None:
    __setup_global_logging_levels()

    formatter = logging.Formatter(
        '%(asctime)s [%(threadName)18s][%(module)14s][%(levelname)8s] %(message)s')

    # Redirect messages lower or equal than INFO to stdout
    stdout_hdlr = logging.StreamHandler(sys.stdout)
    stdout_hdlr.setFormatter(formatter)
    log_filter = MaxLevelFilter(logging.INFO)
    stdout_hdlr.addFilter(log_filter)
    stdout_hdlr.setLevel(logging.DEBUG)

    # Redirect messages higher or equal than WARNING to stderr
    stderr_hdlr = logging.StreamHandler(sys.stderr)
    stderr_hdlr.setFormatter(formatter)
    stderr_hdlr.setLevel(logging.WARNING)

    log = logging.getLogger()
    log.addHandler(stdout_hdlr)
    log.addHandler(stderr_hdlr)


def __setup_global_logging_levels():
    root_log = logging.getLogger()
    root_log.setLevel(logging.DEBUG)

    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)


def setup_config_loggers(loggers: Tuple[logging.Handler]) -> None:
    [logging.getLogger().addHandler(handler) for handler in loggers]
