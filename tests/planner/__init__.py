"""Tests for the planner."""

#: Paths of the planned items of the test export, in plan order.
PLANNED_PATHS = [
    "/dev",
    "/dev/home",
    "/dev/home/diagram.png",
    "/dev/lost-found",
    "/dev/home/snippets",
    "/dev/home/setup-guide",
    "/dev/home/setup-guide/spec.pdf",
    "/dev/home/legacy-notes",
    "/dev/home/release-notes",
]

#: Skipped objects of the test export: (id, reason).
SKIPPED = [
    ("11", "archived space"),
    ("103", "status draft"),
    ("106", "blog posts are not converted"),
    ("107", "status deleted"),
    ("202", "file missing from the export"),
    ("204", "status deleted"),
    ("12", "personal space"),
]
