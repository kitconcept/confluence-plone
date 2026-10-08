from confluence_plone import _types as t
from confluence_plone.reader.entities import iter_objects
from confluence_plone.reader.entities import parse_object
from lxml import etree

import io
import pytest


OBJECT = b"""<object class="Page" package="com.atlassian.confluence.pages">
  <id name="id">100</id>
  <property name="title"><![CDATA[Home]]></property>
  <property name="empty"/>
  <property name="space" class="Space" package="x"><id name="id">10</id></property>
  <property name="broken" class="Space" package="x"></property>
  <collection name="children" class="java.util.List">
    <element class="Page" package="x"><id name="id">101</id></element>
    <element class="Page" package="x"></element>
  </collection>
  <unnamed>ignored</unnamed>
</object>"""


class TestParseObject:
    @pytest.fixture
    def raw(self) -> t.RawObject:
        return parse_object(etree.fromstring(OBJECT))

    def test_class_and_id(self, raw):
        assert raw.cls == "Page"
        assert raw.id == "100"

    @pytest.mark.parametrize(
        "name,expected",
        [
            ("title", "Home"),
            ("empty", ""),
            ("space", t.Ref("Space", "10")),
            ("broken", ""),
        ],
    )
    def test_properties(self, raw, name, expected):
        assert raw.properties[name] == expected

    def test_collections(self, raw):
        assert raw.collections["children"] == [t.Ref("Page", "101")]

    def test_without_id(self):
        raw = parse_object(etree.fromstring(b'<object class="X"/>'))
        assert raw.id == ""


class TestIterObjects:
    def test_iter(self):
        data = (
            b"<hibernate-generic>"
            + OBJECT
            + OBJECT.replace(b"100", b"200")
            + b"</hibernate-generic>"
        )
        objects = list(iter_objects(io.BytesIO(data)))
        assert [raw.id for raw in objects] == ["100", "200"]

    def test_malformed(self):
        data = (
            b"<hibernate-generic><object class='A'><id name='id'>1</id></object><object"
        )
        with pytest.raises(etree.XMLSyntaxError):
            list(iter_objects(io.BytesIO(data)))

    def test_recover(self):
        data = (
            b"<hibernate-generic><object class='A'><id name='id'>1</id></object><object"
        )
        objects = list(iter_objects(io.BytesIO(data), recover=True))
        assert objects[0].id == "1"
