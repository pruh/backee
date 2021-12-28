import os
import logging
from logging import handlers

from typing import Optional, Union, Tuple, Dict, Any

from backee.model.web_handler import WebHandler
from backee.model.max_level_filter import MaxLevelFilter


def __get_log_level(log_level_string: str) -> int:
    if log_level_string is None:
        return None

    log_levels = {
        "debug": logging.DEBUG,
        "info": logging.INFO,
        "warning": logging.WARNING,
        "error": logging.ERROR,
        "critical": logging.CRITICAL,
    }

    if not log_level_string in log_levels.keys():
        raise KeyError(
            f"invalid logging level: {log_level_string} (must be from {log_levels.keys()})"
        )

    return log_levels[log_level_string]


def __parse_file_logger(logger: Dict[str, Any], name: str) -> logging.Handler:
    min_log_level = __get_log_level(logger.get("min_level"))
    min_log_level = logging.DEBUG if min_log_level is None else min_log_level
    max_log_level = __get_log_level(logger.get("max_level"))
    max_log_level = logging.CRITICAL if max_log_level is None else max_log_level

    log_file_path = logger["file"]
    max_size = __parse_file_size(logger.get("max_size"))
    backup_count = logger.get("backup_count", 0)
    formatter = logger.get(
        "format",
        "%(asctime)s [%(threadName)18s][%(module)14s][%(levelname)8s] %(message)s",
    )

    dir_name = os.path.dirname(log_file_path)

    if dir_name and not os.path.exists(dir_name):
        os.mkdir(dir_name)

    filelog = handlers.RotatingFileHandler(
        filename=log_file_path, maxBytes=max_size, backupCount=backup_count
    )
    filelog.setFormatter(logging.Formatter(formatter))
    filelog.setLevel(min_log_level)
    filelog.addFilter(MaxLevelFilter(max_log_level))

    return filelog


def __parse_file_size(file_size: Optional[Union[int, str]]) -> int:
    """
    Parse file size, that can be just integer for bytes, or have suffixes
    like b, k, m, g.
    """
    if file_size is None:
        return 1 * 1024 * 1024

    if isinstance(file_size, int):
        return file_size

    suffixes = {"b": 1, "k": 2 ** 10, "m": 2 ** 20, "g": 2 ** 30}

    # get numbers in from
    num = ""
    multiplier = 1
    for s in file_size:
        if s.isdigit():
            num += s
        elif s in suffixes and len(num) > 0:
            multiplier = suffixes[s]
        else:
            raise ValueError(f"file size {file_size} not supported")

    return int(num) * multiplier


def __parse_web_logger(logger: Dict[str, Any], name: str) -> logging.Handler:
    min_log_level = __get_log_level(logger.get("min_level"))
    min_log_level = logging.DEBUG if min_log_level is None else min_log_level
    max_log_level = __get_log_level(logger.get("max_level"))
    max_log_level = logging.CRITICAL if max_log_level is None else max_log_level

    method = logger["method"]
    url = logger["url"]
    headers = logger.get("headers")
    body = logger.get("body")
    auth = logger.get("auth")

    weblog = WebHandler(method, url, headers, body, auth, name)
    weblog.setFormatter(logging.Formatter("%(message)s"))
    weblog.setLevel(min_log_level)
    weblog.addFilter(MaxLevelFilter(max_log_level))

    return weblog


def __parse_logger(loggers: Dict[str, Any], name: str) -> logging.Handler:
    supported_loggers = {"file": __parse_file_logger, "web": __parse_web_logger}

    logger_type = loggers["type"]
    if logger_type not in supported_loggers:
        raise KeyError(f"Unkown logger name: '{logger_type}'")

    return supported_loggers[logger_type](loggers, name)


def parse_loggers(loggers: Tuple[Dict[str, Any]], name: str) -> Tuple[logging.Handler]:
    if loggers is None:
        return ((),)

    return tuple(__parse_logger(x, name) for x in loggers)
