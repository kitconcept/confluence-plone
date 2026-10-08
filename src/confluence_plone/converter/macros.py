"""Converters for Confluence macros.

Most common macros have a native Plate equivalent: panels become callouts,
``expand`` becomes a toggle, ``code`` a code block. Macros that list pages
(``children``, ``pagetree``) are rendered as a static list, since the
target tree is known at conversion time. Every other macro becomes a
callout naming it, and is reported, so that no loss goes unnoticed.
"""

from confluence_plone import _types as t
from confluence_plone.converter.core import Converter
from confluence_plone.converter.core import Macro
from confluence_plone.converter.core import Marks
from confluence_plone.converter.core import leaf
from confluence_plone.converter.core import macro
from confluence_plone.converter.core import node
from confluence_plone.converter.elements import attachment_ref
from confluence_plone.converter.elements import code_block
from confluence_plone.converter.elements import columns
from confluence_plone.converter.elements import image_block
from confluence_plone.converter.elements import link_node
from confluence_plone.converter.storage import attr
from confluence_plone.converter.storage import find_deep
from confluence_plone.converter.storage import parse_storage
from confluence_plone.converter.storage import tag_name


CALLOUTS = {
    "info": ("ℹ️", "#DEEBFF"),  # noQA: RUF001
    "note": ("📝", "#EAE6FF"),
    "tip": ("💡", "#E3FCEF"),
    "warning": ("⚠️", "#FFFAE6"),
    "panel": ("📌", ""),
}
"""Icon and background color of the callout for each panel macro."""

CODE_LANGUAGES = {
    "actionscript3": "actionscript",
    "bash": "bash",
    "c#": "csharp",
    "cpp": "cpp",
    "csharp": "csharp",
    "css": "css",
    "html": "html",
    "html/xml": "xml",
    "java": "java",
    "javafx": "java",
    "javascript": "javascript",
    "js": "javascript",
    "json": "json",
    "powershell": "powershell",
    "py": "python",
    "python": "python",
    "ruby": "ruby",
    "shell": "bash",
    "sql": "sql",
    "xml": "xml",
    "yaml": "yaml",
}

STATUS_COLORS = {
    "grey": "#DFE1E6",
    "red": "#FFEBE6",
    "yellow": "#FFF0B3",
    "green": "#E3FCEF",
    "blue": "#DEEBFF",
    "purple": "#EAE6FF",
}

TEXT_BLOCKS = frozenset({"p", "h1", "h2", "h3", "h4", "h5", "h6", "blockquote"})
"""Blocks whose text can move into a callout without losing structure."""

TRANSPARENT = (
    "details",
    "div",
    "excerpt",
    "page-properties",
    "span",
)
"""Macros whose body is kept as it is."""

FILE_VIEWERS = (
    "multimedia",
    "view-file",
    "viewdoc",
    "viewfile",
    "view-pdf",
    "viewpdf",
    "viewppt",
    "viewxls",
)
"""Macros that embed an attached file: they become a link to the file."""

DIAGRAMS = ("drawio", "gliffy", "inc-drawio")
"""Diagram macros, rendered by the PNG Confluence attaches to the page."""


def _callout(
    conv: Converter, blocks: list[t.PlateNode], icon: str, color: str, title: str = ""
) -> list[t.PlateNode]:
    """Return a callout holding the text of ``blocks``.

    A Plate callout holds inline content. Paragraphs and headings are joined
    with line breaks; any other block (a list, a table) is placed right after
    the callout, and reported.

    :param conv: The converter.
    :param blocks: Content of the panel.
    :param icon: Emoji of the callout.
    :param color: Background color, or ``""``.
    :param title: Title, shown in bold on the first line.
    :returns: The callout, and the blocks that did not fit in it.
    """
    children: list[t.PlateNode] = []
    after: list[t.PlateNode] = []
    if title:
        children.append(leaf(title, {"bold": True}))
    for block in blocks:
        if block["type"] in TEXT_BLOCKS and "listStyleType" not in block:
            if children:
                children.append(leaf("\n"))
            children.extend(block["children"])
        else:
            after.append(block)
    if after:
        conv.ctx.issue(
            t.Severity.INFO,
            "callout_content_moved",
            "lists or tables moved below a panel",
        )
    props = {"icon": icon}
    if color:
        props["backgroundColor"] = color
    return [node("callout", children or [leaf("")], **props), *after]


