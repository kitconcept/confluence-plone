---
myst:
  html_meta:
    "description": "How confluence-plone converts a Confluence export: read, plan, convert, write, and report."
    "property=og:description": "How confluence-plone converts a Confluence export"
    "property=og:title": "How a conversion works | confluence-plone"
    "keywords": "confluence-plone, pipeline, entities.xml, plone.exportimport, Plate"
---

(concepts-pipeline)=

# How a conversion works

A conversion is a pipeline of five stages.
Each stage has its own module, and each one only reads what the previous stage produced.

```{mermaid}
:config: {"flowchart": {"htmlLabels": false}}

flowchart LR
    export["Confluence export"] --> read["Read"]
    read --> plan["Plan"]
    plan --> convert["Convert"]
    convert --> write["Write"]
    convert --> report["Report"]
    write --> result["plone.exportimport directory"]
    report --> reports["CSV and JSON reports"]
```

## Why the XML space export

Confluence offers several ways out: the REST API, HTML exports, and the XML export.
`confluence-plone` reads the XML export, for three reasons.

- It is a file, so a conversion is repeatable and needs no access to the customer's Confluence.
- It holds the storage format of every page, which keeps the structure that HTML exports flatten: macros, links by page title, and inline comment markers.
- It holds the metadata the other formats lose: authors, dates, labels, comments, restrictions, and the attachments themselves.

The same reader handles exports from Confluence Server and Cloud.
It is tested against exports from Confluence 5.9 to 8.5, and from Confluence Cloud.

## Read

<!-- source: src/confluence_plone/reader/ -->

The export is a zip file, or a directory with the unpacked zip.
Its `entities.xml` is a dump of the Confluence database: one `<object>` element per row, in no particular order, with references between objects by id.

The reader streams the file instead of building its whole XML tree, and keeps only the objects it needs.
It removes the control characters that XML 1.0 forbids, which Confluence writes anyway, and recovers from malformed XML when it can.
Both are reported as warnings.

The objects are then assembled into a model: spaces, pages, attachments, comments, bodies, labels, users, and restrictions.
Only the current version of each page is converted; historical versions are counted, and then ignored.

## Plan

<!-- source: src/confluence_plone/planner.py -->

The planner decides where every item goes before any content is converted.
It creates a Workspace for each selected space, places the pages in their tree with the home page first, and adds the attachments of each page as its children.

Planning first is what makes links work.
When the converter meets a link to a page by its title, the target already has a path and a UID, wherever it sits in the export.

UIDs are deterministic: the same export always produces the same UIDs, paths, and links.
Two conversions of the same export with the same settings produce the same result, so their output can be compared with `diff`.

Pages whose parent is not converted move to the top level of their Workspace, and pages whose parents form a cycle too.
Both are reported.

## Convert

<!-- source: src/confluence_plone/converter/ -->

The body of a Confluence page is XHTML with Confluence elements in two namespaces: `ac:` for structure and macros, and `ri:` for references to pages, attachments, users, and spaces.
The converter walks this tree and builds the Plate value the Wiki Page editor uses.

Each element and each macro has its own converter function, registered by name.
An element or macro without a converter is not dropped: an unknown macro becomes a callout that names it, followed by its content, and is reported.
{doc}`/reference/conversion` lists every converter.

The converter also collects inline comments, which Confluence anchors to a marked range of text, and turns them into Wiki Page discussions anchored to the same text.

## Write

<!-- source: src/confluence_plone/writer.py -->

The result is a directory in the format `plone.exportimport` reads.

```text
<destination>/
├── content/
│   ├── __metadata__.json
│   └── <UID>/
│       ├── data.json
│       └── file/<filename>      (or image/<filename>)
├── discussions.json
└── redirects.json               (when enabled)
```

`plone.exportimport` creates the items in the order `__metadata__.json` lists them, and finds the parent of each one by its path, so parents are always written before their children.

## Report

<!-- source: src/confluence_plone/reports.py -->

Every lossy step is an issue, with a severity and a machine-readable code.
Issues are not log lines: they are written as data, one row per issue, so a migration can be planned, estimated, and checked with a spreadsheet.
{doc}`/reference/reports` describes the files, and {doc}`/reference/issues` lists the codes.

## Related

- {doc}`mapping`
- {doc}`limitations`
- {doc}`/how-to-guides/migrate`
