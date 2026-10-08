"""Converters for HTML elements and Confluence (``ac:``) elements.

Macros have their own module, :mod:`confluence_plone.converter.macros`.
"""

from confluence_plone import _types as t
from confluence_plone.converter.core import BREAK
from confluence_plone.converter.core import Converter
from confluence_plone.converter.core import Marks
from confluence_plone.converter.core import element
from confluence_plone.converter.core import is_inline
from confluence_plone.converter.core import leaf
from confluence_plone.converter.core import node
from confluence_plone.converter.storage import attr
from confluence_plone.converter.storage import find
from confluence_plone.converter.storage import tag_name
from confluence_plone.converter.storage import text_content
from dataclasses import dataclass
from lxml import etree

import re


MARK_TAGS = {
    "b": "bold",
    "strong": "bold",
    "em": "italic",
    "i": "italic",
    "cite": "italic",
    "u": "underline",
    "ins": "underline",
    "s": "strikethrough",
    "del": "strikethrough",
    "strike": "strikethrough",
    "sub": "subscript",
    "sup": "superscript",
    "code": "code",
    "tt": "code",
    "kbd": "code",
}

LIST_STYLES = {"ul": "disc", "ol": "decimal", "ac:task-list": "todo"}

EMOTICONS = {
    "smile": "🙂",
    "sad": "🙁",
    "cheeky": "😛",
    "laugh": "😀",
    "wink": "😉",
    "thumbs-up": "👍",
    "thumbs-down": "👎",
    "information": "ℹ️",  # noQA: RUF001
    "tick": "✅",
    "cross": "❌",
    "warning": "⚠️",
    "plus": "➕",  # noQA: RUF001
    "minus": "➖",  # noQA: RUF001
    "question": "❓",
    "light-on": "💡",
    "light-off": "💡",
    "yellow-star": "⭐",
    "red-star": "⭐",
    "green-star": "⭐",
    "blue-star": "⭐",
    "heart": "❤️",
    "broken-heart": "💔",
}

LAYOUT_WIDTHS = {
    "two_equal": ("50%", "50%"),
    "two_left_sidebar": ("33%", "67%"),
    "two_right_sidebar": ("67%", "33%"),
    "three_equal": ("33%", "34%", "33%"),
    "three_with_sidebars": ("25%", "50%", "25%"),
}

_STYLE = re.compile(r"\s*([a-zA-Z-]+)\s*:\s*([^;]+)")


def image_block(url: str, alt: str = "", align: str = "center") -> t.PlateNode:
    """Return a Plate image block, as the Wiki Page editor writes it.

    :param url: URL of the image.
    :param alt: Alternative text.
    :param align: ``left``, ``center`` or ``right``.
    :returns: The block.
    """
    props = {"@type": "plateimage", "url": url, "alt": alt, "align": align, "size": "l"}
    return {**node("ploneBlock"), **props}


def link_node(url: str, children: list[t.PlateNode]) -> t.PlateNode:
    """Return a link, keeping only the inline nodes of its content.

    :param url: The target URL.
    :param children: Content of the link.
    :returns: The link element.
    """
    content = [item for item in children if "text" in item]
    if not any(item["text"].strip() for item in content):
        content = [leaf(url)]
    return node("a", content, url=url)


def mention_node(conv: Converter, user_ref: str) -> t.PlateNode:
    """Return a mention of a Confluence user.

    :param conv: The converter.
    :param user_ref: User key, account id or user name.
    :returns: The mention element.
    """
    principals = conv.ctx.principals
    principal = principals.principal(user_ref)
    return node("mention", key=principal, value=principals.title(user_ref))


@element(*MARK_TAGS)
def convert_mark(
    conv: Converter, el: etree._Element, marks: Marks
) -> list[t.PlateNode]:
    """Inline formatting: add a mark to the text inside."""
    return conv.inline(el, {**marks, MARK_TAGS[tag_name(el)]: True})


