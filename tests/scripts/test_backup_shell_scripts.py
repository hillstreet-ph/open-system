import json
import os
import shutil
import stat
import subprocess
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]


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
    env = os.environ.copy()
    env.update(
        {
            "HERMES_HOME": str(hermes_home),
            "BACKUP_OUT_DIR": str(output),
            "OPEN_SYSTEM_GIT_SHA": "test-sha",
            "OPEN_SYSTEM_IMAGE_DIGEST": "sha256:" + "a" * 64,
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

    restore_parent = tmp_path / "restore"
    restore_home = restore_parent / "data"
    restore_env = env | {"HERMES_HOME": str(restore_home), "RESTORE_CONFIRM": "YES"}
    run_script("scripts/restore/restore-state.sh", str(backup_dir), env=restore_env)
    assert (restore_home / "state.txt").read_text(encoding="utf-8") == "synthetic-state\n"


def test_database_backup_manifest_and_verification(tmp_path: Path) -> None:
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
        "#!/usr/bin/env bash\nset -euo pipefail\n[[ \"$1\" == '--list' ]]\ntest -s \"$2\"\n",
        encoding="utf-8",
    )
    pg_dump.chmod(pg_dump.stat().st_mode | stat.S_IXUSR)
    pg_restore.chmod(pg_restore.stat().st_mode | stat.S_IXUSR)

    output = tmp_path / "database-backups"
    env = os.environ.copy()
    env.update(
        {
            "PATH": f"{bin_dir}:{env['PATH']}",
            "DATABASE_URL": "postgresql://synthetic.invalid/example",
            "BACKUP_OUT_DIR": str(output),
            "OPEN_SYSTEM_GIT_SHA": "database-test-sha",
        }
    )

    run_script("scripts/supabase/backup-database.sh", env=env)
    backup_dir = newest_directory(output)
    run_script("scripts/backup/verify-backup.sh", str(backup_dir), env=env)
    manifest = json.loads((backup_dir / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["type"] == "postgres"
    assert manifest["git_sha"] == "database-test-sha"
    assert manifest["verification_status"] == "VERIFIED"


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
    env = os.environ | {
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
