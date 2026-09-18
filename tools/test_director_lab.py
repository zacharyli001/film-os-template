#!/usr/bin/env python3
"""Offline tests for the director exploration lab."""

from __future__ import annotations

import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


TOOLS = Path(__file__).resolve().parent
DIRECTOR_LAB = TOOLS / "director_lab.py"


class DirectorLabTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.project = self.root / "project"
        self.lab = self.root / "director-lab"
        (self.project / "governance").mkdir(parents=True)
        (self.project / "tools").mkdir()
        (self.project / ".film-os-local").mkdir()
        (self.project / "02_团队审核").mkdir()
        shutil.copy2(TOOLS / "check_local_authority.py", self.project / "tools/check_local_authority.py")
        key = "director-lab-test-key"
        key_hash = hashlib.sha256(key.encode("utf-8")).hexdigest()
        (self.project / "PROJECT.yaml").write_text(
            "schema_version: film-os/v1\nproject:\n  id: DIRECTOR_LAB_TEST\n  title: Director Lab Test\n",
            encoding="utf-8",
        )
        (self.project / "governance/AUTHORITY.yaml").write_text(
            "schema_version: film-os/authority/v1\n"
            "project_id: DIRECTOR_LAB_TEST\n"
            "director:\n"
            "  github_username: zacharyli001\n"
            f"  local_key_sha256: {key_hash}\n",
            encoding="utf-8",
        )
        (self.project / ".film-os-local/DIRECTOR.key").write_text(key + "\n", encoding="utf-8")
        self.git(self.project, "init", "-q", "-b", "main")
        self.configure_identity(self.project)
        (self.project / "README.md").write_text("# project\n", encoding="utf-8")
        self.git(self.project, "add", "-A")
        self.git(self.project, "commit", "-qm", "project init")

    def tearDown(self) -> None:
        self.temp.cleanup()

    def env(self) -> dict[str, str]:
        values = os.environ.copy()
        values.update(
            {
                "GIT_AUTHOR_NAME": "Film OS Test",
                "GIT_AUTHOR_EMAIL": "film-os-test@example.com",
                "GIT_COMMITTER_NAME": "Film OS Test",
                "GIT_COMMITTER_EMAIL": "film-os-test@example.com",
            }
        )
        return values

    def run_command(self, cwd: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
        result = subprocess.run(
            [*args],
            cwd=cwd,
            text=True,
            capture_output=True,
            check=False,
            env=self.env(),
        )
        if check and result.returncode != 0:
            self.fail(f"command failed: {' '.join(args)}\nstdout={result.stdout}\nstderr={result.stderr}")
        return result

    def git(self, cwd: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
        return self.run_command(cwd, "git", "-c", "core.quotePath=false", *args, check=check)

    def configure_identity(self, repo: Path) -> None:
        self.git(repo, "config", "user.name", "Film OS Test")
        self.git(repo, "config", "user.email", "film-os-test@example.com")

    def lab_command(self, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
        return self.run_command(
            self.project,
            sys.executable,
            str(DIRECTOR_LAB),
            "--project",
            str(self.project),
            "--lab",
            str(self.lab),
            *args,
            check=check,
        )

    def test_private_to_shared_to_promoted(self) -> None:
        init = self.lab_command("init")
        self.assertIn("initialized", init.stdout)
        self.assertIn("探索素材的来源", (self.lab / "README.md").read_text(encoding="utf-8"))
        created = self.lab_command("new", "--title", "Hero Kernel")
        self.assertIn("EX-001", created.stdout)
        exploration = self.lab / "探索/EX-001_hero-kernel"
        self.assertTrue((exploration / "EXPLORATION.yaml").is_file())
        manifest_text = (exploration / "EXPLORATION.yaml").read_text(encoding="utf-8")
        self.assertIn("status: exploring", manifest_text)
        self.assertIn("sources: []", manifest_text)

        shared = self.lab_command("share", "--id", "EX-001", "--commit-main")
        self.assertIn("shared", shared.stdout)
        discussion = self.project / "02_团队审核/探索讨论/EX-001_讨论版"
        self.assertTrue((discussion / "讨论版.md").is_file())
        self.assertIn("探索版，不是正式设定", (discussion / "讨论版.md").read_text(encoding="utf-8"))
        self.assertIn(
            "visibility: \"team_discussion\"",
            (exploration / "EXPLORATION.yaml").read_text(encoding="utf-8"),
        )
        log = self.git(self.project, "log", "--oneline", "-1").stdout
        self.assertIn("share EX-001", log)

        parked = self.lab_command("park", "--id", "EX-001", "--note", "later")
        self.assertIn("paused", parked.stdout)
        self.assertIn("status: \"paused\"", (exploration / "EXPLORATION.yaml").read_text(encoding="utf-8"))

        promoted = self.lab_command(
            "mark-promoted",
            "--id",
            "EX-001",
            "--note",
            "adopted",
            "--canonical-summary",
            "Hero kernel v1",
            "--commit-main",
        )
        self.assertIn("promoted", promoted.stdout)
        self.assertTrue((exploration / "PROMOTION.yaml").is_file())
        self.assertTrue((discussion / "PROMOTION.yaml").is_file())
        exploration_text = (exploration / "EXPLORATION.yaml").read_text(encoding="utf-8")
        self.assertIn("status: \"adopted\"", exploration_text)
        self.assertIn('promotion_status: "promoted"', exploration_text)

    def test_legacy_exploration_without_sources_is_compatible(self) -> None:
        self.lab_command("init")
        created = self.lab_command("new", "--title", "Legacy Exploration")
        self.assertIn("EX-001", created.stdout)
        exploration = self.lab / "探索/EX-001_legacy-exploration"
        manifest = exploration / "EXPLORATION.yaml"
        legacy_text = "\n".join(
            line for line in manifest.read_text(encoding="utf-8").splitlines() if not line.startswith("sources:")
        )
        manifest.write_text(legacy_text + "\n", encoding="utf-8")
        self.git(self.lab, "add", "-A")
        self.git(self.lab, "commit", "-qm", "legacy exploration without sources")

        listed = self.lab_command("list")
        self.assertIn("EX-001", listed.stdout)
        shared = self.lab_command("share", "--id", "EX-001", "--commit-main")
        self.assertIn("shared", shared.stdout)
        parked = self.lab_command("park", "--id", "EX-001", "--note", "legacy")
        self.assertIn("paused", parked.stdout)
        promoted = self.lab_command(
            "mark-promoted",
            "--id",
            "EX-001",
            "--note",
            "legacy",
            "--canonical-summary",
            "legacy promotion",
            "--commit-main",
        )
        self.assertIn("promoted", promoted.stdout)

    def test_lab_must_be_outside_project(self) -> None:
        result = self.run_command(
            self.project,
            sys.executable,
            str(DIRECTOR_LAB),
            "--project",
            str(self.project),
            "--lab",
            str(self.project / "inside-lab"),
            "init",
            check=False,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("正式项目文件夹之外", result.stderr)


if __name__ == "__main__":
    unittest.main()
