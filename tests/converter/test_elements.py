from . import DIAGRAM_UID
from . import SETUP_GUIDE_UID
from . import SPEC_UID
from . import WORKSPACE_UID
from confluence_plone.converter.core import leaf
from confluence_plone.converter.core import node
from confluence_plone.converter.elements import columns
from confluence_plone.converter.elements import emoji_from_id

import pytest


SETUP_URL = f"../../resolveuid/{SETUP_GUIDE_UID}"


class TestText:
    @pytest.mark.parametrize(
        "storage,expected",
        [
            ("<p>plain</p>", [node("p", [leaf("plain")])]),
            ("loose text", [node("p", [leaf("loose text")])]),
            ("<div>in a div</div>", [node("p", [leaf("in a div")])]),
            ("<p>   </p><p></p>", []),
            ("<h2>Title</h2>", [node("h2", [leaf("Title")])]),
            (
                "<p>a <strong>b</strong> <em>c</em> <u>d</u> <s>e</s></p>",
                [
                    node(
                        "p",
                        [
                            leaf("a "),
                            leaf("b", {"bold": True}),
                            leaf(" "),
                            leaf("c", {"italic": True}),
                            leaf(" "),
                            leaf("d", {"underline": True}),
                            leaf(" "),
                            leaf("e", {"strikethrough": True}),
                        ],
                    )
                ],
            ),
            (
                "<p><code>x</code><sub>2</sub><sup>3</sup></p>",
                [
                    node(
                        "p",
                        [
                            leaf("x", {"code": True}),
                            leaf("2", {"subscript": True}),
                            leaf("3", {"superscript": True}),
                        ],
                    )
                ],
            ),
            (
                "<p><strong><em>both</em></strong></p>",
                [node("p", [leaf("both", {"bold": True, "italic": True})])],
            ),
            ("<p>one<br/>two</p>", [node("p", [leaf("one\ntwo")])]),
            (
                '<p><span style="color: rgb(255,0,0); background-color: #eee; '
                'font-size: 9px">red</span></p>',
                [
                    node(
                        "p",
                        [
                            leaf(
                                "red",
                                {"color": "rgb(255,0,0)", "backgroundColor": "#eee"},
                            )
                        ],
                    )
                ],
            ),
            (
                '<p><font color="blue">blue</font></p>',
                [node("p", [leaf("blue", {"color": "blue"})])],
            ),
            ("<p><span>plain span</span></p>", [node("p", [leaf("plain span")])]),
            ("<p>a<!-- comment -->b</p>", [node("p", [leaf("ab")])]),
        ],
    )
    def test_convert(self, convert, storage, expected):
        blocks, _ = convert(storage)
        assert blocks == expected


