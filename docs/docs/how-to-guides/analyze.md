---
myst:
  html_meta:
    "description": "How to analyze a Confluence export with confluence-plone before converting it."
    "property=og:description": "Analyze a Confluence export"
    "property=og:title": "Analyze an export | confluence-plone"
    "keywords": "confluence-plone, analyze, inventory, macros, estimate"
---

(how-to-analyze)=

# Analyze an export

Run `analyze` first on any new export.
It reads the export without converting anything, and reports what it holds.
Its macro list is what an estimate of the migration is built on.

```shell
uv run confluence-plone analyze export.zip
```

The command prints two tables, the totals and the 20 most used macros, and writes two files to the reports directory.

`inventory.json`
: The full inventory: the totals, one entry per space with its content by status, its attachments and their size, the body formats, the number of objects of each Confluence class, the macros, and any warning from reading the export.

`macros.csv`
: One row per macro: its name, the number of pages and uses, and the title of one page that uses it, as an example.

To write the reports somewhere else than the `reports_location` setting, pass `--dst`.

```shell
uv run confluence-plone analyze export.zip --dst ./reports/first-look
```

## What to look for

- **Macros without a converter.**
  Compare `macros.csv` with {doc}`/reference/conversion`.
  Every macro not listed there becomes a callout, and each page using it needs a human look after the migration.
- **Body formats.**
  In `body_types`, `2` is the storage format, and `1` is wiki markup, which is kept as plain text.
- **Restricted content and permissions.**
  `restricted_content` and the `permissions` of each space are what will need to be set up again by hand.
- **Warnings.**
  Characters that XML forbids, or a malformed `entities.xml`, are reported here; the conversion still runs.

## Next steps

- {doc}`map-users`
- {doc}`convert`
