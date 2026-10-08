"""Tests for confluence-plone."""

from pathlib import Path


RESOURCES = Path(__file__).parent / "_resources"
"""Test data, including a small Confluence export."""

EXPORT = RESOURCES / "export"
"""A hand-written Confluence export covering the supported features."""
