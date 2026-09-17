#!/usr/bin/env python3
"""Maintain a project-local semantic version and completed-iteration ledger."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import tempfile
from pathlib import Path
from typing import Any


LEDGER_NAME = ".iteration-version.json"
SCHEMA_VERSION = 1
VERSION_RE = re.compile(
    r"^v?(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
    r"(?P<prerelease>-(?:[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?"
    r"(?P<build>\+(?:[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?$"
)


class VersionLedgerError(ValueError):
    """Raised when a ledger or version transition is invalid."""


def normalize_version(value: str) -> str:
    match = VERSION_RE.fullmatch((value or "").strip())
    if not match:
        raise VersionLedgerError(f"invalid semantic version: {value!r}")
    major, minor, patch = match.group(1), match.group(2), match.group(3)
    return f"v{major}.{minor}.{patch}{match.group('prerelease') or ''}{match.group('build') or ''}"


def split_version(value: str) -> tuple[int, int, int, str, str]:
    normalized = normalize_version(value)
    match = VERSION_RE.fullmatch(normalized)
    assert match is not None
    return (
        int(match.group(1)),
        int(match.group(2)),
        int(match.group(3)),
        match.group("prerelease") or "",
        match.group("build") or "",
    )


def bump_version(current_version: str, level: str, next_version: str | None = None) -> str:
    major, minor, patch, prerelease, _ = split_version(current_version)
    if next_version:
        candidate = normalize_version(next_version)
        next_major, next_minor, next_patch, _, _ = split_version(candidate)
        if (next_major, next_minor, next_patch) < (major, minor, patch):
            raise VersionLedgerError("next version cannot be lower than the current version")
        if candidate == normalize_version(current_version):
            raise VersionLedgerError("next version must differ from the current version")
        return candidate
    if prerelease:
        raise VersionLedgerError("pre-release versions require --next-version to preserve project policy")
    if level == "patch":
        return f"v{major}.{minor}.{patch + 1}"
    if level == "minor":
        return f"v{major}.{minor + 1}.0"
    if level == "major":
        return f"v{major + 1}.0.0"
    raise VersionLedgerError(f"unsupported iteration level: {level}")


def ledger_path(project: str | Path) -> Path:
    return Path(project).resolve() / LEDGER_NAME


def read_ledger(project: str | Path) -> dict[str, Any] | None:
    path = ledger_path(project)
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise VersionLedgerError(f"unable to read ledger {path}: {exc}") from exc
    if not isinstance(data, dict) or data.get("schema_version") != SCHEMA_VERSION:
        raise VersionLedgerError(f"unsupported ledger schema in {path}")
    if not isinstance(data.get("completed_iterations"), int) or data["completed_iterations"] < 0:
        raise VersionLedgerError(f"invalid completed_iterations in {path}")
    if not isinstance(data.get("history"), list):
        raise VersionLedgerError(f"invalid history in {path}")
    data["current_version"] = normalize_version(data.get("current_version", ""))
    return data


def now_iso() -> str:
    return dt.datetime.now().astimezone().isoformat(timespec="seconds")


def create_baseline(current_version: str, version_source: str | None = None) -> dict[str, Any]:
    version = normalize_version(current_version)
    return {
        "schema_version": SCHEMA_VERSION,
        "baseline": {
            "version": version,
            "recorded_at": now_iso(),
            "version_source": version_source or None,
        },
        "current_version": version,
        "completed_iterations": 0,
        "history": [],
    }


def resolve_state(
    project: str | Path,
    current_version: str | None,
    new_project: bool,
    version_source: str | None,
) -> dict[str, Any]:
    state = read_ledger(project)
    if state:
        if current_version and normalize_version(current_version) != state["current_version"]:
            raise VersionLedgerError(
                f"version source {normalize_version(current_version)} conflicts with ledger {state['current_version']}"
            )
        return state
    if new_project:
        return create_baseline("v1.0.0", version_source)
    if not current_version:
        raise VersionLedgerError("existing projects require --current-version when no ledger exists")
    return create_baseline(current_version, version_source)


def make_transition(
    state: dict[str, Any],
    level: str,
    next_version: str | None,
    new_project: bool,
) -> tuple[str, int]:
    if new_project:
        if level != "initial":
            raise VersionLedgerError("new projects must use level initial")
        return "v1.0.0", 1
    if level == "initial":
        raise VersionLedgerError("level initial is only valid for a new project")
    return bump_version(state["current_version"], level, next_version), state["completed_iterations"] + 1


def preview(args: argparse.Namespace) -> dict[str, Any]:
    state = resolve_state(args.project, args.current_version, args.new_project, args.version_source)
    next_version, next_count = make_transition(state, args.level, args.next_version, args.new_project)
    return {
        "status": "preview",
        "ledger": str(ledger_path(args.project)),
        "from_version": None if args.new_project else state["current_version"],
        "to_version": next_version,
        "level": args.level,
        "completed_iterations": next_count,
        "would_create_baseline": read_ledger(args.project) is None,
    }


def atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_name, path)
    except Exception:
        try:
            os.unlink(temporary_name)
        except FileNotFoundError:
            pass
        raise


def record(args: argparse.Namespace) -> dict[str, Any]:
    if not args.verified or not args.verification.strip():
        raise VersionLedgerError("record requires --verified and a non-empty --verification")
    state = resolve_state(args.project, args.current_version, args.new_project, args.version_source)
    for entry in state["history"]:
        if entry.get("id") != args.iteration_id:
            continue
        matching_fields = ("level", "summary", "verification")
        if all(entry.get(field) == getattr(args, field) for field in matching_fields):
            return {
                "status": "reused",
                "id": entry["id"],
                "from_version": entry["from_version"],
                "to_version": entry["to_version"],
                "level": entry["level"],
                "summary": entry["summary"],
                "verification": entry["verification"],
                "completed_iterations": state["completed_iterations"],
            }
        raise VersionLedgerError("iteration_id already exists with different transition data")
    next_version, next_count = make_transition(state, args.level, args.next_version, args.new_project)
    expected = {
        "id": args.iteration_id,
        "from_version": None if args.new_project else state["current_version"],
        "to_version": next_version,
        "level": args.level,
        "summary": args.summary,
        "verification": args.verification,
    }
    entry = {**expected, "recorded_at": now_iso()}
    state["history"].append(entry)
    state["current_version"] = next_version
    state["completed_iterations"] = next_count
    atomic_write_json(ledger_path(args.project), state)
    return {"status": "recorded", **expected, "completed_iterations": next_count}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    for command in ("preview", "record"):
        subparser = subparsers.add_parser(command)
        subparser.add_argument("--project", required=True, help="project root containing the ledger")
        subparser.add_argument("--current-version", help="existing project version when creating a baseline")
        subparser.add_argument("--version-source", help="human-readable location of the existing version source")
        subparser.add_argument("--level", required=True, choices=("initial", "patch", "minor", "major"))
        subparser.add_argument("--next-version", help="explicit version for pre-release or project-specific policy")
        subparser.add_argument("--new-project", action="store_true", help="record the first v1.0.0 delivery")
        if command == "record":
            subparser.add_argument("--iteration-id", required=True)
            subparser.add_argument("--summary", required=True)
            subparser.add_argument("--verification", required=True)
            subparser.add_argument("--verified", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        result = preview(args) if args.command == "preview" else record(args)
    except VersionLedgerError as exc:
        print(json.dumps({"status": "error", "error": str(exc)}, ensure_ascii=False))
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
