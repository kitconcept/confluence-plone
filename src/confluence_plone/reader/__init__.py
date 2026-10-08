"""Read a Confluence XML export into a :class:`ConfluenceExport`."""

from .entities import iter_objects
from .model import build_export
from .sanitize import SanitizingStream
from .source import ExportSource
from confluence_plone import _types as t
from lxml import etree


__all__ = ["ExportSource", "read_export"]


def read_export(source: ExportSource) -> t.ConfluenceExport:
    """Read every object of an export.

    The XML is sanitized first. If it is still malformed, it is parsed again
    with the parser's recovery mode, and the export gets a warning, since
    recovery can drop content.

    :param source: The export to read.
    :returns: The export model.
    """
    try:
        with source.open_entities() as raw_stream:
            stream = SanitizingStream(raw_stream)
            export = build_export(iter_objects(stream))  # type: ignore[arg-type]
    except etree.XMLSyntaxError as exc:
        with source.open_entities() as raw_stream:
            stream = SanitizingStream(raw_stream)
            export = build_export(iter_objects(stream, recover=True))  # type: ignore[arg-type]
        export.warnings.append(f"entities.xml is malformed, recovered: {exc}")
    if stream.removed:
        export.warnings.append(
            f"Removed {stream.removed} characters that XML 1.0 forbids"
        )
    export.descriptor = source.descriptor()
    return export