class TestBlocks:
    def test_blockquote(self, convert):
        blocks, _ = convert(
            "<blockquote><p>quoted</p><ul><li>item</li></ul></blockquote>"
        )
        assert blocks[0] == node("blockquote", [leaf("quoted")])
        assert blocks[1]["listStyleType"] == "disc"

    def test_pre(self, convert):
        blocks, _ = convert("<pre>line 1\nline 2\n</pre>")
        assert blocks == [
            node(
                "code_block",
                [
                    node("code_line", [leaf("line 1")]),
                    node("code_line", [leaf("line 2")]),
                ],
            )
        ]

    def test_hr(self, convert):
        blocks, _ = convert("<hr/>")
        assert blocks == [node("hr")]

    def test_image_splits_paragraph(self, convert):
        blocks, _ = convert(
            '<p>before<img src="https://example.org/a.png" alt="A"/>after</p>'
        )
        assert [block["type"] for block in blocks] == ["p", "ploneBlock", "p"]
        assert blocks[1]["url"] == "https://example.org/a.png"
        assert blocks[1]["alt"] == "A"

    def test_img_without_source(self, convert):
        blocks, _ = convert("<p><img/>text</p>")
        assert blocks == [node("p", [leaf("text")])]

    @pytest.mark.parametrize(
        "storage,expected",
        [
            ('<p><time datetime="2026-10-09"/></p>', "2026-10-09"),
            ('<p><time datetime="2026-10-09T11:07:00"/></p>', "2026-10-09"),
        ],
    )
    def test_time(self, convert, storage, expected):
        blocks, _ = convert(storage)
        date = blocks[0]["children"][1]
        assert date == node("date", value=expected)

    def test_time_without_datetime(self, convert):
        blocks, _ = convert("<p><time>next week</time></p>")
        assert blocks == [node("p", [leaf("next week")])]

    @pytest.mark.parametrize(
        "storage,expected",
        [
            (
                '<p><a href="https://example.org">site</a></p>',
                ("https://example.org", "site"),
            ),
            (
                '<p><a href="https://example.org"></a></p>',
                ("https://example.org", "https://example.org"),
            ),
        ],
    )
    def test_a(self, convert, storage, expected):
        blocks, _ = convert(storage)
        link = blocks[0]["children"][1]
        assert (link["url"], link["children"][0]["text"]) == expected

    def test_a_without_href(self, convert):
        blocks, _ = convert("<p><a name='anchor'>text</a></p>")
        assert blocks == [node("p", [leaf("text")])]

    def test_unknown_confluence_element(self, convert, issue_codes):
        blocks, ctx = convert("<p><ac:unknown>kept</ac:unknown></p>")
        assert blocks == [node("p", [leaf("kept")])]
        assert issue_codes(ctx) == ["unknown_element"]

    def test_unknown_html_element(self, convert, issue_codes):
        blocks, ctx = convert("<p><abbr>HTML</abbr> stays</p>")
        assert blocks == [node("p", [leaf("HTML stays")])]
        assert issue_codes(ctx) == []

    def test_issue_reported_once(self, convert, issue_codes):
        _, ctx = convert("<p><ac:unknown>a</ac:unknown><ac:unknown>b</ac:unknown></p>")
        assert issue_codes(ctx) == ["unknown_element"]

    def test_ignored_elements(self, convert):
        blocks, _ = convert("<p>a<ac:placeholder>type here</ac:placeholder>b</p>")
        assert blocks == [node("p", [leaf("ab")])]


class TestLists:
    def test_nested(self, convert):
        blocks, _ = convert("<ul><li>one<ul><li>nested</li></ul></li><li>two</li></ul>")
        assert [
            (b["children"][0]["text"], b["indent"], b["listStyleType"]) for b in blocks
        ] == [
            ("one", 1, "disc"),
            ("nested", 2, "disc"),
            ("two", 1, "disc"),
        ]

    def test_ordered(self, convert):
        blocks, _ = convert("<ol><li>a</li><li>b</li><li>c</li></ol>")
        assert [b.get("listStart") for b in blocks] == [None, 2, 3]
        assert {b["listStyleType"] for b in blocks} == {"decimal"}

    def test_item_with_paragraphs(self, convert):
        blocks, _ = convert("<ul><li><p>first</p><p>more</p><pre>code</pre></li></ul>")
        assert blocks[0]["listStyleType"] == "disc"
        assert blocks[1] == node("p", [leaf("more")], indent=1)
        assert blocks[2]["type"] == "code_block"

    def test_empty_item(self, convert):
        blocks, _ = convert("<ul><li></li><span>ignored</span></ul>")
        assert blocks == [node("p", indent=1, listStyleType="disc")]

    def test_tasks(self, convert):
        storage = (
            "<ac:task-list>"
            "<ac:task><ac:task-id>1</ac:task-id><ac:task-status>complete</ac:task-status>"
            "<ac:task-body>done</ac:task-body></ac:task>"
            "<ac:task><ac:task-status>incomplete</ac:task-status><ac:task-body>todo"
            "<ac:task-list><ac:task><ac:task-body>sub</ac:task-body></ac:task></ac:task-list>"
            "</ac:task-body></ac:task>"
            "<ac:task><ac:task-status>complete</ac:task-status></ac:task>"
            "</ac:task-list>"
        )
        blocks, _ = convert(storage)
        assert [
            (b.get("indent"), b.get("checked"), b["listStyleType"]) for b in blocks
        ] == [
            (1, True, "todo"),
            (1, False, "todo"),
            (2, False, "todo"),
            (1, True, "todo"),
        ]


