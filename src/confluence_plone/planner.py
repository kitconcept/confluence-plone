"""Plan the target tree: which Plone item each Confluence object becomes.

Each selected space becomes a workspace. Its current pages become Wiki Pages,
nested as in Confluence, and the current attachments of a page become File
or Image items inside it. Everything else (drafts, deleted and archived
content, blog posts, older versions) is left out and reported.

Planning happens before any conversion, so that links between pages can be
resolved while the bodies are converted.
"""

from collections import defaultdict
from collections.abc import Callable
from confluence_plone import _types as t
from confluence_plone.utils.ids import make_uid
from confluence_plone.utils.ids import normalize_id
from confluence_plone.utils.ids import unique_id


AttachmentFinder = Callable[[str | None, str, int], str | None]
"""Find the file of an attachment: ``(container id, attachment id, version)``."""


def _space_skip_reason(space: t.Space, settings: t.ConfluenceSettings) -> str:
    """Return why a space is not converted, or an empty string.

    :param space: The space.
    :param settings: The settings.
    :returns: The reason, or ``""`` when the space is converted.
    """
    source = settings.source
    if source["spaces"] and space.key not in source["spaces"]:
        return "space not selected"
    is_personal = space.space_type == "personal" or space.key.startswith("~")
    if is_personal and not source["include_personal_spaces"]:
        return "personal space"
    if space.status.upper() == "ARCHIVED" and not source["include_archived_spaces"]:
        return "archived space"
    return ""


def _sort_key(page: t.Page, home_id: str | None) -> tuple:
    """Order siblings: the home page first, then by position, then by title.

    :param page: The page.
    :param home_id: Id of the home page of the space.
    :returns: The sort key.
    """
    position = page.position if page.position is not None else 1 << 30
    return (page.id != home_id, position, page.title.lower(), page.id)


