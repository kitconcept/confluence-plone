---
myst:
  html_meta:
    "description": "What confluence-plone does not migrate, what it migrates in a lossy way, and what is not verified yet."
    "property=og:description": "What confluence-plone does not migrate"
    "property=og:title": "Limitations | confluence-plone"
    "keywords": "confluence-plone, limitations, permissions, versions, blog posts, macros"
---

(concepts-limitations)=

# Limitations

Read this page before promising a migration to anyone.
Every item below is reported, either in `skipped.csv` or as an issue, so a dry run of the conversion shows how much of an export each one affects.

## Not migrated

Page history
: Only the current version of each page and attachment is converted.
  Confluence keeps every version, and the export holds them all; they are counted by `analyze`, then ignored.

Permissions
: Page restrictions and space permissions are not migrated.
  Confluence permissions do not map one to one to Plone roles, and in an intranet the groups usually come from a directory that `confluence-plone` cannot see.
  Each restricted page is reported as `restriction_not_migrated`, and each space with permissions as `space_permissions_not_migrated`, so the access rules can be set up in Plone by hand.

Blog posts
: Blog posts are skipped.
  Links to them keep their text, and are reported as `blog_post_link`.

Drafts and deleted content
: Draft pages, and pages and attachments in the trash, are skipped.

Users and groups
: Users are not created.
  See {ref}`concepts-mapping`.

## Migrated with losses

Wiki markup
: Pages last edited before Confluence 4 may still hold wiki markup instead of the storage format.
  Their text is kept as plain paragraphs, without formatting, and reported as `wiki_markup`.

Unsupported macros
: A macro without a converter becomes a callout that names the macro and lists its parameters, followed by its content.
  Use `analyze` to see which macros an export uses before starting.

Page lists and includes
: The `children` and `pagetree` macros become a static list of links, and `include` and `excerpt-include` become a copy of the included content.
  Both are snapshots taken at conversion time, and do not update when the pages change.

Panels
: A Plate callout holds text only.
  Lists, tables, and other blocks inside an `info`, `note`, `tip`, `warning`, or `panel` macro move right below the callout.

Diagrams
: `draw.io` and Gliffy diagrams become the PNG preview Confluence attaches to the page.
  The diagram source is migrated as an attachment, but cannot be edited in Plone.

Footer comments
: Plone comments hold plain text, so formatting, links, and images in footer comments are lost.

Jira issues
: Without a `jira_url` setting, the `jira` macro becomes the issue key as plain text.

## Not verified yet

These work in the output, but have not been checked end to end in a running site.

- The rendering of relative `resolveuid` links inside a Wiki Page.
  Set `link_style = "path"` if they do not resolve.
- The import of `redirects.json`, which is disabled by default.
- Links to an anchor in another page keep the anchor name, but the editor may give headings different ids.

## Related

- {doc}`mapping`
- {doc}`/reference/issues`
- {doc}`/how-to-guides/analyze`
