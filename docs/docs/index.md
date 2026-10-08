---
myst:
  html_meta:
    "description": "Documentation for confluence-plone, the tool that converts a Confluence XML space export for import into a kitconcept.intranet site."
    "property=og:description": "Documentation for confluence-plone"
    "property=og:title": "confluence-plone"
    "keywords": "confluence-plone, Confluence, Plone, kitconcept.intranet, migration, documentation"
---

(index)=

# Confluence to Plone

`confluence-plone` converts a Confluence XML space export into the `plone.exportimport` format, ready to import into a site built with `kitconcept.intranet`.

Each Confluence space becomes a Workspace.
Each page becomes a Wiki Page, with its content converted from the Confluence storage format to the Plate editor value the Wiki Page uses.
Attachments become File and Image items inside their page, and comments become Plone comments or Wiki Page discussions.

The conversion never connects to Confluence or to Plone.
It reads an export file and writes a directory, so you can run it, inspect the result, adjust the settings, and run it again as often as you need.
Every lossy step is recorded as data in a set of reports, so nothing is lost without a trace.

```shell
uv run confluence-plone settings generate
uv run confluence-plone analyze export.zip
uv run confluence-plone convert export.zip ./import
```

## Where to start

- {doc}`concepts/pipeline` explains how a conversion works.
- {doc}`how-to-guides/install` and {doc}`how-to-guides/migrate` take you from a Confluence export to content in Plone.
- {doc}`reference/conversion` lists what each Confluence element and macro becomes.

```{toctree}
:caption: Concepts
:maxdepth: 2
:hidden: true

concepts/index
```

```{toctree}
:caption: How-to guides
:maxdepth: 2
:hidden: true

how-to-guides/index
```

```{toctree}
:caption: Reference
:maxdepth: 2
:hidden: true

reference/index
```

```{toctree}
:caption: Appendices
:maxdepth: 2
:hidden: true

CHANGELOG
genindex
```
