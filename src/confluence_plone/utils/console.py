"""Console output for the command line interface."""

from confluence_plone import get_logger
from rich.console import Console


console = Console(highlight=False)
"""Console used by the commands."""


def report(message: str) -> None:
    """Show a progress message, and write it to the log file.

    :param message: The message.
    """
    console.print(message)
    get_logger().info(message)
