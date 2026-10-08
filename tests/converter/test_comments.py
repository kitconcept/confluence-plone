from confluence_plone import _types as t
from confluence_plone.converter import convert_page
from confluence_plone.converter.comments import _comment_id
from confluence_plone.converter.comments import _root
from confluence_plone.converter.comments import footer_comments
from confluence_plone.converter.comments import inline_discussions
from confluence_plone.converter.comments import page_comments

import pytest


@pytest.fixture
def ctx(make_context):
    """Context for the home page, after its body was converted."""
    value = make_context("100")
    convert_page(value)
    return value


class TestPageComments:
    def test_order(self, ctx):
        assert [c.id for c in page_comments(ctx)] == ["300", "301", "302", "303", "304"]

    def test_other_page(self, make_context):
        assert page_comments(make_context("101")) == []


class TestInlineDiscussions:
    def test_discussions(self, ctx):
        discussions, footer = inline_discussions(ctx, page_comments(ctx))
        assert [c.id for c in footer] == ["300", "301", "304"]
        discussion = discussions["ref-1"]
        assert discussion["id"] == "ref-1"
        assert discussion["documentContent"] == "important part"
        assert discussion["isResolved"] is False
        assert discussion["userId"] == "asmith"
        assert discussion["createdAt"] == "2024-01-16T08:00:00.250Z"
        comments = discussion["comments"]
        assert [c["id"] for c in comments] == ["c302", "c303"]
        assert [c["userId"] for c in comments] == ["asmith", "jdoe"]
        assert [c["isEdited"] for c in comments] == [True, False]
        assert comments[1]["contentRich"][0]["children"] == [{"text": "Yes."}]
        assert comments[0]["contentRich"][0]["id"] == "d302-0001"

    def test_missing_marker_becomes_footer(self, ctx):
        inline_discussions(ctx, page_comments(ctx))
        issues = [(i.code, i.detail) for i in ctx.issues]
        assert ("inline_comment_as_footer", "text that was removed") in issues

    def test_disabled(self, ctx, settings):
        settings.content["inline_comments"] = False
        discussions, footer = inline_discussions(ctx, page_comments(ctx))
        assert discussions == {}
        assert len(footer) == 5

    def test_comment_without_body(self, ctx, export):
        del export.bodies["302"]
        discussions, _ = inline_discussions(ctx, page_comments(ctx))
        assert discussions["ref-1"]["comments"][0]["contentRich"][0]["children"] == [
            {"text": ""}
        ]

    def test_resolved(self, ctx, export):
        export.comments["302"].properties["status"] = "resolved"
        discussions, _ = inline_discussions(ctx, page_comments(ctx))
        assert discussions["ref-1"]["isResolved"] is True


class TestFooterComments:
    def test_items(self, ctx):
        _, footer = inline_discussions(ctx, page_comments(ctx))
        items = footer_comments(ctx, footer)
        assert [item["comment_id"] for item in items] == ["300", "301", "304"]
        first, reply, _ = items
        assert first == {
            "@id": "/dev/home/@comments/300",
            "@parent": None,
            "@type": "Discussion Item",
            "author_name": "John Doe",
            "author_username": "jdoe",
            "comment_id": "300",
            "creation_date": "2024-01-15T08:00:00+00:00",
            "in_reply_to": None,
            "modification_date": "2024-01-15T08:00:00+00:00",
            "text": {"data": "Great page!", "mime-type": "text/plain"},
            "user_notification": None,
        }
        assert reply["in_reply_to"] == "300"
        assert reply["@parent"] == "/dev/home/@comments/300"
        assert reply["text"]["data"] == "Thanks, John."
        # No modification date: the creation date is used
        assert reply["modification_date"] == "2024-01-15T09:00:00+00:00"

    def test_reply_to_comment_not_converted(self, ctx):
        comments = page_comments(ctx)
        reply = next(c for c in comments if c.id == "301")
        items = footer_comments(ctx, [reply])
        assert items[0]["in_reply_to"] is None


class TestHelpers:
    @pytest.mark.parametrize(
        "comment_id,expected",
        [("300", 300), ("abc", 891568578)],
    )
    def test_comment_id(self, comment_id, expected):
        assert _comment_id(t.Comment(id=comment_id)) == expected

    def test_root_stops_at_cycles(self):
        first = t.Comment(id="1", parent_id="2")
        second = t.Comment(id="2", parent_id="1")
        comments = {"1": first, "2": second}
        assert _root(first, comments) is second
