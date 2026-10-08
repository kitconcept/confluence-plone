from confluence_plone.reader import ExportSource
from confluence_plone.reader import read_export


ENTITIES = """<hibernate-generic>
<object class="Space" package="x"><id name="id">1</id>
<property name="key">K</property><property name="name">{name}</property></object>
{tail}
"""


class TestReadExport:
    def test_directory(self, export):
        assert export.descriptor["spaceKey"] == "DEV"
        assert export.warnings == []

    def test_zip(self, export_zip):
        with ExportSource(export_zip) as source:
            export = read_export(source)
        assert len(export.pages) == 11

    def test_forbidden_characters(self, tmp_path):
        data = ENTITIES.format(name="Back\x08space", tail="</hibernate-generic>")
        (tmp_path / "entities.xml").write_bytes(data.encode())
        with ExportSource(tmp_path) as source:
            export = read_export(source)
        assert export.spaces["1"].name == "Backspace"
        assert export.warnings == ["Removed 1 characters that XML 1.0 forbids"]

    def test_malformed(self, tmp_path):
        data = ENTITIES.format(name="Name", tail="<object class='Space'")
        (tmp_path / "entities.xml").write_bytes(data.encode())
        with ExportSource(tmp_path) as source:
            export = read_export(source)
        assert export.spaces["1"].key == "K"
        assert export.warnings[0].startswith("entities.xml is malformed, recovered")
