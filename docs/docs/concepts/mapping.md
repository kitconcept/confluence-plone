---
myst:
  html_meta:
    "description": "How Confluence spaces, pages, attachments, comments, labels, and users map to kitconcept.intranet content."
    "property=og:description": "How Confluence content maps to kitconcept.intranet content"
    "property=og:title": "From Confluence to Plone | confluence-plone"
    "keywords": "confluence-plone, Workspace, Wiki Page, mapping, comments, principals"
---

(concepts-mapping)=

# From Confluence to Plone

This page describes what each kind of Confluence content becomes.
{doc}`/reference/conversion` covers the content of a page, element by element.

| Confluence | Plone | Notes |
| --- | --- | --- |
| Space | Workspace | One per selected space, inside `base_path`. |
| Page | Wiki Page | Keeps its place in the page tree. |
| Attachment | Image or File | A child of its page. |
| Footer comment | Comment | Imported from `discussions.json`, with replies. |
| Inline comment | Wiki Page discussion | Anchored to the commented text. |
| Label | Tag | Only labels in `label_namespaces`. |
| User | Principal id | Users are not created. |

## Spaces

<!-- source: src/confluence_plone/planner.py, src/confluence_plone/pipeline.py -->

Each space becomes a Workspace.
Its title is the name of the space, its id is the space key in lowercase, and its description is the plain text of the space description.

Personal spaces (keys starting with `~`) and archived spaces are skipped unless the settings include them.
The `spaces` setting limits the conversion to a list of space keys.

## Pages

<!-- source: src/confluence_plone/converter/__init__.py, src/confluence_plone/plone.py -->

Each current page becomes a Wiki Page.
The id comes from the title, and the page tree of the space becomes the folder tree of the Workspace, with the home page first and the other pages in their Confluence order.

The Wiki Page stores its content as a Plate value in a block named `__somersault__`.
The value starts with a `title` node, followed by the converted body.

Drafts, deleted pages, and blog posts are skipped, and listed in `skipped.csv`.

## Attachments

<!-- source: src/confluence_plone/planner.py -->

Each current attachment becomes a child of its page.
Attachments whose media type is in `image_media_types` become Image items; all others become File items.
Only the latest version of the file is kept.

An attachment whose file is missing from the export is reported as an error and skipped.

## Dates, authors, and workflow

<!-- source: src/confluence_plone/plone.py -->

Creation and modification dates, the creator, and the last modifier come from Confluence.
Confluence writes dates without a time zone, so the `timezone` setting says which one they are in.

Every Workspace and Wiki Page ends in the `review_state` of the settings, `published` by default.
Its workflow history starts in `initial_state` at the creation date, and moves to `review_state` at the modification date, so both dates survive the import.
Files and Images have no workflow in `kitconcept.intranet`, so they have no history.

## Comments

<!-- source: src/confluence_plone/converter/comments.py -->

Footer comments, with their replies, become `plone.app.discussion` comments.
Their text is converted to plain text, since Plone comments do not hold rich text.

Inline comments become discussions of the Wiki Page, anchored to the same text Confluence anchored them to, and keep whether they were resolved.
An inline comment whose anchor is no longer in the page becomes a footer comment, so it is not lost.

## Labels

Labels become tags.
Confluence labels have namespaces: `global` and `team` labels are shared, while `my` labels are personal.
Only the namespaces in `label_namespaces` are converted.

## Users

<!-- source: src/confluence_plone/utils/principals.py -->

`confluence-plone` does not create users.
In an intranet, users usually come from a directory such as LDAP, which owns them.
Each Confluence user is written as the id of a principal that is expected to exist in the site.

The principal id comes from the mapping file first, and from the `strategy` setting otherwise: the user name, the email address, or the Confluence user key.
A user that cannot be resolved becomes the `default` principal, and is counted in the `unmapped_users` of `summary.json`.

`confluence-plone` cannot check that a principal exists in the site.
{doc}`/how-to-guides/map-users` explains how to prepare the mapping.

## Links

<!-- source: src/confluence_plone/converter/context.py -->

Links to pages and attachments are resolved through the plan, wherever the target is.
By default, they are written as relative `resolveuid` URLs, which keep working when the target moves.
With `link_style = "path"`, they are written as paths instead.

A link to a page that is not converted keeps its text, and is reported.

## Related

- {doc}`pipeline`
- {doc}`limitations`
- {doc}`/reference/settings`
