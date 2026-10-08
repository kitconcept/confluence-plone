from . import DIAGRAM_UID
from . import SPEC_UID
from confluence_plone.converter.core import leaf
from confluence_plone.converter.core import node

import pytest


def macro(
    name: str, params: dict | None = None, body: str = "", plain: str | None = None
) -> str:
    """Return a structured macro in storage format."""
    parts = [f'<ac:structured-macro ac:name="{name}">']
    for key, value in (params or {}).items():
        parts.append(f'<ac:parameter ac:name="{key}">{value}</ac:parameter>')
    if plain is not None:
        parts.append(f"<ac:plain-text-body><![CDATA[{plain}]]></ac:plain-text-body>")
    if body:
        parts.append(f"<ac:rich-text-body>{body}</ac:rich-text-body>")
    parts.append("</ac:structured-macro>")
    return "".join(parts)


class TestPanels:
    @pytest.mark.parametrize(
        "name,icon,color",
        [
            ("info", "ℹ️", "#DEEBFF"),  # noQA: RUF001
            ("note", "📝", "#EAE6FF"),
            ("tip", "💡", "#E3FCEF"),
            ("warning", "⚠️", "#FFFAE6"),
        ],
    )
    def test_panel(self, convert, name, icon, color):
        blocks, _ = convert(macro(name, {"title": "Title"}, "<p>one</p><h3>two</h3>"))
        assert blocks == [
            node(
                "callout",
                [
                    leaf("Title", {"bold": True}),
                    leaf("\n"),
                    leaf("one"),
                    leaf("\n"),
                    leaf("two"),
                ],
                icon=icon,
                backgroundColor=color,
            )
        ]

    def test_panel_colors(self, convert):
        blocks, _ = convert(macro("panel", {"bgColor": "#FFF"}, "<p>x</p>"))
        assert blocks[0]["backgroundColor"] == "#FFF"
        blocks, _ = convert(macro("panel", {}, "<p>x</p>"))
        assert "backgroundColor" not in blocks[0]

    def test_empty_panel(self, convert):
        blocks, _ = convert(macro("info"))
        assert blocks[0]["children"] == [leaf("")]

    def test_other_blocks_move_below(self, convert, issue_codes):
        blocks, ctx = convert(
            macro(
                "note",
                {},
                "<p>text</p><ul><li>item</li></ul><table><tr><td>c</td></tr></table>",
            )
        )
        assert [block["type"] for block in blocks] == ["callout", "p", "table"]
        assert issue_codes(ctx) == ["callout_content_moved"]


class TestCode:
    @pytest.mark.parametrize(
        "params,lang",
        [
            ({"language": "py"}, "python"),
            ({"language": "Shell"}, "bash"),
            ({"language": "brainfuck"}, None),
            ({}, None),
        ],
    )
    def test_code(self, convert, params, lang):
        blocks, _ = convert(macro("code", params, plain="a = 1\nb = 2"))
        assert blocks[0].get("lang") == lang
        assert [line["children"][0]["text"] for line in blocks[0]["children"]] == [
            "a = 1",
            "b = 2",
        ]

    def test_title(self, convert):
        blocks, _ = convert(macro("code", {"title": "Example"}, plain="x"))
        assert blocks[0] == node("p", [leaf("Example", {"bold": True})])
        assert blocks[1]["type"] == "code_block"

    def test_noformat(self, convert):
        blocks, _ = convert(macro("noformat", plain="raw"))
        assert blocks == [node("code_block", [node("code_line", [leaf("raw")])])]

    def test_missing_body(self, convert):
        blocks, _ = convert(macro("code"))
        assert blocks == [node("code_block", [node("code_line", [leaf("")])])]


class TestStructure:
    def test_expand(self, convert):
        blocks, _ = convert(
            macro("expand", {"title": "More"}, "<p>hidden</p><ul><li>item</li></ul>")
        )
        assert blocks[0] == node("toggle", [leaf("More")])
        assert blocks[1] == node("p", [leaf("hidden")], indent=1)
        assert blocks[2]["indent"] == 2

    def test_expand_default_title(self, convert):
        blocks, _ = convert(macro("expand"))
        assert blocks == [node("toggle", [leaf("Click here to expand...")])]

    def test_toc(self, convert):
        blocks, _ = convert(macro("toc"))
        assert blocks == [node("toc")]

    def test_anchor(self, convert):
        blocks, _ = convert("<p>a" + macro("anchor", {"": "here"}) + "b</p>")
        assert blocks == [node("p", [leaf("ab")])]

    @pytest.mark.parametrize(
        "name", ["excerpt", "details", "div", "span", "page-properties"]
    )
    def test_transparent(self, convert, name):
        blocks, _ = convert(macro(name, {}, "<p>kept</p>"))
        assert blocks == [node("p", [leaf("kept")])]

    def test_transparent_without_body(self, convert):
        blocks, _ = convert(macro("excerpt"))
        assert blocks == []

    def test_section(self, convert):
        storage = macro(
            "section",
            {},
            macro("column", {"width": "30%"}, "<p>a</p>")
            + macro("column", {"width": "70%"}, "<p>b</p>")
            + "<p>after</p>",
        )
        blocks, _ = convert(storage)
        assert [c["width"] for c in blocks[0]["children"]] == ["30%", "70%"]
        assert blocks[1] == node("p", [leaf("after")])

    def test_section_without_widths(self, convert):
        storage = macro(
            "section",
            {},
            macro("column", {}, "<p>a</p>") + macro("column", {}, "<p>b</p>"),
        )
        blocks, _ = convert(storage)
        assert [c["width"] for c in blocks[0]["children"]] == ["50%", "50%"]

    def test_section_without_columns(self, convert):
        blocks, _ = convert(macro("section", {}, "<p>plain</p>"))
        assert blocks == [node("p", [leaf("plain")])]

    def test_empty_section(self, convert):
        blocks, _ = convert(macro("section"))
        assert blocks == []

    def test_column_alone(self, convert):
        blocks, _ = convert(macro("column", {}, "<p>alone</p>"))
        assert blocks == [node("p", [leaf("alone")])]


