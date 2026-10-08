"""Run an analysis or a conversion from start to end.

A conversion reads the export, plans the target tree, converts every
planned item, writes the ``plone.exportimport`` layout, and writes the
reports. The result is then imported with ``plone.exportimport``, unchanged.
"""

from collections import Counter
from collections.abc import Callable
from confluence_plone import _types as t
from confluence_plone import plone
from confluence_plone import reports
from confluence_plone.converter import ConversionContext
from confluence_plone.converter import convert_page
from confluence_plone.converter import plain_text
from confluence_plone.converter.comments import footer_comments
from confluence_plone.converter.comments import inline_discussions
from confluence_plone.converter.comments import page_comments
from confluence_plone.planner import plan_migration
from confluence_plone.reader import ExportSource
from confluence_plone.reader import read_export
from confluence_plone.utils.dates import to_iso
from confluence_plone.utils.principals import PrincipalMapper
from confluence_plone.utils.principals import load_mapping
from confluence_plone.writer import ExportWriter
from confluence_plone.writer import safe_filename
from dataclasses import dataclass
from dataclasses import field
from pathlib import Path


Reporter = Callable[[str], None]
"""Receives progress messages."""


def _quiet(message: str) -> None:
    """Ignore a progress message.

    :param message: The message.
    """


@dataclass
class ConversionResult:
    """What a conversion produced."""

    plan: t.MigrationPlan
    items: list[t.ItemReport] = field(default_factory=list)
    issues: list[t.Issue] = field(default_factory=list)
    types: Counter[str] = field(default_factory=Counter)
    """Number of items written, by portal type."""
    footer_comments: int = 0
    inline_discussions: int = 0
    unmapped_users: Counter[str] = field(default_factory=Counter)
    reports: list[Path] = field(default_factory=list)

    def summary(self) -> dict:
        """Return the counts of the conversion.

        :returns: The summary, ready to be written as JSON.
        """
        severities = Counter(issue.severity.value for issue in self.issues)
        codes = Counter(issue.code for issue in self.issues)
        statuses = Counter(item.status for item in self.items)
        return {
            "items": dict(sorted(self.types.items())),
            "statuses": dict(sorted(statuses.items())),
            "skipped": len(self.plan.skipped),
            "footer_comments": self.footer_comments,
            "inline_discussions": self.inline_discussions,
            "issues": dict(sorted(severities.items())),
            "issue_codes": dict(codes.most_common()),
            "unmapped_users": dict(self.unmapped_users.most_common()),
        }


def analyze(src: Path, dst: Path, report: Reporter = _quiet) -> tuple[dict, list[Path]]:
    """Write an inventory of an export.

    :param src: The export: a zip file, a directory or an ``entities.xml``.
    :param dst: Directory for the reports.
    :param report: Receives progress messages.
    :returns: The inventory, and the paths of the written reports.
    """
    with ExportSource(src) as source:
        report(f"Reading {source.path}")
        export = read_export(source)
    data = reports.inventory(export)
    paths = [
        reports.write_json(data, dst / "inventory.json"),
        reports.write_csv(
            data["macros"], ["macro", "pages", "uses", "example"], dst / "macros.csv"
        ),
    ]
    return data, paths


