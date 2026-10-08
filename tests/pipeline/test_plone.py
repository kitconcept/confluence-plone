from confluence_plone import plone

import pytest
import uuid


class TestBlockId:
    def test_stable_uuid(self):
        value = plone.block_id("abc", "title")
        assert value == plone.block_id("abc", "title")
        assert str(uuid.UUID(value)) == value
        assert value != plone.block_id("abc", "other")


class TestWorkflowFields:
    def test_published(self, plan, settings):
        item = plan.item_for("100")
        fields = plone.workflow_fields(item, settings, "c", "m", "jdoe", "asmith")
        assert fields == {
            "review_state": "published",
            "effective": "m",
            "workflow_history": {
                "simple_intranet_workflow": [
                    {
                        "action": None,
                        "actor": "jdoe",
                        "comments": "",
                        "review_state": "private",
                        "time": "c",
                    },
                    {
                        "action": "publish",
                        "actor": "asmith",
                        "comments": "Migrated from Confluence",
                        "review_state": "published",
                        "time": "m",
                    },
                ]
            },
        }

    @pytest.mark.parametrize("state", ["private", "internal"])
    def test_other_states(self, plan, settings, state):
        settings.target["review_state"] = state
        settings.target["initial_state"] = "internal"
        fields = plone.workflow_fields(
            plan.item_for("100"), settings, "c", "m", "a", "b"
        )
        assert fields["review_state"] == state
        assert "effective" not in fields
        assert len(fields["workflow_history"]["simple_intranet_workflow"]) == (
            1 if state == "internal" else 2
        )

    def test_without_workflow(self, plan, settings):
        fields = plone.workflow_fields(
            plan.item_for("200"), settings, "c", "m", "a", "b"
        )
        assert fields == {"review_state": None, "workflow_history": {}}


class TestBasePayload:
    def test_payload(self, plan, settings):
        item = plan.item_for("100")
        data = plone.base_payload(
            item, settings, "c", "m", "jdoe", "jdoe", "desc", ["tag"]
        )
        assert {
            k: data[k] for k in ("@id", "@type", "UID", "id", "title", "description")
        } == {
            "@id": "/dev/home",
            "@type": "WikiPage",
            "UID": item.uid,
            "id": "home",
            "title": "Home",
            "description": "desc",
        }
        assert data["creators"] == ["jdoe"]
        assert data["contributors"] == []
        assert data["subjects"] == ["tag"]
        assert data["is_folderish"] is True

    def test_contributors_and_files(self, plan, settings):
        data = plone.base_payload(
            plan.item_for("200"), settings, "c", "m", "jdoe", "asmith"
        )
        assert data["contributors"] == ["asmith"]
        assert data["subjects"] == []
        assert data["is_folderish"] is False


class TestBlocks:
    def test_workspace(self, plan):
        item = plan.item_for("space:10")
        blocks = plone.workspace_blocks(item)
        title_id = plone.block_id(item.uid, "title")
        assert blocks == {
            "blocks": {title_id: {"@type": "title"}},
            "blocks_layout": {"items": [title_id]},
        }

    def test_wiki_page(self, plan):
        item = plan.item_for("100")
        blocks = plone.wiki_page_blocks(item, [{"type": "p"}], {"d": {}})
        somersault = blocks["blocks"]["__somersault__"]
        assert somersault == {
            "@type": "__somersault__",
            "value": [{"type": "p"}],
            "discussions": {"d": {}},
        }
        assert blocks["blocks_layout"]["items"] == [plone.block_id(item.uid, "title")]

    def test_wiki_page_without_discussions(self, plan):
        blocks = plone.wiki_page_blocks(plan.item_for("100"), [], {})
        assert "discussions" not in blocks["blocks"]["__somersault__"]

    def test_blob_field(self, plan):
        item = plan.item_for("200")
        assert plone.blob_field(item, "image", "d.png", "image/png", 3) == {
            "image": {
                "blob_path": f"{item.uid}/image/d.png",
                "content-type": "image/png",
                "filename": "d.png",
                "size": 3,
            }
        }
