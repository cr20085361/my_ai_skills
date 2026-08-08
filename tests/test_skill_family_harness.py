import json
import os
import sys
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from compiler import ensure_family_target_compatibility, load_active_rules
from families import FamilyValidationError, load_family_manifests
from pgrms import (
    build_repository_metadata,
    hash_file_tree,
    run_sync_skills,
)


def write_manifest(source_dir, family_id, manifest):
    family_dir = source_dir / "families" / family_id
    family_dir.mkdir(parents=True)
    path = family_dir / "family.json"
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def base_manifest(family_id="sample"):
    return {
        "schema_version": 1,
        "id": family_id,
        "title": "Sample Family",
        "description": "Synthetic family for validation.",
        "members": [
            {"skill": "skill-a", "kind": "core", "role": "foundation", "depends_on": []},
            {"skill": "skill-b", "kind": "core", "role": "builder", "depends_on": ["skill-a"]},
            {"skill": "skill-c", "kind": "extension", "role": "workflow", "depends_on": ["skill-b"]},
        ],
        "ownership": {
            "topic-a": "skill-a",
            "topic-b": "skill-b",
            "topic-c": "skill-c",
        },
    }


def test_repository_cst_family_is_valid_and_complete():
    metadata = build_repository_metadata()
    family = metadata["families"]["cst"]
    members = [member["skill"] for member in family["members"]]

    assert members == [
        "cst-control-skill",
        "cst-history-macro-skill",
        "cst-parametric-modeling",
        "cst-advanced-geometry-operations",
        "cst-antenna-paper-reproduction",
        "cst-skills-retrospective",
    ]
    assert all(metadata["rules"][skill].get("family") == "cst" for skill in members)


def test_repository_web_ui_family_is_valid_and_complete():
    metadata = build_repository_metadata()
    family = metadata["families"]["web-ui-delivery"]
    assert [member["skill"] for member in family["members"]] == [
        "ui-ux-pro-max",
        "frontend-design",
        "webapp-testing",
    ]
    assert family["governance"] == {
        "retrospective_skill": "skill-family-governance",
        "shared_retrospective": True,
    }
    assert family["ownership"]["family-governance"] == "skill-family-governance"


def test_valid_manifest_loads(tmp_path):
    source_dir = tmp_path / "source"
    write_manifest(source_dir, "sample", base_manifest())
    families, errors = load_family_manifests(
        str(source_dir),
        rule_names={"skill-a", "skill-b", "skill-c"},
        strict=False,
    )
    assert errors == []
    assert list(families) == ["sample"]


def test_two_member_family_is_valid(tmp_path):
    source_dir = tmp_path / "source"
    manifest = base_manifest()
    manifest["members"] = manifest["members"][:2]
    manifest["ownership"] = {"topic-a": "skill-a", "topic-b": "skill-b"}
    write_manifest(source_dir, "sample", manifest)
    _, errors = load_family_manifests(
        str(source_dir),
        rule_names={"skill-a", "skill-b"},
        strict=False,
    )
    assert errors == []


def test_shared_governance_can_own_a_family_topic(tmp_path):
    source_dir = tmp_path / "source"
    manifest = base_manifest()
    manifest["governance"] = {
        "retrospective_skill": "shared-governance",
        "shared_retrospective": True,
    }
    manifest["ownership"]["family-governance"] = "shared-governance"
    write_manifest(source_dir, "sample", manifest)
    _, errors = load_family_manifests(
        str(source_dir),
        rule_names={"skill-a", "skill-b", "skill-c", "shared-governance"},
        strict=False,
    )
    assert errors == []


def test_unknown_shared_governance_is_rejected(tmp_path):
    source_dir = tmp_path / "source"
    manifest = base_manifest()
    manifest["governance"] = {
        "retrospective_skill": "missing-governance",
        "shared_retrospective": True,
    }
    write_manifest(source_dir, "sample", manifest)
    _, errors = load_family_manifests(
        str(source_dir),
        rule_names={"skill-a", "skill-b", "skill-c"},
        strict=False,
    )
    assert any("not a known skill" in error for error in errors)


@pytest.mark.parametrize(
    "mutator, expected",
    [
        (lambda manifest: manifest["members"].__setitem__(1, {**manifest["members"][1], "skill": "missing"}), "unknown skill"),
        (lambda manifest: manifest["members"].append(dict(manifest["members"][0])), "duplicate member"),
        (lambda manifest: manifest["ownership"].__setitem__("bad-owner", "missing"), "unknown owner"),
        (lambda manifest: manifest["members"][1].update({"depends_on": ["not-a-member"]}), "depends on unknown family member"),
        (lambda manifest: manifest["members"][0].update({"depends_on": ["skill-c"]}), "dependency cycle"),
    ],
)
def test_manifest_validation_failures(tmp_path, mutator, expected):
    source_dir = tmp_path / "source"
    manifest = base_manifest()
    mutator(manifest)
    write_manifest(source_dir, "sample", manifest)
    _, errors = load_family_manifests(
        str(source_dir),
        rule_names={"skill-a", "skill-b", "skill-c"},
        strict=False,
    )
    assert any(expected in error for error in errors)


def test_cross_family_membership_is_rejected(tmp_path):
    source_dir = tmp_path / "source"
    write_manifest(source_dir, "sample", base_manifest())
    second = base_manifest("second")
    write_manifest(source_dir, "second", second)
    _, errors = load_family_manifests(
        str(source_dir),
        rule_names={"skill-a", "skill-b", "skill-c"},
        strict=False,
    )
    assert any("multiple families" in error for error in errors)


