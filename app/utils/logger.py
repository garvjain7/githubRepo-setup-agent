"""Shared logger factory. Every module calls get_logger(__name__) instead of
configuring logging ad hoc, so log format stays consistent."""

import logging
import sys

from app.config import settings

_CONFIGURED = False


def _configure_root() -> None:
    global _CONFIGURED
    if _CONFIGURED:
        return

    settings.log_dir.mkdir(parents=True, exist_ok=True)
    handler_stream = logging.StreamHandler(sys.stdout)
    handler_file = logging.FileHandler(settings.log_dir / "app.log")

    fmt = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler_stream.setFormatter(fmt)
    handler_file.setFormatter(fmt)

    root = logging.getLogger()
    root.setLevel(settings.log_level)
    root.addHandler(handler_stream)
    root.addHandler(handler_file)

    _CONFIGURED = True


def get_logger(name: str) -> logging.Logger:
    _configure_root()
    return logging.getLogger(name)