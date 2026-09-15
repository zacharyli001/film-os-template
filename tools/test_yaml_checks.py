#!/usr/bin/env python3
"""Tests for the real/fallback YAML checks."""

from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from yaml_checks import demo_project_id_files, minimal_yaml_error, parse_yaml_file


class YamlChecksTest(unittest.TestCase):
    def test_bare_indented_text_is_caught(self) -> None:
        text = "fallback:\n  controller: codex-blender\n  use_only_when_preferred_stack_is_unavailable\n"
        error = minimal_yaml_error(text)
        self.assertIsNotNone(error)
        self.assertIn("line 3", error)

    def test_real_parser_rejects_bad_yaml(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "bad.yaml"
            path.write_text("fallback:\n  foo\n", encoding="utf-8")
            error = parse_yaml_file(path)
            if error is not None:
                self.assertTrue("line" in error.lower() or "yaml" in error.lower())

    def test_demo_project_id_is_detected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            path = root / "sample.yaml"
            path.write_text("schema_version: film-os/v1\nproject_id: DEMO\n", encoding="utf-8")
            self.assertEqual(demo_project_id_files(root, [path]), ["sample.yaml"])


if __name__ == "__main__":
    unittest.main()
