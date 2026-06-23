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


def validate_metadata(expected_names, errors):
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


def main():
    errors = []
    expected_names = validate_rule_files(errors)
    validate_forbidden_dirs(errors)
    validate_metadata(expected_names, errors)

    if errors:
        print("Repository validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print(f"Repository validation passed: {len(expected_names)} rules")
    return 0


if __name__ == "__main__":
    sys.exit(main())
