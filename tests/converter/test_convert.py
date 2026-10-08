from confluence_plone import _types as t
from confluence_plone.converter import body_text
from confluence_plone.converter import convert_body
from confluence_plone.converter import convert_page
from confluence_plone.converter.core import leaf
from confluence_plone.converter.core import node

import pytest


class TestConvertBody:
    @pytest.mark.parametrize(
        "body,body_type,expected",
        [
            ("<p>storage</p>", 2, [node("p", [leaf("storage")])]),
            (
                "line 1\n\nline 2",
                0,
                [node("p", [leaf("line 1")]), node("p", [leaf("line 2")])],
            ),
            ("h1. Title", 1, [node("p", [leaf("h1. Title")])]),
        ],
    )
    def test_body_types(self, make_context, body, body_type, expected):
        ctx = make_context()
        content = t.BodyContent(
            id="1", content_id="100", body=body, body_type=body_type
        )
        assert convert_body(ctx, content) == expected

    def test_wiki_markup_is_reported(self, make_context, issue_codes):
        ctx = make_context()
        convert_body(
            ctx, t.BodyContent(id="1", content_id="100", body="x", body_type=1)
        )
        assert issue_codes(ctx) == ["wiki_markup"]

    def test_no_body(self, make_context):
        assert convert_body(make_context(), None) == []

    def test_body_text(self, make_context):
        ctx = make_context()
        content = t.BodyContent(id="1", content_id="100", body="<p>one</p><p>two</p>")
        assert body_text(ctx, content) == "one\ntwo"


class TestConvertPage:
    @pytest.fixture
    def value(self, make_context):
        return convert_page(make_context("100"))

    def test_title_first(self, value):
        assert value[0] == {
            "type": "title",
            "children": [{"text": "Home"}],
            "blockWidth": "default",
            "id": "c100-0001",
        }

    def test_block_types(self, value):
        assert [block["type"] for block in value] == [
            "title",
            "h1",
            "p",
            "ploneBlock",
            "p",
            "callout",
            "p",
            "p",
            "p",
            "p",
        ]

    def test_top_level_blocks_have_width_and_id(self, value):
        assert all(block["blockWidth"] == "default" for block in value)
        assert len({block["id"] for block in value}) == len(value)

    def test_issues(self, make_context, issue_codes):
        ctx = make_context("100")
        convert_page(ctx)
        assert issue_codes(ctx) == ["static_page_list"]
        assert ctx.inline_refs == ["ref-1"]

    def test_page_without_body(self, make_context):
        value = convert_page(make_context("110"))
        assert [block["type"] for block in value] == ["title"]
