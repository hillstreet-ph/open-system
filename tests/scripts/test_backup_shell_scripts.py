import json
import os
import shutil
import stat
import subprocess
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
pytestmark = pytest.mark.skipif(
    os.name == "nt" or shutil.which("bash") is None,
    reason="backup shell scripts require a POSIX host with bash",
)

BACKUP_ENVIRONMENT_KEYS = (
    "BACKUP_ENCRYPT_KEY",
    "BACKUP_S3_URI",
    "AWS_ACCESS_KEY_ID",
    "AWS_SECRET_ACCESS_KEY",
    "AWS_SESSION_TOKEN",
    "AWS_DEFAULT_REGION",
    "AWS_REGION",
)


def clean_backup_environment() -> dict[str, str]:
    env = os.environ.copy()
    for key in BACKUP_ENVIRONMENT_KEYS:
        env.pop(key, None)
    return env


def run_script(path: str, *args: str, env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["bash", str(ROOT / path), *args],
        cwd=ROOT,
        env=env,
        check=True,
        capture_output=True,
        text=True,
    )


def newest_directory(parent: Path) -> Path:
    return max((entry for entry in parent.iterdir() if entry.is_dir()), key=lambda entry: entry.name)


@pytest.mark.parametrize("encrypted", [False, True])
def test_state_backup_verifies_and_restores(tmp_path: Path, encrypted: bool) -> None:
    if encrypted and shutil.which("openssl") is None:
        pytest.skip("openssl is required for encrypted-backup coverage")

    source_parent = tmp_path / "source"
    hermes_home = source_parent / "data"
    hermes_home.mkdir(parents=True)
    (hermes_home / "state.txt").write_text("synthetic-state\n", encoding="utf-8")
    output = tmp_path / "backups"
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    upload_marker = tmp_path / "aws-uploaded"
    aws = bin_dir / "aws"
    aws.write_text(
        "#!/usr/bin/env bash\n"
        "set -euo pipefail\n"
        "[[ \"$1\" == 's3' && \"$2\" == 'cp' && \"$3\" == '--recursive' ]]\n"
        "python3 - \"$4/manifest.json\" <<'PY'\n"
        "import json, sys\n"
        "assert json.load(open(sys.argv[1], encoding='utf-8'))['verification_status'] == 'VERIFIED'\n"
        "PY\n"
        ": > \"$AWS_UPLOAD_MARKER\"\n",
        encoding="utf-8",
    )
    aws.chmod(aws.stat().st_mode | stat.S_IXUSR)
    env = clean_backup_environment()
    env.update(
        {
            "PATH": f"{bin_dir}:{env['PATH']}",
            "HERMES_HOME": str(hermes_home),
            "BACKUP_OUT_DIR": str(output),
            "OPEN_SYSTEM_GIT_SHA": "test-sha",
            "OPEN_SYSTEM_IMAGE_DIGEST": "sha256:" + "a" * 64,
            "BACKUP_S3_URI": "s3://synthetic-test/backups",
            "AWS_UPLOAD_MARKER": str(upload_marker),
        }
    )
    if encrypted:
        env["BACKUP_ENCRYPT_KEY"] = "synthetic-test-passphrase"

    run_script("scripts/backup/backup-state.sh", env=env)
    backup_dir = newest_directory(output)
    run_script("scripts/backup/verify-backup.sh", str(backup_dir), env=env)

    manifest = json.loads((backup_dir / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["git_sha"] == "test-sha"
    assert manifest["verification_status"] == "VERIFIED"
    assert manifest["encrypted"] is encrypted
    assert upload_marker.exists()

    restore_parent = tmp_path / "restore"
    restore_home = restore_parent / "data"
    restore_env = env | {"HERMES_HOME": str(restore_home), "RESTORE_CONFIRM": "YES"}
    run_script("scripts/restore/restore-state.sh", str(backup_dir), env=restore_env)
    assert (restore_home / "state.txt").read_text(encoding="utf-8") == "synthetic-state\n"


def test_scheduled_database_backup_requires_explicit_enablement() -> None:
    workflow = (ROOT / ".github/workflows/backup-scheduled.yml").read_text(encoding="utf-8")
    requirements = (ROOT / "deploy/docs/GITHUB_SECRETS_REQUIREMENTS.md").read_text(
        encoding="utf-8"
    )

    assert "vars.BACKUP_DATABASE_ENABLED == 'true'" in workflow
    assert "secrets.BACKUP_ENCRYPT_KEY" in workflow
    assert "BACKUP_DATABASE_ENABLED" in requirements
    assert "BACKUP_ENCRYPT_KEY" in requirements


@pytest.mark.parametrize("encrypted", [False, True])
def test_database_backup_manifest_and_verification(tmp_path: Path, encrypted: bool) -> None:
    if encrypted and shutil.which("openssl") is None:
        pytest.skip("openssl is required for encrypted-backup coverage")

    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    pg_dump = bin_dir / "pg_dump"
    pg_dump.write_text(
        "#!/usr/bin/env bash\n"
        "set -euo pipefail\n"
        "while (( $# )); do\n"
        "  if [[ \"$1\" == '-f' ]]; then shift; printf 'PGDMPsynthetic' > \"$1\"; exit 0; fi\n"
        "  shift\n"
        "done\n"
        "exit 1\n",
        encoding="utf-8",
    )
    pg_restore = bin_dir / "pg_restore"
    pg_restore.write_text(
        "#!/usr/bin/env bash\n"
        "set -euo pipefail\n"
        "[[ \"$1\" == '--exit-on-error' ]]\n"
        "[[ \"$2\" == '--file=/dev/null' ]]\n"
        "[[ -s \"$3\" ]]\n"
        "grep -q 'PGDMPsynthetic' \"$3\"\n",
        encoding="utf-8",
    )
    pg_dump.chmod(pg_dump.stat().st_mode | stat.S_IXUSR)
    pg_restore.chmod(pg_restore.stat().st_mode | stat.S_IXUSR)
    aws = bin_dir / "aws"
    aws.write_text(
        "#!/usr/bin/env bash\n"
        "set -euo pipefail\n"
        "[[ \"$1\" == 's3' && \"$2\" == 'cp' && \"$3\" == '--recursive' ]]\n"
        "python3 - \"$4/manifest.json\" <<'PY'\n"
        "import json, sys\n"
        "assert json.load(open(sys.argv[1], encoding='utf-8'))['verification_status'] == 'VERIFIED'\n"
        "PY\n"
        ": > \"$AWS_UPLOAD_MARKER\"\n",
        encoding="utf-8",
    )
    aws.chmod(aws.stat().st_mode | stat.S_IXUSR)

    output = tmp_path / "database-backups"
    upload_marker = tmp_path / "aws-uploaded"
    env = clean_backup_environment()
    env.update(
        {
            "PATH": f"{bin_dir}:{env['PATH']}",
            "DATABASE_URL": "postgresql://synthetic.invalid/example",
            "BACKUP_OUT_DIR": str(output),
            "OPEN_SYSTEM_GIT_SHA": "database-test-sha",
            "BACKUP_S3_URI": "s3://synthetic-test/backups",
            "AWS_UPLOAD_MARKER": str(upload_marker),
        }
    )
    if encrypted:
        env["BACKUP_ENCRYPT_KEY"] = "synthetic-database-passphrase"

    run_script("scripts/supabase/backup-database.sh", env=env)
    backup_dir = newest_directory(output)
    run_script("scripts/backup/verify-backup.sh", str(backup_dir), env=env)
    manifest = json.loads((backup_dir / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["type"] == "postgres"
    assert manifest["git_sha"] == "database-test-sha"
    assert manifest["verification_status"] == "VERIFIED"
    assert manifest["encrypted"] is encrypted
    assert upload_marker.exists()


def test_database_backup_does_not_upload_when_full_verification_fails(tmp_path: Path) -> None:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    pg_dump = bin_dir / "pg_dump"
    pg_dump.write_text(
        "#!/usr/bin/env bash\n"
        "set -euo pipefail\n"
        "while (( $# )); do\n"
        "  if [[ \"$1\" == '-f' ]]; then shift; printf 'PGDMPcorrupt' > \"$1\"; exit 0; fi\n"
        "  shift\n"
        "done\n"
        "exit 1\n",
        encoding="utf-8",
    )
    pg_restore = bin_dir / "pg_restore"
    pg_restore.write_text("#!/usr/bin/env bash\nexit 1\n", encoding="utf-8")
    upload_marker = tmp_path / "aws-uploaded"
    aws = bin_dir / "aws"
    aws.write_text(
        "#!/usr/bin/env bash\n: > \"$AWS_UPLOAD_MARKER\"\n",
        encoding="utf-8",
    )
    for executable in (pg_dump, pg_restore, aws):
        executable.chmod(executable.stat().st_mode | stat.S_IXUSR)

    output = tmp_path / "database-backups"
    env = clean_backup_environment() | {
        "PATH": f"{bin_dir}:{os.environ['PATH']}",
        "DATABASE_URL": "postgresql://synthetic.invalid/example",
        "BACKUP_OUT_DIR": str(output),
        "BACKUP_S3_URI": "s3://synthetic-test/backups",
        "AWS_UPLOAD_MARKER": str(upload_marker),
    }
    result = subprocess.run(
        ["bash", str(ROOT / "scripts/supabase/backup-database.sh")],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert not upload_marker.exists()
    manifest = json.loads(
        (newest_directory(output) / "manifest.json").read_text(encoding="utf-8")
    )
    assert manifest["verification_status"] == "UNVERIFIED"


def test_state_restore_rejects_database_backup(tmp_path: Path) -> None:
    backup_dir = tmp_path / "db-backup"
    backup_dir.mkdir()
    archive = backup_dir / "database.dump"
    archive.write_bytes(b"PGDMPsynthetic")
    (backup_dir / "checksums.sha256").write_text(
        f"{__import__('hashlib').sha256(archive.read_bytes()).hexdigest()}  {archive.name}\n",
        encoding="utf-8",
    )
    (backup_dir / "manifest.json").write_text(
        json.dumps(
            {
                "backup_id": "db-backup",
                "type": "postgres",
                "archive": archive.name,
                "verification_status": "UNVERIFIED",
            }
        ),
        encoding="utf-8",
    )
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    pg_restore = bin_dir / "pg_restore"
    pg_restore.write_text("#!/usr/bin/env bash\nexit 0\n", encoding="utf-8")
    pg_restore.chmod(pg_restore.stat().st_mode | stat.S_IXUSR)
    env = clean_backup_environment() | {
        "PATH": f"{bin_dir}:{os.environ['PATH']}",
        "HERMES_HOME": str(tmp_path / "restore" / "data"),
        "RESTORE_CONFIRM": "YES",
    }

    result = subprocess.run(
        ["bash", str(ROOT / "scripts/restore/restore-state.sh"), str(backup_dir)],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 4
    assert "Refusing to restore backup type 'postgres'" in result.stderr