class Conversion:
    """Convert one export.

    :param source: The export.
    :param export: Its content.
    :param settings: The settings.
    :param principals: Maps Confluence users to principals.
    :param writer: Writes the result.
    """

    def __init__(
        self,
        source: ExportSource,
        export: t.ConfluenceExport,
        settings: t.ConfluenceSettings,
        principals: PrincipalMapper,
        writer: ExportWriter,
    ):
        self.source = source
        self.export = export
        self.settings = settings
        self.principals = principals
        self.writer = writer
        self.timezone = settings.config["timezone"]
        self.plan = plan_migration(export, settings, source.find_attachment)
        self.result = ConversionResult(plan=self.plan, issues=list(self.plan.issues))
        self.discussions: dict[str, dict] = {}
        self.redirects: dict[str, str] = {}

    def _context(self, page: t.Page, item: t.PlannedItem) -> ConversionContext:
        """Return a conversion context for a page.

        :param page: The page.
        :param item: Its planned item.
        :returns: The context.
        """
        return ConversionContext(
            export=self.export,
            plan=self.plan,
            settings=self.settings,
            principals=self.principals,
            page=page,
            item=item,
        )

    def _subjects(self, content_id: str) -> list[str]:
        """Return the labels of some content, as subjects.

        :param content_id: Id of the content.
        :returns: The subjects, sorted, without duplicates.
        """
        namespaces = self.settings.content["label_namespaces"]
        labels = self.export.labels.get(content_id, [])
        return sorted({
            name for namespace, name in labels if namespace in namespaces and name
        })

    def _payload(
        self, item: t.PlannedItem, content: t.Content | t.Space, description: str = ""
    ) -> t.PloneItem:
        """Return the base payload of an item.

        :param item: The planned item.
        :param content: The Confluence space or content it comes from.
        :param description: Description of the item.
        :returns: The payload.
        """
        if isinstance(content, t.Space):
            created = modified = to_iso(content.created, self.timezone)
            creator = modifier = self.principals.principal(content.creator)
            subjects: list[str] = []
        else:
            created = to_iso(content.created, self.timezone)
            modified = to_iso(content.modified, self.timezone) or created
            creator = self.principals.principal(content.creator)
            modifier = self.principals.principal(
                content.last_modifier or content.creator
            )
            subjects = self._subjects(content.id)
        return plone.base_payload(
            item,
            self.settings,
            created,
            modified,
            creator,
            modifier,
            description,
            subjects,
        )

    def convert_space(self, item: t.PlannedItem) -> tuple[t.PloneItem, list[t.Issue]]:
        """Build the payload of a workspace.

        :param item: The planned workspace.
        :returns: The payload, and its issues.
        """
        space = self.export.spaces[item.source_id.removeprefix("space:")]
        description = ""
        if space.description_id and (
            body := self.export.bodies.get(space.description_id)
        ):
            description = (
                plain_text(body.body) if body.body_type == 2 else body.body.strip()
            )
        data = self._payload(item, space, description)
        data.update(plone.workspace_blocks(item))
        issues = []
        if count := self.export.space_permissions.get(space.id):
            issues.append(
                t.Issue(
                    item.source_id,
                    t.Severity.WARNING,
                    "space_permissions_not_migrated",
                    f"{count} space permissions",
                )
            )
        return data, issues

    def convert_page(self, item: t.PlannedItem) -> tuple[t.PloneItem, list[t.Issue]]:
        """Build the payload of a Wiki Page, with its comments.

        A page that fails to convert is still written, with its title only,
        so that the tree below it stays intact; the error is reported.

        :param item: The planned page.
        :returns: The payload, and its issues.
        """
        page = self.export.pages[item.source_id]
        ctx = self._context(page, item)
        try:
            value = convert_page(ctx)
        except Exception as exc:
            ctx.issue(t.Severity.ERROR, "conversion_failed", repr(exc))
            value = [
                {"type": "title", "id": "title", "children": [{"text": item.title}]}
            ]
        comments = page_comments(ctx)
        discussions, footer = inline_discussions(ctx, comments)
        self.result.inline_discussions += len(discussions)
        if footer and self.settings.content["footer_comments"]:
            self.discussions[item.uid] = {"items": footer_comments(ctx, footer)}
            self.result.footer_comments += len(footer)
        if restrictions := self.export.restrictions.get(page.id):
            ctx.issue(
                t.Severity.WARNING,
                "restriction_not_migrated",
                ", ".join(sorted(restrictions)),
            )
        data = self._payload(item, page)
        data.update(plone.wiki_page_blocks(item, value, discussions))
        site_root = self.settings.target["site_root"].rstrip("/")
        title = page.title.replace(" ", "+")
        self.redirects[f"{site_root}/display/{item.space_key}/{title}"] = (
            f"{site_root}{item.path}"
        )
        return data, ctx.issues

    def convert_attachment(
        self, item: t.PlannedItem
    ) -> tuple[t.PloneItem, list[t.Issue]]:
        """Copy the binary of an attachment and build its payload.

        :param item: The planned attachment.
        :returns: The payload, and its issues.
        """
        attachment = self.export.attachments[item.source_id]
        field_name = (
            "image"
            if item.portal_type == self.settings.target["image_type"]
            else "file"
        )
        filename = safe_filename(attachment.title, f"file-{attachment.id}")
        assert item.blob_name is not None  # noQA: S101
        with self.source.open(item.blob_name) as stream:
            self.writer.write_blob(item, field_name, filename, stream)
        size = (self.writer.content / item.uid / field_name / filename).stat().st_size
        data = self._payload(item, attachment)
        data.update(
            plone.blob_field(item, field_name, filename, attachment.media_type, size)
        )
        return data, []

    def run(self, report: Reporter = _quiet) -> ConversionResult:
        """Convert every planned item and write the result.

        :param report: Receives progress messages.
        :returns: The result.
        """
        result = self.result
        converters = {
            "space": self.convert_space,
            "page": self.convert_page,
            "attachment": self.convert_attachment,
        }
        issues_by_source: dict[str, list[t.Issue]] = {}
        for issue in self.plan.issues:
            issues_by_source.setdefault(issue.source_id, []).append(issue)
        for item in self.plan.items.values():
            if item.source_type == "space":
                report(f"Converting space {item.space_key}: {item.title}")
            data, issues = converters[item.source_type](item)
            owner = data["creators"][0]
            self.writer.write_item(item, data, owner)
            result.issues.extend(issues)
            item_issues = issues_by_source.get(item.source_id, []) + issues
            result.types[item.portal_type] += 1
            result.items.append(
                t.ItemReport(
                    source_id=item.source_id,
                    source_type=item.source_type,
                    space=item.space_key,
                    title=item.title,
                    path=item.path,
                    portal_type=item.portal_type,
                    uid=item.uid,
                    status=reports.item_status(item_issues),
                    issues=len(item_issues),
                )
            )
        self.writer.write_metadata()
        self.writer.write_json("discussions.json", self.discussions)
        if self.settings.redirects["enabled"]:
            self.writer.write_json("redirects.json", self.redirects)
        result.unmapped_users = self.principals.unmapped
        return result


