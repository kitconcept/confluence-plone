"""State shared by the converters while one body is converted."""

from confluence_plone import _types as t
from confluence_plone.utils.principals import PrincipalMapper
from dataclasses import dataclass
from dataclasses import field


@dataclass
class ConversionContext:
    """Everything a converter needs to know about the body being converted."""

    export: t.ConfluenceExport
    plan: t.MigrationPlan
    settings: t.ConfluenceSettings
    principals: PrincipalMapper
    page: t.Page
    """The Confluence page whose body (or comment) is converted."""
    item: t.PlannedItem
    """The planned item of that page."""
    issues: list[t.Issue] = field(default_factory=list)
    inline_refs: list[str] = field(default_factory=list)
    """Inline comment markers found in the body, in order."""
    include_stack: tuple[str, ...] = ()
    """Ids of the pages being included, to stop include loops."""
    _seen: set[tuple[str, str, str]] = field(default_factory=set, repr=False)

    @property
    def space_key(self) -> str:
        """Key of the space of the page."""
        return self.item.space_key

    def issue(self, severity: t.Severity, code: str, detail: str = "") -> None:
        """Record an issue for the page, once per code and detail.

        :param severity: How bad the issue is.
        :param code: Machine-readable code.
        :param detail: Human-readable detail.
        """
        key = (severity.value, code, detail)
        if key not in self._seen:
            self._seen.add(key)
            self.issues.append(t.Issue(self.page.id, severity, code, detail))

    def url(self, uid: str) -> str:
        """Return the URL to use in the page for a link to another item.

        :param uid: UID of the target item.
        :returns: A relative ``resolveuid`` URL, or the path of the target,
            depending on the ``link_style`` setting.
        """
        if self.settings.target["link_style"] == "path":
            return self.plan.items[uid].path
        return f"{'../' * self.item.depth}resolveuid/{uid}"

    def find_page(self, title: str, space_key: str = "") -> t.PlannedItem | None:
        """Find a migrated page by title.

        :param title: Title of the page; ``@self`` is the current page.
        :param space_key: Key of its space. Defaults to the current space.
        :returns: The planned item, or ``None``.
        """
        if title.strip() == "@self":
            return self.item
        key = (space_key or self.space_key, title.strip().lower())
        uid = self.plan.pages_by_title.get(key)
        return self.plan.items[uid] if uid else None

    def find_attachment(
        self, filename: str, page_title: str = "", space_key: str = ""
    ) -> t.PlannedItem | None:
        """Find a migrated attachment by file name.

        :param filename: File name of the attachment.
        :param page_title: Title of the page it is attached to. Defaults to
            the current page.
        :param space_key: Key of the space of that page.
        :returns: The planned item, or ``None``.
        """
        page_id: str | None = self.page.id
        if page_title:
            page = self.find_page(page_title, space_key)
            page_id = page.source_id if page else None
        if page_id is None:
            return None
        uid = self.plan.attachments_by_name.get((page_id, filename.strip().lower()))
        return self.plan.items[uid] if uid else None

    def for_include(self, page_id: str) -> ConversionContext:
        """Return a context to convert the body of an included page.

        Links still resolve against the current page, and issues and inline
        comments stay with it.

        :param page_id: Id of the included page.
        :returns: The new context.
        """
        return ConversionContext(
            export=self.export,
            plan=self.plan,
            settings=self.settings,
            principals=self.principals,
            page=self.page,
            item=self.item,
            issues=self.issues,
            inline_refs=self.inline_refs,
            include_stack=(*self.include_stack, page_id),
            _seen=self._seen,
        )
