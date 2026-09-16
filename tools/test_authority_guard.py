#!/usr/bin/env python3
"""Behavior tests for the Film OS append-only authority guard."""

from __future__ import annotations

from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


GUARD = Path(__file__).with_name("check_authority_guard.py")
ACTOR = "member-one"
DIRECTOR = "zacharyli001"
PROPOSAL_ID = "20260913T120000Z_scene-three"


def command(root: Path, *args: str) -> str:
    result = subprocess.run(args, cwd=root, check=True, capture_output=True, text=True)
    return result.stdout.strip()


class AuthorityGuardTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        command(self.root, "git", "init", "-b", "main")
        command(self.root, "git", "config", "user.name", "Film OS Test")
        command(self.root, "git", "config", "user.email", "film-os-test@example.invalid")
        (self.root / "正式剧本.md").write_text("导演正式版本\n", encoding="utf-8")
        tools = self.root / "tools"
        tools.mkdir()
        (tools / "check_authority_guard.py").write_text("trusted guard\n", encoding="utf-8")
        command(self.root, "git", "add", ".")
        command(self.root, "git", "commit", "-m", "canonical base")
        self.base = command(self.root, "git", "rev-parse", "HEAD")

    def tearDown(self) -> None:
        self.temp.cleanup()

    @property
    def branch(self) -> str:
        return f"proposal/{ACTOR}/{PROPOSAL_ID}"

    @property
    def proposal_root(self) -> Path:
        return self.root / "submissions" / ACTOR / PROPOSAL_ID

    def add_valid_proposal(self, extra_relative: str = "01_剧本增量提案.md") -> str:
        command(self.root, "git", "switch", "-c", self.branch)
        self.proposal_root.mkdir(parents=True)
        (self.proposal_root / "PROPOSAL.yaml").write_text(
            "\n".join(
                [
                    "schema_version: film-os/proposal/v1",
                    f"proposal_id: {PROPOSAL_ID}",
                    f"author_github: {ACTOR}",
                    'created_at: "2026-09-13T12:00:00Z"',
                    f"base_main_commit: {self.base}",
                    "status: proposed",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        output = self.proposal_root / extra_relative
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text("非正式提案或衍生成果\n", encoding="utf-8")
        command(self.root, "git", "add", ".")
        command(self.root, "git", "commit", "-m", "member proposal")
        return command(self.root, "git", "rev-parse", "HEAD")

    def run_guard(self, head: str, actor: str = ACTOR, head_ref: str | None = None) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                sys.executable,
                str(GUARD),
                "--repo",
                str(self.root),
                "--base",
                self.base,
                "--head",
                head,
                "--actor",
                actor,
                "--head-ref",
                head_ref or self.branch,
                "--director",
                DIRECTOR,
            ],
            capture_output=True,
            text=True,
        )

    def test_member_append_only_proposal_passes(self) -> None:
        head = self.add_valid_proposal("storyboard/S003_SH010.md")
        result = self.run_guard(head)
        self.assertEqual(result.returncode, 0, result.stderr)

    def add_proposal_with_decision(self, decision_lines: list[str]) -> str:
        command(self.root, "git", "switch", "-c", self.branch)
        self.proposal_root.mkdir(parents=True)
        (self.proposal_root / "PROPOSAL.yaml").write_text(
            "\n".join(
                [
                    "schema_version: film-os/proposal/v1",
                    f"proposal_id: {PROPOSAL_ID}",
                    f"author_github: {ACTOR}",
                    'created_at: "2026-09-13T12:00:00Z"',
                    f"base_main_commit: {self.base}",
                    "status: proposed",
                    "director_decision:",
                    *decision_lines,
                    "",
                ]
            ),
            encoding="utf-8",
        )
        (self.proposal_root / "01_剧本增量提案.md").write_text(
            "非正式提案\n", encoding="utf-8"
        )
        command(self.root, "git", "add", ".")
        command(self.root, "git", "commit", "-m", "member proposal")
        return command(self.root, "git", "rev-parse", "HEAD")

    def test_continue_decision_is_accepted(self) -> None:
        head = self.add_proposal_with_decision(
            ["  status: continue", "  promoted_to_canon: false"]
        )
        result = self.run_guard(head)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_continue_decision_cannot_be_promoted(self) -> None:
        head = self.add_proposal_with_decision(
            ["  status: continue", "  promoted_to_canon: true"]
        )
        result = self.run_guard(head)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("promoted_to_canon", result.stderr)

    def test_member_cannot_record_adoption(self) -> None:
        head = self.add_proposal_with_decision(
            ["  status: adopted", "  promoted_to_canon: true"]
        )
        result = self.run_guard(head)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("不能自行记录 adopted", result.stderr)

    def test_decision_status_must_not_be_approved(self) -> None:
        head = self.add_proposal_with_decision(["  status: approved"])
        result = self.run_guard(head)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("director_decision.status", result.stderr)

    def test_proposal_file_may_use_chinese_name(self) -> None:
        head = self.add_valid_proposal("01_剧本增量提案.md")
        result = self.run_guard(head)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_member_modifying_canonical_script_fails(self) -> None:
        command(self.root, "git", "switch", "-c", self.branch)
        (self.root / "正式剧本.md").write_text("成员覆盖版本\n", encoding="utf-8")
        command(self.root, "git", "add", ".")
        command(self.root, "git", "commit", "-m", "overwrite script")
        head = command(self.root, "git", "rev-parse", "HEAD")
        result = self.run_guard(head)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("不能修改", result.stderr)

    def test_member_adding_to_canonical_directory_fails(self) -> None:
        command(self.root, "git", "switch", "-c", self.branch)
        canonical = self.root / "scenes/S003/shots"
        canonical.mkdir(parents=True)
        (canonical / "S003_SH010.yaml").write_text("not canon\n", encoding="utf-8")
        command(self.root, "git", "add", ".")
        command(self.root, "git", "commit", "-m", "inject storyboard")
        head = command(self.root, "git", "rev-parse", "HEAD")
        self.assertNotEqual(self.run_guard(head).returncode, 0)

    def test_member_using_wrong_branch_fails(self) -> None:
        head = self.add_valid_proposal()
        self.assertNotEqual(self.run_guard(head, head_ref="feature/scene-three").returncode, 0)

    def test_member_cannot_tamper_with_guard(self) -> None:
        self.add_valid_proposal()
        (self.root / "tools/check_authority_guard.py").write_text("always pass\n", encoding="utf-8")
        command(self.root, "git", "add", ".")
        command(self.root, "git", "commit", "-m", "tamper with guard")
        head = command(self.root, "git", "rev-parse", "HEAD")
        result = self.run_guard(head)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("不能修改", result.stderr)

    def test_member_cannot_submit_two_child_lines_together(self) -> None:
        self.add_valid_proposal()
        second_id = "20260913T130000Z_other-idea"
        second = self.root / "submissions" / ACTOR / second_id
        second.mkdir(parents=True)
        (second / "PROPOSAL.yaml").write_text(
            "\n".join(
                [
                    "schema_version: film-os/proposal/v1",
                    f"proposal_id: {second_id}",
                    f"author_github: {ACTOR}",
                    'created_at: "2026-09-13T13:00:00Z"',
                    f"base_main_commit: {self.base}",
                    "status: proposed",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        (second / "idea.md").write_text("another child line\n", encoding="utf-8")
        command(self.root, "git", "add", ".")
        command(self.root, "git", "commit", "-m", "two proposals")
        head = command(self.root, "git", "rev-parse", "HEAD")
        self.assertNotEqual(self.run_guard(head).returncode, 0)

    def test_member_cannot_fake_main_baseline(self) -> None:
        self.add_valid_proposal()
        manifest = self.proposal_root / "PROPOSAL.yaml"
        manifest.write_text(
            manifest.read_text(encoding="utf-8").replace(self.base, "deadbeef"),
            encoding="utf-8",
        )
        command(self.root, "git", "add", ".")
        command(self.root, "git", "commit", "-m", "fake baseline")
        head = command(self.root, "git", "rev-parse", "HEAD")
        self.assertNotEqual(self.run_guard(head).returncode, 0)

    def test_director_can_create_new_canonical_version(self) -> None:
        command(self.root, "git", "switch", "-c", "director/script-v02")
        (self.root / "正式剧本.md").write_text("导演正式新版本\n", encoding="utf-8")
        command(self.root, "git", "add", ".")
        command(self.root, "git", "commit", "-m", "director promotion")
        head = command(self.root, "git", "rev-parse", "HEAD")
        result = self.run_guard(head, actor=DIRECTOR, head_ref="director/script-v02")
        self.assertEqual(result.returncode, 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