def convert(
    src: Path, dst: Path, settings: t.ConfluenceSettings, report: Reporter = _quiet
) -> ConversionResult:
    """Convert an export to the ``plone.exportimport`` layout, and write the reports.

    :param src: The export: a zip file, a directory or an ``entities.xml``.
    :param dst: Destination directory for the ``plone.exportimport`` layout.
    :param settings: The settings.
    :param report: Receives progress messages.
    :returns: The result.
    """
    mapping_file = settings.principals["mapping_file"]
    mapping = load_mapping(Path(mapping_file)) if mapping_file else {}
    with ExportSource(src) as source:
        report(f"Reading {source.path}")
        export = read_export(source)
        for warning in export.warnings:
            report(f"Warning: {warning}")
        principals = PrincipalMapper(export, settings, mapping)
        conversion = Conversion(source, export, settings, principals, ExportWriter(dst))
        result = conversion.run(report)
    reports_dir = settings.config["reports_location"]
    result.reports = [
        reports.write_dataclasses(
            result.items, t.ItemReport, reports_dir / "items.csv"
        ),
        reports.write_dataclasses(result.issues, t.Issue, reports_dir / "issues.csv"),
        reports.write_dataclasses(
            result.plan.skipped, t.SkippedItem, reports_dir / "skipped.csv"
        ),
        reports.write_json(result.summary(), reports_dir / "summary.json"),
    ]
    return result
