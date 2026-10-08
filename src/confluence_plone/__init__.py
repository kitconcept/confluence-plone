"""Convert a Confluence XML space export into the ``plone.exportimport`` format."""

from pathlib import Path

import logging


__version__ = "1.0.0a1.dev0"

PACKAGE_NAME = "confluence-plone"


_LOGGER: logging.Logger | None = None


def get_logger() -> logging.Logger:
    """Return the package logger, writing to the log file set in the settings.

    The first call reads the settings in the current working directory, to
    find the log file and whether debug messages are wanted. Without a
    settings file, the defaults are used.

    :returns: The logger for ``confluence-plone``.
    """
    from confluence_plone.settings import logger_settings

    global _LOGGER

    if _LOGGER is None:
        is_debug, path = logger_settings(Path.cwd())
        level = logging.DEBUG if is_debug else logging.INFO
        logger = logging.getLogger(PACKAGE_NAME)
        logger.setLevel(level)
        file_handler = logging.FileHandler(path, "a")
        file_handler.setLevel(level)
        file_formatter = logging.Formatter("%(levelname)s: %(message)s")
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
        _LOGGER = logger
    return _LOGGER
