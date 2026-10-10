"""Open Notify routing, privacy and ambiguous-delivery regression tests."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

SOURCE = Path(__file__).resolve().parents[2] / "scripts/operations/open_notify.py"
spec = importlib.util.spec_from_file_location("open_notify", SOURCE)
notify = importlib.util.module_from_spec(spec)
spec.loader.exec_module(notify)


class NotifyTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.home = Path(self.temp.name)
        (self.home / ".env").write_text("TELEGRAM_PROJECT_BOT_TOKEN=" + str(notify.BOT_ID) + ":synthetic-test-only\n")
        self.calls = []

    def tearDown(self):
        self.temp.cleanup()

    def success(self, token, payload):
        self.calls.append(payload)
        return {"ok": True, "result": {"chat": {"id": notify.CHAT_ID},
                "message_thread_id": payload["message_thread_id"], "message_id": 321}}

    def test_every_project_uses_exact_allowlisted_thread(self):
        for project, thread in notify.PROJECTS.items():
            result = notify.send_event(self.home, project, "run", "Health check", transport=self.success)
            self.assertEqual(result["status"], "delivered")
            self.assertEqual(self.calls[-1]["message_thread_id"], thread)
            self.assertEqual(self.calls[-1]["chat_id"], notify.CHAT_ID)

    def test_duplicate_event_does_not_send_twice(self):
        for _ in range(2):
            notify.send_event(self.home, "open-system", "run", "Health check", transport=self.success)
        self.assertEqual(len(self.calls), 1)

    def test_same_key_changed_payload_is_conflict(self):
        notify.send_event(self.home, "open-system", "run", "Healthy", transport=self.success)
        result = notify.send_event(self.home, "open-system", "run", "Unhealthy", transport=self.success)
        self.assertEqual(result["status"], "conflict")
        self.assertEqual(len(self.calls), 1)

    def test_timeout_is_uncertain_and_not_resent(self):
        def timeout(token, payload):
            self.calls.append(payload)
            raise TimeoutError()
        for _ in range(2):
            result = notify.send_event(self.home, "open-system", "run", "Health check", transport=timeout)
        self.assertEqual(result["status"], "uncertain")
        self.assertEqual(len(self.calls), 1)

    def test_wrong_thread_does_not_count_as_delivery(self):
        def wrong(token, payload):
            return {"ok": True, "result": {"chat": {"id": notify.CHAT_ID}, "message_thread_id": 7}}
        result = notify.send_event(self.home, "open-system", "run", "Health check", transport=wrong)
        self.assertEqual(result["status"], "uncertain")

    def test_rate_limit_defers_and_caps_retries(self):
        def limited(token, payload):
            self.calls.append(payload)
            return {"ok": False, "error_code": 429, "parameters": {"retry_after": 100}}
        result = notify.send_event(self.home, "open-system", "run", "Health check", transport=limited)
        self.assertEqual(result["status"], "retry")
        notify.send_event(self.home, "open-system", "run", "Health check", transport=limited)
        self.assertEqual(len(self.calls), 1)
        ledger_path = self.home / "state/open-notify/ledger.json"
        for _ in range(2):
            ledger = json.loads(ledger_path.read_text())
            next(iter(ledger.values()))["next_attempt"] = 0
            ledger_path.write_text(json.dumps(ledger))
            result = notify.send_event(self.home, "open-system", "run", "Health check", transport=limited)
        self.assertEqual(result["status"], "failed")
        self.assertEqual(len(self.calls), 3)

    def test_restricted_payload_and_unknown_project_rejected(self):
        with self.assertRaises(ValueError):
            notify.send_event(self.home, "open-system", "run", "Staff record", classification="restricted")
        with self.assertRaises(ValueError):
            notify.send_event(self.home, "open-kobeplay", "run", "Client details")
        self.assertEqual(len(self.calls), 0)

    def test_credentials_rejected_before_persisting(self):
        with self.assertRaises(ValueError):
            notify.send_event(self.home, "open-system", "run", "password=do-not-persist")
        self.assertFalse((self.home / "state").exists())

    def test_ledger_contains_fingerprint_not_message_text(self):
        notify.send_event(self.home, "open-system", "run", "Synthetic diagnostic", transport=self.success)
        content = (self.home / "state/open-notify/ledger.json").read_text()
        self.assertNotIn("Synthetic diagnostic", content)
        self.assertNotIn("synthetic-test-only", content)

    def test_wrong_bot_identity_rejected(self):
        (self.home / ".env").write_text("TELEGRAM_PROJECT_BOT_TOKEN=123:synthetic-test-only\n")
        with self.assertRaises(ValueError):
            notify.send_event(self.home, "open-system", "run", "Health check", transport=self.success)


if __name__ == "__main__":
    unittest.main()
