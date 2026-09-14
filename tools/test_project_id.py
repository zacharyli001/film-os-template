#!/usr/bin/env python3
"""Tests for the shared Film OS project-id rule."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path


TOOLS = Path(__file__).resolve().parent
sys.path.insert(0, str(TOOLS))

from create_project import validate_project_id as launcher_project_id  # noqa: E402
from member_common import project_id_from_text, validate_project_id  # noqa: E402


class ProjectIdTest(unittest.TestCase):
    def test_legacy_ids_still_work(self) -> None:
        self.assertEqual(validate_project_id("DEMO"), "DEMO")
        self.assertEqual(launcher_project_id("FESTER"), "FESTER")

    def test_readable_ids_with_underscores_work(self) -> None:
        value = "PUTREFACT_CARNIVAL"
        self.assertEqual(validate_project_id(value), value)
        self.assertEqual(launcher_project_id(value), value)

    def test_rejects_invalid_ids(self) -> None:
        for value in ("_BAD", "BAD-NAME", "BAD NAME", "A", "X" * 65):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    validate_project_id(value)

    def test_reads_nested_project_id(self) -> None:
        text = "schema_version: film-os/v1\nproject:\n  id: PUTREFACT_CARNIVAL\n  title: Test\n"
        self.assertEqual(project_id_from_text(text), "PUTREFACT_CARNIVAL")


if __name__ == "__main__":
    unittest.main()

