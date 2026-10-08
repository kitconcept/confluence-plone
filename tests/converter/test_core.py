from confluence_plone.converter.core import BREAK
from confluence_plone.converter.core import Macro
from confluence_plone.converter.core import assign_ids
from confluence_plone.converter.core import has_content
from confluence_plone.converter.core import is_inline
from confluence_plone.converter.core import leaf
from confluence_plone.converter.core import node
from confluence_plone.converter.core import normalize_inline
from confluence_plone.converter.core import plate_text
from confluence_plone.converter.storage import parse_storage

import pytest


class TestNodes:
    def test_leaf(self):
        assert leaf("x", {"bold": True}) == {"text": "x", "bold": True}
        assert leaf("x") == {"text": "x"}

    def test_node_defaults_to_empty_leaf(self):
        assert node("hr") == {"type": "hr", "children": [{"text": ""}]}

    @pytest.mark.parametrize(
        "item,expected",
        [
            ({"text": "x"}, True),
            (node("a"), True),
            (node("mention"), True),
            (node("date"), True),
            (node("p"), False),
        ],
    )
    def test_is_inline(self, item, expected):
        assert is_inline(item) is expected

    @pytest.mark.parametrize(
        "nodes,expected",
        [
            ([leaf("  ")], False),
            ([], False),
            ([leaf(" x ")], True),
            ([node("mention")], True),
        ],
    )
    def test_has_content(self, nodes, expected):
        assert has_content(nodes) is expected


class TestNormalizeInline:
    @pytest.mark.parametrize(
        "nodes,expected",
        [
            ([leaf("  a  \n b ")], [leaf("a b")]),
            ([leaf("a "), leaf("b")], [leaf("a b")]),
            (
                [leaf("a", {"bold": True}), leaf(" b")],
                [leaf("a", {"bold": True}), leaf(" b")],
            ),
            (
                [leaf("a"), {**leaf("\n"), BREAK: True}, leaf("b")],
                [leaf("a\nb")],
            ),
            # Inline elements get empty text leaves around them
            ([node("mention")], [leaf(""), node("mention"), leaf("")]),
            (
                [node("mention"), node("date")],
                [leaf(""), node("mention"), leaf(""), node("date"), leaf("")],
            ),
            ([leaf(" "), node("a"), leaf(" ")], [leaf(""), node("a"), leaf("")]),
            ([], [leaf("")]),
        ],
    )
    def test_normalize(self, nodes, expected):
        assert normalize_inline(nodes) == expected


class TestPlateText:
    def test_text(self):
        nodes = [
            node("p", [leaf("Hello "), node("mention", value="John")]),
            node("p", [node("a", [leaf("link")])]),
        ]
        assert plate_text(nodes) == "Hello John\nlink\n"


class TestAssignIds:
    def test_assign(self):
        nodes = [node("p", [leaf("a"), node("a", [leaf("b")])]), node("hr", id="keep")]
        assign_ids(nodes, "x-")
        assert nodes[0]["id"] == "x-0001"
        assert nodes[0]["children"][1]["id"] == "x-0002"
        assert nodes[1]["id"] == "keep"
        assert "id" not in nodes[0]["children"][0]


class TestMacro:
    @pytest.fixture
    def macro(self) -> Macro:
        root = parse_storage(
            '<ac:structured-macro ac:name="Code">'
            '<ac:parameter ac:name="language">python</ac:parameter>'
            '<ac:parameter ac:name="">default</ac:parameter>'
            "<ac:plain-text-body><![CDATA[print(1)]]></ac:plain-text-body>"
            "<ac:rich-text-body><p>rich</p></ac:rich-text-body>"
            "<ac:other/>"
            "</ac:structured-macro>"
        )
        return Macro.from_element(root[0])

    def test_name(self, macro):
        assert macro.name == "code"

    def test_parameters(self, macro):
        assert macro.parameters == {"language": "python", "": "default"}
        assert set(macro.parameter_elements) == {"language", ""}

    def test_bodies(self, macro):
        assert macro.plain_body == "print(1)"
        assert macro.rich_body is not None

    @pytest.mark.parametrize(
        "names,default,expected",
        [
            (("language",), "", "python"),
            (("title", "language"), "", "python"),
            (("title",), "none", "none"),
        ],
    )
    def test_get(self, macro, names, default, expected):
        assert macro.get(*names, default=default) == expected
