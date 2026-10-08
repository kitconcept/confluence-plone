from confluence_plone.reader.source import ExportSource

import pytest
import zipfile


class TestExportSource:
    def test_directory(self, export_path):
        with ExportSource(export_path) as source, source.open_entities() as stream:
            assert stream.read(5) == b"<?xml"

    def test_entities_file(self, export_path):
        with ExportSource(export_path / "entities.xml") as source:
            assert source.find_attachment("100", "200", 2) == "attachments/100/200/2"

    def test_zip(self, export_zip):
        with ExportSource(export_zip) as source:
            with source.open_entities() as stream:
                assert stream.read(5) == b"<?xml"
            assert source.find_attachment("101", "201", 1) == "attachments/101/201/1"
            with source.open("attachments/101/201/1") as stream:
                assert stream.read().startswith(b"%PDF")

    def test_missing_path(self, tmp_path):
        with pytest.raises(FileNotFoundError, match="does not exist"):
            ExportSource(tmp_path / "nope.zip")

    def test_no_entities(self, tmp_path):
        with pytest.raises(FileNotFoundError, match=r"No entities\.xml"):
            ExportSource(tmp_path)

    def test_zip_without_entities(self, tmp_path):
        path = tmp_path / "empty.zip"
        with zipfile.ZipFile(path, "w") as archive:
            archive.writestr("other.txt", "nothing")
        with pytest.raises(FileNotFoundError, match=r"No entities\.xml"):
            ExportSource(path)

    def test_descriptor(self, export_path):
        with ExportSource(export_path) as source:
            descriptor = source.descriptor()
        assert descriptor["exportType"] == "space"
        assert descriptor["spaceKey"] == "DEV"
        assert "not a property line" not in descriptor

    def test_descriptor_missing(self, tmp_path):
        (tmp_path / "entities.xml").write_text("<hibernate-generic/>")
        with ExportSource(tmp_path) as source:
            assert source.descriptor() == {}


class TestFindAttachment:
    @pytest.fixture
    def source(self, tmp_path):
        (tmp_path / "entities.xml").write_text("<hibernate-generic/>")
        files = (
            "attachments/1/10/1",
            "attachments/1/10/2",
            "attachments/2/20/1",
            "attachments/3/20/1",
            "attachments/4/30/old",
            "attachments/4/30/new",
            "attachments/notes.txt",
        )
        for name in files:
            path = tmp_path / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(name)
        with ExportSource(tmp_path) as value:
            yield value

    @pytest.mark.parametrize(
        "container_id,attachment_id,version,expected",
        [
            ("1", "10", 2, "attachments/1/10/2"),
            # A missing version falls back to the highest one
            ("1", "10", 5, "attachments/1/10/2"),
            # The container breaks ties between files found elsewhere
            ("3", "20", 1, "attachments/3/20/1"),
            # A file under another container is still found
            ("9", "20", 1, "attachments/2/20/1"),
            (None, "20", 1, "attachments/2/20/1"),
            # Non-numeric versions are sorted by name
            ("4", "30", 1, "attachments/4/30/old"),
            ("1", "99", 1, None),
        ],
    )
    def test_find(self, source, container_id, attachment_id, version, expected):
        assert source.find_attachment(container_id, attachment_id, version) == expected
