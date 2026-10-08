"""Build a :class:`ConfluenceExport` from the raw objects of ``entities.xml``.

The object model differs between Confluence versions: ``parent`` was
``parentPage`` in some 3.x exports, users were referenced by name
(``creatorName``) before they had keys, and attachment metadata moved from
properties to ``ContentProperty`` objects. Those differences are absorbed
here, so the rest of the package sees one model.
"""

from collections import defaultdict
from collections.abc import Iterable
from confluence_plone import _types as t


CONTENT_CLASSES = {"Page": "page", "BlogPost": "blogpost"}
USER_CLASSES = {"ConfluenceUserImpl"}
CROWD_USER_CLASSES = {"InternalUser", "User"}


def _int(value: str, default: int = 0) -> int:
    """Convert a property value to an integer.

    :param value: The property value.
    :param default: Returned when the value is not a number.
    :returns: The integer.
    """
    value = value.strip()
    return int(value) if value.lstrip("-").isdigit() else default


def _ref_id(raw: t.RawObject, *names: str) -> str | None:
    """Return the id of the first reference found among ``names``.

    :param raw: The raw object.
    :param names: Property names to try, in order.
    :returns: The referenced id, or ``None``.
    """
    ref = raw.ref(*names)
    return ref.id if ref else None


def _user(raw: t.RawObject, ref_name: str, text_name: str) -> str | None:
    """Return the user key (or, in old exports, the user name) of a property.

    :param raw: The raw object.
    :param ref_name: Property holding a reference to the user.
    :param text_name: Property holding the user name, in old exports.
    :returns: A user key, a user name, or ``None``.
    """
    return _ref_id(raw, ref_name) or raw.text(text_name).strip() or None


def _content_fields(raw: t.RawObject) -> dict:
    """Read the fields shared by every kind of content.

    :param raw: The raw object.
    :returns: Keyword arguments for :class:`Content` and its subclasses.
    """
    original_id = (
        _ref_id(raw, "originalVersion") or raw.text("originalVersionId").strip()
    )
    return {
        "id": raw.id,
        "title": raw.text("title"),
        "version": _int(raw.text("version"), 1),
        "status": raw.text("contentStatus", "current").strip() or "current",
        "created": raw.text("creationDate"),
        "modified": raw.text("lastModificationDate"),
        "creator": _user(raw, "creator", "creatorName"),
        "last_modifier": _user(raw, "lastModifier", "lastModifierName"),
        "original_id": original_id or None,
        "space_id": _ref_id(raw, "space"),
    }