@macro(*CALLOUTS)
def convert_panel(conv: Converter, data: Macro, marks: Marks) -> list[t.PlateNode]:
    """Panels (``info``, ``note``, ``tip``, ``warning``, ``panel``) become callouts."""
    icon, color = CALLOUTS[data.name]
    color = data.get("bgColor", default=color)
    return _callout(conv, conv.blocks(data.rich_body), icon, color, data.get("title"))


@macro("code", "noformat")
def convert_code(conv: Converter, data: Macro, marks: Marks) -> list[t.PlateNode]:
    """Code and preformatted text become a code block."""
    language = CODE_LANGUAGES.get(data.get("language", "").lower(), "")
    result: list[t.PlateNode] = []
    if title := data.get("title"):
        result.append(node("p", [leaf(title, {"bold": True})]))
    result.append(code_block(data.plain_body or "", language))
    return result


@macro("expand")
def convert_expand(conv: Converter, data: Macro, marks: Marks) -> list[t.PlateNode]:
    """Expand sections become a toggle; the content is indented below it."""
    title = data.get("title", default="Click here to expand...")
    result = [node("toggle", [leaf(title)])]
    for block in conv.blocks(data.rich_body):
        block["indent"] = block.get("indent", 0) + 1
        result.append(block)
    return result


@macro("toc")
def convert_toc(conv: Converter, data: Macro, marks: Marks) -> list[t.PlateNode]:
    """Tables of contents."""
    return [node("toc")]


@macro("anchor")
def convert_anchor(conv: Converter, data: Macro, marks: Marks) -> list[t.PlateNode]:
    """Anchors have no visible content."""
    return []


@macro(*TRANSPARENT)
def convert_transparent(
    conv: Converter, data: Macro, marks: Marks
) -> list[t.PlateNode]:
    """Macros that only wrap content: keep the content."""
    return conv.inline(data.rich_body, marks) if data.rich_body is not None else []


@macro("status")
def convert_status(conv: Converter, data: Macro, marks: Marks) -> list[t.PlateNode]:
    """Status lozenges become bold text on a colored background."""
    title = data.get("title", default=data.get("colour", default="status"))
    color = STATUS_COLORS.get(data.get("colour").lower(), STATUS_COLORS["grey"])
    conv.ctx.issue(t.Severity.INFO, "status_macro", title)
    return [leaf(title.upper(), {**marks, "bold": True, "backgroundColor": color})]


@macro("jira", "jiraissues")
def convert_jira(conv: Converter, data: Macro, marks: Marks) -> list[t.PlateNode]:
    """Jira issues become a link to the issue."""
    key = data.get("key")
    if not key:
        return unsupported(conv, data, marks)
    base_url = conv.ctx.settings.macros["jira_url"].rstrip("/")
    if not base_url:
        conv.ctx.issue(t.Severity.INFO, "jira_without_url", key)
        return [leaf(key, marks)]
    return [link_node(f"{base_url}/browse/{key}", [leaf(key, marks)])]


def _page_list(
    conv: Converter, parent_uid: str, depth: int, level: int = 1
) -> list[t.PlateNode]:
    """Return a bulleted list of links to the child pages of an item.

    :param conv: The converter.
    :param parent_uid: UID of the parent item.
    :param depth: How many levels to list; ``0`` lists every level.
    :param level: Current level, starting at ``1``.
    :returns: List paragraphs.
    """
    ctx = conv.ctx
    page_type = ctx.settings.target["page_type"]
    result: list[t.PlateNode] = []
    for uid in ctx.plan.items[parent_uid].children:
        item = ctx.plan.items[uid]
        if item.portal_type != page_type:
            continue
        link = link_node(ctx.url(uid), [leaf(item.title)])
        result.append(
            node("p", [leaf(""), link, leaf("")], indent=level, listStyleType="disc")
        )
        if depth == 0 or level < depth:
            result.extend(_page_list(conv, uid, depth, level + 1))
    return result