@element("span", "font")
def convert_span(
    conv: Converter, el: etree._Element, marks: Marks
) -> list[t.PlateNode]:
    """Spans: keep the text color and background color."""
    new_marks = dict(marks)
    for name, value in _STYLE.findall(el.get("style", "")):
        match name.lower():
            case "color":
                new_marks["color"] = value.strip()
            case "background-color" | "background":
                new_marks["backgroundColor"] = value.strip()
    if color := el.get("color"):
        new_marks["color"] = color
    return conv.inline(el, new_marks)


@element("br")
def convert_br(conv: Converter, el: etree._Element, marks: Marks) -> list[t.PlateNode]:
    """Line breaks become a newline in the text."""
    return [{**leaf("\n", marks), BREAK: True}]


@element("p", "div", "section", "article", "center")
def convert_paragraph(
    conv: Converter, el: etree._Element, marks: Marks
) -> list[t.PlateNode]:
    """Paragraphs, and containers converted as paragraphs."""
    return conv.group(conv.inline(el, marks))


@element("h1", "h2", "h3", "h4", "h5", "h6")
def convert_heading(
    conv: Converter, el: etree._Element, marks: Marks
) -> list[t.PlateNode]:
    """Headings keep their level."""
    return conv.group(conv.inline(el, marks), tag_name(el))


@element("blockquote")
def convert_blockquote(
    conv: Converter, el: etree._Element, marks: Marks
) -> list[t.PlateNode]:
    """Quotes: each paragraph of the quote becomes a quote block."""
    result = []
    for block in conv.blocks(el, marks):
        if block["type"] == "p" and "listStyleType" not in block:
            block["type"] = "blockquote"
        result.append(block)
    return result


@element("pre")
def convert_pre(conv: Converter, el: etree._Element, marks: Marks) -> list[t.PlateNode]:
    """Preformatted text becomes a code block."""
    return [code_block(text_content(el))]


def code_block(text: str, language: str = "") -> t.PlateNode:
    """Return a code block, one ``code_line`` per line.

    :param text: The code.
    :param language: Language for syntax highlighting.
    :returns: The block.
    """
    lines = text.strip("\n").split("\n")
    props = {"lang": language} if language else {}
    return node(
        "code_block",
        [node("code_line", [leaf(line)]) for line in lines],
        **props,
    )


@element("hr")
def convert_hr(conv: Converter, el: etree._Element, marks: Marks) -> list[t.PlateNode]:
    """Horizontal rules."""
    return [node("hr")]


@element("a")
def convert_a(conv: Converter, el: etree._Element, marks: Marks) -> list[t.PlateNode]:
    """Plain HTML links."""
    href = el.get("href", "").strip()
    children = conv.inline(el, marks)
    if not href:
        return children
    return [link_node(href, children)]


@element("img")
def convert_img(conv: Converter, el: etree._Element, marks: Marks) -> list[t.PlateNode]:
    """Plain HTML images, usually pointing to an external URL."""
    src = el.get("src", "").strip()
    if not src:
        return []
    return [image_block(src, el.get("alt", ""))]


@element("time")
def convert_time(
    conv: Converter, el: etree._Element, marks: Marks
) -> list[t.PlateNode]:
    """Dates become Plate date elements."""
    value = el.get("datetime", "").strip()
    if not value:
        return conv.inline(el, marks)
    return [node("date", value=value[:10])]


LIST_ITEM_TYPES = frozenset({"p", "h1", "h2", "h3", "h4", "h5", "h6"})
"""Block types that can be a list item."""


def _item_props(style: str, number: int, checked: bool) -> dict:
    """Return the properties that make a block a list item.

    :param style: Plate list style: ``disc``, ``decimal`` or ``todo``.
    :param number: Position of the item in its list, starting at ``1``.
    :param checked: Whether a task is done.
    :returns: The properties.
    """
    props: dict = {"listStyleType": style}
    if style == "decimal" and number > 1:
        props["listStart"] = number
    if style == "todo":
        props["checked"] = checked
    return props


