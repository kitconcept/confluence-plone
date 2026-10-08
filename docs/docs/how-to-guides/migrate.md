---
myst:
  html_meta:
    "description": "The steps of a Confluence to kitconcept.intranet migration with confluence-plone, from the export to the import."
    "property=og:description": "Migrate a Confluence space to kitconcept.intranet"
    "property=og:title": "Migrate a Confluence space | confluence-plone"
    "keywords": "confluence-plone, migration, Confluence, kitconcept.intranet, plone-importer"
---

(how-to-migrate)=

# Migrate a Confluence space

A migration is a loop: convert, review the reports, adjust the settings, and convert again, until the result is good enough to import.
Since a conversion never touches Confluence or Plone, each round costs only the time it takes to run.

1. {doc}`Export the spaces from Confluence <export>` as XML.
1. {doc}`Create a settings file <configure>`.
1. {doc}`Analyze the export <analyze>`, to see what it holds and which macros it uses.
1. {doc}`Prepare the user mapping <map-users>`.
1. {doc}`Convert the export <convert>`, and review the reports.
1. Repeat the last two steps until the reports hold no surprises.
1. {doc}`Import the result into the site <import>`.

## Before the first round

Agree on a few decisions before converting, since they change every item in the result.

- Which spaces to migrate, and whether personal and archived spaces are part of it.
- Where the Workspaces go in the site: the site root, or a folder.
- How Confluence users map to the principals of the site.
- What the issues in {doc}`/concepts/limitations` mean for this customer, especially permissions.

## Related

- {doc}`/concepts/pipeline`
- {doc}`/reference/reports`
