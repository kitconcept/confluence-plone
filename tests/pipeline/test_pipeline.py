from . import REPORTS
from . import TYPES
from confluence_plone import pipeline

import csv
import json
import pytest
import shutil


@pytest.fixture
def dst(test_dir):
    return test_dir / "import"


@pytest.fixture
def result(export_path, dst, settings):
    return pipeline.convert(export_path, dst, settings)


@pytest.fixture
def load_item(dst, result):
    """Load the data.json of the item converted from a Confluence object."""

    def func(source_id: str) -> dict:
        uid = result.plan.by_source[source_id]
        return json.loads((dst / "content" / uid / "data.json").read_text())

    return func


class TestAnalyze:
    def test_analyze(self, export_path, test_dir):
        messages = []
        data, paths = pipeline.analyze(
            export_path, test_dir / "reports", messages.append
        )
        assert [path.name for path in paths] == ["inventory.json", "macros.csv"]
        assert json.loads(paths[0].read_text())["totals"] == data["totals"]
        assert messages[0].startswith("Reading ")

    def test_quiet(self, export_path, test_dir):
        data, _ = pipeline.analyze(export_path, test_dir / "reports")
        assert data["totals"]["pages"] == 7


class TestConvert:
    def test_types(self, result):
        assert dict(result.types) == TYPES

    def test_layout(self, dst, result):
        metadata = json.loads((dst / "content" / "__metadata__.json").read_text())
        assert len(metadata["_data_files_"]) == 9
        assert len(metadata["_blob_files_"]) == 2
        assert (dst / "discussions.json").exists()
        assert not (dst / "redirects.json").exists()

    def test_reports(self, result, settings):
        reports_dir = settings.config["reports_location"]
        assert [path.name for path in result.reports] == REPORTS
        items = list(
            csv.DictReader((reports_dir / "items.csv").read_text().splitlines())
        )
        assert len(items) == 9
        statuses = {row["source_id"]: row["status"] for row in items}
        assert statuses["100"] == "ok"
        assert statuses["101"] == "warning"
        assert statuses["space:10"] == "warning"

    def test_summary(self, result):
        summary = result.summary()
        assert summary["items"] == TYPES
        assert summary["skipped"] == 7
        assert summary["footer_comments"] == 3
        assert summary["inline_discussions"] == 1
        assert summary["issues"] == {"error": 1, "info": 3, "warning": 5}
        assert summary["unmapped_users"] == {}

    def test_workspace(self, load_item):
        data = load_item("space:10")
        assert data["@type"] == "Workspace"
        assert data["description"] == "Where the developers write things down."
        assert data["creators"] == ["jdoe"]
        assert data["created"] == "2024-01-10T09:00:00+00:00"

    def test_page(self, load_item):
        data = load_item("100")
        assert data["@id"] == "/dev/home"
        assert data["creators"] == ["jdoe"]
        assert data["contributors"] == ["asmith"]
        assert data["subjects"] == ["howto"]
        assert data["created"] == "2024-01-10T09:00:00+00:00"
        assert data["modified"] == "2024-02-01T10:30:00+00:00"
        assert data["review_state"] == "published"
        somersault = data["blocks"]["__somersault__"]
        assert somersault["value"][0]["type"] == "title"
        assert list(somersault["discussions"]) == ["ref-1"]

    def test_page_without_modification_date(self, load_item):
        data = load_item("102")
        assert data["modified"] == data["created"] == "2024-01-12T09:00:00+00:00"
        assert data["creators"] == ["admin"]

    def test_attachments(self, dst, load_item):
        image = load_item("200")
        assert image["@type"] == "Image"
        assert image["image"]["content-type"] == "image/png"
        assert (
            image["image"]["size"]
            == (dst / "content" / image["image"]["blob_path"]).stat().st_size
        )
        assert image["review_state"] is None
        pdf = load_item("201")
        assert pdf["file"]["filename"] == "spec.pdf"

    def test_discussions(self, dst, result):
        discussions = json.loads((dst / "discussions.json").read_text())
        home = result.plan.by_source["100"]
        assert list(discussions) == [home]
        assert len(discussions[home]["items"]) == 3

    def test_zip(self, export_zip, dst, settings):
        result = pipeline.convert(export_zip, dst, settings)
        assert dict(result.types) == TYPES

    def test_messages(self, export_path, dst, settings):
        messages = []
        pipeline.convert(export_path, dst, settings, messages.append)
        assert messages[1] == "Converting space DEV: Development"


class TestConvertSettings:
    def test_redirects(self, export_path, dst, settings):
        settings.redirects["enabled"] = True
        pipeline.convert(export_path, dst, settings)
        redirects = json.loads((dst / "redirects.json").read_text())
        assert (
            redirects["/Plone/display/DEV/Setup+Guide"] == "/Plone/dev/home/setup-guide"
        )
        assert len(redirects) == 6

    def test_no_footer_comments(self, export_path, dst, settings):
        settings.content["footer_comments"] = False
        result = pipeline.convert(export_path, dst, settings)
        assert result.footer_comments == 0
        assert json.loads((dst / "discussions.json").read_text()) == {}

    def test_mapping_file(self, export_path, dst, settings, test_dir):
        mapping = test_dir / "users.csv"
        mapping.write_text("confluence,principal\njdoe,john.doe\n")
        settings.principals["mapping_file"] = str(mapping)
        result = pipeline.convert(export_path, dst, settings)
        data = json.loads(
            (dst / "content" / result.plan.by_source["100"] / "data.json").read_text()
        )
        assert data["creators"] == ["john.doe"]

    def test_unmapped_users(self, export_path, dst, settings, tmp_path):
        src = tmp_path / "src"
        shutil.copytree(export_path, src)
        entities = src / "entities.xml"
        entities.write_text(
            entities.read_text().replace(
                "[CDATA[asmith]]></property>\n</object>",
                "[CDATA[ghost]]></property>\n</object>",
            )
        )
        result = pipeline.convert(src, dst, settings)
        assert result.unmapped_users == {"ghost": 2}
        assert result.summary()["unmapped_users"] == {"ghost": 2}

    def test_conversion_failure(self, export_path, dst, settings, monkeypatch):
        def broken(ctx):
            raise RuntimeError("boom")

        monkeypatch.setattr(pipeline, "convert_page", broken)
        result = pipeline.convert(export_path, dst, settings)
        failed = [i for i in result.issues if i.code == "conversion_failed"]
        assert len(failed) == 6
        assert failed[0].detail == "RuntimeError('boom')"
        statuses = {item.source_id: item.status for item in result.items}
        assert statuses["100"] == "error"

    def test_warnings_are_reported(self, tmp_path, dst, settings):
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "entities.xml").write_bytes(
            b"<hibernate-generic><object class='Space'><id name='id'>1</id>"
            b"<property name='key'>K\x08</property></object></hibernate-generic>"
        )
        messages = []
        pipeline.convert(tmp_path / "src", dst, settings, messages.append)
        assert "Warning: Removed 1 characters that XML 1.0 forbids" in messages