class ExportBuilder:
    """Collect raw objects and build the export model from them."""

    def __init__(self) -> None:
        self.export = t.ConfluenceExport()
        self._properties: dict[str, tuple[str, str]] = {}
        """``(name, value)`` of each content property, by property id."""
        self._property_owners: dict[str, str] = {}
        """Content id by property id. Either side may hold the link."""
        self._labels: dict[str, tuple[str, str]] = {}
        self._labellings: list[tuple[str, str]] = []
        self._crowd_users: list[t.RawObject] = []

    def add(self, raw: t.RawObject) -> None:
        """Add one raw object.

        :param raw: The raw object.
        """
        self.export.classes[raw.cls] += 1
        for ref in raw.collections.get("contentProperties", []):
            self._property_owners[ref.id] = raw.id
        handlers = {
            "Space": self._add_space,
            "Page": self._add_page,
            "BlogPost": self._add_page,
            "Attachment": self._add_attachment,
            "Comment": self._add_comment,
            "BodyContent": self._add_body,
            "ContentProperty": self._add_property,
            "Label": self._add_label,
            "Labelling": self._add_labelling,
            "ContentPermissionSet": self._add_restriction,
            "SpacePermission": self._add_space_permission,
            **dict.fromkeys(USER_CLASSES, self._add_user),
            **dict.fromkeys(CROWD_USER_CLASSES, self._crowd_users.append),
        }
        if handler := handlers.get(raw.cls):
            handler(raw)

    def _add_space(self, raw: t.RawObject) -> None:
        """Add a ``Space``.

        :param raw: The raw object.
        """
        self.export.spaces[raw.id] = t.Space(
            id=raw.id,
            key=raw.text("key"),
            name=raw.text("name"),
            status=raw.text("spaceStatus", "CURRENT").strip() or "CURRENT",
            space_type=raw.text("spaceType", "global").strip() or "global",
            description_id=_ref_id(raw, "description"),
            home_page_id=_ref_id(raw, "homePage"),
            created=raw.text("creationDate"),
            creator=_user(raw, "creator", "creatorName"),
        )

    def _add_page(self, raw: t.RawObject) -> None:
        """Add a ``Page`` or a ``BlogPost``.

        :param raw: The raw object.
        """
        position = raw.text("position").strip()
        self.export.pages[raw.id] = t.Page(
            **_content_fields(raw),
            kind=CONTENT_CLASSES[raw.cls],
            parent_id=_ref_id(raw, "parent", "parentPage"),
            position=_int(position) if position else None,
        )

    def _add_attachment(self, raw: t.RawObject) -> None:
        """Add an ``Attachment``.

        :param raw: The raw object.
        """
        attachment = t.Attachment(
            **_content_fields(raw),
            container_id=_ref_id(raw, "containerContent", "content", "page"),
        )
        if media_type := raw.text("contentType").strip():
            attachment.media_type = media_type
        if file_size := raw.text("fileSize").strip():
            attachment.file_size = _int(file_size)
        self.export.attachments[raw.id] = attachment

    def _add_comment(self, raw: t.RawObject) -> None:
        """Add a ``Comment``.

        :param raw: The raw object.
        """
        self.export.comments[raw.id] = t.Comment(
            **_content_fields(raw),
            container_id=_ref_id(raw, "containerContent", "owner", "page"),
            parent_id=_ref_id(raw, "parent"),
        )

    def _add_body(self, raw: t.RawObject) -> None:
        """Add a ``BodyContent``. When content has several, the newest wins.

        :param raw: The raw object.
        """
        content_id = _ref_id(raw, "content")
        if not content_id:
            return
        body = t.BodyContent(
            id=raw.id,
            content_id=content_id,
            body=raw.text("body"),
            body_type=_int(raw.text("bodyType"), 2),
        )
        existing = self.export.bodies.get(content_id)
        if existing is None or _int(body.id) > _int(existing.id):
            self.export.bodies[content_id] = body

    def _add_property(self, raw: t.RawObject) -> None:
        """Add a ``ContentProperty``.

        :param raw: The raw object.
        """
        value = (
            raw.text("stringValue") or raw.text("longValue") or raw.text("dateValue")
        )
        self._properties[raw.id] = (raw.text("name").strip(), value.strip())
        if content_id := _ref_id(raw, "content"):
            self._property_owners[raw.id] = content_id

    def _add_label(self, raw: t.RawObject) -> None:
        """Add a ``Label``.

        :param raw: The raw object.
        """
        self._labels[raw.id] = (
            raw.text("namespace", "global").strip() or "global",
            raw.text("name"),
        )

    def _add_labelling(self, raw: t.RawObject) -> None:
        """Add a ``Labelling``: a label put on some content.

        :param raw: The raw object.
        """
        label_id = _ref_id(raw, "label")
        content_id = _ref_id(raw, "content") or raw.text("labelableId").strip()
        if label_id and content_id:
            self._labellings.append((content_id, label_id))

    def _add_restriction(self, raw: t.RawObject) -> None:
        """Add a ``ContentPermissionSet``: a restriction on some content.

        :param raw: The raw object.
        """
        if content_id := _ref_id(raw, "owningContent"):
            restriction = raw.text("type").strip() or "View"
            self.export.restrictions.setdefault(content_id, set()).add(restriction)

    def _add_space_permission(self, raw: t.RawObject) -> None:
        """Count a ``SpacePermission``.

        :param raw: The raw object.
        """
        if space_id := _ref_id(raw, "space"):
            self.export.space_permissions[space_id] += 1

    def _add_user(self, raw: t.RawObject) -> None:
        """Add a ``ConfluenceUserImpl``.

        :param raw: The raw object.
        """
        self.export.users[raw.id] = t.User(
            key=raw.id,
            name=raw.text("name"),
            email=raw.text("email"),
        )

    def _apply_properties(self) -> None:
        """Attach the content properties to their content."""
        export = self.export
        contents: dict[str, t.Content] = {
            **export.pages,
            **export.attachments,
            **export.comments,
        }
        by_content: dict[str, dict[str, str]] = defaultdict(dict)
        for property_id, (name, value) in self._properties.items():
            if content_id := self._property_owners.get(property_id):
                by_content[content_id][name] = value
        for content_id, properties in by_content.items():
            content = contents.get(content_id)
            if content is None:
                continue
            content.properties.update(properties)
            if isinstance(content, t.Attachment):
                if media_type := properties.get("MEDIA_TYPE"):
                    content.media_type = media_type
                if file_size := properties.get("FILESIZE"):
                    content.file_size = _int(file_size)

    def _apply_labels(self) -> None:
        """Attach the labels to the labelled content."""
        labels = self.export.labels
        for content_id, label_id in self._labellings:
            if label := self._labels.get(label_id):
                labels.setdefault(content_id, []).append(label)

    def _apply_crowd_users(self) -> None:
        """Add the display name and email of user directory entries.

        Old exports have no ``ConfluenceUserImpl``: those users are added by
        name, so that they can still be found.
        """
        users = self.export.users
        by_name = {user.name.lower(): user for user in users.values()}
        for raw in self._crowd_users:
            name = raw.text("name")
            if not name:
                continue
            user = by_name.get(name.lower())
            if user is None:
                user = t.User(key=name, name=name)
                users[name] = user
                by_name[name.lower()] = user
            user.display_name = user.display_name or raw.text("displayName")
            user.email = user.email or raw.text("emailAddress")

    def build(self) -> t.ConfluenceExport:
        """Resolve what needs every object, and return the export.

        :returns: The export model.
        """
        self._apply_properties()
        self._apply_labels()
        self._apply_crowd_users()
        return self.export


def build_export(objects: Iterable[t.RawObject]) -> t.ConfluenceExport:
    """Build the export model from raw objects.

    :param objects: The raw objects, in any order.
    :returns: The export model.
    """
    builder = ExportBuilder()
    for raw in objects:
        builder.add(raw)
    return builder.build()