class Planner:
    """Build a :class:`MigrationPlan` for an export.

    :param export: The export.
    :param settings: The settings.
    :param find_attachment: Finds the file of an attachment in the export.
    """

    def __init__(
        self,
        export: t.ConfluenceExport,
        settings: t.ConfluenceSettings,
        find_attachment: AttachmentFinder,
    ):
        self.export = export
        self.settings = settings
        self.find_attachment = find_attachment
        self.plan = t.MigrationPlan()
        self._ids: dict[str, set[str]] = defaultdict(set)
        """Ids in use, by parent UID (``""`` for the base container)."""

    def _add(
        self,
        parent: t.PlannedItem | None,
        source_id: str,
        source_type: str,
        portal_type: str,
        title: str,
        wanted_id: str,
        space_key: str,
    ) -> t.PlannedItem:
        """Add an item to the plan, under ``parent``.

        :param parent: The parent item, or ``None`` for the base container.
        :param source_id: Id of the Confluence object.
        :param source_type: ``space``, ``page`` or ``attachment``.
        :param portal_type: Portal type of the new item.
        :param title: Title of the new item.
        :param wanted_id: Id wanted for the new item; it is made unique.
        :param space_key: Key of the space the object belongs to.
        :returns: The planned item.
        """
        parent_uid = parent.uid if parent else ""
        item_id = unique_id(wanted_id, self._ids[parent_uid])
        base_path = parent.path if parent else self.settings.target["base_path"]
        item = t.PlannedItem(
            source_id=source_id,
            source_type=source_type,
            portal_type=portal_type,
            uid=make_uid(source_type, source_id),
            id=item_id,
            path=f"{base_path.rstrip('/')}/{item_id}",
            title=title,
            space_key=space_key,
            parent_uid=parent.uid if parent else None,
        )
        return self.plan.add(item)

    def _skip(self, content: t.Content, space: t.Space, reason: str) -> None:
        """Record content that is not converted.

        :param content: The content.
        :param space: Its space.
        :param reason: Why it is not converted.
        """
        source_type = getattr(content, "kind", "attachment")
        self.plan.skipped.append(
            t.SkippedItem(content.id, source_type, space.key, content.title, reason)
        )

    def _issue(
        self, source_id: str, severity: t.Severity, code: str, detail: str = ""
    ) -> None:
        """Record an issue found while planning.

        :param source_id: Id of the Confluence object.
        :param severity: How bad the issue is.
        :param code: Machine-readable code.
        :param detail: Human-readable detail.
        """
        self.plan.issues.append(t.Issue(source_id, severity, code, detail))

    def plan_space(self, space: t.Space) -> None:
        """Plan a workspace for a space, with its pages and attachments.

        :param space: The space.
        """
        target = self.settings.target
        workspace = self._add(
            None,
            f"space:{space.id}",
            "space",
            target["workspace_type"],
            space.name or space.key,
            normalize_id(space.key, fallback=f"space-{space.id}"),
            space.key,
        )
        pages = [
            page for page in self.export.pages.values() if page.space_id == space.id
        ]
        current: dict[str, t.Page] = {}
        for page in pages:
            if page.is_historical:
                continue
            if not page.is_current:
                self._skip(page, space, f"status {page.status}")
            elif page.kind != "page":
                self._skip(page, space, "blog posts are not converted")
            else:
                current[page.id] = page
        children: dict[str | None, list[t.Page]] = defaultdict(list)
        for page in current.values():
            parent_id = page.parent_id if page.parent_id in current else None
            if page.parent_id and parent_id is None:
                self._issue(
                    page.id,
                    t.Severity.WARNING,
                    "orphan_page",
                    f"Parent {page.parent_id} is not converted",
                )
            children[parent_id].append(page)
        self._plan_pages(workspace, children, space, current)

    def _plan_pages(
        self,
        workspace: t.PlannedItem,
        children: dict[str | None, list[t.Page]],
        space: t.Space,
        current: dict[str, t.Page],
    ) -> None:
        """Plan the page tree of a space, parents before children.

        Pages that are never reached from the top level (their parents form a
        cycle) are added at the top level, with an issue.

        :param workspace: The workspace of the space.
        :param children: Pages by parent id (``None`` for the top level).
        :param space: The space.
        :param current: The pages to plan, by id.
        """
        home_id = space.home_page_id
        queue: list[tuple[t.PlannedItem, t.Page]] = [
            (workspace, page)
            for page in sorted(children[None], key=lambda p: _sort_key(p, home_id))
        ]
        planned: set[str] = set()
        while True:
            while queue:
                parent, page = queue.pop(0)
                if page.id in planned:
                    # Reached again through a cycle of parents
                    continue
                item = self._add(
                    parent,
                    page.id,
                    "page",
                    self.settings.target["page_type"],
                    page.title,
                    normalize_id(page.title, fallback=f"page-{page.id}"),
                    space.key,
                )
                planned.add(page.id)
                self.plan.pages_by_title.setdefault(
                    (space.key, page.title.lower()), item.uid
                )
                self._plan_attachments(item, page, space)
                queue.extend(
                    (item, child)
                    for child in sorted(
                        children[page.id], key=lambda p: _sort_key(p, home_id)
                    )
                )
            remaining = sorted(set(current) - planned)
            if not remaining:
                break
            page = current[remaining[0]]
            self._issue(
                page.id,
                t.Severity.WARNING,
                "page_cycle",
                "The parent pages form a cycle; moved to the top level",
            )
            queue.append((workspace, page))

    def _plan_attachments(
        self, item: t.PlannedItem, page: t.Page, space: t.Space
    ) -> None:
        """Plan the current attachments of a page as its children.

        :param item: The planned item of the page.
        :param page: The page.
        :param space: The space.
        """
        target = self.settings.target
        attachments = sorted(
            (a for a in self.export.attachments.values() if a.container_id == page.id),
            key=lambda a: (a.title.lower(), a.id),
        )
        for attachment in attachments:
            if attachment.is_historical:
                continue
            if not attachment.is_current:
                self._skip(attachment, space, f"status {attachment.status}")
                continue
            blob_name = self.find_attachment(page.id, attachment.id, attachment.version)
            if blob_name is None:
                self._issue(
                    attachment.id,
                    t.Severity.ERROR,
                    "missing_attachment_file",
                    f"{attachment.title} (version {attachment.version})",
                )
                self._skip(attachment, space, "file missing from the export")
                continue
            is_image = attachment.media_type in target["image_media_types"]
            child = self._add(
                item,
                attachment.id,
                "attachment",
                target["image_type"] if is_image else target["file_type"],
                attachment.title,
                normalize_id(attachment.title, fallback=f"file-{attachment.id}"),
                space.key,
            )
            child.blob_name = blob_name
            self.plan.attachments_by_name[(page.id, attachment.title.lower())] = (
                child.uid
            )

    def build(self) -> t.MigrationPlan:
        """Plan every selected space.

        :returns: The plan.
        """
        wanted = set(self.settings.source["spaces"])
        found = {space.key for space in self.export.spaces.values()}
        for key in sorted(wanted - found):
            self._issue(key, t.Severity.WARNING, "space_not_found", key)
        for space in sorted(self.export.spaces.values(), key=lambda s: s.key):
            if reason := _space_skip_reason(space, self.settings):
                self.plan.skipped.append(
                    t.SkippedItem(space.id, "space", space.key, space.name, reason)
                )
                continue
            self.plan_space(space)
        return self.plan


def plan_migration(
    export: t.ConfluenceExport,
    settings: t.ConfluenceSettings,
    find_attachment: AttachmentFinder,
) -> t.MigrationPlan:
    """Plan the target tree for an export.

    :param export: The export.
    :param settings: The settings.
    :param find_attachment: Finds the file of an attachment in the export.
    :returns: The plan.
    """
    return Planner(export, settings, find_attachment).build()
