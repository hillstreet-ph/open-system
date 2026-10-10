"""Open Notify routing, privacy and ambiguous-delivery regression tests."""
import importlib.util
import errno
import json
import os
from pathlib import Path
import stat
import tempfile
import time
import unittest
from types import SimpleNamespace
import unittest.mock as mock

SOURCE = Path(__file__).resolve().parents[2] / "scripts/operations/open_notify.py"
spec = importlib.util.spec_from_file_location("open_notify", SOURCE)
notify = importlib.util.module_from_spec(spec)
spec.loader.exec_module(notify)


class NotifyTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.home = Path(self.temp.name)
        (self.home / ".env").write_text("TELEGRAM_PROJECT_BOT_TOKEN=" + str(notify.BOT_ID) + ":synthetic-test-only\n", encoding="utf-8")
        self.calls = []

    def write_portfolio(self, path, projects=None):
        path.write_text(json.dumps({
            "telegram": {
                "chat_id": notify.CHAT_ID,
                "expected_bot_id": notify.BOT_ID,
                "no_broadcast": True,
            },
            "projects": projects if projects is not None else {},
        }), encoding="utf-8")

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

    def test_delivery_uses_portfolio_routing_source_of_truth(self):
        config = self.home / "portfolio.json"
        config.write_text(json.dumps({
            "telegram": {
                "chat_id": -1000000000001,
                "expected_bot_id": notify.BOT_ID,
                "no_broadcast": True,
            },
            "projects": {
                "open-system": {"topic_id": 901},
                "open-kobeplay": {"topic_id": None},
            },
        }), encoding="utf-8")

        notify.send_event(
            self.home, "open-system", "config", "Health check",
            transport=self.success, config=config,
        )

        self.assertEqual(self.calls[-1]["chat_id"], -1000000000001)
        self.assertEqual(self.calls[-1]["message_thread_id"], 901)
        with self.assertRaises(ValueError):
            notify.send_event(
                self.home, "open-kobeplay", "config", "Health check",
                transport=self.success, config=config,
            )

    def test_routing_rejects_broadcast_enabled_manifest(self):
        config = self.home / "portfolio.json"
        config.write_text(json.dumps({
            "telegram": {
                "chat_id": notify.CHAT_ID,
                "expected_bot_id": notify.BOT_ID,
                "no_broadcast": False,
            },
            "projects": {"open-system": {"topic_id": 185}},
        }), encoding="utf-8")
        with self.assertRaises(ValueError):
            notify.load_routing(config)

    def test_routing_rejects_duplicate_project_topic_ids(self):
        config = self.home / "portfolio.json"
        self.write_portfolio(config, {
            "open-system": {"topic_id": 185},
            "open-box": {"topic_id": 185},
        })

        with self.assertRaisesRegex(ValueError, "unique"):
            notify.load_routing(config)

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
        cooldown_path = self.home / "state/open-notify/cooldown.json"
        for _ in range(2):
            ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
            next(iter(ledger.values()))["next_attempt"] = 0
            ledger_path.write_text(json.dumps(ledger), encoding="utf-8")
            cooldown = json.loads(cooldown_path.read_text(encoding="utf-8"))
            cooldown["until"] = 0
            cooldown_path.write_text(json.dumps(cooldown), encoding="utf-8")
            result = notify.send_event(self.home, "open-system", "run", "Health check", transport=limited)
        self.assertEqual(result["status"], "failed")
        self.assertEqual(len(self.calls), 3)

    def test_rate_limit_cooldown_defers_other_event_keys(self):
        def limited(token, payload):
            self.calls.append(payload)
            return {"ok": False, "error_code": 429, "parameters": {"retry_after": 100}}

        first = notify.send_event(self.home, "open-system", "first", "Health check", transport=limited)
        second = notify.send_event(self.home, "open-box", "second", "Health check", transport=limited)

        self.assertEqual(first["status"], "retry")
        self.assertEqual(second, {"status": "retry", "project": "open-box", "deferred": True})
        self.assertEqual(len(self.calls), 1)

    def test_global_cooldown_records_deferred_event_before_return(self):
        def limited(token, payload):
            self.calls.append(payload)
            return {"ok": False, "error_code": 429, "parameters": {"retry_after": 100}}

        notify.send_event(self.home, "open-system", "first", "Health check", transport=limited)
        deferred = notify.send_event(
            self.home, "open-box", "second", "Box health check", transport=limited,
        )

        ledger = json.loads(
            (self.home / "state/open-notify/ledger.json").read_text(encoding="utf-8")
        )
        deferred_entries = [entry for entry in ledger.values() if entry["project"] == "open-box"]
        self.assertEqual(deferred, {"status": "retry", "project": "open-box", "deferred": True})
        self.assertEqual(len(deferred_entries), 1)
        self.assertEqual(deferred_entries[0]["status"], "retry")
        self.assertEqual(deferred_entries[0]["attempts"], 0)
        self.assertGreater(deferred_entries[0]["next_attempt"], time.time())
        conflict = notify.send_event(
            self.home, "open-box", "second", "Changed box health", transport=limited,
        )
        self.assertEqual(conflict["status"], "conflict")
        self.assertEqual(len(self.calls), 1)

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

    def test_secret_bearing_query_parameters_rejected_before_persisting(self):
        samples = [
            "OAuth callback https://example.invalid/cb?code=opaque-short-value",
            "Signed file https://example.invalid/file?x=1&signature=opaque-short-value",
            "Encoded key https://example.invalid/file?x%2Damz%2Dsignature=opaque-short-value",
            "Google signed file https://example.invalid/file?X-Goog-Signature=opaque-short-value",
            "Azure signed file https://example.invalid/file?sv=1&sig=opaque-short-value",
        ]
        for sample in samples:
            with self.subTest(sample=sample), self.assertRaises(ValueError):
                notify.send_event(self.home, "open-system", "query", sample, transport=self.success)
        self.assertFalse((self.home / "state").exists())
        result = notify.send_event(
            self.home, "open-system", "public-query",
            "Metrics https://example.invalid/report?page=3&session_id=public",
            transport=self.success,
        )
        self.assertEqual(result["status"], "delivered")

    def test_ledger_contains_fingerprint_not_message_text(self):
        notify.send_event(self.home, "open-system", "run", "Synthetic diagnostic", transport=self.success)
        content = (self.home / "state/open-notify/ledger.json").read_text(encoding="utf-8")
        self.assertNotIn("Synthetic diagnostic", content)
        self.assertNotIn("synthetic-test-only", content)

    def test_atomic_save_fsyncs_parent_directory(self):
        observed = []
        real_fsync = os.fsync

        def record_fsync(descriptor):
            observed.append(stat.S_ISDIR(os.fstat(descriptor).st_mode))
            real_fsync(descriptor)

        with mock.patch.object(notify.os, "fsync", side_effect=record_fsync):
            notify.atomic_save(self.home / "ledger.json", {"entry": {"status": "uncertain"}})

        self.assertIn(True, observed)

    @unittest.skipIf(os.name == "nt", "POSIX directory durability")
    def test_new_state_hierarchy_is_synced_before_transport(self):
        opened_directories = []
        real_open = os.open

        def record_open(path, flags, *args, **kwargs):
            if flags & getattr(os, "O_DIRECTORY", 0):
                opened_directories.append(Path(path))
            return real_open(path, flags, *args, **kwargs)

        with mock.patch.object(notify.os, "open", side_effect=record_open):
            notify.send_event(self.home, "open-system", "durable", "Health check", transport=self.success)

        self.assertIn(self.home, opened_directories)
        self.assertIn(self.home / "state", opened_directories)

    def test_provider_injected_environment_without_env_file(self):
        (self.home / ".env").unlink()
        with mock.patch.dict(os.environ, {"TELEGRAM_PROJECT_BOT_TOKEN": str(notify.BOT_ID) + ":synthetic-env-only"}):
            result = notify.send_event(self.home, "open-system", "env", "Health check", transport=self.success)
        self.assertEqual(result["status"], "delivered")

    def test_fine_grained_github_credential_is_rejected(self):
        with self.assertRaises(ValueError):
            notify.send_event(self.home, "open-system", "pat", "github_pat_synthetic_noncredential")
        self.assertFalse((self.home / "state").exists())

    def test_scheduler_bom_and_legacy_enabled_default(self):
        (self.home / "cron").mkdir()
        jobs = [{"id": "legacy", "last_status": "error"},
                {"id": "disabled", "enabled": False, "last_status": "error"}]
        (self.home / "cron/jobs.json").write_text(json.dumps({"jobs": jobs}), encoding="utf-8-sig")
        config = self.home / "portfolio.json"
        self.write_portfolio(config)
        with mock.patch.object(notify, "send_event", return_value={"status": "delivered"}) as sender:
            notify.reconcile(self.home, config)
        self.assertIn("1 enabled jobs", sender.call_args.args[3])

    def test_scheduler_tolerates_idless_error_records(self):
        (self.home / "cron").mkdir()
        jobs = [{"last_status": "error"}, {"id": "known", "last_status": "error"}]
        (self.home / "cron/jobs.json").write_text(json.dumps({"jobs": jobs}), encoding="utf-8")
        config = self.home / "portfolio.json"
        self.write_portfolio(config)
        with mock.patch.object(notify, "send_event", return_value={"status": "delivered"}) as sender:
            notify.reconcile(self.home, config)
        self.assertIn("2 enabled jobs", sender.call_args.args[3])

    def test_other_provider_credentials_rejected_without_state(self):
        samples = ["xoxb-" + "A" * 20, "xapp-1-" + "A" * 20,
                   "AKIA" + "A" * 16, "AIza" + "A" * 35,
                   "glpat-" + "A" * 20, "SG." + "A" * 20,
                   "ntn_" + "A" * 20, "pypi-" + "A" * 20,
                   "sk_live_" + "A" * 20, "hf_" + "A" * 20]
        for sample in samples:
            with self.subTest(prefix=sample[:5]), self.assertRaises(ValueError):
                notify.send_event(self.home, "open-system", "provider", sample)
        self.assertFalse((self.home / "state").exists())

    def test_utf16_overflow_rejected_before_ledger(self):
        with self.assertRaises(ValueError):
            notify.send_event(self.home, "open-system", "emoji", "😀" * 3000, transport=self.success)
        self.assertFalse((self.home / "state").exists())
        result = notify.send_event(self.home, "open-system", "emoji", "😀" * 100, transport=self.success)
        self.assertEqual(result["status"], "delivered")

    def test_windows_lock_retries_beyond_ten_seconds(self):
        win = SimpleNamespace(LK_NBLCK=2, LK_UNLCK=0,
                              locking=mock.Mock(side_effect=[OSError(errno.EACCES, "busy")] * 12 + [None, None]))
        path = self.home / "contention.lock"
        with mock.patch.dict("sys.modules", {"msvcrt": win}), mock.patch.object(notify.os, "name", "nt"):
            with mock.patch.object(notify.time, "monotonic", side_effect=range(30)), mock.patch.object(notify.time, "sleep"):
                with notify.delivery_lock(path):
                    pass
        self.assertEqual(win.locking.call_count, 14)

    def test_opaque_assignments_auth_urls_and_jwt_rejected(self):
        samples = ["API_KEY=synthetic-opaque", "db_pw: synthetic-opaque",
                   '"client_secret": "synthetic-opaque"', "Authorization: Basic synthetic-opaque",
                   "https://user:synthetic-password@example.invalid/private",
                   "https://synthetic-opaque-access@host.invalid/repo", "eyJ" + "A" * 12,
                   "eyJ" + "A" * 16 + "." + "B" * 16 + "." + "C" * 16]
        for sample in samples:
            with self.assertRaises(ValueError):
                notify.send_event(self.home, "open-system", "opaque", sample)
        self.assertFalse((self.home / "state").exists())

    def test_non_http_authenticated_urls_rejected(self):
        for scheme in ["postgresql", "postgres", "redis", "rediss", "ssh", "mongodb", "mongodb+srv", "amqp", "ftp"]:
            with self.assertRaises(ValueError):
                notify.send_event(self.home, "open-system", "url", scheme + "://admin:synthetic-password@host.invalid/db")
        self.assertFalse((self.home / "state").exists())

    def test_bot_prefixed_telegram_credentials_rejected(self):
        token = "bot1234567890:" + "A" * 35
        for summary in [token, "https://api.telegram.org/" + token + "/getMe"]:
            with self.assertRaises(ValueError):
                notify.send_event(self.home, "open-system", "bot-url", summary)
        self.assertFalse((self.home / "state").exists())

    def test_legacy_dotenv_alias(self):
        (self.home / ".env").write_text("OPEN_NOTIFY_BOT_TOKEN=" + str(notify.BOT_ID) + ":synthetic-alias-only\n", encoding="utf-8")
        result = notify.send_event(self.home, "open-system", "alias", "Health check", transport=self.success)
        self.assertEqual(result["status"], "delivered")

    def test_scheduler_unescaped_legacy_control_character(self):
        (self.home / "cron").mkdir()
        content = json.dumps({"jobs": [{"id": "legacy", "last_status": "error", "prompt": "legacy" + chr(10) + "value"}]}).replace("\\n", chr(10))
        with self.assertRaises(json.JSONDecodeError):
            json.loads(content)
        (self.home / "cron/jobs.json").write_text(content, encoding="utf-8")
        config = self.home / "portfolio.json"
        self.write_portfolio(config)
        with mock.patch.object(notify, "send_event", return_value={"status": "delivered"}) as sender:
            notify.reconcile(self.home, config)
        self.assertIn("1 enabled jobs", sender.call_args.args[3])

    def test_wrong_bot_identity_rejected(self):
        (self.home / ".env").write_text("TELEGRAM_PROJECT_BOT_TOKEN=123:synthetic-test-only\n", encoding="utf-8")
        with self.assertRaises(ValueError):
            notify.send_event(self.home, "open-system", "run", "Health check", transport=self.success)


if __name__ == "__main__":
    unittest.main()
