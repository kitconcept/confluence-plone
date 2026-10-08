from confluence_plone.converter.storage import attr
from confluence_plone.converter.storage import find
from confluence_plone.converter.storage import find_deep
from confluence_plone.converter.storage import parse_storage
from confluence_plone.converter.storage import plain_text
from confluence_plone.converter.storage import tag_name
from confluence_plone.converter.storage import text_content
from lxml import etree

import pytest


class TestParseStorage:
    def test_fragment(self):
        root = parse_storage("<p>one</p><p>two</p>")
        assert [tag_name(child) for child in root] == ["p", "p"]

    def test_namespaces(self):
        root = parse_storage('<ac:link><ri:page ri:content-title="Home" /></ac:link>')
        link = root[0]
        assert tag_name(link) == "ac:link"
        assert attr(link[0], "ri:content-title") == "Home"

    @pytest.mark.parametrize(
        "body,expected",
        [
            ("<p>a&nbsp;b</p>", "a\u00a0b"),
            ("<p>&mdash;&amp;&lt;</p>", "—&<"),
            ("<p>&unknownentity;</p>", "&unknownentity;"),
        ],
    )
    def test_entities(self, body, expected):
        assert text_content(parse_storage(body)) == expected

    def test_recovers_broken_markup(self):
        root = parse_storage("<p>open <strong>bold</p>")
        assert "bold" in text_content(root)

    def test_cdata(self):
        root = parse_storage(
            "<ac:plain-text-body><![CDATA[a < b]]></ac:plain-text-body>"
        )
        assert root[0].text == "a < b"

    def test_empty(self):
        assert len(parse_storage("")) == 0

    def test_unparsable(self, monkeypatch):
        monkeypatch.setattr(etree, "fromstring", lambda *args, **kwargs: None)
        assert parse_storage("<p>x</p>").tag == "root"


class TestTagName:
    def test_comment(self):
        root = parse_storage("<!-- note --><p>x</p>")
        assert tag_name(root[0]) == ""
        assert tag_name(root[1]) == "p"

    def test_unknown_namespace(self):
        element = etree.fromstring('<x:a xmlns:x="urn:other"/>')
        assert tag_name(element) == "a"

    def test_upper_case(self):
        assert tag_name(etree.fromstring("<P/>")) == "p"


class TestAttr:
    def test_plain_and_default(self):
        element = etree.fromstring('<a href="x"/>')
        assert attr(element, "href") == "x"
        assert attr(element, "title", "none") == "none"


class TestFind:
    def test_find(self):
        root = parse_storage(
            "<ac:link><ac:link-body>x</ac:link-body>"
            '<ri:page ri:content-title="A"/></ac:link>'
        )
        assert tag_name(find(root[0], "ri:page")) == "ri:page"
        assert find(root[0], "ri:user") is None

    def test_find_deep(self):
        root = parse_storage(
            "<ac:parameter><ac:link>"
            '<ri:page ri:content-title="A"/></ac:link></ac:parameter>'
        )
        param = root[0]
        assert find(param, "ri:page") is None
        assert attr(find_deep(param, "ri:page"), "ri:content-title") == "A"
        assert find_deep(param, "ac:parameter") is None


class TestPlainText:
    def test_plain_text(self):
        assert (
            plain_text("<p>Hello   <b>World</b></p>\n<p>again</p>")
            == "Hello World again"
        )
