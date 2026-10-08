---
myst:
  html_meta:
    "description": "How to convert a Confluence export into the plone.exportimport format with confluence-plone, and review the result."
    "property=og:description": "Convert a Confluence export"
    "property=og:title": "Convert an export | confluence-plone"
    "keywords": "confluence-plone, convert, plone.exportimport, reports, issues"
---

(how-to-convert)=

# Convert an export

```shell
uv run confluence-plone convert export.zip ./import
```

The first argument is the export: a zip file, or the directory of an unpacked one.
The second is the destination directory, where the result is written in the `plone.exportimport` format.

The command prints a summary: the number of items of each type, the skipped content, the comments, and the issues by severity.

## Convert again

The destination must be empty.
To replace the result of a previous conversion, pass `--clean-up`, which removes the content of the destination first.

```shell
uv run confluence-plone convert export.zip ./import --clean-up
```

## Review the reports

The reports are written to the `reports_location` directory, `reports` by default.
Review them in this order.

1. `summary.json`, for the totals, the issues by code, and the unmapped users.
1. `issues.csv`, sorted by severity.
   Errors mean content is missing from the result; warnings mean a page needs a human look.
1. `skipped.csv`, to confirm that everything left out was meant to be.
1. `items.csv`, which maps each Confluence id to its path and UID in Plone, with the worst severity of its issues.

{doc}`/reference/issues` explains each issue code, and what to do about it.

## Next steps

- {doc}`import`
- {doc}`/reference/reports`