def test_duplicate_family_id_is_rejected(tmp_path):
    source_dir = tmp_path / "source"
    write_manifest(source_dir, "sample", base_manifest())
    duplicate = base_manifest()
    write_manifest(source_dir, "second-directory", duplicate)
    _, errors = load_family_manifests(
        str(source_dir),
        rule_names={"skill-a", "skill-b", "skill-c"},
        strict=False,
    )
    assert any("duplicate family id" in error for error in errors)


def test_explicit_family_selection_is_ordered_and_ignores_project_tags():
    metadata = build_repository_metadata()
    selected = load_active_rules(
        project_tags=["unrelated-tag"],
        family_ids=["cst"],
        metadata=metadata,
    )
    assert [rule["name"] for rule in selected] == [
        member["skill"] for member in metadata["families"]["cst"]["members"]
    ]


def test_shared_governance_is_packaged_after_web_ui_members():
    metadata = build_repository_metadata()
    selected = load_active_rules(
        family_ids=["web-ui-delivery"],
        metadata=metadata,
    )
    assert [rule["name"] for rule in selected] == [
        "ui-ux-pro-max",
        "frontend-design",
        "webapp-testing",
        "skill-family-governance",
    ]


def test_explicit_codex_family_deployment_rejects_archive_members():
    with pytest.raises(FamilyValidationError, match="would exclude archive members"):
        ensure_family_target_compatibility(
            [{"name": "archive-member", "audience": "archive"}],
            "codex",
        )


def test_every_managed_member_and_shared_governor_has_evals():
    metadata = build_repository_metadata()
    repo_root = Path(__file__).resolve().parents[1]
    for family in metadata["families"].values():
        managed = [member["skill"] for member in family["members"]]
        governance = family.get("governance", {})
        if governance.get("shared_retrospective"):
            managed.append(governance["retrospective_skill"])
        for skill in managed:
            rule = metadata["rules"][skill]
            eval_path = repo_root / rule["path"] / "evals" / "evals.json"
            data = json.loads(eval_path.read_text(encoding="utf-8"))
            assert data["skill_name"] == skill
            assert data["evals"]


def test_retrospective_evals_cover_positive_negative_and_noop_cases():
    repo_root = Path(__file__).resolve().parents[1]
    skill_dir = repo_root / "source" / "custom" / "engineering" / "cst-skills-retrospective"
    rule_text = (skill_dir / "RULE.md").read_text(encoding="utf-8")
    evals = json.loads((skill_dir / "evals" / "evals.json").read_text(encoding="utf-8"))["evals"]
    prompts = "\n".join(item["prompt"] for item in evals)

    assert "Wait for explicit user approval before writing" in rule_text
    assert "stop without editing, compiling, or synchronizing" in rule_text
    assert "CST 相关 skills 复盘" in prompts
    assert "S11" in prompts
    assert "远场方向图" in prompts
    assert "没有发现跨项目可复用" in prompts


def test_antenna_taper_lessons_are_routed_to_their_cst_owners():
    repo_root = Path(__file__).resolve().parents[1]
    engineering = repo_root / "source" / "custom" / "engineering"
    expectations = {
        "cst-history-macro-skill": "History/VBA parser preflight",
        "cst-parametric-modeling": "Physical-endpoint coordinate contract",
        "cst-advanced-geometry-operations": "Linear tapered rails and spacer bodies",
        "cst-control-skill": "Recovery after a History error",
    }
    for skill, heading in expectations.items():
        skill_dir = engineering / skill
        rule_text = (skill_dir / "RULE.md").read_text(encoding="utf-8")
        evals = json.loads((skill_dir / "evals" / "evals.json").read_text(encoding="utf-8"))["evals"]
        assert heading in rule_text
        assert any(item["id"] == 5 for item in evals)


def test_sync_skills_dry_run_does_not_create_home(tmp_path):
    fake_home = tmp_path / "home"
    manifest = run_sync_skills(family_ids=["cst"], apply=False, home_dir=str(fake_home))
    assert manifest is not None
    assert manifest["families"] == ["cst"]
    assert not fake_home.exists()


def test_sync_skills_apply_is_verified_non_pruning_and_idempotent(tmp_path):
    fake_home = tmp_path / "home"
    for relative in (".agent/skills", ".agents/skills", ".codex/skills"):
        foreign = fake_home / relative / "foreign-skill"
        foreign.mkdir(parents=True)
        (foreign / "sentinel.txt").write_text("preserve", encoding="utf-8")

    old_skill = fake_home / ".codex" / "skills" / "cst-control-skill"
    old_skill.mkdir(parents=True)
    (old_skill / "old.txt").write_text("old-version", encoding="utf-8")

    first = run_sync_skills(family_ids=["cst"], apply=True, home_dir=str(fake_home))
    assert first is not None
    for relative in (".agent/skills", ".agents/skills", ".codex/skills"):
        root = fake_home / relative
        assert (root / "foreign-skill" / "sentinel.txt").read_text(encoding="utf-8") == "preserve"
        assert (root / "cst-skills-retrospective" / "SKILL.md").exists()

    backups = list((fake_home / ".pgrms-deploy-logs" / "backups").rglob("old.txt"))
    assert backups
    assert backups[0].read_text(encoding="utf-8") == "old-version"

    before = {
        relative: hash_file_tree(str(fake_home / relative))
        for relative in (".agent/skills", ".agents/skills", ".codex/skills")
    }
    second = run_sync_skills(family_ids=["cst"], apply=True, home_dir=str(fake_home))
    assert second is not None
    after = {
        relative: hash_file_tree(str(fake_home / relative))
        for relative in (".agent/skills", ".agents/skills", ".codex/skills")
    }
    assert before == after
    assert not (fake_home / ".gitconfig").exists()
    assert not (fake_home / ".gemini" / "GEMINI.md").exists()
    assert not (fake_home / "AppData" / "Roaming" / "Code" / "User" / "prompts").exists()
