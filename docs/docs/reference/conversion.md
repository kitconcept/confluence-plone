---
myst:
  html_meta:
    "description": "What confluence-plone converts each Confluence storage format element and macro into, in the Plate value of a Wiki Page."
    "property=og:description": "Conversion rules of confluence-plone"
    "property=og:title": "Elements and macros | confluence-plone"
    "keywords": "confluence-plone, storage format, macros, Plate, Wiki Page, conversion"
---

(reference-conversion)=

# Elements and macros

<!-- source: src/confluence_plone/converter/elements.py, src/confluence_plone/converter/macros.py -->

This page lists what each part of the Confluence storage format becomes in the Plate value of a Wiki Page.
Anything not listed here keeps its content: an unknown HTML element is converted as its content, and an unknown macro becomes a callout, reported as `unsupported_macro`.

## Text and blocks

| Confluence | Plate | Notes |
| --- | --- | --- |
| `p`, `div`, `section`, `article`, `center` | `p` | |
| `h1` to `h6` | `h1` to `h6` | |
| `blockquote` | `blockquote` | One block per paragraph of the quote. |
| `pre` | `code_block` | One `code_line` per line. |
| `hr` | `hr` | |
| `br` | Line break in the text | |
| `b`, `strong` | Bold | |
| `i`, `em`, `cite` | Italic | |
| `u`, `ins` | Underline | |
| `s`, `del`, `strike` | Strikethrough | |
| `sub`, `sup` | Subscript, superscript | |
| `code`, `tt`, `kbd` | Code | |
| `span`, `font` | Text color and background color | Other styles are dropped. |
| `time` | `date` | |
| `ul`, `ol` | Indent list | Paragraphs with `listStyleType` `disc` or `decimal`, and an `indent` for the nesting level. |
| `ac:task-list` | Indent list | `listStyleType` `todo`, with `checked` for completed tasks. |
| `table` | `table` | Header cells, and merged cells with `colSpan` and `rowSpan`. |
| `ac:layout` | `column_group` | One per section with two or more cells, with the widths of the Confluence layout. Single-cell sections become plain blocks. |
| `ac:emoticon` | Emoji | Cloud emoji are converted from their code points. |
| `ac:adf-extension` | Its fallback content | Reported as `adf_extension`. |

## Links, images, and mentions

| Confluence | Plate | Notes |
| --- | --- | --- |
| `ac:link` to a page | `a` | To the Wiki Page, with the anchor when there is one. |
| `ac:link` to an attachment | `a` | To the File or Image. |
| `ac:link` to a space | `a` | To the Workspace. |
| `ac:link` to a user | `mention` | With the principal id and the display name. |
| `ac:link` to a URL | `a` | |
| `ac:link` to a blog post | Its text | Blog posts are not converted. |
| `a` | `a` | |
| `ac:image` of an attachment | Image block | A `ploneBlock` of type `plateimage`, with the alignment and alternative text. An attachment that is not an image becomes a link. |
| `ac:image` of a URL, `img` | Image block | Points to the external URL. |
| `ac:inline-comment-marker` | Comment mark | Anchors the discussion of the inline comment. |

## Macros

| Macro | Plate | Notes |
| --- | --- | --- |
| `info`, `note`, `tip`, `warning`, `panel` | `callout` | With an icon and background color for each kind, and the title in bold. Lists and tables move below the callout. |
| `code`, `noformat` | `code_block` | With the language, when Plate knows it, and the title as a bold paragraph above. |
| `expand` | `toggle` | The content follows the toggle, indented. |
| `toc` | `toc` | |
| `section` and `column` | `column_group` | With the widths of the columns, when they all have one. |
| `children` | Indent list of links | The child pages, as they are at conversion time, to the given depth. |
| `pagetree` | Indent list of links | The page tree of the Workspace, as it is at conversion time. |
| `attachments` | Indent list of links | The attachments of the page. |
| `gallery` | Image blocks | One per image attached to the page. |
| `include`, `excerpt-include` | The included content | A copy, as it is at conversion time. `excerpt-include` copies only the `excerpt` macro of the page. |
| `view-file`, `viewfile`, `viewdoc`, `view-pdf`, `viewpdf`, `viewppt`, `viewxls`, `multimedia` | Link | To the attached file. |
| `drawio`, `inc-drawio`, `gliffy` | Image block | The PNG preview of the diagram, when the page has it. |
| `jira`, `jiraissues` | Link | To the issue, under `jira_url`. Without `jira_url`, the issue key as text. |
| `status` | Text | The title in capitals, bold, on the background color of the status. |
| `details`, `div`, `excerpt`, `page-properties`, `span` | Their content | |
| `anchor` | Nothing | |
| Any other macro | `callout` | Names the macro and lists its parameters, followed by its content. |

## Related

- {doc}`issues`
- {doc}`/concepts/limitations`
