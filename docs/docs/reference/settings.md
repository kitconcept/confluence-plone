---
myst:
  html_meta:
    "description": "Every setting of confluence-plone.toml, with its default value."
    "property=og:description": "The settings of confluence-plone"
    "property=og:title": "Settings | confluence-plone"
    "keywords": "confluence-plone, settings, confluence-plone.toml, TOML"
---

(reference-settings)=

# Settings

<!-- source: src/confluence_plone/settings/default.toml -->

The settings live in `confluence-plone.toml`, in the current directory.
A setting missing from the file keeps its default value.
Paths are relative to the current directory.

## `[config]`

| Setting | Default | Description |
| --- | --- | --- |
| `debug` | `false` | Write debug messages to the log file. |
| `log_file` | `"confluence-plone.log"` | Log file. |
| `reports_location` | `"reports"` | Directory where the reports are written. |
| `timezone` | `"UTC"` | Time zone of the dates in the export, since Confluence writes them without one. An IANA name, such as `"Europe/Berlin"`. |

## `[source]`

| Setting | Default | Description |
| --- | --- | --- |
| `spaces` | `[]` | Keys of the spaces to convert. An empty list converts every space. A key not in the export is reported as `space_not_found`. |
| `include_personal_spaces` | `false` | Convert personal spaces, whose keys start with `~`. |
| `include_archived_spaces` | `false` | Convert archived spaces. |

## `[target]`

| Setting | Default | Description |
| --- | --- | --- |
| `site_root` | `"/Plone"` | Path of the Plone site. Used only for redirects. |
| `base_path` | `""` | Existing container where one Workspace per space is created. `""` is the site root. |
| `workspace_type` | `"Workspace"` | Portal type of spaces. |
| `page_type` | `"WikiPage"` | Portal type of pages. |
| `file_type` | `"File"` | Portal type of attachments that are not images. |
| `image_type` | `"Image"` | Portal type of image attachments. |
| `workflow` | `"simple_intranet_workflow"` | Workflow of Workspaces and pages, for their workflow history. |
| `initial_state` | `"private"` | First state of the workflow history, at the creation date. |
| `review_state` | `"published"` | State every Workspace and page ends in, at the modification date. |
| `link_style` | `"resolveuid"` | Links to pages, attachments, and images: `"resolveuid"`, which survives moves, or `"path"`. |
| `types_without_workflow` | `["File", "Image"]` | Portal types that have no workflow, and therefore no review state. |
| `image_media_types` | GIF, JPEG, PNG, SVG, and WebP | Attachments with these media types become images; all others become files. |

## `[principals]`

| Setting | Default | Description |
| --- | --- | --- |
| `default` | `"admin"` | Principal used for a Confluence user that cannot be mapped. |
| `strategy` | `"username"` | How a Confluence user becomes a principal: `"username"`, `"email"`, or `"key"`. |
| `mapping_file` | `""` | CSV file with the columns `confluence` and `principal`. See {doc}`/how-to-guides/map-users`. |

## `[content]`

| Setting | Default | Description |
| --- | --- | --- |
| `label_namespaces` | `["global", "team"]` | Label namespaces converted to tags. `my` labels are personal. |
| `footer_comments` | `true` | Convert footer comments to Plone comments. |
| `inline_comments` | `true` | Convert inline comments to Wiki Page discussions. When `false`, they become footer comments. |

## `[macros]`

| Setting | Default | Description |
| --- | --- | --- |
| `jira_url` | `""` | Base URL of the Jira server, used to link issues from the `jira` macro. |

## `[redirects]`

| Setting | Default | Description |
| --- | --- | --- |
| `enabled` | `false` | Write `redirects.json`, mapping the old Confluence URLs (`/display/KEY/Title`) to the new paths, under `site_root`. |

## Related

- {doc}`/how-to-guides/configure`
- {doc}`cli`