class TestTables:
    def test_table(self, convert):
        storage = (
            "<table><colgroup><col/></colgroup><tbody>"
            '<tr><th colspan="2">Head</th></tr>'
            '<tr><td rowspan="2">a</td><td colspan="x">b</td></tr>'
            "<tr><td></td></tr><caption>ignored</caption>"
            "</tbody></table>"
        )
        blocks, _ = convert(storage)
        table = blocks[0]
        rows = table["children"]
        assert table["type"] == "table"
        assert rows[0]["children"][0] == node(
            "th", [node("p", [leaf("Head")])], colSpan=2
        )
        assert rows[1]["children"][0]["rowSpan"] == 2
        assert "colSpan" not in rows[1]["children"][1]
        assert rows[2]["children"][0] == node("td", [node("p")])

    def test_rows_without_tbody(self, convert):
        blocks, _ = convert("<table><tr><td>x</td></tr><tr></tr></table>")
        assert len(blocks[0]["children"]) == 1

    def test_empty_table(self, convert):
        blocks, _ = convert("<table></table>")
        assert blocks == []


class TestLinks:
    @pytest.mark.parametrize(
        "storage,url,text",
        [
            (
                '<ac:link><ri:page ri:content-title="Setup Guide"/></ac:link>',
                SETUP_URL,
                "Setup Guide",
            ),
            (
                '<ac:link><ri:page ri:content-title="setup guide" ri:space-key="DEV"/>'
                "<ac:link-body><strong>bold</strong> body</ac:link-body></ac:link>",
                SETUP_URL,
                "bold",
            ),
            (
                '<ac:link ac:anchor="install">'
                '<ri:page ri:content-title="Setup Guide"/></ac:link>',
                f"{SETUP_URL}#install",
                "Setup Guide",
            ),
            (
                '<ac:link><ri:page ri:content-title="@self"/></ac:link>',
                "../../resolveuid/59a9673062955d68951493a360cd931a",
                "@self",
            ),
            (
                '<ac:link><ri:attachment ri:filename="diagram.png"/></ac:link>',
                f"../../resolveuid/{DIAGRAM_UID}",
                "diagram.png",
            ),
            (
                '<ac:link><ri:attachment ri:filename="spec.pdf">'
                '<ri:page ri:content-title="Setup Guide"/></ri:attachment>'
                "<ac:plain-text-link-body><![CDATA[the spec]]>"
                "</ac:plain-text-link-body></ac:link>",
                f"../../resolveuid/{SPEC_UID}",
                "the spec",
            ),
            (
                '<ac:link><ri:space ri:space-key="DEV"/></ac:link>',
                f"../../resolveuid/{WORKSPACE_UID}",
                "Development",
            ),
            (
                '<ac:link><ri:url ri:value="https://example.org"/></ac:link>',
                "https://example.org",
                "https://example.org",
            ),
        ],
    )
    def test_link(self, convert, issue_codes, storage, url, text):
        blocks, ctx = convert(f"<p>{storage}</p>")
        link = blocks[0]["children"][1]
        assert link["type"] == "a"
        assert link["url"] == url
        assert link["children"][0]["text"] == text
        assert issue_codes(ctx) == []

    @pytest.mark.parametrize(
        "storage,text,code",
        [
            (
                '<ac:link><ri:page ri:content-title="Nowhere"/></ac:link>',
                "Nowhere",
                "broken_page_link",
            ),
            (
                '<ac:link><ri:page ri:content-title="Gone"/>'
                "<ac:link-body>label</ac:link-body></ac:link>",
                "label",
                "broken_page_link",
            ),
            (
                '<ac:link><ri:attachment ri:filename="nope.zip"/></ac:link>',
                "nope.zip",
                "broken_attachment_link",
            ),
            (
                '<ac:link><ri:attachment ri:filename="x.png">'
                '<ri:page ri:content-title="Gone"/>'
                "</ri:attachment></ac:link>",
                "x.png",
                "broken_attachment_link",
            ),
            (
                '<ac:link><ri:space ri:space-key="OPS"/></ac:link>',
                "OPS",
                "broken_space_link",
            ),
            (
                '<ac:link><ri:blog-post ri:content-title="News"/></ac:link>',
                "News",
                "blog_post_link",
            ),
            (
                '<ac:link ac:anchor="top"><ac:link-body>up</ac:link-body></ac:link>',
                "up",
                None,
            ),
            ('<ac:link ac:anchor="top"></ac:link>', "top", None),
        ],
    )
    def test_unresolved(self, convert, issue_codes, storage, text, code):
        blocks, ctx = convert(f"<p>{storage}</p>")
        assert blocks == [node("p", [leaf(text)])]
        assert issue_codes(ctx) == ([code] if code else [])

    def test_unsupported(self, convert, issue_codes):
        blocks, ctx = convert("<p>x<ac:link><ri:shortcut ri:key='g'/></ac:link></p>")
        assert blocks == [node("p", [leaf("x")])]
        assert issue_codes(ctx) == ["unsupported_link"]

    @pytest.mark.parametrize(
        "storage,key,value",
        [
            ('<ri:user ri:userkey="u1"/>', "jdoe", "John Doe"),
            ('<ri:user ri:account-id="u2"/>', "asmith", "asmith"),
            ('<ri:user ri:username="jdoe"/>', "jdoe", "John Doe"),
            ('<ri:user ri:userkey="ghost"/>', "admin", "admin"),
        ],
    )
    def test_mention(self, convert, storage, key, value):
        blocks, _ = convert(f"<p><ac:link>{storage}</ac:link></p>")
        mention = blocks[0]["children"][1]
        assert mention == node("mention", key=key, value=value)

    def test_path_link_style(self, convert, settings):
        settings.target["link_style"] = "path"
        blocks, _ = convert(
            '<p><ac:link><ri:page ri:content-title="Setup Guide"/></ac:link></p>'
        )
        assert blocks[0]["children"][1]["url"] == "/dev/home/setup-guide"


