"""Turn a parsed storage-format body into a Plate value.

A Plate value is a list of block nodes (``p``, ``h2``, ``table``…) whose
children are inline nodes: text leaves carrying marks (``bold``,
``italic``…) and inline elements (``a``, ``mention``, ``date``). The storage
format mixes both freely: an image inside a paragraph is a block for Plate.

Conversion therefore works in two steps. Each element converter returns a
flat list of nodes, inline and block mixed. :meth:`Converter.group` then
wraps every run of inline nodes into a block, which splits a paragraph
around an image without any converter having to care.

Converters are registered by tag (:func:`element`) or by macro name
(:func:`macro`), so supporting a new construct means adding one function.
"""

from collections.abc import Callable
from confluence_plone import _types as t
from confluence_plone.converter.context import ConversionContext
from confluence_plone.converter.storage import attr
from confluence_plone.converter.storage import tag_name
from confluence_plone.converter.storage import text_content
from dataclasses import dataclass
from dataclasses import field
from lxml import etree
from typing import Any

import re


Marks = dict[str, Any]
"""Text marks, for example ``{"bold": True}``."""

ElementConverter = Callable[["Converter", etree._Element, Marks], list[t.PlateNode]]
MacroConverter = Callable[["Converter", "Macro", Marks], list[t.PlateNode]]

ELEMENTS: dict[str, ElementConverter] = {}
"""Element converters by tag, for example ``p`` or ``ac:link``."""
MACROS: dict[str, MacroConverter] = {}
"""Macro converters by macro name, for example ``info``."""

INLINE_TYPES = frozenset({"a", "mention", "date"})
"""Plate element types that live inside a block."""

BREAK = "_break"
"""Key marking a text leaf created by ``<br>``, so its newline is kept."""

_SPACES = re.compile(r"\s+")


def element(*names: str) -> Callable[[ElementConverter], ElementConverter]:
    """Register a converter for one or more element tags.

    :param names: Tags, for example ``strong`` or ``ac:link``.
    :returns: The decorator.
    """

    def decorator(func: ElementConverter) -> ElementConverter:
        for name in names:
            ELEMENTS[name] = func
        return func

    return decorator


def macro(*names: str) -> Callable[[MacroConverter], MacroConverter]:
    """Register a converter for one or more macro names.

    :param names: Macro names, for example ``info`` or ``code``.
    :returns: The decorator.
    """

    def decorator(func: MacroConverter) -> MacroConverter:
        for name in names:
            MACROS[name] = func
        return func

    return decorator


@dataclass
class Macro:
    """A macro, read from ``ac:structured-macro`` or ``ac:macro``."""

    name: str
    element: etree._Element
    parameters: dict[str, str] = field(default_factory=dict)
    """Parameter values as text, by name (``""`` for the default one)."""
    parameter_elements: dict[str, etree._Element] = field(default_factory=dict)
    """Parameter elements, for values that hold ``ri:`` references."""
    rich_body: etree._Element | None = None
    plain_body: str | None = None

    @classmethod
    def from_element(cls, el: etree._Element) -> Macro:
        """Read a macro element.

        :param el: An ``ac:structured-macro`` or ``ac:macro`` element.
        :returns: The macro.
        """
        result = cls(name=attr(el, "ac:name").strip().lower(), element=el)
        for child in el:
            match tag_name(child):
                case "ac:parameter":
                    name = attr(child, "ac:name")
                    result.parameters[name] = text_content(child).strip()
                    result.parameter_elements[name] = child
                case "ac:rich-text-body":
                    result.rich_body = child
                case "ac:plain-text-body":
                    result.plain_body = child.text or ""
        return result

    def get(self, *names: str, default: str = "") -> str:
        """Return the first parameter found among ``names``.

        :param names: Parameter names, in order of preference.
        :param default: Returned when none is set.
        :returns: The parameter value.
        """
        for name in names:
            if value := self.parameters.get(name):
                return value
        return default


def leaf(text: str, marks: Marks | None = None) -> t.PlateNode:
    """Return a text leaf.

    :param text: The text.
    :param marks: Marks for the text.
    :returns: The leaf.
    """
    return {"text": text, **(marks or {})}


def node(kind: str, children: list[t.PlateNode] | None = None, **props) -> t.PlateNode:
    """Return an element node.

    :param kind: Plate type, for example ``p``.
    :param children: Child nodes. An element without children gets one empty
        text leaf, as Plate requires.
    :param props: Other properties of the element.
    :returns: The element.
    """
    return {"type": kind, "children": children or [leaf("")], **props}


def is_inline(item: t.PlateNode) -> bool:
    """Whether a node goes inside a block.

    :param item: The node.
    :returns: ``True`` for text leaves and inline elements.
    """
    return "text" in item or item.get("type") in INLINE_TYPES


def _same_marks(first: t.PlateNode, second: t.PlateNode) -> bool:
    """Whether two text leaves carry the same marks.

    :param first: A text leaf.
    :param second: Another text leaf.
    :returns: ``True`` when only the text differs.
    """
    keys = (set(first) | set(second)) - {"text", BREAK}
    return all(first.get(key) == second.get(key) for key in keys)


def _merge_leaves(nodes: list[t.PlateNode]) -> list[t.PlateNode]:
    """Collapse whitespace, and merge neighbouring leaves with the same marks.

    The newline of a ``<br>`` is kept.

    :param nodes: Inline nodes.
    :returns: New inline nodes.
    """
    result: list[t.PlateNode] = []
    for item in nodes:
        if "text" not in item:
            result.append(item)
            continue
        text = item["text"] if item.get(BREAK) else _SPACES.sub(" ", item["text"])
        current = {key: value for key, value in item.items() if key != BREAK}
        current["text"] = text
        previous = result[-1] if result else None
        if (
            previous is not None
            and "text" in previous
            and _same_marks(previous, current)
        ):
            previous["text"] += text
        else:
            result.append(current)
    if result and "text" in result[0]:
        result[0]["text"] = result[0]["text"].lstrip()
    if result and "text" in result[-1]:
        result[-1]["text"] = result[-1]["text"].rstrip()
    return result


