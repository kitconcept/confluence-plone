"""Reports: an inventory of an export, and the results of a conversion.

The inventory is meant to be the first thing run on a customer export: it
counts what the export holds and lists every macro used, with the number of
pages using it. That list is what drives the estimate of a migration.

After a conversion, three CSV files describe the result, one row per
object: ``items.csv`` (what was created), ``issues.csv`` (every lossy step,
as data) and ``skipped.csv`` (what was left out, and why).
"""

from collections import Counter
from collections import defaultdict
from confluence_plone import _types as t
from confluence_plone.converter.storage import attr
from confluence_plone.converter.storage import parse_storage
from confluence_plone.converter.storage import tag_name
from dataclasses import asdict
from dataclasses import fields
from pathlib import Path
from typing import Any

import csv
import orjson


def macro_inventory(export: t.ConfluenceExport) -> list[dict[str, Any]]:
    """List the macros used by the current pages of an export.

    :param export: The export.
    :returns: One row per macro: its name, the number of pages using it, the
        number of uses, and the title of one page using it. Most used first.
    """
    pages: dict[str, set[str]] = defaultdict(set)
    uses: Counter[str] = Counter()
    examples: dict[str, str] = {}
    for page in export.pages.values():
        body = export.bodies.get(page.id)
        if not page.is_current or body is None or body.body_type != 2:
            continue
        for el in parse_storage(body.body).iter():
            if tag_name(el) in ("ac:structured-macro", "ac:macro"):
                name = attr(el, "ac:name").strip().lower()
                pages[name].add(page.id)
                uses[name] += 1
                examples.setdefault(name, page.title)
    rows = [
        {
            "macro": name,
            "pages": len(pages[name]),
            "uses": uses[name],
            "example": examples[name],
        }
        for name in pages
    ]
    return sorted(rows, key=lambda row: (-row["pages"], row["macro"]))


def inventory(export: t.ConfluenceExport) -> dict[str, Any]:
    """Count what an export holds.

    :param export: The export.
    :returns: The inventory, ready to be written as JSON.
    """
    spaces = []
    for space in sorted(export.spaces.values(), key=lambda s: s.key):
        contents = [p for p in export.pages.values() if p.space_id == space.id]
        statuses: Counter[str] = Counter()
        for content in contents:
            status = "historical" if content.is_historical else content.status
            statuses[f"{content.kind}:{status}"] += 1
        attachments = [
            a
            for a in export.attachments.values()
            if a.space_id == space.id and a.is_current
        ]
        spaces.append({
            "key": space.key,
            "name": space.name,
            "type": space.space_type,
            "status": space.status,
            "contents": dict(sorted(statuses.items())),
            "attachments": len(attachments),
            "attachments_size": sum(a.file_size for a in attachments),
            "permissions": export.space_permissions.get(space.id, 0),
        })
    comments = [c for c in export.comments.values() if c.is_current]
    body_types = Counter(body.body_type for body in export.bodies.values())
    return {
        "descriptor": export.descriptor,
        "spaces": spaces,
        "totals": {
            "spaces": len(export.spaces),
            "pages": sum(
                1 for p in export.pages.values() if p.kind == "page" and p.is_current
            ),
            "blog_posts": sum(
                1
                for p in export.pages.values()
                if p.kind == "blogpost" and p.is_current
            ),
            "historical_versions": sum(
                1 for p in export.pages.values() if p.is_historical
            ),
            "attachments": sum(1 for a in export.attachments.values() if a.is_current),
            "footer_comments": sum(1 for c in comments if not c.is_inline),
            "inline_comments": sum(1 for c in comments if c.is_inline),
            "users": len(export.users),
            "labelled_content": len(export.labels),
            "restricted_content": len(export.restrictions),
        },
        "body_types": {str(key): value for key, value in sorted(body_types.items())},
        "classes": dict(sorted(export.classes.items())),
        "macros": macro_inventory(export),
        "warnings": export.warnings,
    }


def write_json(data: Any, path: Path) -> Path:
    """Write data as indented JSON.

    :param data: The data.
    :param path: The file to write.
    :returns: The path.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(orjson.dumps(data, option=orjson.OPT_INDENT_2))
    return path


def write_csv(rows: list[dict[str, Any]], headers: list[str], path: Path) -> Path:
    """Write rows as CSV.

    :param rows: The rows.
    :param headers: The column names.
    :param path: The file to write.
    :returns: The path.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, headers)
        writer.writeheader()
        writer.writerows(rows)
    return path


def write_dataclasses(items: list, cls: type, path: Path) -> Path:
    """Write a list of dataclass instances as CSV, one column per field.

    :param items: The instances.
    :param cls: Their dataclass.
    :param path: The file to write.
    :returns: The path.
    """
    headers = [field.name for field in fields(cls)]
    return write_csv([asdict(item) for item in items], headers, path)


def item_status(issues: list[t.Issue]) -> str:
    """Return the status of an item after its worst issue.

    :param issues: The issues of the item.
    :returns: ``ok``, ``warning`` or ``error``.
    """
    severities = {issue.severity for issue in issues}
    if t.Severity.ERROR in severities:
        return "error"
    if t.Severity.WARNING in severities:
        return "warning"
    return "ok"
