"""Exercise the actual workflow merge script against disposable Git repositories."""

import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import textwrap
import unittest


WORKFLOW = Path(__file__).resolve().parents[2] / ".github/workflows/upstream-sync.yml"


def merge_script():
    text = WORKFLOW.read_text()
    step = text.split("      - name: Create sync branch and merge\n", 1)[1]
    step = step.split("      - name: Open pull request\n", 1)[0]
    return textwrap.dedent(step.split("        run: |\n", 1)[1])


@unittest.skipUnless(shutil.which("git") and shutil.which("bash"), "requires Git and Bash")
class UpstreamSyncSafetyTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.repo = self.root / "fork"
        self.origin = self.root / "origin.git"
        self.repo.mkdir()
        self.git("init", "-b", "main")
        self.git("config", "user.name", "Sync test")
        self.git("config", "user.email", "sync-test@example.invalid")
        self.commit_file("shared.txt", "base\n", "base")
        self.base = self.git("rev-parse", "HEAD")
        subprocess.run(["git", "init", "--bare", str(self.origin)], check=True, capture_output=True)
        self.git("remote", "add", "origin", str(self.origin))

    def git(self, *args):
        result = subprocess.run(["git", *args], cwd=self.repo, check=True, capture_output=True, text=True)
        return result.stdout.strip()

    def commit_file(self, name, content, message):
        (self.repo / name).write_text(content)
        self.git("add", name)
        self.git("commit", "-m", message)

    def setup_histories(self, conflict=False):
        self.git("checkout", "-b", "upstream", self.base)
        self.commit_file("shared.txt" if conflict else "upstream.txt", "upstream\n", "upstream")
        upstream = self.git("rev-parse", "HEAD")
        self.git("checkout", "main")
        self.commit_file("shared.txt" if conflict else "fork.txt", "fork\n", "fork integration")
        self.git("push", "origin", "main")
        return upstream, self.git("rev-parse", "HEAD")

    def run_sync(self, upstream):
        return subprocess.run(
            ["bash", "-e", "-o", "pipefail", "-c", merge_script()],
            cwd=self.repo,
            env={**os.environ, "SYNC_BRANCH": "upstream-sync/test", "UPSTREAM_SHA": upstream,
                 "GITHUB_OUTPUT": str(self.root / "outputs")},
            capture_output=True, text=True,
        )

    def test_conflict_preserves_fork_and_pushes_nothing(self):
        upstream, fork = self.setup_histories(conflict=True)
        result = self.run_sync(upstream)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("fork history preserved", result.stdout)
        self.assertEqual(self.git("rev-parse", "HEAD"), fork)
        self.assertEqual((self.repo / "shared.txt").read_text(), "fork\n")
        self.assertEqual(self.git("status", "--porcelain"), "")
        self.assertEqual(self.git("ls-remote", "origin", "refs/heads/upstream-sync/test"), "")
        self.assertEqual(self.git("ls-remote", "origin", "refs/heads/main").split()[0], fork)

    def test_clean_merge_contains_both_histories(self):
        upstream, fork = self.setup_histories()
        result = self.run_sync(upstream)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.git("merge-base", "--is-ancestor", fork, "HEAD")
        self.git("merge-base", "--is-ancestor", upstream, "HEAD")
        self.assertEqual(self.git("ls-remote", "origin", "refs/heads/upstream-sync/test").split()[0], self.git("rev-parse", "HEAD"))
        self.assertEqual(self.git("ls-remote", "origin", "refs/heads/main").split()[0], fork)

    def test_existing_divergent_branch_is_not_overwritten(self):
        upstream, fork = self.setup_histories()
        self.git("checkout", "-b", "existing-review", fork)
        self.commit_file("review.txt", "reviewer work\n", "reviewer work")
        existing = self.git("rev-parse", "HEAD")
        self.git("push", "origin", "HEAD:refs/heads/upstream-sync/test")
        self.git("checkout", "main")
        result = self.run_sync(upstream)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.git("ls-remote", "origin", "refs/heads/upstream-sync/test").split()[0], existing)

    def test_dispatch_ref_cannot_execute_shell(self):
        step = WORKFLOW.read_text().split("      - name: Resolve upstream ref\n", 1)[1]
        step = step.split("      - name: Check if already up to date\n", 1)[0]
        script = textwrap.dedent(step.split("        run: |\n", 1)[1])
        dangerous_ref = "$(touch${IFS}injected)"
        self.git("check-ref-format", "refs/heads/" + dangerous_ref)
        result = subprocess.run(
            ["bash", "-e", "-o", "pipefail", "-c", script], cwd=self.repo,
            env={**os.environ, "REQUESTED_REF": dangerous_ref,
                 "GITHUB_OUTPUT": str(self.root / "outputs")},
            capture_output=True, text=True,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse((self.repo / "injected").exists())


if __name__ == "__main__":
    unittest.main()
