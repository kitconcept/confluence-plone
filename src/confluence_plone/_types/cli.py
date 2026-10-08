from .settings import ConfluenceSettings
from dataclasses import dataclass


__all__ = ["ContextObject"]


@dataclass
class ContextObject:
    """Context object used by the command line interface."""

    settings: ConfluenceSettings