def _list_items(
    conv: Converter, el: etree._Element, marks: Marks, style: str
) -> list[t.PlateNode]:
    """Convert the items of a list into Plate indent-list paragraphs.

    :param conv: The converter.
    :param el: The ``ul``, ``ol`` or ``ac:task-list`` element.
    :param marks: Marks for the text.
    :param style: Plate list style: ``disc``, ``decimal`` or ``todo``.
    :returns: Block nodes.
    """
    conv.list_depth += 1
    indent = conv.list_depth
    result: list[t.PlateNode] = []
    number = 0
    for item in el:
        name = tag_name(item)
        if name not in ("li", "ac:task"):
            continue
        number += 1
        checked = False
        content: etree._Element | None = item
        if name == "ac:task":
            status = find(item, "ac:task-status")
            checked = status is not None and text_content(status).strip() == "complete"
            content = find(item, "ac:task-body")
        first = True
        for block in conv.blocks(content, marks):
            if "listStyleType" in block or block["type"] not in LIST_ITEM_TYPES:
                result.append(block)
                continue
            block["indent"] = indent
            if first:
                block.update(_item_props(style, number, checked))
                first = False
            result.append(block)
        if first:
            result.append(
                node("p", indent=indent, **_item_props(style, number, checked))
            )
    conv.list_depth -= 1
    return result


@element("ul", "ol", "ac:task-list")
def convert_list(
    conv: Converter, el: etree._Element, marks: Marks
) -> list[t.PlateNode]:
    """Lists and task lists become Plate indent lists."""
    return _list_items(conv, el, marks, LIST_STYLES[tag_name(el)])


def _cell(conv: Converter, el: etree._Element) -> t.PlateNode:
    """Convert a table cell.

    :param conv: The converter.
    :param el: The ``th`` or ``td`` element.
    :returns: The cell node.
    """
    props = {}
    for attribute, prop in (("colspan", "colSpan"), ("rowspan", "rowSpan")):
        value = el.get(attribute, "1").strip()
        if value.isdigit() and int(value) > 1:
            props[prop] = int(value)
    blocks = conv.blocks(el) or [node("p")]
    return node(tag_name(el), blocks, **props)


@element("table")
def convert_table(
    conv: Converter, el: etree._Element, marks: Marks
) -> list[t.PlateNode]:
    """Tables, with header cells and merged cells."""
    sections = [
        el,
        *(child for child in el if tag_name(child) in ("thead", "tbody", "tfoot")),
    ]
    rows = []
    for section in sections:
        for row in section:
            if tag_name(row) != "tr":
                continue
            cells = [
                _cell(conv, cell) for cell in row if tag_name(cell) in ("th", "td")
            ]
            if cells:
                rows.append(node("tr", cells))
    return [node("table", rows)] if rows else []


def attachment_ref(target: etree._Element) -> tuple[str, str, str]:
    """Read a ``ri:attachment`` element.

    :param target: The ``ri:attachment`` element.
    :returns: The file name, and the title and space key of the page it is
        attached to (empty for the current page).
    """
    page = find(target, "ri:page")
    if page is None:
        return attr(target, "ri:filename"), "", ""
    return (
        attr(target, "ri:filename"),
        attr(page, "ri:content-title"),
        attr(page, "ri:space-key"),
    )


@dataclass
class Link:
    """The parts of an ``ac:link`` every kind of target needs."""

    body: list[t.PlateNode]
    """Inline content of the link body, possibly empty."""
    marks: Marks
    anchor: str

    def text(self, default: str) -> list[t.PlateNode]:
        """Return the link body, or ``default`` when the body is empty.

        :param default: Text used when the link has no body.
        :returns: Inline nodes.
        """
        if any(item.get("text", "x").strip() for item in self.body):
            return self.body
        return [leaf(default, self.marks)]


def _link_page(
    conv: Converter, target: etree._Element, link: Link
) -> list[t.PlateNode]:
    """A link to a page."""
    ctx = conv.ctx
    title = attr(target, "ri:content-title")
    space_key = attr(target, "ri:space-key")
    if item := ctx.find_page(title, space_key):
        suffix = f"#{link.anchor}" if link.anchor else ""
        return [link_node(ctx.url(item.uid) + suffix, link.text(title))]
    detail = f"{space_key or ctx.space_key}:{title}"
    ctx.issue(t.Severity.WARNING, "broken_page_link", detail)
    return link.text(title)


