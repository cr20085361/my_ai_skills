from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace


SCRIPT = Path(__file__).parents[1] / "source" / "custom" / "engineering" / "project-version-manager" / "scripts" / "version_ledger.py"
SPEC = importlib.util.spec_from_file_location("version_ledger", SCRIPT)
assert SPEC and SPEC.loader
version_ledger = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(version_ledger)


def arguments(project: Path, **overrides):
    values = {
        "project": str(project),
        "current_version": "v1.2.9",
        "version_source": "package.json#version",
        "level": "patch",
        "next_version": None,
        "new_project": False,
        "iteration_id": "iteration-001",
        "summary": "修复导入异常",
        "verification": "python -m unittest",
        "verified": True,
    }
    values.update(overrides)
    return SimpleNamespace(**values)


class ProjectVersionManagerTests(unittest.TestCase):
    def test_standard_bumps_do_not_roll_over_at_nine(self):
        self.assertEqual(version_ledger.bump_version("v1.2.9", "patch"), "v1.2.10")
        self.assertEqual(version_ledger.bump_version("v1.2.10", "minor"), "v1.3.0")
        self.assertEqual(version_ledger.bump_version("v1.3.4", "major"), "v2.0.0")

    def test_preview_does_not_write_and_record_creates_existing_project_baseline(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            result = version_ledger.preview(arguments(project))
            self.assertEqual(result["to_version"], "v1.2.10")
            self.assertFalse((project / ".iteration-version.json").exists())
            result = version_ledger.record(arguments(project))
            self.assertEqual(result["status"], "recorded")
            ledger = json.loads((project / ".iteration-version.json").read_text(encoding="utf-8"))
            self.assertEqual(ledger["baseline"]["version"], "v1.2.9")
            self.assertEqual(ledger["current_version"], "v1.2.10")
            self.assertEqual(ledger["completed_iterations"], 1)

    def test_same_iteration_id_is_idempotent_but_conflicts_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            version_ledger.record(arguments(project))
            reused = version_ledger.record(arguments(project, current_version="v1.2.10"))
            self.assertEqual(reused["status"], "reused")
            with self.assertRaises(version_ledger.VersionLedgerError):
                version_ledger.record(arguments(project, current_version="v1.2.10", summary="不同摘要"))

    def test_new_project_initial_delivery_and_verification_requirement(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            result = version_ledger.record(arguments(project, current_version=None, new_project=True, level="initial"))
            self.assertEqual(result["to_version"], "v1.0.0")
            self.assertEqual(result["completed_iterations"], 1)
            with self.assertRaises(version_ledger.VersionLedgerError):
                version_ledger.record(arguments(project / "failed", verified=False))

    def test_pre_release_requires_explicit_next_version_and_bad_ledger_fails(self):
        with self.assertRaises(version_ledger.VersionLedgerError):
            version_ledger.bump_version("v2.0.0-rc.1", "patch")
        self.assertEqual(version_ledger.bump_version("v2.0.0-rc.1", "patch", "v2.0.0"), "v2.0.0")
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            (project / ".iteration-version.json").write_text("not json", encoding="utf-8")
            with self.assertRaises(version_ledger.VersionLedgerError):
                version_ledger.preview(arguments(project))


if __name__ == "__main__":
    unittest.main()