class TestInlineMacros:
    @pytest.mark.parametrize(
        "params,text,color",
        [
            ({"title": "done", "colour": "Green"}, "DONE", "#E3FCEF"),
            ({"colour": "Purple"}, "PURPLE", "#EAE6FF"),
            ({}, "STATUS", "#DFE1E6"),
        ],
    )
    def test_status(self, convert, issue_codes, params, text, color):
        blocks, ctx = convert("<p>" + macro("status", params) + "</p>")
        assert blocks[0]["children"] == [
            leaf(text, {"bold": True, "backgroundColor": color})
        ]
        assert issue_codes(ctx) == ["status_macro"]

    def test_jira(self, convert, settings):
        settings.macros["jira_url"] = "https://jira.example.org/"
        blocks, _ = convert("<p>" + macro("jira", {"key": "INT-1"}) + "</p>")
        link = blocks[0]["children"][1]
        assert link["url"] == "https://jira.example.org/browse/INT-1"
        assert link["children"] == [leaf("INT-1")]

    def test_jira_without_url(self, convert, issue_codes):
        blocks, ctx = convert("<p>" + macro("jira", {"key": "INT-1"}) + "</p>")
        assert blocks[0]["children"] == [leaf("INT-1")]
        assert issue_codes(ctx) == ["jira_without_url"]

    def test_jira_query(self, convert, issue_codes):
        blocks, ctx = convert(macro("jiraissues", {"jqlQuery": "project = INT"}))
        assert blocks[0]["type"] == "callout"
        assert issue_codes(ctx) == ["unsupported_macro"]


def _links(blocks) -> list[tuple[int, str]]:
    return [
        (block["indent"], block["children"][1]["children"][0]["text"])
        for block in blocks
    ]


class TestPageLists:
    def test_children(self, convert):
        blocks, _ = convert(macro("children"))
        assert _links(blocks) == [
            (1, "Snippets"),
            (1, "Setup Guide"),
            (1, "Legacy Notes"),
            (1, "Release Notes"),
        ]

    def test_children_of_other_page(self, convert):
        page = '<ac:link><ri:page ri:content-title="Home"/></ac:link>'
        blocks, _ = convert(macro("children", {"page": page}), page_id="101")
        assert len(blocks) == 4

    def test_children_of_missing_page(self, convert, issue_codes):
        page = '<ac:link><ri:page ri:content-title="Gone"/></ac:link>'
        blocks, ctx = convert(macro("children", {"page": page}))
        assert blocks == []
        assert issue_codes(ctx) == ["broken_page_link"]

    @pytest.mark.parametrize(
        "params,expected",
        [
            ({"depth": "2"}, 4),
            ({"depth": "all"}, 4),
            ({"all": "true"}, 4),
            ({"depth": "x"}, 4),
        ],
    )
    def test_children_depth(self, convert, params, expected):
        blocks, _ = convert(macro("children", params))
        assert len(blocks) == expected

    def test_pagetree(self, convert):
        blocks, _ = convert(macro("pagetree"), page_id="101")
        assert _links(blocks) == [
            (1, "Home"),
            (2, "Snippets"),
            (2, "Setup Guide"),
            (2, "Legacy Notes"),
            (2, "Release Notes"),
            (1, "Lost & Found"),
        ]


