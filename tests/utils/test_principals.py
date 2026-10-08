from confluence_plone.utils.principals import PrincipalMapper
from confluence_plone.utils.principals import load_mapping

import pytest


class TestLoadMapping:
    def test_load(self, tmp_path):
        path = tmp_path / "users.csv"
        path.write_text(
            "confluence,principal\nJDoe,john.doe\nanna@example.org,anna\n,empty\nx,\n"
        )
        assert load_mapping(path) == {"jdoe": "john.doe", "anna@example.org": "anna"}

    def test_missing_column(self, tmp_path):
        path = tmp_path / "users.csv"
        path.write_text("user,principal\njdoe,john\n")
        with pytest.raises(ValueError, match="needs the columns"):
            load_mapping(path)

    def test_empty_file(self, tmp_path):
        path = tmp_path / "users.csv"
        path.write_text("")
        with pytest.raises(ValueError, match="needs the columns"):
            load_mapping(path)


class TestPrincipalMapper:
    @pytest.mark.parametrize(
        "strategy,value,expected",
        [
            ("username", "u1", "jdoe"),
            ("username", "jdoe", "jdoe"),
            ("email", "u1", "john@example.org"),
            ("key", "u1", "u1"),
            # A user without email falls back to the default principal
            ("email", "legacy", "admin"),
            ("username", "unknown", "admin"),
            ("username", None, "admin"),
        ],
    )
    def test_principal(self, export, settings, strategy, value, expected):
        settings.principals["strategy"] = strategy
        mapper = PrincipalMapper(export, settings)
        assert mapper.principal(value) == expected

    def test_unmapped(self, export, settings):
        mapper = PrincipalMapper(export, settings)
        mapper.principal("unknown")
        mapper.principal("unknown")
        mapper.principal(None)
        assert mapper.unmapped == {"unknown": 2}

    @pytest.mark.parametrize(
        "value,expected",
        [
            ("u1", "john"),
            ("u2", "anna"),
            ("unknown", "ghost"),
            ("legacy", "admin"),
        ],
    )
    def test_mapping(self, export, settings, value, expected):
        settings.principals["strategy"] = "email"
        mapping = {"jdoe": "john", "anna@example.org": "anna", "unknown": "ghost"}
        mapper = PrincipalMapper(export, settings, mapping)
        assert mapper.principal(value) == expected

    def test_unknown_strategy(self, export, settings):
        settings.principals["strategy"] = "magic"
        with pytest.raises(ValueError, match="Unknown principals strategy 'magic'"):
            PrincipalMapper(export, settings)

    @pytest.mark.parametrize(
        "value,expected",
        [("u1", "John Doe"), ("u2", "asmith"), ("unknown", "admin")],
    )
    def test_title(self, principals, value, expected):
        assert principals.title(value) == expected