@macro("children")
def convert_children(conv: Converter, data: Macro, marks: Marks) -> list[t.PlateNode]:
    """The list of child pages, as it is at migration time."""
    ctx = conv.ctx
    item: t.PlannedItem | None = ctx.item
    if (param := data.parameter_elements.get("page")) is not None and (
        target := find_deep(param, "ri:page")
    ) is not None:
        item = ctx.find_page(
            attr(target, "ri:content-title"), attr(target, "ri:space-key")
        )
    if item is None:
        ctx.issue(t.Severity.WARNING, "broken_page_link", data.get("page"))
        return []
    depth_value = data.get("depth", default="1")
    if data.get("all") == "true" or depth_value == "all":
        depth = 0
    else:
        depth = int(depth_value) if depth_value.isdigit() else 1
    ctx.issue(t.Severity.INFO, "static_page_list", data.name)
    return _page_list(conv, item.uid, depth)


@macro("pagetree")
def convert_pagetree(conv: Converter, data: Macro, marks: Marks) -> list[t.PlateNode]:
    """The page tree of the space, as it is at migration time."""
    ctx = conv.ctx
    item = ctx.item
    while item.source_type != "space" and item.parent_uid:
        item = ctx.plan.items[item.parent_uid]
    ctx.issue(t.Severity.INFO, "static_page_list", data.name)
    return _page_list(conv, item.uid, 0)


def _page_attachments(conv: Converter) -> list[t.PlannedItem]:
    """Return the migrated attachments of the current page.

    :param conv: The converter.
    :returns: The planned items, in order.
    """
    ctx = conv.ctx
    page_type = ctx.settings.target["page_type"]
    items = [ctx.plan.items[uid] for uid in ctx.item.children]
    return [item for item in items if item.portal_type != page_type]


@macro("attachments")
def convert_attachments(
    conv: Converter, data: Macro, marks: Marks
) -> list[t.PlateNode]:
    """The list of attachments of the page."""
    result = []
    for item in _page_attachments(conv):
        link = link_node(conv.ctx.url(item.uid), [leaf(item.title)])
        result.append(
            node("p", [leaf(""), link, leaf("")], indent=1, listStyleType="disc")
        )
    return result


@macro("gallery")
def convert_gallery(conv: Converter, data: Macro, marks: Marks) -> list[t.PlateNode]:
    """An image gallery: every image attached to the page."""
    image_type = conv.ctx.settings.target["image_type"]
    return [
        image_block(conv.ctx.url(item.uid), item.title)
        for item in _page_attachments(conv)
        if item.portal_type == image_type
    ]


def _attachment_param(data: Macro) -> tuple[str, str, str]:
    """Return the file name, page title and space key an attachment parameter names.

    :param data: The macro.
    :returns: A tuple with the file name, the page title and the space key.
    """
    for param in data.parameter_elements.values():
        if (target := find_deep(param, "ri:attachment")) is not None:
            return attachment_ref(target)
    return data.get("name"), "", ""


@macro(*FILE_VIEWERS)
def convert_file_viewer(
    conv: Converter, data: Macro, marks: Marks
) -> list[t.PlateNode]:
    """Embedded files become a link to the file."""
    filename, page_title, space_key = _attachment_param(data)
    item = (
        conv.ctx.find_attachment(filename, page_title, space_key) if filename else None
    )
    if item is None:
        conv.ctx.issue(
            t.Severity.WARNING, "broken_attachment_link", filename or data.name
        )
        return []
    return [
        node(
            "p",
            [leaf(""), link_node(conv.ctx.url(item.uid), [leaf(item.title)]), leaf("")],
        )
    ]


