"""Exercise real SQLite storage, retries, and cross-project board isolation.

Also runnable offline with: python -m unittest discover -s tests/hermes_cli -p test_portfolio.py
"""
import os
import subprocess
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from hermes_cli import kanban_db as kb
from hermes_cli import portfolio


class PortfolioTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "portfolio"
        self.env = patch.dict(os.environ, {"HERMES_KANBAN_HOME": str(self.root),
                                          "HERMES_HOME": str(self.root)}, clear=False)
        self.env.start()
        self.addCleanup(self.env.stop)
        for key in ("HERMES_KANBAN_DB", "HERMES_KANBAN_BOARD", "HERMES_DELEGATED_CHILD_CONTEXT"):
            os.environ.pop(key, None)

    def configure_routing(self, project="open-system", category="engineering"):
        from hermes_cli.profiles import get_profile_dir
        for role in portfolio.ROLES[category]:
            profile = get_profile_dir(f"{project}-{category}-{role}")
            profile.mkdir(parents=True)
            (profile / "config.yaml").write_text("model: test-only\n")
        repo = Path(self.temp.name) / project
        subprocess.run(["git", "init", str(repo)], check=True, capture_output=True)
        subprocess.run(["git", "-C", str(repo), "remote", "add", "origin",
                        f"https://github.com/hillstreet-ph/{project}.git"], check=True)
        kb.write_board_metadata(project, default_workdir=str(repo))
        return repo

    def test_missing_profiles_creates_no_task(self):
        portfolio.onboard(apply=True)
        with self.assertRaisesRegex(ValueError, "Missing dedicated"):
            portfolio.intake("open-system", "engineering", "Goal", "id", apply=True)
        with kb.connect_closing(board="open-system") as conn:
            self.assertEqual(kb.list_tasks(conn), [])

    def test_profile_alias_to_default_rejected(self):
        from hermes_cli.profiles import get_profile_dir
        portfolio.onboard(apply=True)
        self.configure_routing()
        profile = get_profile_dir("open-system-engineering-coordinator")
        (profile / "config.yaml").unlink()
        profile.rmdir()
        profile.symlink_to(self.root, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, "Missing dedicated"):
            portfolio.intake("open-system", "engineering", "Goal", "id", apply=True)
        with kb.connect_closing(board="open-system") as conn:
            self.assertEqual(kb.list_tasks(conn), [])

    def test_missing_or_cross_project_workdir_creates_no_task(self):
        portfolio.onboard(apply=True)
        repo = self.configure_routing()
        kb.write_board_metadata("open-system", default_workdir="")
        with self.assertRaisesRegex(ValueError, "default_workdir"):
            portfolio.intake("open-system", "engineering", "Goal", "id", apply=True)
        kb.write_board_metadata("open-system", default_workdir=str(repo))
        subprocess.run(["git", "-C", str(repo), "remote", "set-url", "origin",
                        "https://github.com/hillstreet-ph/open-connect.git"], check=True)
        with self.assertRaisesRegex(ValueError, "does not match"):
            portfolio.intake("open-system", "engineering", "Goal", "id", apply=True)
        with kb.connect_closing(board="open-system") as conn:
            self.assertEqual(kb.list_tasks(conn), [])

    def test_dry_run_does_not_create_storage(self):
        self.assertEqual(len(portfolio.onboard()), 5)
        portfolio.intake("open-box", "data", "Organize verified source references", "source:123")
        self.assertFalse(self.root.exists())

    def test_onboarding_preserves_metadata_and_is_idempotent(self):
        self.assertTrue(all(row["action"] == "created" for row in portfolio.onboard(apply=True)))
        kb.write_board_metadata("open-box", name="Existing title", archived=True)
        metadata = kb.board_metadata_path("open-box").read_bytes()
        self.assertTrue(all(row["action"] == "existing" for row in portfolio.onboard(apply=True)))
        self.assertEqual(kb.board_metadata_path("open-box").read_bytes(), metadata)
        self.assertEqual(len({kb.kanban_db_path(project) for project in portfolio.PROJECTS}), 5)

    def test_intake_retries_and_project_isolation(self):
        portfolio.onboard(apply=True)
        self.configure_routing()
        first = portfolio.intake("open-system", "engineering", "Implement routing", "issue:45", apply=True)
        retry = portfolio.intake("open-system", "engineering", "Implement routing", "issue:45", apply=True)
        self.assertEqual(first["task_id"], retry["task_id"])
        with kb.connect_closing(board="open-system") as conn:
            tasks = kb.list_tasks(conn)
            self.assertEqual(len(tasks), 1)
            self.assertEqual(tasks[0].status, "blocked")
            self.assertEqual(tasks[0].workspace_kind, "worktree")
            self.assertEqual(tasks[0].workspace_path, str(Path(self.temp.name) / "open-system"))
            self.assertEqual(tasks[0].assignee, "open-system-engineering-coordinator")
        with kb.connect_closing(board="open-connect") as conn:
            self.assertEqual(kb.list_tasks(conn), [])

    def test_dispatch_recompute_cannot_promote_intake_and_replay_preserves_activation(self):
        portfolio.onboard(apply=True)
        self.configure_routing()
        result = portfolio.intake("open-system", "engineering", "Goal", "sticky", apply=True)
        with kb.connect_closing(board="open-system") as conn:
            self.assertEqual(kb.recompute_ready(conn), 0)
            self.assertEqual(kb.get_task(conn, result["task_id"]).status, "blocked")
            self.assertEqual(kb.get_task(conn, result["task_id"]).block_kind, "needs_input")
            self.assertTrue(kb.unblock_task(conn, result["task_id"]))
            self.assertEqual(kb.get_task(conn, result["task_id"]).status, "ready")
            event_count = len(kb.list_events(conn, result["task_id"]))
        replay = portfolio.intake("open-system", "engineering", "Goal", "sticky", apply=True)
        self.assertEqual(replay["task_id"], result["task_id"])
        self.assertEqual(replay["status"], "ready")
        with kb.connect_closing(board="open-system") as conn:
            self.assertEqual(len(kb.list_events(conn, result["task_id"])), event_count)

    def test_native_initial_block_backward_compatibility_and_validation(self):
        portfolio.onboard(apply=True)
        with kb.connect_closing(board="open-system") as conn:
            task_id = kb.create_task(conn, title="Legacy recoverable block", initial_status="blocked")
            self.assertEqual(kb.recompute_ready(conn), 1)
            self.assertEqual(kb.get_task(conn, task_id).status, "ready")
            for reason in ("", "   ", 123):
                with self.subTest(reason=reason), self.assertRaises(ValueError):
                    kb.create_task(conn, title="Invalid", initial_status="blocked", initial_block_reason=reason)
            with self.assertRaises(ValueError):
                kb.create_task(conn, title="Invalid", initial_block_reason="Requires blocked")
            self.assertEqual(len(kb.list_tasks(conn)), 1)

    def test_worker_or_pinned_context_rejected(self):
        for key in ("HERMES_KANBAN_DB", "HERMES_KANBAN_BOARD", "HERMES_DELEGATED_CHILD_CONTEXT"):
            with self.subTest(key=key), patch.dict(os.environ, {key: "pinned"}):
                with self.assertRaisesRegex(ValueError, key):
                    portfolio.onboard(apply=True)
        self.assertFalse(self.root.exists())

    def test_intake_rejects_missing_archived_or_unknown_project(self):
        with self.assertRaisesRegex(ValueError, "missing"):
            portfolio.intake("open-box", "data", "Organize", "id", apply=True)
        with self.assertRaisesRegex(ValueError, "known"):
            portfolio.intake("other-project", "data", "Organize", "id", apply=True)
        portfolio.onboard(apply=True)
        kb.write_board_metadata("open-box", archived=True)
        with self.assertRaisesRegex(ValueError, "archived"):
            portfolio.intake("open-box", "data", "Organize", "id", apply=True)


if __name__ == "__main__":
    unittest.main()
