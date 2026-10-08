---
myst:
  html_meta:
    "description": "The report files written by confluence-plone, and their columns."
    "property=og:description": "The reports of confluence-plone"
    "property=og:title": "Reports | confluence-plone"
    "keywords": "confluence-plone, reports, items.csv, issues.csv, skipped.csv, summary.json, inventory.json"
---

(reference-reports)=

# Reports

<!-- source: src/confluence_plone/reports.py, src/confluence_plone/_types/report.py, src/confluence_plone/pipeline.py -->

Reports are written to the `reports_location` directory, and replaced on every run.
CSV files are UTF-8, with a header row.

In every report, `source_id` is the id of the Confluence object: the content id of a page or an attachment, and `space:<id>` for a space.

## Written by `analyze`

### `inventory.json`

| Key | Content |
| --- | --- |
| `descriptor` | The properties in `exportDescriptor.properties`, such as the Confluence version and the export type. Empty when the export lacks the file. |
| `spaces` | One entry per space: `key`, `name`, `type`, `status`, `contents` (counts by kind and status, such as `page:current`), `attachments`, `attachments_size` in bytes, and `permissions`. |
| `totals` | Counts of `spaces`, `pages`, `blog_posts`, `historical_versions`, `attachments`, `footer_comments`, `inline_comments`, `users`, `labelled_content`, and `restricted_content`. |
| `body_types` | Number of bodies by format: `2` is the storage format, `1` wiki markup, `0` plain text. |
| `classes` | Number of objects of each Confluence class in `entities.xml`. |
| `macros` | The rows of `macros.csv`. |
| `warnings` | Problems found while reading the export. |

### `macros.csv`

| Column | Content |
| --- | --- |
| `macro` | Name of the macro. |
| `pages` | Number of current pages using it. |
| `uses` | Number of uses. |
| `example` | Title of one page using it. |

Rows are sorted by the number of pages, most used first.

## Written by `convert`

### `items.csv`

One row per item created in Plone.

| Column | Content |
| --- | --- |
| `source_id` | Id of the Confluence object. |
| `source_type` | `space`, `page`, or `attachment`. |
| `space` | Key of the space. |
| `title` | Title. |
| `path` | Path of the item in Plone, relative to the site root. |
| `portal_type` | Portal type of the item. |
| `uid` | UID of the item. |
| `status` | `ok`, `warning`, or `error`, after the worst issue of the item. An item with only `info` issues is `ok`. |
| `issues` | Number of issues of the item. |

### `issues.csv`

One row per issue.

| Column | Content |
| --- | --- |
| `source_id` | Id of the Confluence object; for `space_not_found`, the space key. |
| `severity` | `info`, `warning`, or `error`. |
| `code` | Machine-readable code. See {doc}`issues`. |
| `detail` | Human-readable detail, such as the name of the macro or the title of the missing page. |

An issue with the same code and detail is reported once per page, even when the same problem appears several times in it.

### `skipped.csv`

One row per Confluence object that was not converted.

| Column | Content |
| --- | --- |
| `source_id` | Id of the Confluence object. |
| `source_type` | `space`, `page`, `blogpost`, or `attachment`. |
| `space` | Key of the space. |
| `title` | Title. |
| `reason` | Why it was skipped. |

The reasons are `space not selected`, `personal space`, `archived space`, `blog posts are not converted`, `file missing from the export`, and `status <status>` for drafts and deleted content.

### `summary.json`

| Key | Content |
| --- | --- |
| `items` | Number of items by portal type. |
| `statuses` | Number of items by status. |
| `skipped` | Number of skipped objects. |
| `footer_comments` | Number of comments written to `discussions.json`. |
| `inline_discussions` | Number of Wiki Page discussions. |
| `issues` | Number of issues by severity. |
| `issue_codes` | Number of issues by code, most frequent first. |
| `unmapped_users` | Confluence users mapped to the `default` principal, with the number of times each one appears. |

## Related

- {doc}`issues`
- {doc}`/how-to-guides/convert`