@macro(*DIAGRAMS)
def convert_diagram(conv: Converter, data: Macro, marks: Marks) -> list[t.PlateNode]:
    """Diagrams: the PNG preview Confluence keeps as an attachment."""
    ctx = conv.ctx
    if name := data.get("diagramName", "name"):
        for filename in (f"{name}.png", name):
            item = ctx.find_attachment(filename)
            if (
                item is not None
                and item.portal_type == ctx.settings.target["image_type"]
            ):
                ctx.issue(t.Severity.INFO, "diagram_as_image", name)
                return [image_block(ctx.url(item.uid), name)]
    return unsupported(conv, data, marks)


@macro("section")
def convert_section(conv: Converter, data: Macro, marks: Marks) -> list[t.PlateNode]:
    """Sections of ``column`` macros become a column group."""
    body = data.rich_body
    if body is None:
        return []
    cells: list[list[t.PlateNode]] = []
    widths: list[str] = []
    other: list[t.PlateNode] = []
    for child in body:
        if (
            tag_name(child) in ("ac:structured-macro", "ac:macro")
            and attr(child, "ac:name") == "column"
        ):
            column = Macro.from_element(child)
            cells.append(conv.blocks(column.rich_body))
            widths.append(column.get("width"))
        else:
            other.extend(conv.group(conv.convert(child)))
    if not cells:
        return other
    return [columns(cells, widths if all(widths) else None), *other]


@macro("column")
def convert_column(conv: Converter, data: Macro, marks: Marks) -> list[t.PlateNode]:
    """A ``column`` macro outside a ``section``: keep its content."""
    return conv.blocks(data.rich_body)


@macro("include", "excerpt-include")
def convert_include(conv: Converter, data: Macro, marks: Marks) -> list[t.PlateNode]:
    """Included pages: a snapshot of the included content."""
    ctx = conv.ctx
    target = None
    for param in data.parameter_elements.values():
        if (target := find_deep(param, "ri:page")) is not None:
            break
    title = attr(target, "ri:content-title") if target is not None else data.get("")
    space_key = attr(target, "ri:space-key") if target is not None else ""
    item = ctx.find_page(title, space_key) if title else None
    body = ctx.export.bodies.get(item.source_id) if item else None
    if item is None or body is None:
        ctx.issue(t.Severity.WARNING, "broken_include", title or data.name)
        return []
    if item.source_id in ctx.include_stack or item.source_id == ctx.page.id:
        ctx.issue(t.Severity.WARNING, "include_loop", title)
        return []
    root = parse_storage(body.body)
    if data.name == "excerpt-include":
        excerpt = next(
            (
                el
                for el in root.iter()
                if tag_name(el) in ("ac:structured-macro", "ac:macro")
                and attr(el, "ac:name") == "excerpt"
            ),
            None,
        )
        if excerpt is not None:
            excerpt_body = Macro.from_element(excerpt).rich_body
            root = excerpt_body if excerpt_body is not None else root
    ctx.issue(t.Severity.INFO, "include_snapshot", title)
    included = Converter(ctx.for_include(item.source_id))
    return included.blocks(root)


@macro("__unsupported__")
def unsupported(conv: Converter, data: Macro, marks: Marks) -> list[t.PlateNode]:
    """Any other macro: a callout naming it, followed by its content."""
    conv.ctx.issue(t.Severity.WARNING, "unsupported_macro", data.name)
    children = [leaf(f"Unsupported Confluence macro: {data.name}", {"bold": True})]
    for name, value in sorted(data.parameters.items()):
        if value:
            children.append(leaf(f"\n{name or 'default'}: {value}"))
    result = [node("callout", children, icon="🧩")]
    if data.rich_body is not None:
        result.extend(conv.blocks(data.rich_body))
    elif data.plain_body:
        result.append(code_block(data.plain_body))
    return result
