#!/usr/bin/env python3
"""Offline tests for the Film OS member delivery workflow."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


TOOLS = Path(__file__).resolve().parent
START = TOOLS / "member_workspace_start.py"
FINISH = TOOLS / "member_workspace_finish.py"
SYNC = TOOLS / "sync_member_repositories.py"


class MemberWorkflowTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def run_command(self, cwd: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
        result = subprocess.run(
            [*args],
            cwd=cwd,
            text=True,
            capture_output=True,
            check=False,
        )
        if check and result.returncode != 0:
            self.fail(f"command failed: {' '.join(args)}\nstdout={result.stdout}\nstderr={result.stderr}")
        return result

    def git(self, cwd: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
        return self.run_command(cwd, "git", "-c", "core.quotePath=false", *args, check=check)

    def configure_identity(self, repo: Path) -> None:
        self.git(repo, "config", "user.name", "Film OS Test")
        self.git(repo, "config", "user.email", "film-os-test@example.com")

    def make_canonical(
        self,
        project_id: str = "TEST_PROJECT",
        with_authority: bool = False,
        member_remote: str | None = None,
    ) -> tuple[Path, Path, str]:
        work = self.root / "canonical-work"
        work.mkdir()
        self.git(work, "init", "-q", "-b", "main")
        self.configure_identity(work)
        (work / "PROJECT.yaml").write_text(
            "schema_version: film-os/v1\n"
            "project:\n"
            f"  id: {project_id}\n"
            "  title: Test Project\n",
            encoding="utf-8",
        )
        (work / "submissions").mkdir()
        (work / "submissions/README.md").write_text("# submissions\n", encoding="utf-8")
        (work / ".gitignore").write_text(".film-os-local/\n.film-os-member/\n__pycache__/\n", encoding="utf-8")
        if with_authority:
            (work / "tools").mkdir()
            shutil.copy2(TOOLS / "check_local_authority.py", work / "tools/check_local_authority.py")
            (work / "governance").mkdir()
            key = "test-director-key"
            key_hash = hashlib.sha256(key.encode("utf-8")).hexdigest()
            (work / "governance/AUTHORITY.yaml").write_text(
                "schema_version: film-os/authority/v1\n"
                f"project_id: {project_id}\n"
                "director:\n"
                "  github_username: tester\n"
                f"  local_key_sha256: {key_hash}\n",
                encoding="utf-8",
            )
            (work / ".film-os-local").mkdir()
            (work / ".film-os-local/DIRECTOR.key").write_text(key + "\n", encoding="utf-8")
            if not member_remote:
                self.fail("with_authority requires member_remote")
            (work / "governance/MEMBER_DELIVERY_REPOSITORIES.yaml").write_text(
                "schema_version: film-os/member-delivery-repositories/v1\n"
                f"project_id: {project_id}\n"
                "review_trigger:\n"
                "  phrases:\n"
                "    - 需要审批\n"
                "  behavior: fetch_all_then_review_only\n"
                "default_branch: main\n"
                "proposal_branch_prefix: proposal/\n"
                "repositories:\n"
                "  - member_id: MemberOne\n"
                "    display_name: Member One\n"
                f"    remote_url: {member_remote}\n"
                "    local_dir: member-review\n",
                encoding="utf-8",
            )
        self.git(work, "add", "-A")
        self.git(work, "commit", "-qm", "canonical baseline")
        bare = self.root / "canonical.git"
        self.git(work, "clone", "-q", "--bare", str(work), str(bare))
        return bare, work, self.git(work, "rev-parse", "HEAD").stdout.strip()

    def make_member_repo(self) -> tuple[Path, Path]:
        member = self.root / "member"
        member.mkdir()
        self.git(member, "init", "-q", "-b", "main")
        self.configure_identity(member)
        (member / "README.md").write_text("# member delivery repo\n", encoding="utf-8")
        self.git(member, "add", "-A")
        self.git(member, "commit", "-qm", "initial member readme")
        origin = self.root / "member-origin.git"
        self.git(member, "clone", "-q", "--bare", str(member), str(origin))
        self.git(member, "remote", "add", "origin", str(origin))
        self.git(member, "push", "-q", "-u", "origin", "main")
        return member, origin

    def fill_manifest(self, workspace: Path, slug: str = "test-proposal") -> Path:
        matches = list((workspace / "submissions").glob(f"*/*{slug}*/PROPOSAL.yaml"))
        if not matches:
            self.fail("proposal manifest not found")
        manifest = matches[0]
        text = manifest.read_text(encoding="utf-8")
        text = text.replace("proposal_type: pending_member_choice", "proposal_type: documentation_fix")
        text = text.replace("target_scope: pending_member_description", "target_scope: README.md")
        text = text.replace(
            "  请在提交前填写这份提案要解决的问题和希望导演审核的内容。",
            "  测试提案：验证成员工作流可以连续使用。",
        )
        text = text.replace(
            "  请在提交前填写依据、风险与预期影响。",
            "  这是离线测试，不包含真实项目内容。",
        )
        manifest.write_text(text, encoding="utf-8")
        return manifest

    def test_full_cycle_and_second_proposal(self) -> None:
        canonical, canonical_work, canonical_head = self.make_canonical()
        member, _ = self.make_member_repo()
        started = self.run_command(
            member,
            sys.executable,
            str(START),
            "--workspace",
            str(member),
            "--member-id",
            "MemberOne",
            "--canonical-url",
            str(canonical),
            "--slug",
            "test-proposal",
            "--adopt-main",
            "--push-main",
        )
        self.assertIn("ready_for_member_work", started.stdout)
        self.assertEqual(
            self.git(member, "rev-parse", "main^{tree}").stdout.strip(),
            self.git(member, "rev-parse", "canonical/main^{tree}").stdout.strip(),
        )
        first_branch = self.git(member, "branch", "--show-current").stdout.strip()
        self.assertTrue(first_branch.startswith("proposal/MemberOne/"))
        self.fill_manifest(member)

        finished = self.run_command(
            member,
            sys.executable,
            str(FINISH),
            "--workspace",
            str(member),
            "--member-id",
            "MemberOne",
        )
        self.assertIn("submitted_locally", finished.stdout)
        self.assertEqual(
            self.git(member, "rev-parse", "main^{tree}").stdout.strip(),
            self.git(member, "rev-parse", "canonical/main^{tree}").stdout.strip(),
        )
        self.assertEqual(self.git(member, "branch", "--show-current").stdout.strip(), first_branch)
        self.assertEqual(self.git(member, "status", "--porcelain=v1").stdout.strip(), "")

        (canonical_work / "new-canonical.txt").write_text("new baseline\n", encoding="utf-8")
        self.git(canonical_work, "add", "-A")
        self.git(canonical_work, "commit", "-qm", "advance canonical")
        new_canonical_head = self.git(canonical_work, "rev-parse", "HEAD").stdout.strip()
        self.git(canonical_work, "push", "-q", str(canonical), "main")

        second = self.run_command(
            member,
            sys.executable,
            str(START),
            "--workspace",
            str(member),
            "--member-id",
            "MemberOne",
            "--canonical-url",
            str(canonical),
            "--slug",
            "second-proposal",
        )
        self.assertIn("ready_for_member_work", second.stdout)
        self.assertEqual(
            self.git(member, "rev-parse", "main^{tree}").stdout.strip(),
            self.git(member, "rev-parse", "canonical/main^{tree}").stdout.strip(),
        )
        second_branch = self.git(member, "branch", "--show-current").stdout.strip()
        self.assertNotEqual(first_branch, second_branch)
        self.assertEqual(
            self.git(member, "rev-parse", "main^{tree}").stdout.strip(),
            self.git(member, "rev-parse", "canonical/main^{tree}").stdout.strip(),
        )
        session = (member / ".film-os-member/SESSION.yaml").read_text(encoding="utf-8")
        self.assertIn("status: \"working\"", session)
        self.assertIn(new_canonical_head, session)

    def test_finish_blocks_changes_outside_proposal(self) -> None:
        canonical, _, _ = self.make_canonical()
        member, _ = self.make_member_repo()
        self.run_command(
            member,
            sys.executable,
            str(START),
            "--workspace",
            str(member),
            "--member-id",
            "MemberOne",
            "--canonical-url",
            str(canonical),
            "--slug",
            "outside-check",
            "--adopt-main",
        )
        self.fill_manifest(member, "outside-check")
        (member / "outside.txt").write_text("must be blocked\n", encoding="utf-8")
        finished = self.run_command(
            member,
            sys.executable,
            str(FINISH),
            "--workspace",
            str(member),
            "--member-id",
            "MemberOne",
            check=False,
        )
        self.assertNotEqual(finished.returncode, 0)
        self.assertIn("提案目录外", finished.stderr)

    def test_sync_reports_proposal_branch_without_canonical_changes(self) -> None:
        member, _ = self.make_member_repo()
        canonical, project, canonical_head = self.make_canonical(
            with_authority=True,
            member_remote=str(self.root / "member-origin.git"),
        )
        self.run_command(
            member,
            sys.executable,
            str(START),
            "--workspace",
            str(member),
            "--member-id",
            "MemberOne",
            "--canonical-url",
            str(canonical),
            "--slug",
            "sync-check",
            "--adopt-main",
            "--push-main",
        )
        self.fill_manifest(member, "sync-check")
        self.run_command(
            member,
            sys.executable,
            str(FINISH),
            "--workspace",
            str(member),
            "--member-id",
            "MemberOne",
            "--push",
        )

        before = self.git(project, "rev-parse", "HEAD").stdout.strip()

        cache = self.root / "cache"
        synced = self.run_command(
            project,
            sys.executable,
            str(SYNC),
            "--project",
            str(project),
            "--cache-root",
            str(cache),
        )
        report = json.loads(synced.stdout)
        self.assertEqual(report["authority"], "director_verified")
        repositories = report["repositories"]
        self.assertEqual(len(repositories), 1)
        proposals = repositories[0]["proposals"]
        self.assertEqual(len(proposals), 1)
        self.assertTrue(proposals[0]["proposal_id"].endswith("_sync-check"))
        self.assertTrue(proposals[0]["base_exists_in_canonical"])
        self.assertEqual(self.git(project, "rev-parse", "HEAD").stdout.strip(), before)
        self.assertEqual(self.git(project, "status", "--porcelain=v1").stdout.strip(), "")
        self.assertTrue(repositories[0]["main_tree_matches_canonical"])


if __name__ == "__main__":
    unittest.main()
