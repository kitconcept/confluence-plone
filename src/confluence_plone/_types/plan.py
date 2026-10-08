"""Types describing the target tree, before any file is written."""

from .report import Issue
from .report import SkippedItem
from dataclasses import dataclass
from dataclasses import field
from typing import Any


__all__ = ["MigrationPlan", "PlannedItem", "PlateNode", "PloneItem"]


PloneItem = dict[str, Any]
"""The content of one ``data.json`` file in the ``plone.exportimport`` format."""

PlateNode = dict[str, Any]
"""One node of a Plate value: an element (with ``type``) or a text leaf."""


@dataclass(slots=True)
class PlannedItem:
    """One Plone item that will be created from a Confluence object."""

    source_id: str
    """Id of the Confluence object (the space id, for a workspace)."""
    source_type: str
    """``space``, ``page`` or ``attachment``."""
    portal_type: str
    uid: str
    id: str
    path: str
    """Path relative to the site root, for example ``/dev/home/setup``."""
    title: str
    space_key: str
    parent_uid: str | None = None
    position: int = 0
    """Position among the siblings, starting at ``0``."""
    children: list[str] = field(default_factory=list)
    """UIDs of the children, in order."""
    blob_name: str | None = None
    """For an attachment, the file in the export holding the binary."""

    @property
    def depth(self) -> int:
        """Number of segments of the path."""
        return len([part for part in self.path.split("/") if part])


@dataclass(slots=True)
class MigrationPlan:
    """The target tree, and what was left out of it."""

    items: dict[str, PlannedItem] = field(default_factory=dict)
    """Planned items by UID, every parent before its children."""
    by_source: dict[str, str] = field(default_factory=dict)
    """UIDs by Confluence object id."""
    pages_by_title: dict[tuple[str, str], str] = field(default_factory=dict)
    """Page UIDs by ``(space key, lower-case title)``."""
    attachments_by_name: dict[tuple[str, str], str] = field(default_factory=dict)
    """Attachment UIDs by ``(page id, lower-case file name)``."""
    skipped: list[SkippedItem] = field(default_factory=list)
    issues: list[Issue] = field(default_factory=list)

    def add(self, item: PlannedItem) -> PlannedItem:
        """Add an item to the plan, and to the children of its parent.

        :param item: The item to add.
        :returns: The same item.
        """
        self.items[item.uid] = item
        self.by_source[item.source_id] = item.uid
        if item.parent_uid and (parent := self.items.get(item.parent_uid)):
            item.position = len(parent.children)
            parent.children.append(item.uid)
        return item

    def item_for(self, source_id: str | None) -> PlannedItem | None:
        """Return the planned item for a Confluence object id.

        :param source_id: Id of the Confluence object.
        :returns: The planned item, or ``None`` when the object is not migrated.
        """
        if source_id and (uid := self.by_source.get(source_id)):
            return self.items[uid]
        return None
