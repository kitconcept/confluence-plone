"""Stream the objects of ``entities.xml``.

``entities.xml`` is a Hibernate dump: a ``<hibernate-generic>`` root with a
flat list of ``<object class="…">`` elements. Each object has an ``<id>``,
scalar ``<property>`` elements (often in CDATA), ``<property>`` elements that
reference another object by id, and ``<collection>`` elements holding
references. Objects reference each other in any order, so this module only
turns elements into :class:`RawObject` values; resolving the references is
the job of :mod:`confluence_plone.reader.model`.
"""

from collections.abc import Iterator
from confluence_plone import _types as t
from lxml import etree
from typing import BinaryIO


def _ref(element: etree._Element) -> t.Ref | None:
    """Read a reference from a ``<property>`` or ``<element>`` element.

    :param element: An element with a ``class`` attribute and an ``<id>``.
    :returns: The reference, or ``None`` when the element has no ``<id>``.
    """
    id_element = element.find("id")
    if id_element is None:
        return None
    return t.Ref(cls=element.get("class", ""), id=(id_element.text or "").strip())


def parse_object(element: etree._Element) -> t.RawObject:
    """Turn one ``<object>`` element into a :class:`RawObject`.

    :param element: The ``<object>`` element.
    :returns: The raw object.
    """
    id_element = element.find("id")
    object_id = (id_element.text or "").strip() if id_element is not None else ""
    raw = t.RawObject(cls=element.get("class", ""), id=object_id)
    for child in element:
        name = child.get("name")
        if not name:
            continue
        if child.tag == "property":
            value = _ref(child) if child.get("class") else None
            raw.properties[name] = value if value is not None else (child.text or "")
        elif child.tag == "collection":
            refs = [_ref(item) for item in child.iterchildren("element")]
            raw.collections[name] = [ref for ref in refs if ref is not None]
    return raw


def iter_objects(stream: BinaryIO, recover: bool = False) -> Iterator[t.RawObject]:
    """Yield every object of an ``entities.xml`` stream.

    The stream is parsed incrementally, and each element is cleared once
    read, so memory use does not grow with the size of the export.

    :param stream: A binary stream with the content of ``entities.xml``.
    :param recover: Ask the parser to skip over malformed XML instead of
        failing. Content can be lost, so use it only as a fallback.
    :returns: An iterator of raw objects.
    :raises lxml.etree.XMLSyntaxError: When the XML is malformed and
        ``recover`` is false.
    """
    context = etree.iterparse(
        stream,
        events=("end",),
        tag="object",
        huge_tree=True,
        recover=recover,
        resolve_entities=False,
        no_network=True,
    )
    for _, element in context:
        yield parse_object(element)
        element.clear()
        # Drop the references the root keeps to the objects already read
        while element.getprevious() is not None:
            del element.getparent()[0]
