from confluence_plone.writer import ExportWriter
from confluence_plone.writer import json_dumps
from confluence_plone.writer import safe_filename

import io
import json
import pytest


class TestHelpers:
    def test_json_dumps(self):
        assert (
            json_dumps({"b": 1, "a": [1]}) == b'{\n  "a": [\n    1\n  ],\n  "b": 1\n}'
        )

    @pytest.mark.parametrize(
        "filename,expected",
        [
            ("report.pdf", "report.pdf"),
            ("a/b\\c.txt", "a_b_c.txt"),
            (" .. ", "fallback"),
        ],
    )
    def test_safe_filename(self, filename, expected):
        assert safe_filename(filename, "fallback") == expected


class TestExportWriter:
    @pytest.fixture
    def writer(self, test_dir) -> ExportWriter:
        return ExportWriter(test_dir / "import")

    def test_item_and_metadata(self, writer, plan):
        item = plan.item_for("200")
        writer.write_blob(item, "image", "d.png", io.BytesIO(b"png"))
        path = writer.write_item(item, {"@id": item.path}, "jdoe")
        metadata = json.loads(writer.write_metadata().read_text())
        assert json.loads(path.read_text()) == {"@id": "/dev/home/diagram.png"}
        assert (writer.content / item.uid / "image" / "d.png").read_bytes() == b"png"
        assert metadata == {
            "__version__": "1.0.0",
            "_blob_files_": [f"{item.uid}/image/d.png"],
            "_data_files_": [f"{item.uid}/data.json"],
            "default_page": {},
            "local_permissions": {},
            "local_roles": {item.uid: {"local_roles": {"jdoe": ["Owner"]}}},
            "ordering": {item.uid: 0},
            "relations": [],
        }

    def test_write_json(self, writer):
        path = writer.write_json("discussions.json", {})
        assert path == writer.dst / "discussions.json"
        assert path.read_text() == "{}"