def normalize_inline(nodes: list[t.PlateNode]) -> list[t.PlateNode]:
    """Clean a run of inline nodes so it can be the children of a block.

    Whitespace is collapsed as a browser would, leading and trailing
    whitespace is removed, neighbouring leaves with the same marks are
    merged, and empty text leaves are added around inline elements, as Slate
    expects.

    :param nodes: Inline nodes.
    :returns: The children for a block.
    """
    result = _merge_leaves(nodes)
    padded: list[t.PlateNode] = []
    for item in result:
        if "text" in item and not item["text"] and padded:
            continue
        if "text" not in item and (not padded or "text" not in padded[-1]):
            padded.append(leaf(""))
        padded.append(item)
    if not padded or "text" not in padded[-1]:
        padded.append(leaf(""))
    return padded


def has_content(nodes: list[t.PlateNode]) -> bool:
    """Whether a run of inline nodes has something worth a block.

    :param nodes: Inline nodes.
    :returns: ``False`` when the run is only whitespace.
    """
    return any("text" not in item or item["text"].strip() for item in nodes)


def plate_text(nodes: list[t.PlateNode]) -> str:
    """Return the text of Plate nodes, one line per block.

    :param nodes: Plate nodes.
    :returns: The text.
    """
    lines = []
    for item in nodes:
        if "text" in item:
            lines.append(item["text"])
        elif item.get("type") in INLINE_TYPES:
            lines.append(item.get("value") or plate_text(item.get("children", [])))
        else:
            lines.append(plate_text(item.get("children", [])) + "\n")
    return "".join(lines)


class Converter:
    """Convert storage-format elements to Plate nodes.

    :param ctx: The conversion context.
    """

    ctx: ConversionContext
    list_depth: int
    """Nesting level of the list being converted (``0`` outside lists)."""

    def __init__(self, ctx: ConversionContext):
        self.ctx = ctx
        self.list_depth = 0

    def convert(
        self, el: etree._Element, marks: Marks | None = None
    ) -> list[t.PlateNode]:
        """Convert one element, with the converter registered for its tag.

        Elements without a converter are transparent: their content is
        converted, and unknown Confluence elements are reported.

        :param el: The element.
        :param marks: Marks inherited from the enclosing elements.
        :returns: Plate nodes, inline and block mixed.
        """
        marks = marks or {}
        name = tag_name(el)
        if not name:
            return []
        if converter := ELEMENTS.get(name):
            return converter(self, el, marks)
        if name.startswith(("ac:", "ri:", "at:")):
            self.ctx.issue(t.Severity.INFO, "unknown_element", name)
        return self.inline(el, marks)

    def inline(
        self, el: etree._Element, marks: Marks | None = None
    ) -> list[t.PlateNode]:
        """Convert the content of an element: its text and its children.

        :param el: The element.
        :param marks: Marks for the text.
        :returns: Plate nodes, inline and block mixed.
        """
        marks = marks or {}
        result: list[t.PlateNode] = []
        if el.text:
            result.append(leaf(el.text, marks))
        for child in el:
            result.extend(self.convert(child, marks))
            if child.tail:
                result.append(leaf(child.tail, marks))
        return result

    def group(
        self, nodes: list[t.PlateNode], kind: str = "p", **props
    ) -> list[t.PlateNode]:
        """Wrap every run of inline nodes into a block.

        Runs made only of whitespace are dropped.

        :param nodes: Plate nodes, inline and block mixed.
        :param kind: Type of the blocks wrapping the inline runs.
        :param props: Properties of those blocks.
        :returns: Block nodes.
        """
        result: list[t.PlateNode] = []
        run: list[t.PlateNode] = []

        def flush() -> None:
            if has_content(run):
                result.append(node(kind, normalize_inline(run), **props))
            run.clear()

        for item in nodes:
            if is_inline(item):
                run.append(item)
            else:
                flush()
                result.append(item)
        flush()
        return result

    def blocks(
        self, el: etree._Element | None, marks: Marks | None = None
    ) -> list[t.PlateNode]:
        """Convert the content of an element into blocks.

        :param el: The element, or ``None``.
        :param marks: Marks for the text.
        :returns: Block nodes.
        """
        if el is None:
            return []
        return self.group(self.inline(el, marks))

    def macro(self, el: etree._Element, marks: Marks) -> list[t.PlateNode]:
        """Convert a macro with the converter registered for its name.

        :param el: An ``ac:structured-macro`` or ``ac:macro`` element.
        :param marks: Marks inherited from the enclosing elements.
        :returns: Plate nodes.
        """
        data = Macro.from_element(el)
        if converter := MACROS.get(data.name):
            return converter(self, data, marks)
        return MACROS["__unsupported__"](self, data, marks)


def assign_ids(
    nodes: list[t.PlateNode], prefix: str, counter: list[int] | None = None
) -> None:
    """Give every element node a stable id, in place.

    :param nodes: Plate nodes.
    :param prefix: Prefix of the ids, unique per page.
    :param counter: Shared counter, for the recursion.
    """
    counter = counter if counter is not None else [0]
    for item in nodes:
        if "text" in item:
            continue
        counter[0] += 1
        item.setdefault("id", f"{prefix}{counter[0]:04d}")
        assign_ids(item.get("children", []), prefix, counter)