def _link_attachment(
    conv: Converter, target: etree._Element, link: Link
) -> list[t.PlateNode]:
    """A link to an attachment."""
    ctx = conv.ctx
    filename, page_title, space_key = attachment_ref(target)
    if item := ctx.find_attachment(filename, page_title, space_key):
        return [link_node(ctx.url(item.uid), link.text(filename))]
    ctx.issue(t.Severity.WARNING, "broken_attachment_link", filename)
    return link.text(filename)


def _link_user(
    conv: Converter, target: etree._Element, link: Link
) -> list[t.PlateNode]:
    """A link to a user becomes a mention."""
    user_ref = (
        attr(target, "ri:userkey")
        or attr(target, "ri:account-id")
        or attr(target, "ri:username")
    )
    return [mention_node(conv, user_ref)]


def _link_space(
    conv: Converter, target: etree._Element, link: Link
) -> list[t.PlateNode]:
    """A link to a space becomes a link to its workspace."""
    ctx = conv.ctx
    space_key = attr(target, "ri:space-key")
    for item in ctx.plan.items.values():
        if item.source_type == "space" and item.space_key == space_key:
            return [link_node(ctx.url(item.uid), link.text(item.title))]
    ctx.issue(t.Severity.WARNING, "broken_space_link", space_key)
    return link.text(space_key)


def _link_url(conv: Converter, target: etree._Element, link: Link) -> list[t.PlateNode]:
    """A link to an external URL."""
    url = attr(target, "ri:value")
    return [link_node(url, link.text(url))]


def _link_blog_post(
    conv: Converter, target: etree._Element, link: Link
) -> list[t.PlateNode]:
    """A link to a blog post: blog posts are not converted, so keep the text."""
    title = attr(target, "ri:content-title")
    conv.ctx.issue(t.Severity.INFO, "blog_post_link", title)
    return link.text(title)


LINK_TARGETS = {
    "ri:page": _link_page,
    "ri:attachment": _link_attachment,
    "ri:user": _link_user,
    "ri:space": _link_space,
    "ri:url": _link_url,
    "ri:blog-post": _link_blog_post,
}
"""Converters for the target of an ``ac:link``, by tag of the target."""


@element("ac:link")
def convert_link(
    conv: Converter, el: etree._Element, marks: Marks
) -> list[t.PlateNode]:
    """Links to pages, attachments, users, spaces and URLs."""
    body: list[t.PlateNode] = []
    if (link_body := find(el, "ac:link-body")) is not None:
        body = [item for item in conv.inline(link_body, marks) if is_inline(item)]
    elif (plain := find(el, "ac:plain-text-link-body")) is not None:
        body = [leaf(plain.text or "", marks)]
    link = Link(body=body, marks=marks, anchor=attr(el, "ac:anchor"))
    for name, converter in LINK_TARGETS.items():
        if (target := find(el, name)) is not None:
            return converter(conv, target, link)
    if link.anchor:
        return link.text(link.anchor)
    detail = etree.tostring(el, encoding="unicode")[:200]
    conv.ctx.issue(t.Severity.WARNING, "unsupported_link", detail)
    return body


@element("ac:image")
def convert_image(
    conv: Converter, el: etree._Element, marks: Marks
) -> list[t.PlateNode]:
    """Images: attachments of a page, or external URLs."""
    ctx = conv.ctx
    align = attr(el, "ac:align") or "center"
    alt = attr(el, "ac:alt") or attr(el, "ac:title")
    if (target := find(el, "ri:url")) is not None:
        return [image_block(attr(target, "ri:value"), alt, align)]
    target = find(el, "ri:attachment")
    if target is None:
        ctx.issue(t.Severity.WARNING, "broken_image", "image without source")
        return []
    filename, page_title, space_key = attachment_ref(target)
    item = ctx.find_attachment(filename, page_title, space_key)
    if item is None:
        ctx.issue(t.Severity.WARNING, "broken_image", filename)
        return []
    if item.portal_type != ctx.settings.target["image_type"]:
        return [link_node(ctx.url(item.uid), [leaf(filename, marks)])]
    return [image_block(ctx.url(item.uid), alt or filename, align)]


