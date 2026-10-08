"""Types used by the migration reports."""

from dataclasses import dataclass
from enum import StrEnum


__all__ = ["Issue", "ItemReport", "Severity", "SkippedItem"]


class Severity(StrEnum):
    """How bad an issue is."""

    INFO = "info"
    """Something was converted in a lossy but expected way."""
    WARNING = "warning"
    """Something was not converted, and the page needs a human look."""
    ERROR = "error"
    """Something failed, and content is missing from the result."""


@dataclass(slots=True)
class Issue:
    """A problem found while converting one item."""

    source_id: str
    """Id of the Confluence content the issue belongs to."""
    severity: Severity
    code: str
    """Machine-readable code, for example ``unsupported_macro``."""
    detail: str = ""
    """Human-readable detail, for example the macro name."""


@dataclass(slots=True)
class ItemReport:
    """One row of the items report: a Confluence object and its Plone item."""

    source_id: str
    source_type: str
    space: str
    title: str
    path: str
    """Path of the item in Plone, relative to the site root."""
    portal_type: str
    uid: str
    status: str = "ok"
    """``ok``, ``warning`` or ``error``, after the worst issue of the item."""
    issues: int = 0


@dataclass(slots=True)
class SkippedItem:
    """A Confluence object that was not migrated."""

    source_id: str
    source_type: str
    space: str
    title: str
    reason: str
