---
myst:
  html_meta:
    "description": "Every issue code confluence-plone reports, its severity, and what to do about it."
    "property=og:description": "The issue codes of confluence-plone"
    "property=og:title": "Issue codes | confluence-plone"
    "keywords": "confluence-plone, issues, issue codes, severity, issues.csv"
---

(reference-issues)=

# Issue codes

<!-- source: src/confluence_plone/planner.py, src/confluence_plone/pipeline.py, src/confluence_plone/converter/ -->

Every issue has a severity.

`info`
: Something was converted in a lossy but expected way. No action is needed, but it is worth knowing.

`warning`
: Something was not converted, and the item needs a human look.

`error`
: Something failed, and content is missing from the result.

## Planning

| Code | Severity | Meaning | What to do |
| --- | --- | --- | --- |
| `space_not_found` | warning | A key in the `spaces` setting is not in the export. | Fix the setting, or export the space. |
| `orphan_page` | warning | The parent of the page is not converted, so the page moved to the top level of its Workspace. | Move the page in Plone, or convert the parent. |
| `page_cycle` | warning | The parents of the page form a cycle, so the page moved to the top level of its Workspace. | Move the page in Plone. |
| `missing_attachment_file` | error | The file of an attachment is not in the export, so the attachment is skipped. | Export again, with the attachments. |

## Spaces and pages

| Code | Severity | Meaning | What to do |
| --- | --- | --- | --- |
| `space_permissions_not_migrated` | warning | The space has permissions; the detail says how many. | Set up the access to the Workspace in Plone. |
| `restriction_not_migrated` | warning | The page has view or edit restrictions. | Set up the access to the page in Plone. |
| `conversion_failed` | error | The body of the page could not be converted. The page is written with its title only, so that the pages below it keep their place. | Report it as a bug, with the detail. |
| `wiki_markup` | warning | The body is in wiki markup, and is kept as plain text. | Format the page by hand. |

## Content of a page

| Code | Severity | Meaning | What to do |
| --- | --- | --- | --- |
| `unsupported_macro` | warning | The macro has no converter. It became a callout naming it, followed by its content. | Rebuild the content by hand. |
| `broken_page_link` | warning | A link, or a `children` macro, points to a page that is not converted. The link text is kept. | Fix the link, or convert the target page. |
| `broken_attachment_link` | warning | A link or a file macro points to an attachment that is not converted. | Fix the link, or convert the attachment. |
| `broken_space_link` | warning | A link points to a space that is not converted. | Fix the link, or convert the space. |
| `broken_image` | warning | An image points to an attachment that is not converted, or has no source. | Add the image by hand. |
| `broken_include` | warning | An `include` macro points to a page that is not converted. | Copy the content by hand. |
| `include_loop` | warning | An `include` macro includes a page that is already being included. | None; the loop is cut. |
| `unsupported_link` | warning | A link has a target the converter does not know. The detail holds the start of its markup. | Fix the link by hand. |
| `blog_post_link` | info | A link points to a blog post, which is not converted. The link text is kept. | None. |
| `static_page_list` | info | A `children` or `pagetree` macro became a static list of the pages at conversion time. | None. |
| `include_snapshot` | info | An `include` or `excerpt-include` macro became a copy of the included content. | None. |
| `diagram_as_image` | info | A `draw.io` or Gliffy diagram became its PNG preview. | None. |
| `callout_content_moved` | info | A panel held lists or tables, which moved below the callout. | None. |
| `status_macro` | info | A status lozenge became bold text on a colored background. | None. |
| `jira_without_url` | info | A `jira` macro became its issue key as text, since `jira_url` is not set. | Set `jira_url`. |
| `adf_extension` | info | A Cloud editor extension was converted from the fallback content Confluence provides. | None. |
| `unknown_emoticon` | info | An emoticon has no known emoji, and became its fallback text, or its name in parentheses. | None. |
| `unknown_element` | info | A Confluence element (`ac:`, `ri:`, or `at:`) has no converter; its content is kept. Unknown HTML elements keep their content without an issue. | None. |

## Comments

| Code | Severity | Meaning | What to do |
| --- | --- | --- | --- |
| `inline_comment_as_footer` | info | The text an inline comment was anchored to is no longer in the page, or `inline_comments` is `false`, so it became a footer comment. | None. |

## Related

- {doc}`reports`
- {doc}`/concepts/limitations`
