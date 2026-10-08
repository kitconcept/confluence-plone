from confluence_plone import get_logger
from confluence_plone.utils.console import report

import logging


class TestGetLogger:
    def test_default_log_file(self, test_dir):
        logger = get_logger()
        logger.info("hello")
        assert "INFO: hello" in (test_dir / "confluence-plone.log").read_text()
        assert logger.level == logging.INFO

    def test_same_logger(self):
        assert get_logger() is get_logger()

    def test_debug_from_settings(self, test_dir):
        (test_dir / "confluence-plone.toml").write_text(
            '[config]\ndebug = true\nlog_file = "custom.log"\n'
        )
        logger = get_logger()
        logger.debug("details")
        assert logger.level == logging.DEBUG
        assert "DEBUG: details" in (test_dir / "custom.log").read_text()


class TestReport:
    def test_report(self, test_dir, capsys):
        report("Converting")
        assert "Converting" in capsys.readouterr().out
        assert "INFO: Converting" in (test_dir / "confluence-plone.log").read_text()
