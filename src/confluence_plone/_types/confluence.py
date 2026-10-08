"""Types describing the content of a Confluence XML export."""

from collections import Counter
from dataclasses import dataclass
from dataclasses import field


__all__ = [
    "Attachment",
    "BodyContent",
    "Comment",
    "ConfluenceExport",
    "Content",
    "Page",
    "RawObject",
    "Ref",
    "Space",
    "User",
]


@dataclass(frozen=True, slots=True)
class Ref:
    """A reference from one exported object to another."""

    cls: str
    """Class name of the referenced object, for example ``Page``."""
    id: str
    """Id (or key, for users) of the referenced object."""


@dataclass(slots=True)
class RawObject:
    """One ``<object>`` element of ``entities.xml``, before interpretation."""

    cls: str
    """Class name, for example ``Page`` or ``BodyContent``."""
    id: str
    """Value of the ``<id>`` element."""
    properties: dict[str, str | Ref] = field(default_factory=dict)
    """Scalar properties, and references to other objects."""
    collections: dict[str, list[Ref]] = field(default_factory=dict)
    """Collections of references to other objects."""

    def text(self, name: str, default: str = "") -> str:
        """Return a scalar property, or ``default`` when it is missing.

        :param name: Name of the property.
        :param default: Value returned when the property is missing or is a
            reference.
        :returns: The property value.
        """
        value = self.properties.get(name)
        return value if isinstance(value, str) else default

    def ref(self, *names: str) -> Ref | None:
        """Return the first property among ``names`` that is a reference.

        :param names: Property names to try, in order.
        :returns: The reference, or ``None`` when none of them is one.
        """
        for name in names:
            value = self.properties.get(name)
            if isinstance(value, Ref):
                return value
        return None


@dataclass(slots=True)
class User:
    """A Confluence user."""

    key: str
    """User key (a hash on Data Center, an account id on Cloud)."""
    name: str
    """User name, used to log in on Data Center."""
    email: str = ""
    """Email address, when the export carries it."""
    display_name: str = ""
    """Full name, when the export carries it."""

    @property
    def title(self) -> str:
        """Name to show for this user."""
        return self.display_name or self.name or self.key


@dataclass(slots=True)
class Space:
    """A Confluence space."""

    id: str
    key: str
    name: str
    status: str = "CURRENT"
    """``CURRENT`` or ``ARCHIVED``."""
    space_type: str = "global"
    """``global`` or ``personal``."""
    description_id: str | None = None
    """Id of the ``SpaceDescription`` holding the description body."""
    home_page_id: str | None = None
    created: str = ""
    creator: str | None = None


@dataclass(slots=True)
class Content:
    """Fields shared by pages, blog posts, attachments and comments."""

    id: str
    title: str = ""
    version: int = 1
    status: str = "current"
    """Value of ``contentStatus``: ``current``, ``draft``, ``deleted``…"""
    created: str = ""
    modified: str = ""
    creator: str | None = None
    """User key or user name of the creator."""
    last_modifier: str | None = None
    """User key or user name of the last modifier."""
    original_id: str | None = None
    """For a historical version, the id of the current version."""
    space_id: str | None = None
    properties: dict[str, str] = field(default_factory=dict)
    """Content properties (``ContentProperty`` objects) by name."""

    @property
    def is_current(self) -> bool:
        """Whether this is the current, published version of the content."""
        return self.status == "current" and self.original_id is None

    @property
    def is_historical(self) -> bool:
        """Whether this is an older version of some other content."""
        return self.original_id is not None


@dataclass(slots=True)
class Page(Content):
    """A page or a blog post."""

    kind: str = "page"
    """``page`` or ``blogpost``."""
    parent_id: str | None = None
    position: int | None = None
    """Position among the siblings, when the export sets one."""


@dataclass(slots=True)
class Attachment(Content):
    """A file attached to a page."""

    container_id: str | None = None
    """Id of the content the file is attached to."""
    media_type: str = "application/octet-stream"
    file_size: int = 0


@dataclass(slots=True)
class Comment(Content):
    """A footer or inline comment."""

    container_id: str | None = None
    """Id of the content that was commented."""
    parent_id: str | None = None
    """Id of the comment this one replies to."""

    @property
    def inline_ref(self) -> str | None:
        """The marker reference, for an inline comment."""
        return self.properties.get("inline-marker-ref") or None

    @property
    def is_inline(self) -> bool:
        """Whether this is an inline comment, or a reply to one."""
        return (
            self.properties.get("inline-comment") == "true"
            or self.properties.get("actualCommentType") == "inline"
            or self.inline_ref is not None
        )

    @property
    def is_resolved(self) -> bool:
        """Whether an inline comment was resolved."""
        return self.properties.get("status") == "resolved"


@dataclass(slots=True)
class BodyContent:
    """The body of a page, blog post, comment or space description."""

    id: str
    content_id: str
    body: str = ""
    body_type: int = 2
    """``2`` for storage format, ``1`` for wiki markup, ``0`` for plain text."""


@dataclass(slots=True)
class ConfluenceExport:
    """Everything read from one Confluence XML export."""

    descriptor: dict[str, str] = field(default_factory=dict)
    """Values from ``exportDescriptor.properties``."""
    spaces: dict[str, Space] = field(default_factory=dict)
    pages: dict[str, Page] = field(default_factory=dict)
    """Pages and blog posts, in every status and version, by id."""
    attachments: dict[str, Attachment] = field(default_factory=dict)
    comments: dict[str, Comment] = field(default_factory=dict)
    bodies: dict[str, BodyContent] = field(default_factory=dict)
    """Bodies by the id of the content they belong to."""
    users: dict[str, User] = field(default_factory=dict)
    """Users by key."""
    labels: dict[str, list[tuple[str, str]]] = field(default_factory=dict)
    """``(namespace, name)`` pairs by the id of the labelled content."""
    restrictions: dict[str, set[str]] = field(default_factory=dict)
    """Restriction types (``View``, ``Edit``) by the id of the content."""
    space_permissions: Counter[str] = field(default_factory=Counter)
    """Count of space permissions by space id."""
    classes: Counter[str] = field(default_factory=Counter)
    """Count of exported objects by class name."""
    warnings: list[str] = field(default_factory=list)
    """Problems found while reading the export."""

    def user(self, value: str | None) -> User | None:
        """Find a user by key or by user name.

        :param value: A user key or a user name.
        :returns: The user, or ``None`` when it is unknown.
        """
        if not value:
            return None
        if user := self.users.get(value):
            return user
        lower = value.lower()
        for user in self.users.values():
            if user.name.lower() == lower:
                return user
        return None
