#!/usr/bin/env python3
"""Bounded, project-specific Open Notify delivery; never broadcasts."""
from __future__ import annotations

import argparse
import errno
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import re
import time
import urllib.error
import urllib.request

PROJECTS = {"open-system": 185, "open-box": 186, "open-connect": 187,
            "open-tgate": 188, "open-teleset": 189}
CHAT_ID = -1004449684934
BOT_ID = 8902902175

# Keep provider-prefix coverage aligned with agent/redact.py.
CREDENTIAL_PREFIX_PATTERNS = [
    r"sk-[A-Za-z0-9_-]{10,}",           # OpenAI / OpenRouter / Anthropic (sk-ant-*)
    r"ghp_[A-Za-z0-9]{10,}",            # GitHub PAT (classic)
    r"github_pat_[A-Za-z0-9_]{10,}",    # GitHub PAT (fine-grained)
    r"gho_[A-Za-z0-9]{10,}",            # GitHub OAuth access token
    r"ghu_[A-Za-z0-9]{10,}",            # GitHub user-to-server token
    r"ghs_[A-Za-z0-9]{10,}",            # GitHub server-to-server token
    r"ghr_[A-Za-z0-9]{10,}",            # GitHub refresh token
    r"xapp-\d+-[A-Za-z0-9-]{10,}",      # Slack app-Level token
    r"xox[baprs]-[A-Za-z0-9-]{10,}",    # Slack bot/app/user tokens
    r"AIza[A-Za-z0-9_-]{30,}",          # Google API keys
    r"pplx-[A-Za-z0-9]{10,}",           # Perplexity
    r"fal_[A-Za-z0-9_-]{10,}",          # Fal.ai
    r"fc-[A-Za-z0-9]{10,}",             # Firecrawl
    r"bb_live_[A-Za-z0-9_-]{10,}",      # BrowserBase
    r"gAAAA[A-Za-z0-9_=-]{20,}",        # Codex encrypted tokens
    r"AKIA[A-Z0-9]{16}",                # AWS Access Key ID
    r"sk_live_[A-Za-z0-9]{10,}",        # Stripe secret key (live)
    r"sk_test_[A-Za-z0-9]{10,}",        # Stripe secret key (test)
    r"rk_live_[A-Za-z0-9]{10,}",        # Stripe restricted key
    r"SG\.[A-Za-z0-9_-]{10,}",          # SendGrid API key
    r"hf_[A-Za-z0-9]{10,}",             # HuggingFace token
    r"r8_[A-Za-z0-9]{10,}",             # Replicate API token
    r"npm_[A-Za-z0-9]{10,}",            # npm access token
    r"pypi-[A-Za-z0-9_-]{10,}",         # PyPI API token
    r"dop_v1_[A-Za-z0-9]{10,}",         # DigitalOcean PAT
    r"doo_v1_[A-Za-z0-9]{10,}",         # DigitalOcean OAuth
    r"am_[A-Za-z0-9_-]{10,}",           # AgentMail API key
    r"sk_[A-Za-z0-9_]{10,}",            # ElevenLabs TTS key (sk_ underscore, not sk- dash)
    r"tvly-[A-Za-z0-9]{10,}",           # Tavily search API key
    r"exa_[A-Za-z0-9]{10,}",            # Exa search API key
    r"gsk_[A-Za-z0-9]{10,}",            # Groq Cloud API key
    r"syt_[A-Za-z0-9]{10,}",            # Matrix access token
    r"retaindb_[A-Za-z0-9]{10,}",       # RetainDB API key
    r"hsk-[A-Za-z0-9]{10,}",            # Hindsight API key
    r"mem0_[A-Za-z0-9]{10,}",           # Mem0 Platform API key
    r"brv_[A-Za-z0-9]{10,}",            # ByteRover API key
    r"xai-[A-Za-z0-9]{30,}",            # xAI (Grok) API key
    r"ntn_[A-Za-z0-9]{10,}",            # Notion internal integration token
    r"fw-[A-Za-z0-9]{30,}",             # Fireworks AI API key
    r"fw_[A-Za-z0-9]{30,}",             # Fireworks AI API key
    r"fpk_[A-Za-z0-9]{30,}",            # Fireworks AI project key
    # GitLab token families (each pattern keeps a full literal prefix so the
    # _PREFIX_SUBSTRINGS pre-screen stays false-negative-free). Ported from
    # openclaw/openclaw#112954; follow-up invited in #4541.
    r"glpat-[A-Za-z0-9_\-]{10,}",       # GitLab personal access token
    r"gloas-[A-Za-z0-9_\-]{10,}",       # GitLab OAuth application secret
    r"gldt-[A-Za-z0-9_\-]{10,}",        # GitLab deploy token
    r"glrt-[A-Za-z0-9_.\-]{10,}",       # GitLab runner authentication token (routable tokens are dotted)
    r"glrtr-[A-Za-z0-9_.\-]{10,}",      # GitLab runner registration token (routable)
    r"glcbt-[A-Za-z0-9_\-]{10,}",       # GitLab CI/CD job token
    r"glptt-[A-Za-z0-9_\-]{10,}",       # GitLab pipeline trigger token
    r"glft-[A-Za-z0-9_\-]{10,}",        # GitLab feed token
    r"glimt-[A-Za-z0-9_\-]{10,}",       # GitLab incoming mail token
    r"glagent-[A-Za-z0-9_\-]{10,}",     # GitLab agent (KAS) token
    r"glsoat-[A-Za-z0-9_\-]{10,}",      # GitLab service-account access token
    r"glffct-[A-Za-z0-9_\-]{10,}",      # GitLab feature-flags client token
    r"glwt-[A-Za-z0-9_\-]{10,}",        # GitLab workspace token
    r"GR1348941[A-Za-z0-9_\-]{10,}",    # GitLab legacy runner registration token
    r"pk-lf-[A-Za-z0-9\-]{8,}",         # Langfuse public key (sk-lf- already covered by sk- pattern)
]
SECRET = re.compile(
    r"(?i:\b(?:bot)?\d{8,12}:[A-Za-z0-9_-]{30,}\b)|"
    r"\b(?:github_pat_[A-Za-z0-9_]+|gh[pousr]_[A-Za-z0-9_]+|sk-[A-Za-z0-9_-]{12,})|"
    r"-----BEGIN .*PRIVATE KEY-----|"
    r"(?i:bearer\s+\S+|password\s*[:=]|token\s*[:=]|secret\s*[:=])"
    + "|" + "|".join(CREDENTIAL_PREFIX_PATTERNS)
    + r"|(?i:\b[\w.-]*(?:api[_.-]?key|key|password|passwd|pass|pw|token|secret|credential|auth)[\w.-]*[\"\']?\s*[:=])"
    + r"|(?i:[a-z][a-z0-9+.-]*://[^\s/:@]+:[^\s/@]+@)"
    + r"|\beyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}"
)

