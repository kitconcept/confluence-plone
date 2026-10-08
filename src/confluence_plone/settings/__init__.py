from .parse import get_default_settings
from .parse import get_settings
from pathlib import Path


__all__ = ("get_default_settings", "get_settings", "logger_settings")


def logger_settings(cwd: Path) -> tuple[bool, Path]:
    """Return whether debug is enabled, and the path of the log file.

    Without a settings file in ``cwd``, the defaults apply.

    :param cwd: The current working directory.
    :returns: A tuple with the debug flag and the log file path.
    """
    try:
        settings = get_settings(cwd)
    except FileNotFoundError:
        settings = get_default_settings()
    log_file = settings.config["log_file"]
    return settings.is_debug, cwd / log_file
