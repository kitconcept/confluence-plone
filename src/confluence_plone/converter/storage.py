"""Parse the Confluence storage format.

The storage format is XHTML with Confluence elements in the ``ac:`` and
``ri:`` namespaces, but a body is a fragment: it has no root element, no
namespace declarations, and it uses HTML named entities (``&nbsp;``) that
XML does not define. This module wraps the fragment in a root element that
declares the namespaces, turns named entities into numeric ones, and parses
it with a recovering parser, so broken markup loses as little as possible.
"""

from html.entities import name2codepoint
from lxml import etree

import re


NAMESPACES = {
    "ac": "http://atlassian.com/content",
    "ri": "http://atlassian.com/resource/identifier",
    "at": "http://atlassian.com/template",
}
_PREFIXES = {uri: prefix for prefix, uri in NAMESPACES.items()}
_XML_ENTITIES = {"amp", "lt", "gt", "quot", "apos"}
_ENTITY = re.compile(r"&([A-Za-z][A-Za-z0-9]*);")


def _numeric_entity(match: re.Match) -> str:
    """Replace an HTML named entity by a numeric one.

    :param match: The match of ``&name;``.
    :returns: The replacement.
    """
    name = match.group(1)
    if name in _XML_ENTITIES:
        return match.group(0)
    codepoint = name2codepoint.get(name)
    return f"&#{codepoint};" if codepoint else f"&amp;{name};"


def parse_storage(body: str) -> etree._Element:
    """Parse a body in storage format.

    :param body: The body, as stored in ``BodyContent``.
    :returns: A ``root`` element holding the content of the body.
    """
    declarations = " ".join(
        f'xmlns:{prefix}="{uri}"' for prefix, uri in NAMESPACES.items()
    )
    text = _ENTITY.sub(_numeric_entity, body)
    wrapped = f"<root {declarations}>{text}</root>"
    parser = etree.XMLParser(
        recover=True,
        huge_tree=True,
        resolve_entities=False,
        no_network=True,
        strip_cdata=True,
    )
    root = etree.fromstring(wrapped.encode("utf-8"), parser)
    return root if root is not None else etree.Element("root")


def tag_name(element: etree._Element) -> str:
    """Return the tag of an element, with the ``ac:`` / ``ri:`` prefix.

    :param element: The element.
    :returns: For example ``p``, ``ac:structured-macro`` or ``ri:page``. An
        empty string for comments and processing instructions.
    """
    tag = element.tag
    if not isinstance(tag, str):
        return ""
    if tag.startswith("{"):
        uri, _, local = tag[1:].partition("}")
        prefix = _PREFIXES.get(uri)
        return f"{prefix}:{local}" if prefix else local
    return tag.lower()


def attr(element: etree._Element, name: str, default: str = "") -> str:
    """Read an attribute, accepting the ``ac:`` / ``ri:`` prefix.

    :param element: The element.
    :param name: Attribute name, for example ``ac:name`` or ``href``.
    :param default: Returned when the attribute is missing.
    :returns: The attribute value.
    """
    prefix, _, local = name.rpartition(":")
    if prefix in NAMESPACES:
        return element.get(f"{{{NAMESPACES[prefix]}}}{local}", default)
    return element.get(name, default)


def find(element: etree._Element, name: str) -> etree._Element | None:
    """Find the first direct child with a given prefixed tag.

    :param element: The parent element.
    :param name: Tag, for example ``ri:page``.
    :returns: The child, or ``None``.
    """
    for child in element:
        if tag_name(child) == name:
            return child
    return None


def find_deep(element: etree._Element, name: str) -> etree._Element | None:
    """Find the first descendant with a given prefixed tag.

    Macro parameters wrap their references in different ways (a bare
    ``ri:page``, or one inside an ``ac:link``), so they are searched deep.

    :param element: The element to search in.
    :param name: Tag, for example ``ri:page``.
    :returns: The descendant, or ``None``.
    """
    for child in element.iter():
        if child is not element and tag_name(child) == name:
            return child
    return None


def text_content(element: etree._Element) -> str:
    """Return all the text inside an element.

    :param element: The element.
    :returns: The text.
    """
    return "".join(str(text) for text in element.itertext())


def plain_text(body: str) -> str:
    """Return the text of a body in storage format, with collapsed spaces.

    :param body: The body.
    :returns: The text.
    """
    return " ".join(text_content(parse_storage(body)).split())
