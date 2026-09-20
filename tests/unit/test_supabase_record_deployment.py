"""Exercise the recorder against local HTTP responses, never a provider account."""

import json
import os
from pathlib import Path
import shutil
import subprocess
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread
import unittest


SCRIPT = Path(__file__).resolve().parents[2] / "scripts/supabase/record-deployment.sh"
SYNTHETIC_KEY = "synthetic-test-key-never-a-provider-credential"
RESPONSE_MARKER = "provider-response-must-not-be-logged"


@unittest.skipUnless(shutil.which("bash") and shutil.which("curl"), "requires bash and curl")
class TestSupabaseRecordDeployment(unittest.TestCase):
    def invoke(self, url, digest=None):
        env = os.environ.copy()
        for name in list(env):
            if name.startswith("OPEN_SYSTEM_") or name in {
                "GIT_SHA", "IMAGE_REF", "IMAGE_DIGEST", "ENV_NAME",
            }:
                del env[name]
        env.update({
            "SUPABASE_URL": url,
            "SUPABASE_SERVICE_ROLE_KEY": SYNTHETIC_KEY,
            "OPEN_SYSTEM_GIT_SHA": "a" * 40,
            "OPEN_SYSTEM_IMAGE_REF": "example.invalid/image:sha-aaaaaaa",
            "OPEN_SYSTEM_ENV": "build-artifact",
            "NO_PROXY": "127.0.0.1",
            "no_proxy": "127.0.0.1",
        })
        if digest is not None:
            env["OPEN_SYSTEM_IMAGE_DIGEST"] = digest
        result = subprocess.run(
            ["bash", str(SCRIPT)], env=env, text=True, capture_output=True, timeout=10,
        )
        self.assertNotIn(SYNTHETIC_KEY, result.stdout + result.stderr)
        self.assertNotIn(RESPONSE_MARKER, result.stdout + result.stderr)
        self.assertNotIn(url, result.stdout + result.stderr)
        return result

    def request(self, status, digest=None):
        received = []

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                received.append({
                    "path": self.path,
                    "body": json.loads(self.rfile.read(int(self.headers["Content-Length"]))),
                    "authorization": self.headers.get("Authorization"),
                    "apikey": self.headers.get("apikey"),
                })
                self.send_response(status)
                self.send_header("Location", "/must-not-follow")
                self.end_headers()
                self.wfile.write(f"{RESPONSE_MARKER} {SYNTHETIC_KEY}".encode())

            def log_message(self, *_args):
                pass

        with ThreadingHTTPServer(("127.0.0.1", 0), Handler) as server:
            thread = Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                result = self.invoke(f"http://127.0.0.1:{server.server_port}", digest)
            finally:
                server.shutdown()
                thread.join(timeout=2)
        self.assertEqual(len(received), 1)
        request = received[0]
        self.assertEqual(request["path"], "/rest/v1/open_system_deployments")
        self.assertEqual(request["authorization"], f"Bearer {SYNTHETIC_KEY}")
        self.assertEqual(request["apikey"], SYNTHETIC_KEY)
        self.assertEqual(request["body"], {
            "git_sha": "a" * 40,
            "image_ref": "example.invalid/image:sha-aaaaaaa",
            "image_digest": digest if digest is not None else "unknown",
            "environment": "build-artifact",
            "status": "recorded",
        })
        return result

    def test_success_requires_2xx_and_preserves_supplied_identity(self):
        for status in (200, 201, 204):
            with self.subTest(status=status):
                result = self.request(status, "sha256:" + "b" * 64)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(result.stdout.strip(), "DEPLOYMENT_RECORDED")

    def test_unavailable_digest_is_explicitly_unknown(self):
        self.assertEqual(self.request(201).returncode, 0)

    def test_http_errors_and_redirects_fail_without_response_leakage(self):
        for status in (302, 400, 401, 403, 500, 503):
            with self.subTest(status=status):
                result = self.request(status)
                self.assertNotEqual(result.returncode, 0)
                self.assertNotIn("DEPLOYMENT_RECORDED", result.stdout)
                self.assertIn(f"HTTP {status}", result.stderr)

    def test_transport_error_fails_without_url_or_credential_output(self):
        # Reserve a local port without listening, guaranteeing connection refusal.
        with ThreadingHTTPServer(("127.0.0.1", 0), BaseHTTPRequestHandler,
                                 bind_and_activate=False) as server:
            server.server_bind()
            result = self.invoke(f"http://127.0.0.1:{server.server_port}")
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn("DEPLOYMENT_RECORDED", result.stdout)
        self.assertIn("failed before HTTP confirmation", result.stderr)


if __name__ == "__main__":
    unittest.main()