class TestImages:
    def test_attachment(self, convert, issue_codes):
        blocks, ctx = convert(
            '<ac:image ac:align="left" ac:alt="Diagram">'
            '<ri:attachment ri:filename="diagram.png"/></ac:image>'
        )
        assert blocks == [
            {
                **node("ploneBlock"),
                "@type": "plateimage",
                "url": f"../../resolveuid/{DIAGRAM_UID}",
                "alt": "Diagram",
                "align": "left",
                "size": "l",
            }
        ]
        assert issue_codes(ctx) == []

    def test_url(self, convert):
        blocks, _ = convert(
            '<ac:image ac:title="T"><ri:url ri:value="https://example.org/i.png"/></ac:image>'
        )
        assert blocks[0]["url"] == "https://example.org/i.png"
        assert blocks[0]["alt"] == "T"
        assert blocks[0]["align"] == "center"

    def test_file_becomes_link(self, convert):
        blocks, _ = convert(
            '<ac:image><ri:attachment ri:filename="spec.pdf">'
            '<ri:page ri:content-title="Setup Guide"/>'
            "</ri:attachment></ac:image>"
        )
        assert blocks[0]["children"][1]["url"] == f"../../resolveuid/{SPEC_UID}"

    @pytest.mark.parametrize(
        "storage,detail",
        [
            (
                '<ac:image><ri:attachment ri:filename="nope.png"/></ac:image>',
                "nope.png",
            ),
            ("<ac:image></ac:image>", "image without source"),
        ],
    )
    def test_broken(self, convert, storage, detail):
        blocks, ctx = convert(storage)
        assert blocks == []
        assert [(i.code, i.detail) for i in ctx.issues] == [("broken_image", detail)]