def emoji_from_id(emoji_id: str) -> str:
    """Return the emoji for a Cloud emoji id, made of hexadecimal code points.

    :param emoji_id: The id, for example ``1f4cb`` or ``31-20e3``.
    :returns: The emoji, or ``""`` when the id is not made of code points.
    """
    try:
        return "".join(chr(int(part, 16)) for part in emoji_id.split("-") if part)
    except ValueError:
        return ""


@element("ac:emoticon")
def convert_emoticon(
    conv: Converter, el: etree._Element, marks: Marks
) -> list[t.PlateNode]:
    """Emoticons become emoji."""
    name = attr(el, "ac:name")
    if emoji := EMOTICONS.get(name) or emoji_from_id(attr(el, "ac:emoji-id")):
        return [leaf(emoji, marks)]
    fallback = attr(el, "ac:emoji-fallback")
    if fallback and not fallback.startswith(":"):
        return [leaf(fallback, marks)]
    conv.ctx.issue(t.Severity.INFO, "unknown_emoticon", name or fallback)
    return [leaf(fallback or f"({name})", marks)]


@element("ac:inline-comment-marker")
def convert_comment_marker(
    conv: Converter, el: etree._Element, marks: Marks
) -> list[t.PlateNode]:
    """Text with an inline comment gets the comment mark of the discussion."""
    ref = attr(el, "ac:ref")
    if not ref or not conv.ctx.settings.content["inline_comments"]:
        return conv.inline(el, marks)
    if ref not in conv.ctx.inline_refs:
        conv.ctx.inline_refs.append(ref)
    return conv.inline(el, {**marks, "comment": True, f"comment_{ref}": True})


@element("ac:structured-macro", "ac:macro")
def convert_macro(
    conv: Converter, el: etree._Element, marks: Marks
) -> list[t.PlateNode]:
    """Macros are dispatched to the macro converters."""
    return conv.macro(el, marks)


@element("ac:layout")
def convert_layout(
    conv: Converter, el: etree._Element, marks: Marks
) -> list[t.PlateNode]:
    """Page layouts: each section with more than one cell becomes columns."""
    result: list[t.PlateNode] = []
    for section in el:
        if tag_name(section) != "ac:layout-section":
            continue
        cells = [
            conv.blocks(cell) for cell in section if tag_name(cell) == "ac:layout-cell"
        ]
        cells = [cell for cell in cells if cell]
        if len(cells) < 2:
            result.extend(cells[0] if cells else [])
            continue
        widths = LAYOUT_WIDTHS.get(attr(section, "ac:type"), ())
        result.append(columns(cells, list(widths)))
    return result


def columns(
    cells: list[list[t.PlateNode]], widths: list[str] | None = None
) -> t.PlateNode:
    """Return a column group.

    :param cells: Blocks of each column.
    :param widths: Width of each column. Equal widths are used when the
        number of widths does not match the number of columns.
    :returns: The ``column_group`` node.
    """
    if not widths or len(widths) != len(cells):
        widths = [f"{100 / len(cells):.0f}%"] * len(cells)
    return node(
        "column_group",
        [
            node("column", cell or [node("p")], width=width)
            for cell, width in zip(cells, widths, strict=True)
        ],
    )


@element(
    "ac:placeholder",
    "ac:parameter",
    "ri:page",
    "ri:attachment",
    "ri:user",
    "ri:url",
    "ri:space",
)
def convert_ignored(
    conv: Converter, el: etree._Element, marks: Marks
) -> list[t.PlateNode]:
    """Elements without visible content."""
    return []


@element("ac:adf-extension")
def convert_adf_extension(
    conv: Converter, el: etree._Element, marks: Marks
) -> list[t.PlateNode]:
    """Cloud editor extensions: use the fallback content Confluence provides."""
    fallback = find(el, "ac:adf-fallback")
    conv.ctx.issue(
        t.Severity.INFO, "adf_extension", "converted from the fallback content"
    )
    return conv.inline(fallback, marks) if fallback is not None else []
