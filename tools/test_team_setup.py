#!/usr/bin/env python3
"""Offline tests for Film OS team setup."""

from __future__ import annotations

import hashlib
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


TOOLS = Path(__file__).resolve().parent
TEAM_SETUP = TOOLS / "team_setup.py"


class TeamSetupTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.project = Path(self.temp.name) / "project"
        (self.project / "governance").mkdir(parents=True)
        (self.project / "tools").mkdir()
        (self.project / ".film-os-local").mkdir()
        shutil.copy2(TOOLS / "check_local_authority.py", self.project / "tools/check_local_authority.py")
        key = "test-director-key"
        key_hash = hashlib.sha256(key.encode("utf-8")).hexdigest()
        (self.project / "PROJECT.yaml").write_text(
            "schema_version: film-os/v1\n"
            "project:\n"
            "  id: TEAM_TEST\n"
            "  title: Team Test\n",
            encoding="utf-8",
        )
        (self.project / "governance/AUTHORITY.yaml").write_text(
            "schema_version: film-os/authority/v1\n"
            "project_id: TEAM_TEST\n"
            "director:\n"
            "  github_username: zacharyli001\n"
            f"  local_key_sha256: {key_hash}\n",
            encoding="utf-8",
        )
        (self.project / ".film-os-local/DIRECTOR.key").write_text(key + "\n", encoding="utf-8")
        (self.project / "项目工作区").mkdir()

    def tearDown(self) -> None:
        self.temp.cleanup()

    def run_setup(self, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
        result = subprocess.run(
            [sys.executable, str(TEAM_SETUP), "--project", str(self.project), *args],
            text=True,
            capture_output=True,
            check=False,
        )
        if check and result.returncode != 0:
            self.fail(f"team setup failed\nstdout={result.stdout}\nstderr={result.stderr}")
        return result

    def test_create_and_update_team(self) -> None:
        self.run_setup(
            "--director-name",
            "Zac",
            "--director-github",
            "zacharyli001",
            "--expected-size",
            "3",
            "--member",
            "Yoe|Yoecobx|编剧|https://github.com/fester-studio/fester-yoe-delivery.git",
            "--member",
            "Sarah|Sarah|美术|https://github.com/fester-studio/fester-sarah-delivery.git",
        )
        team = (self.project / "governance/TEAM.yaml").read_text(encoding="utf-8")
        self.assertIn("team_size: 3", team)
        self.assertIn('display_name: "Zac"', team)
        self.assertIn('github_username: "Yoecobx"', team)
        self.assertIn('github_username: "Sarah"', team)
        rendered = (self.project / "项目工作区/00_团队与权限.md").read_text(encoding="utf-8")
        self.assertIn("Yoe", rendered)
        self.assertIn("Sarah", rendered)
        delivery = (self.project / "governance/MEMBER_DELIVERY_REPOSITORIES.yaml").read_text(encoding="utf-8")
        self.assertIn("member_id: \"Yoecobx\"", delivery)
        self.assertIn("member_id: \"Sarah\"", delivery)

        self.run_setup("--member", "Yoe|Yoecobx|故事架构|https://github.com/fester-studio/fester-yoe-delivery.git")
        updated = (self.project / "governance/TEAM.yaml").read_text(encoding="utf-8")
        self.assertIn('role: "故事架构"', updated)

    def test_expected_size_mismatch_is_blocked(self) -> None:
        result = self.run_setup(
            "--director-name",
            "Zac",
            "--director-github",
            "zacharyli001",
            "--expected-size",
            "3",
            check=False,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("团队人数不一致", result.stderr)


if __name__ == "__main__":
    unittest.main()

