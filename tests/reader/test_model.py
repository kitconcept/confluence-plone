from . import PAGE_IDS
from . import USER_KEYS
from confluence_plone import _types as t
from confluence_plone.reader.model import build_export

import pytest


class TestExportModel:
    def test_spaces(self, export):
        assert {space.key for space in export.spaces.values()} == {
            "DEV",
            "ARCH",
            "~jdoe",
        }

    @pytest.mark.parametrize(
        "attr,expected",
        [
            ("key", "DEV"),
            ("name", "Development"),
            ("status", "CURRENT"),
            ("space_type", "global"),
            ("description_id", "50"),
            ("home_page_id", "100"),
            ("created", "2024-01-10 09:00:00.000"),
            ("creator", "u1"),
        ],
    )
    def test_space(self, export, attr, expected):
        assert getattr(export.spaces["10"], attr) == expected

    def test_pages(self, export):
        assert set(export.pages) == PAGE_IDS

    @pytest.mark.parametrize(
        "page_id,attr,expected",
        [
            ("100", "title", "Home"),
            ("100", "version", 3),
            ("100", "creator", "u1"),
            ("100", "last_modifier", "u2"),
            ("100", "position", 0),
            ("100", "is_current", True),
            ("101", "parent_id", "100"),
            ("101", "creator", "asmith"),
            ("102", "parent_id", "100"),
            ("103", "status", "draft"),
            ("103", "is_current", False),
            ("103", "position", None),
            ("104", "original_id", "100"),
            ("104", "is_historical", True),
            ("104", "is_current", False),
            ("106", "kind", "blogpost"),
        ],
    )
    def test_page(self, export, page_id, attr, expected):
        assert getattr(export.pages[page_id], attr) == expected

    def test_newest_body_wins(self, export):
        body = export.bodies["100"]
        assert body.id == "500"
        assert body.body.startswith("<h1>Welcome</h1>")

    def test_wiki_markup_body(self, export):
        assert export.bodies["108"].body_type == 1

    def test_space_description_body(self, export):
        assert "developers" in export.bodies["50"].body

    @pytest.mark.parametrize(
        "attachment_id,attr,expected",
        [
            # From ContentProperty objects, linked from either side
            ("200", "media_type", "image/png"),
            ("200", "file_size", 68),
            ("200", "container_id", "100"),
            # From properties of the attachment (old exports)
            ("201", "media_type", "application/pdf"),
            ("201", "file_size", 25),
            ("202", "media_type", "application/octet-stream"),
            ("203", "is_historical", True),
            ("204", "status", "deleted"),
        ],
    )
    def test_attachment(self, export, attachment_id, attr, expected):
        assert getattr(export.attachments[attachment_id], attr) == expected

    @pytest.mark.parametrize(
        "comment_id,inline,ref,parent_id",
        [
            ("300", False, None, None),
            ("301", False, None, "300"),
            ("302", True, "ref-1", None),
            ("303", False, None, "302"),
            ("304", True, "ref-gone", None),
        ],
    )
    def test_comment(self, export, comment_id, inline, ref, parent_id):
        comment = export.comments[comment_id]
        assert comment.is_inline is inline
        assert comment.inline_ref == ref
        assert comment.parent_id == parent_id
        assert comment.container_id == "100"

    def test_users(self, export):
        assert set(export.users) == USER_KEYS

    @pytest.mark.parametrize(
        "key,name,email,title",
        [
            ("u1", "jdoe", "john@example.org", "John Doe"),
            ("u2", "asmith", "anna@example.org", "asmith"),
            ("legacy", "legacy", "", "Legacy User"),
        ],
    )
    def test_user(self, export, key, name, email, title):
        user = export.users[key]
        assert (user.name, user.email, user.title) == (name, email, title)

    def test_labels(self, export):
        assert export.labels["100"] == [("global", "howto"), ("my", "favourite")]

    def test_restrictions(self, export):
        assert export.restrictions == {"101": {"View"}}

    def test_space_permissions(self, export):
        assert export.space_permissions["10"] == 2

    def test_classes(self, export):
        assert export.classes["Page"] == 10
        assert export.classes["BlogPost"] == 1
        assert export.classes["OutgoingLink"] == 1


class TestExportUser:
    @pytest.mark.parametrize(
        "value,expected",
        [
            ("u1", "u1"),
            ("jdoe", "u1"),
            ("JDoe", "u1"),
            ("nobody", None),
            ("", None),
            (None, None),
        ],
    )
    def test_user(self, export, value, expected):
        user = export.user(value)
        assert (user.key if user else None) == expected


class TestBuildExport:
    def test_minimal_objects(self):
        objects = [
            t.RawObject("Space", "1", {"key": "K", "name": "N", "spaceStatus": " "}),
            t.RawObject("BodyContent", "2", {}),
            t.RawObject("Labelling", "3", {"labelableId": "5"}),
            t.RawObject("ContentPermissionSet", "4", {}),
            t.RawObject("SpacePermission", "5", {}),
            t.RawObject("Comment", "6", {"version": "x"}),
            t.RawObject("Unknown", "7", {}),
        ]
        export = build_export(objects)
        assert export.spaces["1"].status == "CURRENT"
        assert export.bodies == {}
        assert export.labels == {}
        assert export.restrictions == {}
        assert export.space_permissions == {}
        assert export.comments["6"].version == 1
        assert export.classes["Unknown"] == 1

    def test_properties(self):
        attachment = t.Ref("Attachment", "1")
        objects = [
            t.RawObject("Attachment", "1", {"title": "a.txt"}),
            t.RawObject(
                "ContentProperty",
                "2",
                {"name": "HIDDEN", "stringValue": "true", "content": attachment},
            ),
            # A property nothing points to, and that points to nothing
            t.RawObject("ContentProperty", "3", {"name": "lost", "stringValue": "x"}),
        ]
        export = build_export(objects)
        result = export.attachments["1"]
        assert result.properties == {"HIDDEN": "true"}
        assert result.media_type == "application/octet-stream"
        assert result.file_size == 0

    def test_restriction_type_defaults_to_view(self):
        ref = t.Ref("Page", "9")
        export = build_export([
            t.RawObject("ContentPermissionSet", "1", {"owningContent": ref})
        ])
        assert export.restrictions == {"9": {"View"}}
