import logging
import sys

from backee.model.max_level_filter import MaxLevelFilter


log = logging.getLogger(__name__)


def setup_std_logger():
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
