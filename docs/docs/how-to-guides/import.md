---
myst:
  html_meta:
    "description": "How to import the result of confluence-plone into a kitconcept.intranet site with plone-importer."
    "property=og:description": "Import the result into Plone"
    "property=og:title": "Import into Plone | confluence-plone"
    "keywords": "confluence-plone, plone-importer, plone.exportimport, kitconcept.intranet, import"
---

(how-to-import)=

# Import into Plone

The result of a conversion is imported with `plone-importer`, the command line importer of `plone.exportimport`.
It is installed in the backend of every `kitconcept.intranet` project.

## Before importing

- Back up the site, or import into a copy of it first.
  The import cannot be undone.
- When `base_path` is set, the folder it names must exist in the site.
- The Workspace and Wiki Page content types must be installed, which they are in a `kitconcept.intranet` site.

## Run the import

Stop the backend, then run the importer from the backend directory of the project.
Its arguments are the Zope configuration file, the id of the Plone site, and the directory written by `convert`.

```shell
cd backend
uv run plone-importer instance/etc/zope.conf Plone /path/to/import
```

Start the backend again, and open one of the Workspaces.

## Check the result

- The number of items in the site matches the `items` of `summary.json`.
- The pages listed in `issues.csv` with a warning look acceptable.
- Images in pages, links between pages, and the comments of a few pages work.

## Related

- {doc}`convert`
- {doc}`/concepts/limitations`
