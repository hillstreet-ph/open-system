"""HillStreet portfolio onboarding using the native Hermes Kanban store.

Run with ``python -m hermes_cli.portfolio``. Inspection is the default;
mutations require --apply and never start workers or copy credentials.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
from pathlib import Path

from hermes_cli import kanban_db as kb

PROJECTS = ("open-system", "open-connect", "open-box", "open-tgate", "open-teleset")
ROLES = {
    "engineering": ("coordinator", "developer", "reviewer", "qa"),
    "business": ("coordinator", "operations", "reviewer"),
    "agency": ("coordinator", "service-provider", "reviewer"),
    "data": ("coordinator", "data-organizer", "reviewer"),
}


def _check_context() -> None:
    # Native DB overrides outrank board= and must not collapse project stores.
    for key in ("HERMES_KANBAN_DB", "HERMES_KANBAN_BOARD", "HERMES_DELEGATED_CHILD_CONTEXT"):
        if os.environ.get(key, "").strip():
            raise ValueError(f"Portfolio administration cannot run with {key} set")


def onboard(*, apply: bool = False) -> list[dict]:
    """Create only missing native boards; preserve existing metadata and tasks."""
    _check_context()
    result = []
    for project in PROJECTS:
        exists = kb.board_exists(project)
        if apply and not exists:
            kb.create_board(project, name=project, description=f"hillstreet-ph/{project}")
        result.append({"project": project, "action": "existing" if exists else
                       ("created" if apply else "would-create"),
                       "db_path": str(kb.kanban_db_path(project))})
    return result


def _validate_routing(project: str, required_profiles: list[str]) -> Path:
    from hermes_cli.profiles import get_profile_dir

    for name in required_profiles:
        path = get_profile_dir(name)
        # A directory alias to default or another project is not isolation.
        if path.is_symlink() or path.resolve().name != name or not (path / "config.yaml").is_file():
            raise ValueError(f"Missing dedicated configured profile: {name}")
    metadata = kb.read_board_metadata(project)
    if metadata.get("project_id"):
        raise ValueError("Linked native project routing requires reconciliation before portfolio intake")
    workdir = metadata.get("default_workdir")
    if not workdir or not Path(workdir).is_absolute() or not Path(workdir).is_dir():
        raise ValueError("Board requires an existing absolute default_workdir")
    path = Path(workdir).resolve()
    def git(*args: str) -> str:
        result = subprocess.run(["git", "-C", str(path), *args], capture_output=True,
                                text=True, encoding="utf-8", errors="replace", timeout=10)
        if result.returncode:
            raise ValueError("Board workdir must be a project Git repository")
        return result.stdout.strip()
    if Path(git("rev-parse", "--show-toplevel")).resolve() != path:
        raise ValueError("Board default_workdir must be the repository root")
    origin = git("remote", "get-url", "origin")
    expected = f"hillstreet-ph/{project}"
    if origin.removesuffix(".git") not in (
        f"https://github.com/{expected}", f"git@github.com:{expected}",
        f"ssh://git@github.com/{expected}",
    ):
        raise ValueError("Board workdir origin does not match the selected project")
    return path


def intake(project: str, category: str, goal: str, request_id: str, *, apply: bool = False) -> dict:
    """Route an explicitly scoped goal into blocked intake, deduplicated by request ID.

    Role names are project-specific profile targets, not claimed provisioned
    accounts. A coordinator must provision/review profiles before promotion.
    """
    _check_context()
    if project not in PROJECTS or category not in ROLES:
        raise ValueError("Choose a known project and category")
    if not goal.strip() or not request_id.strip():
        raise ValueError("goal and request-id must be non-empty")
    profiles = [f"{project}-{category}-{role}" for role in ROLES[category]]
    plan = {"project": project, "category": category, "status": "blocked",
            "assignee": profiles[0], "required_profiles": profiles,
            "idempotency_key": f"portfolio:{project}:{request_id.strip()}",
            "action": "would-intake"}
    if apply:
        if not kb.board_exists(project):
            raise ValueError("Board is missing: run onboarding with --apply first")
        if kb.read_board_metadata(project).get("archived"):
            raise ValueError("Cannot intake into an archived board")
        workdir = _validate_routing(project, profiles)
        with kb.connect_closing(board=project) as conn:
            plan["task_id"] = kb.create_task(
                conn, title=goal.strip().splitlines()[0][:160],
                body=f"Category: {category}\nRequired profiles: {', '.join(profiles)}\n\n"
                     f"Goal:\n{goal.strip()}\n\n"
                     "Before promotion: validate project source references, access boundaries, "
                     "worker profiles, acceptance criteria, issue lock and independent review.",
                assignee=profiles[0], created_by="portfolio-intake", initial_status="blocked",
                initial_block_reason="Portfolio activation requires operator review and explicit unblock",
                workspace_kind="worktree", workspace_path=str(workdir),
                idempotency_key=plan["idempotency_key"], board=project,
            )
            plan["status"] = kb.get_task(conn, plan["task_id"]).status
        plan["action"] = "intake-recorded"
    return plan


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="Explicitly persist changes")
    parser.add_argument("--project", choices=PROJECTS)
    parser.add_argument("--category", choices=tuple(ROLES))
    parser.add_argument("--goal-file", type=Path, help="UTF-8 goal (no credentials)")
    parser.add_argument("--request-id", help="Stable source ID for retry deduplication")
    args = parser.parse_args(argv)
    fields = (args.project, args.category, args.goal_file, args.request_id)
    if any(fields) and not all(fields):
        parser.error("Goal intake requires --project, --category, --goal-file and --request-id")
    try:
        result = (intake(args.project, args.category, args.goal_file.read_text(encoding="utf-8"),
                         args.request_id, apply=args.apply) if all(fields)
                  else onboard(apply=args.apply))
    except (ValueError, OSError) as exc:
        parser.exit(2, f"{exc}\n")
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
