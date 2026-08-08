#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Lightweight repository validation for PGRMS.
"""

import json
import os
import re
import subprocess
import sys
import tempfile
import contextlib
import io

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from families import FamilyValidationError, load_family_manifests

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCE_DIR = os.path.join(ROOT_DIR, "source")
METADATA_FILE = os.path.join(ROOT_DIR, "metadata.json")

REQUIRED_FIELDS = {"name", "description", "category", "audience", "tags", "status", "score"}
ALLOWED_CATEGORIES = {"design", "engineering", "productivity", "registry"}
ALLOWED_AUDIENCES = {"codex-core", "codex-project", "archive"}
FORBIDDEN_DIRS = {".agent", ".agents", "temp_git_fetch", "__pycache__", ".pytest_cache", ".git"}
NAME_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")


def parse_frontmatter(path):
    with open(path, "r", encoding="utf-8-sig") as f:
        content = f.read()
    if not content.startswith("---"):
        return None
    parts = content.split("---", 2)
    if len(parts) < 3:
        return None
    data = {}
    for line in parts[1].strip().splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        data[key.strip()] = value.strip()
    return data


def normalize_name(name):
    name = re.sub(r"[^a-z0-9-]+", "-", (name or "").strip().lower())
    name = re.sub(r"-+", "-", name).strip("-")
    return name


def find_rule_files():
    rule_files = []
    for root, dirs, files in os.walk(SOURCE_DIR):
        dirs[:] = [d for d in dirs if d not in {".git"}]
        if "RULE.md" in files:
            rule_files.append(os.path.join(root, "RULE.md"))
    return sorted(rule_files)


def validate_rule_files(errors):
    expected_names = set()
    seen_paths = {}
    for path in find_rule_files():
        rel = os.path.relpath(path, ROOT_DIR).replace("\\", "/")
        meta = parse_frontmatter(path)
        if not meta:
            errors.append(f"{rel}: missing YAML frontmatter")
            continue

        missing = sorted(REQUIRED_FIELDS - set(meta))
        if missing:
            errors.append(f"{rel}: missing required fields: {', '.join(missing)}")

        normalized = normalize_name(meta.get("name", ""))
        if not normalized or not NAME_RE.match(normalized):
            errors.append(f"{rel}: invalid normalized name: {meta.get('name')!r}")
        elif normalized != meta.get("name"):
            errors.append(f"{rel}: name must be normalized as {normalized!r}")
        else:
            if normalized in seen_paths:
                errors.append(f"{rel}: duplicate rule name also used by {seen_paths[normalized]}")
            else:
                seen_paths[normalized] = rel
            expected_names.add(normalized)

        category = meta.get("category")
        if category not in ALLOWED_CATEGORIES:
            errors.append(f"{rel}: invalid category {category!r}")

        audience = meta.get("audience")
        if audience not in ALLOWED_AUDIENCES:
            errors.append(f"{rel}: invalid audience {audience!r}")

        tags = meta.get("tags", "")
        if not (tags.startswith("[") and tags.endswith("]")):
            errors.append(f"{rel}: tags must use inline list syntax")

    return expected_names


def validate_forbidden_dirs(errors):
    try:
        result = subprocess.run(
            ["git", "ls-files"],
            cwd=ROOT_DIR,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
    except Exception as exc:
        errors.append(f"unable to inspect tracked files: {exc}")
        return

    for tracked in result.stdout.splitlines():
        parts = tracked.replace("\\", "/").split("/")
        if any(part in FORBIDDEN_DIRS for part in parts):
            errors.append(f"forbidden tracked path: {tracked}")


def validate_metadata(expected_names, families, errors):
    if not os.path.exists(METADATA_FILE):
        errors.append("metadata.json is missing")
        return
    with open(METADATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    metadata_names = set(data.get("rules", {}))
    missing = sorted(expected_names - metadata_names)
    stale = sorted(metadata_names - expected_names)
    if missing:
        errors.append(f"metadata.json missing rules: {', '.join(missing)}")
    if stale:
        errors.append(f"metadata.json has stale rules: {', '.join(stale)}")
    if data.get("schema_version") != 2:
        errors.append("metadata.json schema_version must be 2")
    metadata_families = data.get("families", {})
    if set(metadata_families) != set(families):
        errors.append("metadata.json family index is stale")
    for family_id, family in families.items():
        if metadata_families.get(family_id) != family:
            errors.append(f"metadata.json family {family_id!r} is stale")
        for member in family.get("members", []):
            skill = member["skill"]
            if data.get("rules", {}).get(skill, {}).get("family") != family_id:
                errors.append(f"metadata.json rule {skill!r} has stale family projection")

    try:
        from pgrms import build_repository_metadata
        with contextlib.redirect_stdout(io.StringIO()):
            expected_metadata = build_repository_metadata(existing_metadata_file=METADATA_FILE)
        if data != expected_metadata:
            errors.append("metadata.json is not a fresh scan of source/")
    except (FamilyValidationError, OSError, ValueError) as exc:
        errors.append(f"unable to check metadata freshness: {exc}")


def validate_family_evals(metadata, families, errors):
    """要求每个受管成员和共享治理者都提供可执行示例。"""
    rule_map = metadata.get("rules", {})
    for family_id, family in families.items():
        required = [member["skill"] for member in family.get("members", [])]
        governance = family.get("governance", {})
        if governance.get("shared_retrospective"):
            required.append(governance["retrospective_skill"])
        for skill in sorted(set(required)):
            rule = rule_map.get(skill)
            if not rule:
                errors.append(f"family {family_id!r} eval target {skill!r} is missing from metadata")
                continue
            eval_path = os.path.join(ROOT_DIR, rule["path"], "evals", "evals.json")
            if not os.path.isfile(eval_path):
                errors.append(f"family {family_id!r} member {skill!r} is missing evals/evals.json")
                continue
            try:
                with open(eval_path, "r", encoding="utf-8") as handle:
                    eval_data = json.load(handle)
            except (OSError, json.JSONDecodeError) as exc:
                errors.append(f"family {family_id!r} member {skill!r} has unreadable evals: {exc}")
                continue
            if eval_data.get("skill_name") != skill or not isinstance(eval_data.get("evals"), list) or not eval_data["evals"]:
                errors.append(f"family {family_id!r} member {skill!r} has invalid or empty evals")


def validate_dashboard_freshness(errors):
    dashboard_file = os.path.join(ROOT_DIR, "dashboard.html")
    if not os.path.exists(dashboard_file):
        errors.append("dashboard.html is missing")
        return
    try:
        from dashboard import generate_html_dashboard
        with tempfile.TemporaryDirectory(prefix="pgrms-dashboard-check-") as temp_dir:
            expected_file = os.path.join(temp_dir, "dashboard.html")
            with contextlib.redirect_stdout(io.StringIO()):
                generate_html_dashboard(metadata_file=METADATA_FILE, output_file=expected_file)
            with open(dashboard_file, "rb") as actual, open(expected_file, "rb") as expected:
                if actual.read() != expected.read():
                    errors.append("dashboard.html is stale; run pgrms.py scan")
    except Exception as exc:
        errors.append(f"unable to check dashboard freshness: {exc}")


def main():
    errors = []
    expected_names = validate_rule_files(errors)
    families, family_errors = load_family_manifests(
        SOURCE_DIR,
        rule_names=expected_names,
        strict=False,
    )
    errors.extend(family_errors)
    validate_forbidden_dirs(errors)
    validate_metadata(expected_names, families, errors)
    if os.path.exists(METADATA_FILE):
        with open(METADATA_FILE, "r", encoding="utf-8") as handle:
            validate_family_evals(json.load(handle), families, errors)
    validate_dashboard_freshness(errors)

    if errors:
        print("Repository validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print(f"Repository validation passed: {len(expected_names)} rules, {len(families)} families")
    return 0


if __name__ == "__main__":
    sys.exit(main())