class TestEmoticons:
    @pytest.mark.parametrize(
        "storage,text,issues",
        [
            ('<ac:emoticon ac:name="smile"/>', "🙂", 0),
            ('<ac:emoticon ac:name="clipboard" ac:emoji-id="1f4cb"/>', "📋", 0),
            ('<ac:emoticon ac:emoji-id="31-20e3"/>', "1⃣", 0),
            ('<ac:emoticon ac:emoji-fallback="🥳"/>', "🥳", 0),
            (
                '<ac:emoticon ac:emoji-id="atlassian-x" ac:emoji-fallback=":x:"/>',
                ":x:",
                1,
            ),
            ('<ac:emoticon ac:name="mystery"/>', "(mystery)", 1),
        ],
    )
    def test_emoticon(self, convert, storage, text, issues):
        blocks, ctx = convert(f"<p>{storage}</p>")
        assert blocks[0]["children"] == [leaf(text)]
        assert len(ctx.issues) == issues

    @pytest.mark.parametrize(
        "emoji_id,expected",
        [("1f642", "🙂"), ("", ""), ("not-hex", "")],
    )
    def test_emoji_from_id(self, emoji_id, expected):
        assert emoji_from_id(emoji_id) == expected


class TestInlineComments:
    def test_marker(self, convert):
        blocks, ctx = convert(
            '<p><ac:inline-comment-marker ac:ref="r1">x</ac:inline-comment-marker>'
            '<ac:inline-comment-marker ac:ref="r1">y</ac:inline-comment-marker></p>'
        )
        assert blocks[0]["children"] == [
            leaf("xy", {"comment": True, "comment_r1": True})
        ]
        assert ctx.inline_refs == ["r1"]

    def test_marker_without_ref(self, convert):
        blocks, ctx = convert(
            "<p><ac:inline-comment-marker>x</ac:inline-comment-marker></p>"
        )
        assert blocks[0]["children"] == [leaf("x")]
        assert ctx.inline_refs == []

    def test_disabled(self, convert, settings):
        settings.content["inline_comments"] = False
        blocks, ctx = convert(
            '<p><ac:inline-comment-marker ac:ref="r1">x</ac:inline-comment-marker></p>'
        )
        assert blocks[0]["children"] == [leaf("x")]
        assert ctx.inline_refs == []


class TestLayout:
    def test_layout(self, convert):
        storage = (
            "<ac:layout>"
            '<ac:layout-section ac:type="single">'
            "<ac:layout-cell><p>full</p></ac:layout-cell></ac:layout-section>"
            '<ac:layout-section ac:type="two_left_sidebar">'
            "<ac:layout-cell><p>side</p></ac:layout-cell><ac:layout-cell><p>main</p></ac:layout-cell>"
            "</ac:layout-section>"
            '<ac:layout-section ac:type="two_equal">'
            "<ac:layout-cell><p>only</p></ac:layout-cell><ac:layout-cell></ac:layout-cell>"
            "</ac:layout-section>"
            '<ac:layout-section ac:type="two_equal">'
            "<ac:layout-cell/><ac:layout-cell/></ac:layout-section>"
            "<p>not a section</p>"
            "</ac:layout>"
        )
        blocks, _ = convert(storage)
        assert blocks[0] == node("p", [leaf("full")])
        assert blocks[1]["type"] == "column_group"
        assert [c["width"] for c in blocks[1]["children"]] == ["33%", "67%"]
        assert blocks[2] == node("p", [leaf("only")])
        assert len(blocks) == 3

    @pytest.mark.parametrize(
        "widths,expected",
        [
            (None, ["50%", "50%"]),
            (["10%"], ["50%", "50%"]),
            (["30%", "70%"], ["30%", "70%"]),
        ],
    )
    def test_columns(self, widths, expected):
        group = columns([[node("p")], []], widths)
        assert [c["width"] for c in group["children"]] == expected
        assert group["children"][1]["children"] == [node("p")]


class TestAdfExtension:
    def test_fallback(self, convert, issue_codes):
        blocks, ctx = convert(
            "<ac:adf-extension><ac:adf-node/><ac:adf-fallback><p>fallback</p></ac:adf-fallback></ac:adf-extension>"
        )
        assert blocks == [node("p", [leaf("fallback")])]
        assert issue_codes(ctx) == ["adf_extension"]

    def test_without_fallback(self, convert):
        blocks, _ = convert("<ac:adf-extension><ac:adf-node/></ac:adf-extension>")
        assert blocks == []
