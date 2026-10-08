from confluence_plone.utils.settings import settings_to_toml

import tomlkit


class TestSettingsToToml:
    def test_round_trip(self):
        data = {
            "config": {"debug": False, "nested": {"values": ["a", "b"]}},
            "source": {"spaces": ["DEV"], "empty": []},
            "plain": "value",
        }
        text = tomlkit.dumps(settings_to_toml(data))
        assert tomlkit.parse(text).unwrap() == data

    def test_multiline_arrays(self):
        text = tomlkit.dumps(
            settings_to_toml({"a": {"many": ["x", "y"], "one": ["z"]}})
        )
        assert 'many = [\n    "x",\n    "y",\n]' in text
        assert 'one = ["z"]' in text