class TestAttachmentMacros:
    def test_attachments(self, convert):
        blocks, _ = convert(macro("attachments"))
        assert _links(blocks) == [(1, "diagram.png")]

    def test_gallery(self, convert):
        blocks, _ = convert(macro("gallery"))
        assert [block["url"] for block in blocks] == [f"../../resolveuid/{DIAGRAM_UID}"]

    @pytest.mark.parametrize(
        "name,params,page_id,uid",
        [
            (
                "view-file",
                {"name": '<ri:attachment ri:filename="spec.pdf"/>'},
                "101",
                SPEC_UID,
            ),
            (
                "viewpdf",
                {
                    "name": (
                        '<ri:attachment ri:filename="spec.pdf">'
                        '<ri:page ri:content-title="Setup Guide"/></ri:attachment>'
                    )
                },
                "100",
                SPEC_UID,
            ),
            ("multimedia", {"name": "diagram.png"}, "100", DIAGRAM_UID),
        ],
    )
    def test_file_viewer(self, convert, name, params, page_id, uid):
        blocks, _ = convert(macro(name, params), page_id=page_id)
        assert blocks[0]["children"][1]["url"].endswith(uid)

    @pytest.mark.parametrize("params", [{}, {"name": "nope.pdf"}])
    def test_file_viewer_broken(self, convert, issue_codes, params):
        blocks, ctx = convert(macro("view-file", params))
        assert blocks == []
        assert issue_codes(ctx) == ["broken_attachment_link"]

    @pytest.mark.parametrize(
        "params", [{"diagramName": "diagram"}, {"name": "diagram.png"}]
    )
    def test_diagram(self, convert, issue_codes, params):
        blocks, ctx = convert(macro("drawio", params))
        assert blocks[0]["url"].endswith(DIAGRAM_UID)
        assert issue_codes(ctx) == ["diagram_as_image"]

    @pytest.mark.parametrize("params", [{}, {"diagramName": "missing"}])
    def test_diagram_missing(self, convert, issue_codes, params):
        blocks, ctx = convert(macro("gliffy", params))
        assert blocks[0]["type"] == "callout"
        assert issue_codes(ctx) == ["unsupported_macro"]

    def test_diagram_file_is_not_an_image(self, convert, issue_codes):
        _, ctx = convert(macro("drawio", {"name": "spec.pdf"}), page_id="101")
        assert issue_codes(ctx) == ["unsupported_macro"]


class TestInclude:
    def test_include(self, convert, issue_codes):
        page = '<ac:link><ri:page ri:content-title="Snippets"/></ac:link>'
        blocks, ctx = convert(macro("include", {"": page}))
        assert blocks == [
            node("p", [leaf("Reusable snippet.")]),
            node("p", [leaf("Not part of the excerpt.")]),
        ]
        assert issue_codes(ctx) == ["include_snapshot"]

    def test_excerpt_include(self, convert):
        page = '<ri:page ri:content-title="Snippets"/>'
        blocks, _ = convert(macro("excerpt-include", {"": page}))
        assert blocks == [node("p", [leaf("Reusable snippet.")])]

    def test_excerpt_include_text_only(self, convert, export):
        # An excerpt body without child elements is still the excerpt
        export.bodies["102"].body = macro("excerpt", {}, "just text") + "<p>rest</p>"
        blocks, _ = convert(macro("excerpt-include", {"": "Snippets"}))
        assert blocks == [node("p", [leaf("just text")])]

    def test_excerpt_include_without_excerpt(self, convert):
        blocks, _ = convert(macro("excerpt-include", {"": "Setup Guide"}))
        assert blocks[0]["listStyleType"] == "decimal"

    def test_include_by_title_parameter(self, convert):
        blocks, _ = convert(macro("include", {"": "Snippets"}))
        assert len(blocks) == 2

    @pytest.mark.parametrize(
        "params,code",
        [
            ({"": "Gone"}, "broken_include"),
            ({}, "broken_include"),
            ({"": "Release Notes"}, "broken_include"),
            ({"": "Home"}, "include_loop"),
        ],
    )
    def test_broken(self, convert, issue_codes, params, code):
        blocks, ctx = convert(macro("include", params))
        assert blocks == []
        assert issue_codes(ctx) == [code]

    def test_nested_loop(self, convert, issue_codes, export):
        # Snippets includes Setup Guide, which includes Snippets
        export.bodies["102"].body = macro("include", {"": "Setup Guide"})
        blocks, ctx = convert(macro("include", {"": "Snippets"}))
        assert "include_loop" in issue_codes(ctx)
        assert blocks[0]["listStyleType"] == "decimal"


class TestUnsupported:
    def test_unsupported(self, convert, issue_codes):
        blocks, ctx = convert(
            macro("recently-updated", {"max": "5", "": "x", "empty": ""}, "<p>body</p>")
        )
        assert blocks[0] == node(
            "callout",
            [
                leaf("Unsupported Confluence macro: recently-updated", {"bold": True}),
                leaf("\ndefault: x"),
                leaf("\nmax: 5"),
            ],
            icon="🧩",
        )
        assert blocks[1] == node("p", [leaf("body")])
        assert [(i.code, i.detail) for i in ctx.issues] == [
            ("unsupported_macro", "recently-updated")
        ]

    def test_plain_body(self, convert):
        blocks, _ = convert(macro("html", plain="<b>raw</b>"))
        assert blocks[1]["type"] == "code_block"

    def test_old_macro_element(self, convert):
        blocks, _ = convert('<ac:macro ac:name="toc"/>')
        assert blocks == [node("toc")]
