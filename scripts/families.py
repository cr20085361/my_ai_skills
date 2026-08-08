#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PGRMS skill-family manifest loading, validation, and resolution."""

import json
import os
import re


FAMILY_ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")
ALLOWED_MEMBER_KINDS = {"core", "extension", "governance"}
MIN_FAMILY_MEMBERS = 2
REQUIRED_MANIFEST_FIELDS = {
    "schema_version",
    "id",
    "title",
    "description",
    "members",
    "ownership",
}


class FamilyValidationError(ValueError):
    """Raised when one or more family manifests are invalid."""

    def __init__(self, errors):
        self.errors = list(errors)
        super().__init__("\n".join(self.errors))


def _manifest_paths(source_dir):
    families_dir = os.path.join(source_dir, "families")
    if not os.path.isdir(families_dir):
        return []
    paths = []
    for item in sorted(os.listdir(families_dir)):
        path = os.path.join(families_dir, item, "family.json")
        if os.path.isfile(path):
            paths.append(path)
    return paths


def _display_path(path, source_dir):
    repo_root = os.path.dirname(source_dir)
    return os.path.relpath(path, repo_root).replace("\\", "/")


def _validate_dependency_graph(family_id, members, errors, display_path):
    member_ids = {member["skill"] for member in members if "skill" in member}
    graph = {member_id: [] for member_id in member_ids}
    for member in members:
        skill = member.get("skill")
        if skill not in graph:
            continue
        depends_on = member.get("depends_on", [])
        if not isinstance(depends_on, list):
            errors.append(f"{display_path}: member {skill!r} depends_on must be a list")
            continue
        for dependency in depends_on:
            if dependency == skill:
                errors.append(f"{display_path}: member {skill!r} cannot depend on itself")
            elif dependency not in member_ids:
                errors.append(
                    f"{display_path}: member {skill!r} depends on unknown family member {dependency!r}"
                )
            else:
                graph[skill].append(dependency)

    visiting = set()
    visited = set()

    def visit(node, chain):
        if node in visiting:
            cycle = " -> ".join(chain + [node])
            errors.append(f"{display_path}: dependency cycle in family {family_id!r}: {cycle}")
            return
        if node in visited:
            return
        visiting.add(node)
        for dependency in graph.get(node, []):
            visit(dependency, chain + [node])
        visiting.remove(node)
        visited.add(node)

    for node in sorted(graph):
        visit(node, [])


def validate_family_manifest(manifest, path, source_dir, rule_names=None):
    """Return a normalized manifest and a list of validation errors."""
    display_path = _display_path(path, source_dir)
    errors = []
    if not isinstance(manifest, dict):
        return None, [f"{display_path}: manifest root must be an object"]

    missing = sorted(REQUIRED_MANIFEST_FIELDS - set(manifest))
    if missing:
        errors.append(f"{display_path}: missing fields: {', '.join(missing)}")

    family_id = manifest.get("id")
    expected_id = os.path.basename(os.path.dirname(path))
    if not isinstance(family_id, str) or not FAMILY_ID_RE.match(family_id):
        errors.append(f"{display_path}: invalid family id {family_id!r}")
    elif family_id != expected_id:
        errors.append(f"{display_path}: family id must match directory name {expected_id!r}")

    if manifest.get("schema_version") != 1:
        errors.append(f"{display_path}: unsupported schema_version {manifest.get('schema_version')!r}")

    members = manifest.get("members", [])
    if not isinstance(members, list):
        errors.append(f"{display_path}: members must be a list")
        members = []
    elif len(members) < MIN_FAMILY_MEMBERS:
        errors.append(
            f"{display_path}: a family must contain at least {MIN_FAMILY_MEMBERS} members"
        )

    seen_members = set()
    normalized_members = []
    for index, raw_member in enumerate(members):
        if not isinstance(raw_member, dict):
            errors.append(f"{display_path}: members[{index}] must be an object")
            continue
        skill = raw_member.get("skill")
        kind = raw_member.get("kind")
        role = raw_member.get("role")
        depends_on = raw_member.get("depends_on", [])
        if not isinstance(skill, str) or not FAMILY_ID_RE.match(skill):
            errors.append(f"{display_path}: members[{index}] has invalid skill {skill!r}")
            continue
        if skill in seen_members:
            errors.append(f"{display_path}: duplicate member {skill!r}")
            continue
        seen_members.add(skill)
        if rule_names is not None and skill not in rule_names:
            errors.append(f"{display_path}: unknown skill {skill!r}")
        if kind not in ALLOWED_MEMBER_KINDS:
            errors.append(f"{display_path}: member {skill!r} has invalid kind {kind!r}")
        if not isinstance(role, str) or not role.strip():
            errors.append(f"{display_path}: member {skill!r} must have a non-empty role")
        if not isinstance(depends_on, list) or any(not isinstance(item, str) for item in depends_on):
            errors.append(f"{display_path}: member {skill!r} depends_on must contain skill names")
            depends_on = []
        normalized_members.append(
            {
                "skill": skill,
                "kind": kind,
                "role": role,
                "depends_on": list(depends_on),
            }
        )

    _validate_dependency_graph(family_id, normalized_members, errors, display_path)

    governance = manifest.get("governance", {})
    if governance and not isinstance(governance, dict):
        errors.append(f"{display_path}: governance must be an object")
        governance = {}
    retrospective = governance.get("retrospective_skill") if governance else None
    shared_retrospective = governance.get("shared_retrospective", False) if governance else False
    if not isinstance(shared_retrospective, bool):
        errors.append(f"{display_path}: shared_retrospective must be a boolean")
        shared_retrospective = False

    ownership_members = set(seen_members)
    if retrospective:
        member_map = {member["skill"]: member for member in normalized_members}
        if retrospective not in member_map and not shared_retrospective:
            errors.append(
                f"{display_path}: retrospective_skill must be a family member "
                "unless shared_retrospective is true"
            )
        elif retrospective not in member_map:
            if rule_names is not None and retrospective not in rule_names:
                errors.append(
                    f"{display_path}: shared retrospective_skill {retrospective!r} is not a known skill"
                )
            ownership_members.add(retrospective)
        elif member_map[retrospective].get("kind") != "governance":
            errors.append(f"{display_path}: retrospective_skill must have kind 'governance'")
        elif shared_retrospective:
            errors.append(
                f"{display_path}: shared_retrospective is only valid for a governance skill outside the family"
            )
    elif shared_retrospective:
        errors.append(f"{display_path}: shared_retrospective requires retrospective_skill")

    ownership = manifest.get("ownership", {})
    if not isinstance(ownership, dict) or not ownership:
        errors.append(f"{display_path}: ownership must be a non-empty object")
        ownership = {}
    else:
        for topic, owner in ownership.items():
            if not isinstance(topic, str) or not FAMILY_ID_RE.match(topic):
                errors.append(f"{display_path}: invalid ownership topic {topic!r}")
            if owner not in ownership_members:
                errors.append(f"{display_path}: ownership topic {topic!r} has unknown owner {owner!r}")

    normalized = {
        "schema_version": 1,
        "id": family_id,
        "title": manifest.get("title", family_id),
        "description": manifest.get("description", ""),
        "members": normalized_members,
        "ownership": ownership,
        "governance": governance,
        "path": display_path,
        "validation": {"status": "valid" if not errors else "invalid", "errors": errors},
    }
    return normalized, errors