class DeliveryBusyError(OSError):
    """Another delivery owns the state lock; no event was attempted."""


@contextmanager
def delivery_lock(path: Path):
    """Lock delivery state on POSIX and Windows."""
    with path.open("a+b") as handle:
        if os.name == "nt":
            import msvcrt
            handle.seek(0, os.SEEK_END)
            if handle.tell() == 0:
                handle.write(b"0")
                handle.flush()
            handle.seek(0)
        else:
            import fcntl
            os.chmod(path, 0o600)
        deadline = time.monotonic() + 45
        while True:
            try:
                if os.name == "nt":
                    handle.seek(0)
                    msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
                else:
                    fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except OSError as exc:
                if exc.errno not in (errno.EACCES, errno.EAGAIN, errno.EDEADLK):
                    raise
                if time.monotonic() >= deadline:
                    raise DeliveryBusyError("Delivery state busy") from None
                time.sleep(0.1)
        try:
            yield
        finally:
            if os.name == "nt":
                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(handle, fcntl.LOCK_UN)


def load_token(home: Path) -> str:
    token = os.environ.get("TELEGRAM_PROJECT_BOT_TOKEN") or os.environ.get("OPEN_NOTIFY_BOT_TOKEN", "")
    if not token:
        path = home / ".env"
        if path.exists():
            dotenv = {}
            for line in path.read_text(encoding="utf-8").splitlines():
                key, sep, value = line.partition("=")
                key = key.strip()
                if sep and key in ("TELEGRAM_PROJECT_BOT_TOKEN", "OPEN_NOTIFY_BOT_TOKEN"):
                    dotenv[key] = value.strip().strip("\"'")
            token = dotenv.get("TELEGRAM_PROJECT_BOT_TOKEN") or dotenv.get("OPEN_NOTIFY_BOT_TOKEN", "")
    if not token.startswith(str(BOT_ID) + ":"):
        raise ValueError("Open Notify credential missing or bot identity mismatch")
    return token


