from confluence_plone.utils.ids import MAX_ID_LENGTH
from confluence_plone.utils.ids import make_uid
from confluence_plone.utils.ids import normalize_id
from confluence_plone.utils.ids import unique_id

import pytest


class TestNormalizeId:
    @pytest.mark.parametrize(
        "value,expected",
        [
            ("Home", "home"),
            ("Setup Guide", "setup-guide"),
            ("Lost & Found", "lost-found"),
            # "ß" has no ASCII decomposition, so it is dropped
            ("Überblick: Größe", "uberblick-groe"),
            ("diagram.png", "diagram.png"),
            ("  --Spaced--  ", "spaced"),
            ("What is Confluence? (step 1 of 9)", "what-is-confluence-step-1-of-9"),
            ("日本語", "item"),
            ("", "item"),
        ],
    )
    def test_normalize(self, value, expected):
        assert normalize_id(value) == expected

    def test_fallback(self):
        assert normalize_id("???", fallback="page-1") == "page-1"

    def test_max_length(self):
        result = normalize_id("word " * 40)
        assert len(result) <= MAX_ID_LENGTH
        assert not result.endswith("-")


class TestUniqueId:
    @pytest.mark.parametrize(
        "value,existing,expected",
        [
            ("home", set(), "home"),
            ("home", {"home"}, "home-1"),
            ("home", {"home", "home-1"}, "home-2"),
            ("diagram.png", {"diagram.png"}, "diagram-1.png"),
            (".hidden", {".hidden"}, ".hidden-1"),
        ],
    )
    def test_unique(self, value, existing, expected):
        assert unique_id(value, existing) == expected
        assert expected in existing


class TestMakeUid:
    def test_stable(self):
        assert make_uid("page", "100") == make_uid("page", "100")

    def test_differs_by_kind(self):
        assert make_uid("page", "100") != make_uid("attachment", "100")

    def test_format(self):
        uid = make_uid("page", "100")
        assert len(uid) == 32
        assert int(uid, 16)
