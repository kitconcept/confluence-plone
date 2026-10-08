from . import PLANNED_PATHS
from . import SKIPPED
from confluence_plone import _types as t
from confluence_plone.planner import plan_migration

import pytest


@pytest.fixture
def replan(export, settings, source):
    """Plan the test export again, after changing the settings or the export."""

    def func() -> t.MigrationPlan:
        return plan_migration(export, settings, source.find_attachment)

    return func


class TestPlan:
    def test_paths(self, plan):
        assert [item.path for item in plan.items.values()] == PLANNED_PATHS

    def test_parents_come_first(self, plan):
        seen: set[str] = set()
        for item in plan.items.values():
            assert item.parent_uid is None or item.parent_uid in seen
            seen.add(item.uid)

    @pytest.mark.parametrize(
        "path,portal_type,source_type,position,depth",
        [
            ("/dev", "Workspace", "space", 0, 1),
            ("/dev/home", "WikiPage", "page", 0, 2),
            ("/dev/lost-found", "WikiPage", "page", 1, 2),
            ("/dev/home/diagram.png", "Image", "attachment", 0, 3),
            ("/dev/home/snippets", "WikiPage", "page", 1, 3),
            ("/dev/home/release-notes", "WikiPage", "page", 4, 3),
            ("/dev/home/setup-guide/spec.pdf", "File", "attachment", 0, 4),
        ],
    )
    def test_item(self, plan, path, portal_type, source_type, position, depth):
        item = next(i for i in plan.items.values() if i.path == path)
        assert item.portal_type == portal_type
        assert item.source_type == source_type
        assert item.position == position
        assert item.depth == depth
        assert item.space_key == "DEV"

    def test_children(self, plan):
        home = plan.item_for("100")
        titles = [plan.items[uid].title for uid in home.children]
        assert titles == [
            "diagram.png",
            "Snippets",
            "Setup Guide",
            "Legacy Notes",
            "Release Notes",
        ]

    def test_lookups(self, plan):
        assert plan.pages_by_title[("DEV", "setup guide")] == plan.by_source["101"]
        assert plan.attachments_by_name[("101", "spec.pdf")] == plan.by_source["201"]
        assert plan.item_for("103") is None
        assert plan.item_for(None) is None

    def test_blob_names(self, plan):
        assert plan.item_for("200").blob_name == "attachments/100/200/2"

    def test_skipped(self, plan):
        assert [(s.source_id, s.reason) for s in plan.skipped] == SKIPPED

    def test_issues(self, plan):
        assert [(i.source_id, i.severity, i.code) for i in plan.issues] == [
            ("105", t.Severity.WARNING, "orphan_page"),
            ("202", t.Severity.ERROR, "missing_attachment_file"),
        ]


class TestSettings:
    def test_selected_spaces(self, settings, replan):
        settings.source["spaces"] = ("DEV", "NOPE")
        plan = replan()
        assert {i.space_key for i in plan.items.values()} == {"DEV"}
        assert next((i.source_id, i.code) for i in plan.issues) == (
            "NOPE",
            "space_not_found",
        )
        assert ("12", "space not selected") in [
            (s.source_id, s.reason) for s in plan.skipped
        ]

    def test_include_personal_and_archived(self, settings, replan):
        settings.source["include_personal_spaces"] = True
        settings.source["include_archived_spaces"] = True
        plan = replan()
        workspaces = [i.path for i in plan.items.values() if i.source_type == "space"]
        assert workspaces == ["/arch", "/dev", "/jdoe"]

    def test_base_path(self, settings, replan):
        settings.target["base_path"] = "/wikis/"
        plan = replan()
        assert plan.item_for("100").path == "/wikis/dev/home"

    def test_types(self, settings, replan):
        settings.target["page_type"] = "Document"
        settings.target["image_media_types"] = ()
        plan = replan()
        assert plan.item_for("100").portal_type == "Document"
        assert plan.item_for("200").portal_type == "File"


class TestEdgeCases:
    def test_duplicate_titles(self, export, replan):
        export.pages["108"].title = "Snippets"
        plan = replan()
        assert plan.item_for("108").path == "/dev/home/snippets-1"
        # The first page with a title wins the title lookup
        assert plan.pages_by_title[("DEV", "snippets")] == plan.by_source["102"]

    def test_untitled_page(self, export, replan):
        export.pages["108"].title = "???"
        assert replan().item_for("108").id == "page-108"

    def test_space_without_name(self, export, replan):
        export.spaces["10"].name = ""
        export.spaces["10"].key = "!!"
        workspace = replan().item_for("space:10")
        assert workspace.title == "!!"
        assert workspace.id == "space-10"

    def test_cycle(self, export, replan):
        export.pages["102"].parent_id = "108"
        export.pages["108"].parent_id = "102"
        plan = replan()
        assert plan.item_for("102").path == "/dev/snippets"
        assert plan.item_for("108").path == "/dev/snippets/legacy-notes"
        assert [i.code for i in plan.issues].count("page_cycle") == 1

    def test_position_and_home_order(self, export, replan):
        export.pages["105"].parent_id = None
        export.pages["105"].position = 0
        plan = replan()
        workspace = plan.item_for("space:10")
        # The home page comes first, whatever the positions
        assert [plan.items[uid].title for uid in workspace.children] == [
            "Home",
            "Lost & Found",
        ]