def api_call(token: str, payload: dict) -> dict:
    request = urllib.request.Request(
        "https://api.telegram.org/bot" + token + "/sendMessage",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"}, method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            return json.load(response)
    except urllib.error.HTTPError as exc:
        # Never return exception text: urllib exceptions can contain credential URLs.
        try:
            data = json.load(exc)
        except (ValueError, OSError):
            data = {}
        return {"ok": False, "error_code": exc.code,
                "parameters": {"retry_after": data.get("parameters", {}).get("retry_after", 60)}}
    except (OSError, ValueError):
        return {"ok": False, "ambiguous": True}


def atomic_save(path: Path, data: dict) -> None:
    temp = path.with_suffix(".tmp")
    descriptor = os.open(temp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
        json.dump(data, handle)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temp, path)


def send_event(home: Path, project: str, event_key: str, summary: str,
               classification: str = "operational", transport=api_call) -> dict:
    if project not in PROJECTS:
        raise ValueError("Unknown project; no fallback destination")
    if classification not in ("operational", "client-safe"):
        raise ValueError("Restricted records cannot be delivered to shared topics")
    if not event_key or len(event_key) > 300 or not summary or len(summary) > 3000:
        raise ValueError("Event key and bounded summary required")
    text = "Open Notify • " + project + "\n" + summary
    if len(text.encode("utf-16-le")) // 2 > 4096:
        raise ValueError("Outbound message exceeds Telegram UTF-16 limit")
    if SECRET.search(summary):
        raise ValueError("Credential-like content rejected")
    token = load_token(home)
    state = home / "state" / "open-notify"
    state.mkdir(parents=True, exist_ok=True, mode=0o700)
    key = hashlib.sha256((project + ":" + event_key).encode()).hexdigest()
    digest = hashlib.sha256(summary.encode()).hexdigest()
    ledger_path = state / "ledger.json"
    with delivery_lock(state / "delivery.lock"):
        ledger = json.loads(ledger_path.read_text(encoding="utf-8")) if ledger_path.exists() else {}
        entry = ledger.get(key, {})
        if entry:
            if entry.get("digest") != digest:
                return {"status": "conflict", "project": project}
            if entry.get("status") != "retry":
                return {"status": entry["status"], "project": project, "duplicate": True}
            if entry.get("next_attempt", 0) > time.time():
                return {"status": "retry", "project": project, "deferred": True}
            if entry.get("attempts", 0) >= 3:
                return {"status": "failed", "project": project}
        attempts = entry.get("attempts", 0) + 1
        # Persist before network I/O. A crash after Telegram accepts a message is
        # uncertain; future invocations must not resend it blindly.
        entry = {"digest": digest, "status": "uncertain", "attempts": attempts,
                 "project": project, "updated_at": time.time()}
        ledger[key] = entry
        atomic_save(ledger_path, ledger)
        try:
            result = transport(token, {
                "chat_id": CHAT_ID, "message_thread_id": PROJECTS[project],
                "text": text,
                "disable_notification": True, "link_preview_options": {"is_disabled": True},
            })
        except Exception:
            result = {"ok": False, "ambiguous": True}
        message = result.get("result", {})
        if (result.get("ok") and message.get("chat", {}).get("id") == CHAT_ID
                and message.get("message_thread_id") == PROJECTS[project]):
            entry.update(status="delivered", message_id=message.get("message_id"))
        elif result.get("error_code") == 429 and attempts < 3:
            delay = result.get("parameters", {}).get("retry_after", 60)
            try:
                delay = max(1, min(int(delay), 86400))
            except (ValueError, TypeError):
                delay = 60
            entry.update(status="retry", next_attempt=time.time() + delay)
        elif result.get("ok") or result.get("ambiguous") or result.get("error_code", 0) >= 500:
            entry["status"] = "uncertain"
        else:
            entry["status"] = "failed"
        ledger[key] = entry
        # Keep the newest 500 event fingerprints. No message content is persisted.
        ledger = dict(sorted(ledger.items(), key=lambda pair: pair[1]["updated_at"])[-500:])
        atomic_save(ledger_path, ledger)
        return {"status": entry["status"], "project": project,
                "message_id": entry.get("message_id"), "attempts": attempts}


def probe(url: str, expected_body: str | None = None) -> dict:
    request = urllib.request.Request(url, headers={"User-Agent": "HillStreet-Open-Notify/1"})
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            status = response.status
            body_ok = expected_body is None or response.read(64).decode().strip() == expected_body
        return {"http": status, "body_ok": body_ok}
    except urllib.error.HTTPError as exc:
        return {"http": exc.code, "body_ok": False}
    except (OSError, ValueError):
        return {"http": None, "body_ok": False}


def reconcile(home: Path, config: Path) -> list[dict]:
    portfolio = json.loads(config.read_text(encoding="utf-8"))
    outcomes = []
    for project, settings in portfolio["projects"].items():
        url = settings.get("health_url")
        if project not in PROJECTS or not url:
            continue
        observation = probe(url, settings.get("expected_body"))
        label = "REACHABLE" if observation["http"] == 200 and observation["body_ok"] else "CHECK REQUIRED"
        summary = label + ": public endpoint HTTP " + str(observation["http"])
        summary += "\nObservation from Open-System runtime; this is not full production verification."
        fingerprint = hashlib.sha256(json.dumps(observation, sort_keys=True).encode()).hexdigest()[:20]
        # Local day prevents indefinite silence after a long stable interval.
        period = time.strftime("%Y-%m-%d", time.gmtime())
        outcomes.append(send_event(home, project, "health:" + period + ":" + fingerprint, summary))
    jobs_file = home / "cron" / "jobs.json"
    if jobs_file.exists():
        jobs_text = jobs_file.read_text(encoding="utf-8-sig")
        try:
            jobs_data = json.loads(jobs_text)
        except json.JSONDecodeError:
            # Match cron/jobs.py::_parse_jobs_file for supported legacy files
            # containing unescaped control characters.
            jobs_data = json.loads(jobs_text, strict=False)
        jobs = jobs_data.get("jobs", []) if isinstance(jobs_data, dict) else jobs_data
        failed = sorted(str(job["id"]) for job in jobs if job.get("enabled", True) and job.get("last_status") == "error")
        digest = hashlib.sha256(json.dumps(failed).encode()).hexdigest()[:20]
        period = time.strftime("%Y-%m-%d", time.gmtime())
        summary = "Scheduler audit: " + str(len(failed)) + " enabled jobs last reported an error."
        summary += "\nFailure details remain in the private execution ledger; no automatic credential rotation."
        outcomes.append(send_event(home, "open-system", "scheduler:" + period + ":" + digest, summary))
    return outcomes


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--home", type=Path, default=Path(os.environ.get("HERMES_HOME", "/opt/data")))
    parser.add_argument("--config", type=Path)
    parser.add_argument("--reconcile", action="store_true")
    parser.add_argument("--project", choices=PROJECTS)
    parser.add_argument("--event-key")
    parser.add_argument("--summary")
    parser.add_argument("--classification", choices=("operational", "client-safe"), default="operational")
    args = parser.parse_args()
    try:
        if args.reconcile:
            if args.config is None:
                parser.error("--config required for --reconcile")
            result = reconcile(args.home, args.config)
            ok = all(item["status"] in ("delivered", "retry") for item in result)
        else:
            if not args.project or not args.event_key or not args.summary:
                parser.error("--project, --event-key and --summary required")
            result = send_event(args.home, args.project, args.event_key, args.summary, args.classification)
            ok = result["status"] in ("delivered", "retry")
        print(json.dumps(result))
        return 0 if ok else 1
    except DeliveryBusyError:
        print(json.dumps({"status": "busy"}))
        return 75
    except (OSError, ValueError):
        print(json.dumps({"status": "configuration_error"}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
