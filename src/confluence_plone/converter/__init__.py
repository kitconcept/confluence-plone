"""Convert Confluence bodies to Plate values for Wiki Pages."""

from . import elements  # noQA: F401 (registers the element converters)
from . import macros  # noQA: F401 (registers the macro converters)
from .context import ConversionContext
from .core import Converter
from .core import assign_ids
from .core import leaf
from .core import node
from .core import plate_text
from .storage import parse_storage
from .storage import plain_text
from confluence_plone import _types as t


__all__ = [
    "ConversionContext",
    "Converter",
    "body_text",
    "convert_body",
    "convert_page",
    "plain_text",
]


def _text_paragraphs(text: str) -> list[t.PlateNode]:
    """Return one paragraph per non-empty line of ``text``.

    :param text: The text.
    :returns: Paragraph blocks.
    """
    return [node("p", [leaf(line)]) for line in text.splitlines() if line.strip()]


def convert_body(
    ctx: ConversionContext, body: t.BodyContent | None
) -> list[t.PlateNode]:
    """Convert a body to Plate blocks.

    :param ctx: The conversion context.
    :param body: The body, or ``None`` for content without one.
    :returns: Block nodes.
    """
    if body is None:
        return []
    match body.body_type:
        case 2:
            return Converter(ctx).blocks(parse_storage(body.body))
        case 1:
            ctx.issue(t.Severity.WARNING, "wiki_markup", "body kept as plain text")
            return _text_paragraphs(body.body)
        case _:
            return _text_paragraphs(body.body)


def body_text(ctx: ConversionContext, body: t.BodyContent | None) -> str:
    """Convert a body to plain text, one line per block.

    :param ctx: The conversion context.
    :param body: The body, or ``None``.
    :returns: The text.
    """
    return plate_text(convert_body(ctx, body)).strip()


def convert_page(ctx: ConversionContext) -> list[t.PlateNode]:
    """Convert the body of a page to the Plate value of a Wiki Page.

    The value starts with the ``title`` node the Wiki Page editor expects,
    and every element gets a stable id.

    :param ctx: The conversion context, for the page.
    :returns: The Plate value.
    """
    blocks = convert_body(ctx, ctx.export.bodies.get(ctx.page.id))
    for block in blocks:
        block.setdefault("blockWidth", "default")
    value = [node("title", [leaf(ctx.item.title)], blockWidth="default"), *blocks]
    assign_ids(value, f"c{ctx.page.id}-")
    return value
