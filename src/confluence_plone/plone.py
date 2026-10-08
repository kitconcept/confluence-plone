"""Build the ``data.json`` payloads, in the ``plone.exportimport`` format."""

from confluence_plone import _types as t
from confluence_plone.utils.ids import make_uid
from typing import Any

import uuid


SOMERSAULT_KEY = "__somersault__"
"""Key of the block holding the Plate value of a Wiki Page."""


def block_id(uid: str, name: str) -> str:
    """Return a stable Volto block id for an item.

    :param uid: UID of the item.
    :param name: Name of the block within the item.
    :returns: A UUID string, as Volto writes block ids.
    """
    return str(uuid.UUID(make_uid(name, uid)))


def workflow_fields(
    item: t.PlannedItem,
    settings: t.ConfluenceSettings,
    created: str | None,
    modified: str | None,
    creator: str,
    modifier: str,
) -> dict[str, Any]:
    """Return the review state, workflow history and effective date of an item.

    The history starts in the initial state, at the creation date, and moves
    to the configured state at the modification date, so the dates survive
    the import.

    :param item: The planned item.
    :param settings: The settings.
    :param created: Creation date.
    :param modified: Modification date.
    :param creator: Principal that created the content.
    :param modifier: Principal that last modified the content.
    :returns: Fields for the payload.
    """
    target = settings.target
    if item.portal_type in target["types_without_workflow"]:
        return {"review_state": None, "workflow_history": {}}
    review_state = target["review_state"]
    history = [
        {
            "action": None,
            "actor": creator,
            "comments": "",
            "review_state": target["initial_state"],
            "time": created,
        }
    ]
    if review_state != target["initial_state"]:
        history.append({
            "action": "publish",
            "actor": modifier,
            "comments": "Migrated from Confluence",
            "review_state": review_state,
            "time": modified,
        })
    fields: dict[str, Any] = {
        "review_state": review_state,
        "workflow_history": {target["workflow"]: history},
    }
    if review_state == "published":
        fields["effective"] = modified
    return fields


def base_payload(
    item: t.PlannedItem,
    settings: t.ConfluenceSettings,
    created: str | None,
    modified: str | None,
    creator: str,
    modifier: str,
    description: str = "",
    subjects: list[str] | None = None,
) -> t.PloneItem:
    """Return the fields shared by every item.

    :param item: The planned item.
    :param settings: The settings.
    :param created: Creation date.
    :param modified: Modification date.
    :param creator: Principal that created the content.
    :param modifier: Principal that last modified the content.
    :param description: Description of the item.
    :param subjects: Tags of the item.
    :returns: The payload.
    """
    contributors = [modifier] if modifier != creator else []
    return {
        "@id": item.path,
        "@type": item.portal_type,
        "UID": item.uid,
        "id": item.id,
        "title": item.title,
        "description": description,
        "created": created,
        "modified": modified,
        "creators": [creator],
        "contributors": contributors,
        "subjects": subjects or [],
        "exclude_from_nav": False,
        "allow_discussion": None,
        "is_folderish": item.source_type != "attachment",
        **workflow_fields(item, settings, created, modified, creator, modifier),
    }


def workspace_blocks(item: t.PlannedItem) -> dict[str, Any]:
    """Return the blocks of a workspace: a title block.

    :param item: The planned workspace.
    :returns: The ``blocks`` and ``blocks_layout`` fields.
    """
    title_id = block_id(item.uid, "title")
    return {
        "blocks": {title_id: {"@type": "title"}},
        "blocks_layout": {"items": [title_id]},
    }


def wiki_page_blocks(
    item: t.PlannedItem, value: list[t.PlateNode], discussions: dict[str, dict]
) -> dict[str, Any]:
    """Return the blocks of a Wiki Page.

    The Plate value lives in the ``__somersault__`` block. The editor also
    needs a ``title`` block listed in ``blocks_layout``: with an empty
    layout, the page opens but the editor fails on save.

    :param item: The planned page.
    :param value: The Plate value.
    :param discussions: Inline comment discussions, by id.
    :returns: The ``blocks`` and ``blocks_layout`` fields.
    """
    title_id = block_id(item.uid, "title")
    somersault: dict[str, Any] = {"@type": SOMERSAULT_KEY, "value": value}
    if discussions:
        somersault["discussions"] = discussions
    return {
        "blocks": {title_id: {"@type": "title"}, SOMERSAULT_KEY: somersault},
        "blocks_layout": {"items": [title_id]},
    }


def blob_field(
    item: t.PlannedItem, field_name: str, filename: str, media_type: str, size: int
) -> dict[str, Any]:
    """Return the file or image field of an attachment.

    :param item: The planned attachment.
    :param field_name: ``file`` or ``image``.
    :param filename: Name of the file.
    :param media_type: Media type of the file.
    :param size: Size of the file in bytes.
    :returns: The field name and its value, as a one-key dictionary.
    """
    return {
        field_name: {
            "blob_path": f"{item.uid}/{field_name}/{filename}",
            "content-type": media_type,
            "filename": filename,
            "size": size,
        }
    }