def load_family_manifests(source_dir, rule_names=None, strict=True):
    """Load all manifests and enforce one primary family per skill."""
    families = {}
    errors = []
    member_families = {}
    for path in _manifest_paths(source_dir):
        display_path = _display_path(path, source_dir)
        try:
            with open(path, "r", encoding="utf-8") as handle:
                raw_manifest = json.load(handle)
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"{display_path}: unable to read JSON: {exc}")
            continue
        manifest, manifest_errors = validate_family_manifest(
            raw_manifest, path, source_dir, rule_names=rule_names
        )
        errors.extend(manifest_errors)
        if not manifest or not manifest.get("id"):
            continue
        family_id = manifest["id"]
        if family_id in families:
            errors.append(f"{display_path}: duplicate family id {family_id!r}")
            continue
        families[family_id] = manifest
        for member in manifest.get("members", []):
            skill = member["skill"]
            previous = member_families.get(skill)
            if previous:
                errors.append(
                    f"{display_path}: skill {skill!r} belongs to multiple families: {previous!r}, {family_id!r}"
                )
            else:
                member_families[skill] = family_id

    if errors and strict:
        raise FamilyValidationError(errors)
    return families, errors


def index_family_memberships(families):
    memberships = {}
    for family_id, family in families.items():
        for member in family.get("members", []):
            memberships[member["skill"]] = family_id
    return memberships


def resolve_family_rules(metadata, family_ids):
    """Resolve explicitly selected families to an ordered, complete rule list."""
    families = metadata.get("families", {})
    rules = metadata.get("rules", {})
    selected = []
    seen = set()
    for family_id in family_ids or []:
        if family_id not in families:
            raise FamilyValidationError([f"unknown family {family_id!r}"])
        family = families[family_id]
        required_skills = [member["skill"] for member in family.get("members", [])]
        governance = family.get("governance", {})
        if governance.get("shared_retrospective"):
            required_skills.append(governance["retrospective_skill"])
        for skill in required_skills:
            rule = rules.get(skill)
            if not rule:
                raise FamilyValidationError(
                    [f"family {family_id!r} references missing rule {skill!r}"]
                )
            if rule.get("status") != "active" or rule.get("score", 10.0) < 5.0:
                raise FamilyValidationError(
                    [f"family {family_id!r} member {skill!r} is not active and healthy"]
                )
            if skill not in seen:
                selected.append(rule)
                seen.add(skill)
    return selected
