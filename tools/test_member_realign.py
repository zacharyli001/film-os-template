#!/usr/bin/env python3
"""Offline tests for the member main realignment flow."""

from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


TOOLS = Path(__file__).resolve().parent
START = TOOLS / "member_workspace_start.py"


class MemberRealignTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def run_command(self, cwd: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
        result = subprocess.run([*args], cwd=cwd, text=True, capture_output=True, check=False)
        if check and result.returncode != 0:
            self.fail(f"command failed: {' '.join(args)}\nstdout={result.stdout}\nstderr={result.stderr}")
        return result

    def git(self, cwd: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
        return self.run_command(cwd, "git", "-c", "core.quotePath=false", *args, check=check)

    def configure_identity(self, repo: Path) -> None:
        self.git(repo, "config", "user.name", "Film OS Test")
        self.git(repo, "config", "user.email", "film-os-test@example.com")

    def make_canonical(self) -> tuple[Path, Path, str]:
        work = self.root / "canonical-work"
        work.mkdir()
        self.git(work, "init", "-q", "-b", "main")
        self.configure_identity(work)
        (work / "PROJECT.yaml").write_text(
            "schema_version: film-os/v1\nproject:\n  id: REALIGN_TEST\n  title: Realign Test\n",
            encoding="utf-8",
        )
        (work / "submissions").mkdir()
        (work / "submissions/README.md").write_text("# submissions\n", encoding="utf-8")
        self.git(work, "add", "-A")
        self.git(work, "commit", "-qm", "canonical baseline")
        bare = self.root / "canonical.git"
        self.git(work, "clone", "-q", "--bare", str(work), str(bare))
        return bare, work, self.git(work, "rev-parse", "HEAD").stdout.strip()

    def advance_canonical(self, bare: Path, work: Path, name: str) -> str:
        (work / name).write_text("advance\n", encoding="utf-8")
        self.git(work, "add", "-A")
        self.git(work, "commit", "-qm", f"advance {name}")
        self.git(work, "push", "-q", str(bare), "main")
        return self.git(work, "rev-parse", "HEAD").stdout.strip()

    def make_member(self) -> tuple[Path, Path]:
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

    def fetch_canonical(self, member: Path, canonical: Path) -> None:
        existing = self.git(member, "remote", "get-url", "canonical", check=False)
        if existing.returncode != 0:
            self.git(member, "remote", "add", "canonical", str(canonical))
        self.git(member, "fetch", "-q", "canonical", "main")

    def commit_tree(self, member: Path, parent: str, message: str, extra_parents: list[str] | None = None) -> str:
        tree = self.git(member, "rev-parse", "canonical/main^{tree}").stdout.strip()
        command = ["commit-tree", tree, "-p", parent, "-m", message]
        for extra in extra_parents or []:
            command.extend(["-p", extra])
        return self.git(member, *command).stdout.strip()

    def start(
        self,
        member: Path,
        canonical: Path,
        slug: str,
        *extra: str,
        check: bool = True,
    ) -> subprocess.CompletedProcess[str]:
        return self.run_command(
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
            slug,
            "--realign-main",
            *extra,
            check=check,
        )

    def start_normal(
        self,
        member: Path,
        canonical: Path,
        slug: str,
        *extra: str,
        check: bool = True,
    ) -> subprocess.CompletedProcess[str]:
        return self.run_command(
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
            slug,
            *extra,
            check=check,
        )

    def cleanup_proposal(self, member: Path) -> None:
        self.git(member, "switch", "main", check=False)
        proposal_root = member / "submissions/MemberOne"
        if proposal_root.exists():
            shutil.rmtree(proposal_root)
        session = member / ".film-os-member/SESSION.yaml"
        if session.exists():
            session.unlink()

    def assert_mirror(self, member: Path, canonical: Path) -> None:
        self.fetch_canonical(member, canonical)
        self.assertEqual(
            self.git(member, "rev-parse", "main^{tree}").stdout.strip(),
            self.git(member, "rev-parse", "canonical/main^{tree}").stdout.strip(),
        )

    def test_main_behind_mirror_can_advance(self) -> None:
        canonical, work, _ = self.make_canonical()
        member, _ = self.make_member()
        first = self.start(member, canonical, "baseline", "--push-main")
        self.assertIn("ready_for_member_work", first.stdout)
        self.cleanup_proposal(member)
        self.advance_canonical(canonical, work, "canonical-two.txt")
        second = self.start(member, canonical, "behind", "--push-main")
        payload = json.loads(second.stdout)
        self.assertEqual(payload["realign"]["action"], "mirror_rebuilt")
        self.assert_mirror(member, canonical)

    def test_old_style_sync_commit_is_rebuilt(self) -> None:
        canonical, work, _ = self.make_canonical()
        member, origin = self.make_member()
        self.fetch_canonical(member, canonical)
        old_main = self.git(member, "rev-parse", "main").stdout.strip()
        old_style = self.commit_tree(member, old_main, "old style sync")
        self.git(member, "reset", "--hard", old_style)
        self.git(member, "push", "-q", "origin", "main")
        self.advance_canonical(canonical, work, "canonical-two.txt")
        result = self.start(member, canonical, "old-style", "--push-main")
        payload = json.loads(result.stdout)
        self.assertEqual(payload["realign"]["action"], "mirror_rebuilt")
        tag = payload["realign"]["backup_tag"]
        remote_tag = self.git(member, "ls-remote", "origin", f"refs/tags/{tag}").stdout.strip()
        self.assertTrue(remote_tag)
        self.assert_mirror(member, canonical)
        parents = self.git(member, "rev-list", "--parents", "-n", "1", "main").stdout.split()
        self.assertGreaterEqual(len(parents), 3)

    def test_no_common_ancestor_is_rebuilt(self) -> None:
        canonical, work, _ = self.make_canonical()
        member, _ = self.make_member()
        self.advance_canonical(canonical, work, "canonical-two.txt")
        result = self.start(member, canonical, "no-ancestor", "--push-main")
        payload = json.loads(result.stdout)
        self.assertEqual(payload["realign"]["action"], "mirror_rebuilt")
        self.assert_mirror(member, canonical)
        parents = self.git(member, "rev-list", "--parents", "-n", "1", "main").stdout.split()
        self.assertGreaterEqual(len(parents), 3)

    def test_already_aligned_is_idempotent(self) -> None:
        canonical, _, _ = self.make_canonical()
        member, _ = self.make_member()
        self.start(member, canonical, "baseline", "--push-main")
        self.cleanup_proposal(member)
        before = self.git(member, "tag", "--list", "archive/member-main-before-mirror-*").stdout.splitlines()
        result = self.start(member, canonical, "idempotent", "--push-main")
        payload = json.loads(result.stdout)
        self.assertIn(payload["realign"]["action"], {"already_exact", "already_mirror"})
        after = self.git(member, "tag", "--list", "archive/member-main-before-mirror-*").stdout.splitlines()
        self.assertEqual(before, after)
        self.assert_mirror(member, canonical)

    def test_local_main_behind_origin_is_fast_forwarded(self) -> None:
        canonical, work, _ = self.make_canonical()
        member, _ = self.make_member()
        self.fetch_canonical(member, canonical)
        initial = self.git(member, "rev-parse", "main").stdout.strip()
        m1 = self.commit_tree(member, initial, "mirror one")
        self.git(member, "reset", "--hard", m1)
        self.git(member, "push", "-q", "origin", "main")
        self.advance_canonical(canonical, work, "canonical-two.txt")
        self.fetch_canonical(member, canonical)
        canonical_two = self.git(member, "rev-parse", "canonical/main").stdout.strip()
        m2 = self.commit_tree(member, m1, "mirror two", extra_parents=[canonical_two])
        self.git(member, "reset", "--hard", m2)
        self.git(member, "push", "-q", "origin", "main")
        self.git(member, "reset", "--hard", m1)
        result = self.start(member, canonical, "behind-origin", "--push-main")
        payload = json.loads(result.stdout)
        self.assertEqual(payload["realign"]["action"], "already_mirror")
        self.assertEqual(
            self.git(member, "rev-parse", "main").stdout.strip(),
            self.git(member, "rev-parse", "origin/main").stdout.strip(),
        )

    def test_dirty_worktree_stops(self) -> None:
        canonical, _, _ = self.make_canonical()
        member, _ = self.make_member()
        (member / "dirty.txt").write_text("dirty\n", encoding="utf-8")
        result = self.start(member, canonical, "dirty", check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("工作区必须干净", result.stderr)

    def test_auto_sync_old_style_local_to_remote_mirror(self) -> None:
        canonical, _, _ = self.make_canonical()
        member, _ = self.make_member()
        self.fetch_canonical(member, canonical)
        initial = self.git(member, "rev-parse", "main").stdout.strip()
        old_style = self.commit_tree(member, initial, "old style sync")
        self.git(member, "reset", "--hard", old_style)
        self.git(member, "push", "-q", "origin", "main")
        canonical_head = self.git(member, "rev-parse", "canonical/main").stdout.strip()
        mirror = self.commit_tree(member, old_style, "mirror", extra_parents=[canonical_head])
        self.git(member, "reset", "--hard", mirror)
        self.git(member, "push", "-q", "origin", "main")
        self.git(member, "reset", "--hard", old_style)
        result = self.start_normal(member, canonical, "auto-old-style")
        self.assertIn("ready_for_member_work", result.stdout)
        self.assertEqual(
            self.git(member, "rev-parse", "main").stdout.strip(),
            self.git(member, "rev-parse", "origin/main").stdout.strip(),
        )
        self.assert_mirror(member, canonical)

    def test_auto_sync_multi_generation(self) -> None:
        canonical, work, _ = self.make_canonical()
        member, _ = self.make_member()
        self.fetch_canonical(member, canonical)
        initial = self.git(member, "rev-parse", "main").stdout.strip()
        c1 = self.git(member, "rev-parse", "canonical/main").stdout.strip()
        m1 = self.commit_tree(member, initial, "mirror one", extra_parents=[c1])
        self.git(member, "reset", "--hard", m1)
        self.git(member, "push", "-q", "origin", "main")
        self.advance_canonical(canonical, work, "canonical-two.txt")
        self.fetch_canonical(member, canonical)
        c2 = self.git(member, "rev-parse", "canonical/main").stdout.strip()
        m2 = self.commit_tree(member, m1, "mirror two", extra_parents=[c2])
        self.git(member, "reset", "--hard", m2)
        self.git(member, "push", "-q", "origin", "main")
        self.git(member, "reset", "--hard", m1)
        result = self.start_normal(member, canonical, "auto-multi")
        self.assertIn("ready_for_member_work", result.stdout)
        self.assertEqual(
            self.git(member, "rev-parse", "main").stdout.strip(),
            self.git(member, "rev-parse", "origin/main").stdout.strip(),
        )
        self.assert_mirror(member, canonical)

    def test_auto_sync_diverged_stops_with_realign_hint(self) -> None:
        canonical, _, _ = self.make_canonical()
        member, _ = self.make_member()
        self.fetch_canonical(member, canonical)
        initial = self.git(member, "rev-parse", "main").stdout.strip()
        c1 = self.git(member, "rev-parse", "canonical/main").stdout.strip()
        mirror = self.commit_tree(member, initial, "mirror", extra_parents=[c1])
        self.git(member, "reset", "--hard", mirror)
        self.git(member, "push", "-q", "origin", "main")
        self.git(member, "reset", "--hard", initial)
        (member / "local-only.txt").write_text("local\n", encoding="utf-8")
        self.git(member, "add", "local-only.txt")
        self.git(member, "commit", "-qm", "local divergent commit")
        result = self.start_normal(member, canonical, "auto-diverged", check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("--realign-main", result.stderr)

    def test_auto_sync_local_ahead_stops_and_reports(self) -> None:
        canonical, _, _ = self.make_canonical()
        member, _ = self.make_member()
        (member / "ahead.txt").write_text("ahead\n", encoding="utf-8")
        self.git(member, "add", "ahead.txt")
        self.git(member, "commit", "-qm", "local ahead commit")
        result = self.start_normal(member, canonical, "auto-ahead", check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("领先", result.stderr)
        self.assertIn("local ahead commit", result.stderr)

    def test_auto_sync_already_aligned_is_idempotent(self) -> None:
        canonical, _, _ = self.make_canonical()
        member, _ = self.make_member()
        self.start(member, canonical, "baseline", "--push-main")
        self.cleanup_proposal(member)
        before = self.git(member, "rev-parse", "main").stdout.strip()
        result = self.start_normal(member, canonical, "auto-idempotent")
        self.assertIn("ready_for_member_work", result.stdout)
        self.assertEqual(self.git(member, "rev-parse", "main").stdout.strip(), before)

    def test_auto_sync_dirty_worktree_stops(self) -> None:
        canonical, _, _ = self.make_canonical()
        member, _ = self.make_member()
        (member / "dirty.txt").write_text("dirty\n", encoding="utf-8")
        result = self.start_normal(member, canonical, "auto-dirty", check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("工作区必须干净", result.stderr)


if __name__ == "__main__":
    unittest.main()
