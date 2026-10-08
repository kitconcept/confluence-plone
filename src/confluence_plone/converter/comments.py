"""Convert Confluence comments.

Footer comments become ``plone.app.discussion`` comments, imported by
``plone.exportimport`` from ``discussions.json``, with their threading.

Inline comments become discussions of the Wiki Page: they are stored in the
``__somersault__`` block, next to the value, and the commented text carries
a ``comment_<discussion id>`` mark. The discussion id is the marker
reference Confluence uses (``ac:inline-comment-marker ac:ref``), so the mark
and the discussion meet without a lookup table. An inline comment whose
marker is no longer in the page becomes a footer comment instead, so it is
not lost.
"""

from confluence_plone import _types as t
from confluence_plone.converter import body_text
from confluence_plone.converter import convert_body
from confluence_plone.converter.context import ConversionContext
from confluence_plone.converter.core import assign_ids
from confluence_plone.converter.core import leaf
from confluence_plone.converter.core import node
from confluence_plone.utils.dates import to_iso
from confluence_plone.utils.dates import to_js_iso

import zlib


def page_comments(ctx: ConversionContext) -> list[t.Comment]:
    """Return the current comments of the page, oldest first.

    :param ctx: The conversion context, for the page.
    :returns: The comments.
    """
    comments = [
        comment
        for comment in ctx.export.comments.values()
        if comment.container_id == ctx.page.id and comment.is_current
    ]
    return sorted(
        comments, key=lambda c: (c.created, int(c.id) if c.id.isdigit() else 0, c.id)
    )


def _root(comment: t.Comment, comments: dict[str, t.Comment]) -> t.Comment:
    """Return the first comment of a thread.

    :param comment: A comment.
    :param comments: The comments of the page, by id.
    :returns: The comment at the top of its thread.
    """
    seen = {comment.id}
    while comment.parent_id in comments and comment.parent_id not in seen:
        comment = comments[comment.parent_id]
        seen.add(comment.id)
    return comment


def _comment_id(comment: t.Comment) -> int:
    """Return a numeric id for a comment, as ``plone.app.discussion`` needs.

    :param comment: The comment.
    :returns: The Confluence id when it is numeric, a checksum otherwise.
    """
    return int(comment.id) if comment.id.isdigit() else zlib.crc32(comment.id.encode())


def inline_discussions(
    ctx: ConversionContext, comments: list[t.Comment]
) -> tuple[dict[str, dict], list[t.Comment]]:
    """Convert inline comments to Wiki Page discussions.

    :param ctx: The conversion context, after the page body was converted.
    :param comments: The comments of the page.
    :returns: The discussions by id, and the comments that stay footer
        comments.
    """
    by_id = {comment.id: comment for comment in comments}
    discussions: dict[str, dict] = {}
    footer: list[t.Comment] = []
    enabled = ctx.settings.content["inline_comments"]
    for comment in comments:
        root = _root(comment, by_id)
        ref = root.inline_ref
        if not root.is_inline:
            footer.append(comment)
            continue
        if not enabled or ref not in ctx.inline_refs:
            if comment is root:
                ctx.issue(
                    t.Severity.INFO,
                    "inline_comment_as_footer",
                    root.properties.get("inline-original-selection", ""),
                )
            footer.append(comment)
            continue
        assert ref is not None  # noQA: S101
        user_id = ctx.principals.principal(comment.creator)
        created = to_js_iso(comment.created, ctx.settings.config["timezone"]) or ""
        content = convert_body(ctx, ctx.export.bodies.get(comment.id)) or [
            node("p", [leaf("")])
        ]
        assign_ids(content, f"d{comment.id}-")
        discussion = discussions.setdefault(
            ref,
            {
                "comments": [],
                "createdAt": created,
                "documentContent": root.properties.get("inline-original-selection", ""),
                "id": ref,
                "isResolved": root.is_resolved,
                "userId": user_id,
            },
        )
        discussion["comments"].append({
            "contentRich": content,
            "createdAt": created,
            "discussionId": ref,
            "id": f"c{comment.id}",
            "isEdited": comment.version > 1,
            "userId": user_id,
        })
    return discussions, footer


def footer_comments(ctx: ConversionContext, comments: list[t.Comment]) -> list[dict]:
    """Convert footer comments to ``discussions.json`` items.

    :param ctx: The conversion context, for the page.
    :param comments: The comments, oldest first.
    :returns: The conversation items.
    """
    timezone = ctx.settings.config["timezone"]
    path = ctx.item.path
    ids = {comment.id for comment in comments}
    result = []
    for comment in comments:
        comment_id = _comment_id(comment)
        parent = ctx.export.comments.get(comment.parent_id or "")
        in_reply_to = str(_comment_id(parent)) if parent and parent.id in ids else None
        created = to_iso(comment.created, timezone)
        result.append({
            "@id": f"{path}/@comments/{comment_id}",
            "@parent": f"{path}/@comments/{in_reply_to}" if in_reply_to else None,
            "@type": "Discussion Item",
            "author_name": ctx.principals.title(comment.creator),
            "author_username": ctx.principals.principal(comment.creator),
            "comment_id": str(comment_id),
            "creation_date": created,
            "in_reply_to": in_reply_to,
            "modification_date": to_iso(comment.modified, timezone) or created,
            "text": {
                "data": body_text(ctx, ctx.export.bodies.get(comment.id)),
                "mime-type": "text/plain",
            },
            "user_notification": None,
        })
    return result
