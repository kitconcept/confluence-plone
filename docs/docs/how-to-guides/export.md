---
myst:
  html_meta:
    "description": "How to export Confluence spaces as XML for confluence-plone."
    "property=og:description": "Export Confluence spaces as XML"
    "property=og:title": "Export from Confluence | confluence-plone"
    "keywords": "confluence-plone, Confluence, XML export, space export, site export"
---

(how-to-export)=

# Export from Confluence

`confluence-plone` reads the XML export of Confluence.
It does not read the HTML, PDF, Word, or CSV exports.

## Export one space

A Confluence administrator, or an administrator of the space, exports it from the space settings: choose to export the space, then **XML**, then **Full export**.
The menu names differ between Confluence versions; see the Atlassian documentation for your version.

- [Confluence Cloud: Export content to Word, PDF, HTML, and XML](https://support.atlassian.com/confluence-cloud/docs/export-content-to-word-pdf-html-and-xml/)
- [Confluence Data Center: Export content to Word, PDF, HTML, and XML](https://confluence.atlassian.com/doc/export-content-to-word-pdf-html-and-xml-139475.html)

Choose the full export, which includes the attachments and the comments.
Without attachments, every attachment is reported as `missing_attachment_file` and skipped.

## Export a whole site

A site export, made by a Confluence administrator for backups, has the same format, and holds every space.
Use the `spaces` setting to choose which ones to convert.

## What you get

The export is a zip file holding `entities.xml`, `exportDescriptor.properties`, and an `attachments` directory.
`confluence-plone` reads the zip file directly; you can also unpack it and pass the directory.

## Next steps

- {doc}`configure`
- {doc}`analyze`
