#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PGRMS (个人全局规则管理系统) - 主控制命令行程序
"""

import os
import sys
import argparse
import json
import datetime
import time
import shutil
import re
import subprocess
import hashlib
import tempfile

# 将脚本所在目录加入系统路径以方便导入其他模块
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 从共享工具模块导入（内部已处理 Windows UTF-8 编码）
from utils import (
    ROOT_DIR, SOURCE_DIR, METADATA_FILE, SCRIPTS_DIR, DIST_DIR,
    read_file_safely, safe_write_json, ensure_utf8_console,
    cli_success, cli_warning, cli_error, cli_info, cli_summary
)
from families import (
    FamilyValidationError,
    index_family_memberships,
    load_family_manifests,
    resolve_family_rules,
)

GLOBAL_DEPLOY_LOG_DIRNAME = ".pgrms-deploy-logs"


def normalize_rule_name(name):
    """
    Normalize rule identifiers for stable directory names and CLI usage.
    """
    normalized = re.sub(r"[^a-z0-9-]+", "-", (name or "").strip().lower())
    normalized = re.sub(r"-+", "-", normalized).strip("-")
    return normalized


def build_repository_metadata(existing_metadata_file=METADATA_FILE):
    """Build the complete repository index in memory without writing files."""
    metadata = {"schema_version": 2, "rules": {}, "families": {}}

    # 尝试读取已有的 metadata.json，以便保留动态运行统计
    existing_metadata = {}
    if existing_metadata_file and os.path.exists(existing_metadata_file):
        try:
            with open(existing_metadata_file, "r", encoding="utf-8") as f:
                existing_metadata = json.load(f).get("rules", {})
        except Exception as e:
            cli_warning(f"读取旧 metadata.json 失败: {str(e)}，将重新生成...")

    # 扫描 source/custom/ — 自动发现所有分类子目录（不再硬编码列表）
    custom_dir = os.path.join(SOURCE_DIR, "custom")
    if os.path.exists(custom_dir):
        for category in os.listdir(custom_dir):
            cat_path = os.path.join(custom_dir, category)
            if not os.path.isdir(cat_path):
                continue

            for item in os.listdir(cat_path):
                rule_path = os.path.join(cat_path, item)
                rule_file = os.path.join(rule_path, "RULE.md")

                if os.path.isdir(rule_path) and os.path.exists(rule_file):
                    rule_info = parse_rule_metadata(rule_file, "custom", category, f"source/custom/{category}/{item}")
                    if rule_info:
                        name = rule_info["name"]
                        if name in existing_metadata:
                            rule_info["score"] = existing_metadata[name].get("score", rule_info.get("score", 10.0))
                            rule_info["usage_count"] = existing_metadata[name].get("usage_count", 0)
                            rule_info["last_used_date"] = existing_metadata[name].get("last_used_date", "N/A")

                        metadata["rules"][name] = rule_info
                        print(f"  发现原创规则: [{category}] {name} (评分: {rule_info['score']})")

    # 扫描 source/registry/ 第三方目录
    registry_dir = os.path.join(SOURCE_DIR, "registry")
    if os.path.exists(registry_dir):
        for author in os.listdir(registry_dir):
            author_path = os.path.join(registry_dir, author)
            if not os.path.isdir(author_path):
                continue

            for item in os.listdir(author_path):
                rule_path = os.path.join(author_path, item)
                rule_file = os.path.join(rule_path, "RULE.md")

                if os.path.isdir(rule_path) and os.path.exists(rule_file):
                    rule_info = parse_rule_metadata(rule_file, "registry", "registry", f"source/registry/{author}/{item}")
                    if rule_info:
                        name = rule_info["name"]
                        meta_yml_path = os.path.join(rule_path, "metadata.yml")
                        if os.path.exists(meta_yml_path):
                            rule_info["registry_info"] = load_yaml_metadata(meta_yml_path)

                        if name in existing_metadata:
                            rule_info["score"] = existing_metadata[name].get("score", rule_info.get("score", 10.0))
                            rule_info["usage_count"] = existing_metadata[name].get("usage_count", 0)
                            rule_info["last_used_date"] = existing_metadata[name].get("last_used_date", "N/A")

                        metadata["rules"][name] = rule_info
                        print(f"  发现第三方规则: [{author}] {name} (评分: {rule_info['score']})")

    families, _ = load_family_manifests(
        SOURCE_DIR,
        rule_names=set(metadata["rules"]),
        strict=True,
    )
    memberships = index_family_memberships(families)
    for skill, family_id in memberships.items():
        metadata["rules"][skill]["family"] = family_id
    metadata["families"] = families
    return metadata


def scan_repository(write=True):
    """Scan source, validate families, and optionally rebuild generated snapshots."""
    t0 = time.time()
    cli_info("开始扫描 source 目录以重建规则索引库...")
    try:
        metadata = build_repository_metadata()
    except FamilyValidationError as exc:
        for error in exc.errors:
            cli_error(error)
        return None

    if not write:
        return metadata

    # 原子化安全写入
    try:
        safe_write_json(METADATA_FILE, metadata)

        # 自动重新生成 HTML 交互看板大屏
        try:
            from dashboard import generate_html_dashboard
            generate_html_dashboard()
        except Exception as err:
            cli_warning(f"自动更新交互看板大屏失败: {str(err)}")

        elapsed = time.time() - t0
        cli_summary(
            f"扫描完成 | 共记录 {len(metadata['rules'])} 条规则 | "
            f"{len(metadata['families'])} 个技能族 | 耗时 {elapsed:.2f}s"
        )
        return metadata
    except Exception as e:
        cli_error(f"保存 metadata.json 失败: {str(e)}")
        return None


def parse_rule_metadata(rule_file_path, source_type, category, relative_path):
    """
    解析 RULE.md 顶部的 YAML Frontmatter 获取元数据
    """
    try:
        content, used_enc = read_file_safely(rule_file_path)
        content = content.lstrip("\ufeff")

        if not content.strip().startswith("---"):
            return None

        parts = content.split("---")
        if len(parts) < 3:
            return None

        yaml_text = parts[1]
        metadata = {
            "name": "",
            "title": "",
            "description": "",
            "category": category,
            "audience": "archive",
            "tags": [],
            "status": "active",
            "score": 10.0,
            "usage_count": 0,
            "last_used_date": "N/A",
            "source_type": source_type,
            "path": relative_path
        }

        for line in yaml_text.strip().split("\n"):
            if ":" not in line:
                continue
            key, val = line.split(":", 1)
            key = key.strip().lower()
            val = val.strip()

            if val.startswith('"') and val.endswith('"'):
                val = val[1:-1]
            elif val.startswith("'") and val.endswith("'"):
                val = val[1:-1]

            if key == "name":
                metadata["name"] = val
            elif key == "title":
                metadata["title"] = val
            elif key == "description":
                metadata["description"] = val
            elif key == "category":
                metadata["category"] = val
            elif key == "audience":
                metadata["audience"] = val.lower()
            elif key == "status":
                metadata["status"] = val
            elif key == "score":
                try:
                    metadata["score"] = float(val)
                except:
                    pass
            elif key == "tags":
                val = val.replace("[", "").replace("]", "")
                metadata["tags"] = [t.strip() for t in val.split(",") if t.strip()]

        if not metadata["name"]:
            metadata["name"] = os.path.basename(os.path.dirname(rule_file_path))
        normalized_name = normalize_rule_name(metadata["name"])
        if normalized_name:
            metadata["name"] = normalized_name
        if not metadata["title"]:
            metadata["title"] = metadata["name"]

        return metadata
    except Exception as e:
        cli_error(f"解析 {rule_file_path} 出错: {str(e)}")
        return None


def load_yaml_metadata(yml_path):
    """
    轻量解析 YAML 辅助元数据
    """
    data = {}
    try:
        with open(yml_path, "r", encoding="utf-8") as f:
            for line in f:
                if ":" not in line:
                    continue
                k, v = line.split(":", 1)
                data[k.strip()] = v.strip()
    except Exception as e:
        cli_warning(f"解析 yaml 元数据出错: {str(e)}")
    return data


def list_rules(sort_by="name"):
    """
    列出当前系统的所有规则信息，支持排序
    """
    if not os.path.exists(METADATA_FILE):
        cli_warning("未检测到索引库，请先运行 'scan' 命令重建索引。")
        return

    try:
        with open(METADATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        cli_error(f"读取索引库失败: {str(e)}")
        return

    rules = data.get("rules", {})
    if not rules:
        cli_warning("当前系统内无任何已注册的规则！")
        return

    items = list(rules.values())
    if sort_by == "score":
        items.sort(key=lambda r: r.get("score", 0), reverse=True)
    elif sort_by == "usage":
        items.sort(key=lambda r: r.get("usage_count", 0), reverse=True)
    else:
        items.sort(key=lambda r: r.get("name", ""))

    print("\n" + "=" * 100)
    print(f"{'唯一标识ID':<25} | {'来源':<6} | {'分类':<12} | {'评分':<6} | {'调用':<5} | {'标签':<20} | {'状态':<6}")
    print("=" * 100)

    for r_info in items:
        src = "原创" if r_info["source_type"] == "custom" else "三方"
        cat = r_info["category"]
        score = f"{r_info['score']:.1f}"
        usage = str(r_info.get("usage_count", 0))
        tags_str = ", ".join(r_info.get("tags", [])) or "—"
        if len(tags_str) > 20:
            tags_str = tags_str[:17] + "..."
        status = "已激活" if r_info["status"] == "active" else "已停用"
        print(f"{r_info['name']:<25} | {src:<6} | {cat:<12} | {score:<6} | {usage:<5} | {tags_str:<20} | {status:<6}")
    print("=" * 100 + "\n")


def get_fresh_family_metadata():
    metadata = scan_repository(write=False)
    if metadata is None:
        raise FamilyValidationError(["unable to build a valid family index"])
    return metadata


def run_family_command(action, family_id=None):
    """List, show, or validate source-controlled skill families."""
    try:
        metadata = get_fresh_family_metadata()
    except FamilyValidationError as exc:
        for error in exc.errors:
            cli_error(error)
        return 1

    families = metadata.get("families", {})
    if action == "list":
        if not families:
            cli_warning("当前仓库没有登记技能族。")
            return 0
        for current_id in sorted(families):
            family = families[current_id]
            print(f"{current_id}: {family['title']} ({len(family['members'])} members)")
        return 0

    selected_ids = sorted(families) if family_id in (None, "--all") else [family_id]
    missing = [item for item in selected_ids if item not in families]
    if missing:
        cli_error(f"未知技能族: {', '.join(missing)}")
        return 1

    if action == "show":
        print(json.dumps(families[family_id], ensure_ascii=False, indent=2))
        return 0

    if action == "validate":
        for current_id in selected_ids:
            family = families[current_id]
            cli_success(f"技能族 {current_id} 校验通过: {len(family['members'])} members")
        return 0

    cli_error(f"未知 family 操作: {action}")
    return 1


def run_binding(project_path, manual_tags_str=None, force=False, preferred_ide=None):
    """
    智能分析指定路径的项目技术栈，并生成 .pgrms.json 绑定配置文件
    """
    abs_path = os.path.abspath(project_path)
    if not os.path.exists(abs_path) or not os.path.isdir(abs_path):
        cli_error(f"目标项目路径不存在或不是一个目录: {abs_path}")
        return

    config_file = os.path.join(abs_path, ".pgrms.json")
    if os.path.exists(config_file) and not force:
        cli_info(f"该项目已存在绑定配置: {config_file}")
        cli_info("若需要强制重新自适应绑定，请带上 --force 参数。")
        return

    detected_tags = set()

    if manual_tags_str:
        for tag in manual_tags_str.split(","):
            tag_clean = tag.strip().lower()
            if tag_clean:
                detected_tags.add(tag_clean)
        cli_info(f"正在采用手动指定的技术栈标签: {sorted(detected_tags)}")
    else:
        cli_info(f"启动自适应智能探测器，分析项目路径: {abs_path} ...")

        # 1. 探测前端与设计栈 (package.json)
        pkg_json = os.path.join(abs_path, "package.json")
        if os.path.exists(pkg_json):
            detected_tags.add("general")
            try:
                with open(pkg_json, "r", encoding="utf-8") as f:
                    pkg_data = json.load(f)
                deps = {**pkg_data.get("dependencies", {}), **pkg_data.get("devDependencies", {})}

                tech_keywords = {
                    "react": ["react", "next"],
                    "vue": ["vue", "nuxt"],
                    "typescript": ["typescript", "ts-loader"],
                    "tailwind": ["tailwindcss", "tailwind"],
                    "javascript": ["js", "esbuild"]
                }
                for tag, kws in tech_keywords.items():
                    for kw in kws:
                        if any(kw in dep_name.lower() for dep_name in deps):
                            detected_tags.add(tag)
                            break
            except Exception as e:
                cli_warning(f"读取 package.json 失败，将仅进行文件存在匹配: {str(e)}")
                detected_tags.add("javascript")

        # 2. 探测 Python 与科学计算栈
        req_txt = os.path.join(abs_path, "requirements.txt")
        pipfile = os.path.join(abs_path, "Pipfile")
        pyproj = os.path.join(abs_path, "pyproject.toml")

        has_python_configs = os.path.exists(req_txt) or os.path.exists(pipfile) or os.path.exists(pyproj)

        has_py_files = False
        for root, dirs, files in os.walk(abs_path):
            if root.count(os.sep) - abs_path.count(os.sep) > 2:
                continue
            if any(f.endswith(".py") for f in files):
                has_py_files = True
                break

        if has_python_configs or has_py_files:
            detected_tags.add("python")

            if os.path.exists(req_txt):
                try:
                    with open(req_txt, "r", encoding="utf-8", errors="ignore") as f:
                        req_content = f.read().lower()

                    py_kws = {
                        "django": ["django"],
                        "flask": ["flask"],
                        "fastapi": ["fastapi", "uvicorn"],
                        "numpy": ["numpy"],
                        "pandas": ["pandas"],
                        "matplotlib": ["matplotlib"],
                        "scipy": ["scipy"]
                    }
                    for tag, kws in py_kws.items():
                        if any(kw in req_content for kw in kws):
                            detected_tags.add(tag)
                except Exception:
                    pass

        # 3. 探测 MATLAB 栈
        has_m_files = False
        for root, dirs, files in os.walk(abs_path):
            if root.count(os.sep) - abs_path.count(os.sep) > 2:
                continue
            if any(f.endswith(".m") for f in files):
                has_m_files = True
                break
        if has_m_files:
            detected_tags.add("matlab")

        # 4. 探测 Rust / Go / Java / Docker
        if os.path.exists(os.path.join(abs_path, "Cargo.toml")):
            detected_tags.add("rust")
        if os.path.exists(os.path.join(abs_path, "go.mod")):
            detected_tags.add("go")
        if os.path.exists(os.path.join(abs_path, "pom.xml")) or os.path.exists(os.path.join(abs_path, "build.gradle")):
            detected_tags.add("java")
        if os.path.exists(os.path.join(abs_path, "Dockerfile")) or os.path.exists(os.path.join(abs_path, "docker-compose.yml")):
            detected_tags.add("docker")

        # 5. 探测 Git
        if os.path.exists(os.path.join(abs_path, ".git")):
            detected_tags.add("git")

        # 6. 兜底匹配
        if not detected_tags:
            detected_tags.add("general")
            detected_tags.add("productivity")

    tags_list = sorted(list(detected_tags))

    binding_info = {
        "bound_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "project_path": abs_path.replace("\\", "/"),
        "tags": tags_list,
        "preferred_ide": preferred_ide or "cursor"
    }

    try:
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(binding_info, f, ensure_ascii=False, indent=2)
        cli_success(f"绑定成功！配置已保存至: {config_file}")
        cli_info(f"技术栈标签: {tags_list}")
        cli_info(f"首选 IDE: {binding_info['preferred_ide']}")
    except Exception as e:
        cli_error(f"写入绑定配置文件失败: {str(e)}")


def run_touching(rule_name, metadata_file=METADATA_FILE, dashboard_file=None):
    """
    静默累加指定规则的使用次数，并刷新看板
    """
    if not os.path.exists(metadata_file):
        cli_warning("索引库文件不存在，自动进行扫描重建...")
        if metadata_file != METADATA_FILE:
            cli_error("隔离的索引库不存在。")
            return
        scan_repository()

    try:
        with open(metadata_file, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        cli_error(f"读取索引库失败: {str(e)}")
        return

    rules = data.get("rules", {})
    if rule_name not in rules:
        cli_error(f"在索引库中未找到标识为 '{rule_name}' 的注册规则！")
        return

    rules[rule_name]["usage_count"] = rules[rule_name].get("usage_count", 0) + 1
    rules[rule_name]["last_used_date"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    try:
        safe_write_json(metadata_file, data)
        cli_success(f"已累加规则 '{rule_name}' 使用统计 (当前: {rules[rule_name]['usage_count']} 次)")

        try:
            from dashboard import generate_html_dashboard
            generate_html_dashboard(
                metadata_file=metadata_file,
                output_file=dashboard_file or os.path.join(os.path.dirname(metadata_file), "dashboard.html"),
            )
        except Exception:
            pass
    except Exception as e:
        cli_error(f"更新使用次数元数据失败: {str(e)}")


def get_global_skill_dirs(home_dir=None):
    """
    返回需要同步的全局技能目录。
    - ~/.agent/skills: 兼容现有 Antigravity/Gemini 工作流
    - ~/.agents/skills: VS Code Copilot 自定义技能目录
    """
    base_home = home_dir or os.path.expanduser("~")
    return [
        os.path.join(base_home, ".agent", "skills"),
        os.path.join(base_home, ".agents", "skills")
    ]


def get_codex_skill_dir(home_dir=None):
    """
    返回 Codex 用户级全局技能目录。
    """
    base_home = home_dir or os.path.expanduser("~")
    return os.path.join(base_home, ".codex", "skills")


def make_deploy_log_dir(home_dir=None):
    base_home = home_dir or os.path.expanduser("~")
    log_dir = os.path.join(base_home, GLOBAL_DEPLOY_LOG_DIRNAME)
    os.makedirs(log_dir, exist_ok=True)
    return log_dir


def write_deploy_log(home_dir, lines):
    log_dir = make_deploy_log_dir(home_dir)
    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    log_file = os.path.join(log_dir, f"deploy-{stamp}.log")
    with open(log_file, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines) + "\n")
    return log_file


def backup_path_for(target_path, backup_root):
    normalized = os.path.normcase(os.path.abspath(target_path))
    digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:12]
    basename = os.path.basename(os.path.normpath(target_path)) or "target"
    return os.path.join(backup_root, f"{basename}-{digest}")


def deploy_global_skill_packages(dist_skills, home_dir=None, backup=True, target_dirs=None):
    """
    将编译好的技能包同步到所有受支持的全局目录。
    返回成功写入的目录列表。
    """
    if not os.path.exists(dist_skills):
        return []

    deployed_dirs = []
    log_lines = [f"PGRMS skill deploy: {datetime.datetime.now().isoformat(timespec='seconds')}"]
    seen_dirs = set()
    backup_root = None
    if backup:
        backup_root = os.path.join(make_deploy_log_dir(home_dir), "backups", datetime.datetime.now().strftime("%Y%m%d-%H%M%S"))
        os.makedirs(backup_root, exist_ok=True)

    for target_dir in (target_dirs or get_global_skill_dirs(home_dir)):
        normalized_dir = os.path.normpath(target_dir)
        if normalized_dir in seen_dirs:
            continue
        seen_dirs.add(normalized_dir)

        os.makedirs(target_dir, exist_ok=True)
        for item in os.listdir(dist_skills):
            src = os.path.join(dist_skills, item)
            dst = os.path.join(target_dir, item)
            if os.path.isdir(src):
                if os.path.exists(dst):
                    if backup_root:
                        shutil.copytree(dst, backup_path_for(dst, backup_root), dirs_exist_ok=True)
                    shutil.rmtree(dst)
                shutil.copytree(src, dst)
            else:
                if os.path.exists(dst) and backup_root:
                    os.makedirs(os.path.dirname(backup_path_for(dst, backup_root)), exist_ok=True)
                    shutil.copy2(dst, backup_path_for(dst, backup_root))
                shutil.copy2(src, dst)
            log_lines.append(f"{src} -> {dst}")
        deployed_dirs.append(target_dir)

    if deployed_dirs:
        log_file = write_deploy_log(home_dir, log_lines)
        cli_info(f"Deployment log: {log_file}")
    return deployed_dirs


def hash_file_tree(root_dir):
    """Return deterministic SHA-256 hashes keyed by relative file path."""
    hashes = {}
    if not os.path.isdir(root_dir):
        return hashes
    for current_root, dirs, files in os.walk(root_dir):
        dirs.sort()
        for filename in sorted(files):
            path = os.path.join(current_root, filename)
            rel = os.path.relpath(path, root_dir).replace("\\", "/")
            digest = hashlib.sha256()
            with open(path, "rb") as handle:
                for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                    digest.update(chunk)
            hashes[rel] = digest.hexdigest()
    return hashes


def build_skill_sync_manifest(staging_dir, rules, family_ids):
    targets = {}
    for target_name in ("antigravity", "codex"):
        skills_root = os.path.join(staging_dir, target_name, "skills")
        targets[target_name] = {}
        if os.path.isdir(skills_root):
            for skill in sorted(os.listdir(skills_root)):
                skill_dir = os.path.join(skills_root, skill)
                if os.path.isdir(skill_dir):
                    targets[target_name][skill] = hash_file_tree(skill_dir)
    return {
        "schema_version": 1,
        "families": list(family_ids or []),
        "skills": [rule["name"] for rule in rules],
        "targets": targets,
    }


def verify_deployed_skill_packages(staging_skills, target_dirs):
    for skill in sorted(os.listdir(staging_skills)):
        source_skill = os.path.join(staging_skills, skill)
        if not os.path.isdir(source_skill):
            continue
        source_hashes = hash_file_tree(source_skill)
        for target_dir in target_dirs:
            target_skill = os.path.join(target_dir, skill)
            target_hashes = hash_file_tree(target_skill)
            if source_hashes != target_hashes:
                raise RuntimeError(f"skill verification failed: {source_skill} != {target_skill}")


def write_sync_manifest(home_dir, manifest):
    log_dir = make_deploy_log_dir(home_dir)
    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    manifest_path = os.path.join(log_dir, f"sync-skills-{stamp}.json")
    safe_write_json(manifest_path, manifest)
    return manifest_path


def run_sync_skills(family_ids=None, apply=False, home_dir=None):
    """Build fresh skill packages and optionally overlay only those packages globally."""
    family_ids = list(family_ids or [])
    metadata = scan_repository(write=False)
    if metadata is None:
        return None

    try:
        if family_ids:
            rules = resolve_family_rules(metadata, family_ids)
        else:
            rules = [
                rule for rule in metadata.get("rules", {}).values()
                if rule.get("status") == "active" and rule.get("score", 10.0) >= 5.0
            ]
    except FamilyValidationError as exc:
        for error in exc.errors:
            cli_error(error)
        return None

    if not rules:
        cli_warning("没有可同步的技能。")
        return None

    from compiler import (
        compile_for_antigravity,
        compile_for_codex,
        ensure_family_target_compatibility,
    )

    if family_ids:
        try:
            ensure_family_target_compatibility(rules, "codex")
        except FamilyValidationError as exc:
            for error in exc.errors:
                cli_error(error)
            return None

    with tempfile.TemporaryDirectory(prefix="pgrms-sync-") as staging_dir:
        compile_for_antigravity(rules, dist_root=staging_dir)
        compile_for_codex(rules, dist_root=staging_dir)
        manifest = build_skill_sync_manifest(staging_dir, rules, family_ids)

        antigravity_skills = os.path.join(staging_dir, "antigravity", "skills")
        codex_skills = os.path.join(staging_dir, "codex", "skills")
        antigravity_targets = get_global_skill_dirs(home_dir)
        codex_targets = [get_codex_skill_dir(home_dir)]

        if not apply:
            cli_warning("Dry-run only. Add --apply to synchronize skill packages.")
            print(f"  Families: {', '.join(family_ids) if family_ids else 'all'}")
            print(f"  Skills: {', '.join(manifest['skills'])}")
            for path in antigravity_targets + codex_targets:
                print(f"  Target: {path}")
            return manifest

        deployed_antigravity = deploy_global_skill_packages(
            antigravity_skills,
            home_dir=home_dir,
            target_dirs=antigravity_targets,
        )
        deployed_codex = deploy_global_skill_packages(
            codex_skills,
            home_dir=home_dir,
            target_dirs=codex_targets,
        )
        verify_deployed_skill_packages(antigravity_skills, deployed_antigravity)
        verify_deployed_skill_packages(codex_skills, deployed_codex)
        manifest["applied_targets"] = deployed_antigravity + deployed_codex
        manifest_path = write_sync_manifest(home_dir, manifest)
        manifest["manifest_path"] = manifest_path
        cli_success(f"技能同步和 SHA-256 验证完成: {manifest_path}")
        return manifest


def get_vscode_user_prompts_dir(home_dir=None):
    """
    返回 VS Code 用户级 prompts 目录。
    优先读取环境变量覆盖，便于测试和跨环境部署。
    """
    env_prompts_dir = os.environ.get("VSCODE_USER_PROMPTS_FOLDER")
    if env_prompts_dir:
        return os.path.abspath(os.path.expanduser(env_prompts_dir))

    base_home = home_dir or os.path.expanduser("~")
    if sys.platform.startswith("win"):
        if home_dir:
            return os.path.join(base_home, "AppData", "Roaming", "Code", "User", "prompts")
        appdata_dir = os.environ.get("APPDATA")
        if appdata_dir:
            return os.path.join(appdata_dir, "Code", "User", "prompts")
        return os.path.join(base_home, "AppData", "Roaming", "Code", "User", "prompts")

    if sys.platform == "darwin":
        return os.path.join(base_home, "Library", "Application Support", "Code", "User", "prompts")

    config_home = os.environ.get("XDG_CONFIG_HOME", os.path.join(base_home, ".config"))
    return os.path.join(config_home, "Code", "User", "prompts")


def build_vscode_global_instruction_content(rule_file_path):
    """
    将 RULE.md 转换为 VS Code Copilot 可读取的 user-level .instructions.md 内容。
    """
    rule_meta = parse_rule_metadata(rule_file_path, "custom", "productivity", rule_file_path)
    if not rule_meta:
        return None

    content, _ = read_file_safely(rule_file_path)
    parts = content.split("---", 2)
    if len(parts) < 3:
        return None

    body = parts[2].lstrip()
    description = rule_meta.get("description", "PGRMS 全局 Copilot 约束")

    return (
        "---\n"
        "applyTo: '**'\n"
        f"description: {json.dumps(description, ensure_ascii=False)}\n"
        "---\n\n"
        f"{body}"
    )


def deploy_vscode_global_instructions(prompts_dir=None, rule_file_path=None, home_dir=None):
    """
    同步 VS Code Copilot 用户级全局 instructions。
    """
    source_rule = rule_file_path or os.path.join(
        SOURCE_DIR, "custom", "productivity", "chinese-output-constraint", "RULE.md"
    )
    if not os.path.exists(source_rule):
        return None

    instruction_content = build_vscode_global_instruction_content(source_rule)
    if not instruction_content:
        return None

    target_dir = prompts_dir or get_vscode_user_prompts_dir(home_dir)
    os.makedirs(target_dir, exist_ok=True)

    target_file = os.path.join(target_dir, "pgrms-global.instructions.md")
    with open(target_file, "w", encoding="utf-8", newline="\n") as f:
        f.write(instruction_content)

    return target_file


def run_sync_vscode(home_dir=None):
    """
    将全局中文输出约束同步为 VS Code Copilot 用户级 instructions。
    """
    target_file = deploy_vscode_global_instructions(home_dir=home_dir)
    if target_file:
        cli_success(f"VS Code Copilot 全局指令已同步至: {target_file}")
    else:
        cli_warning("未找到可同步的 VS Code Copilot 全局指令源文件，已跳过。")
    return target_file


def build_deploy_plan(home_dir=None):
    home = home_dir or os.path.expanduser("~")
    return [
        ("skills", os.path.join(home, ".agent", "skills")),
        ("skills", os.path.join(home, ".agents", "skills")),
        ("codex", os.path.join(home, ".codex", "skills")),
        ("gitignore", os.path.join(home, ".gitignore_global")),
        ("gemini", os.path.join(home, ".gemini", "GEMINI.md")),
        ("vscode", get_vscode_user_prompts_dir(home)),
    ]


def print_deploy_plan(home_dir=None):
    cli_warning("Dry-run only. Add --apply to write user-global files.")
    for label, path in build_deploy_plan(home_dir):
        exists = "exists" if os.path.exists(path) else "missing"
        print(f"  [{label}] {path} ({exists})")


def configure_global_gitignore(gitignore_path):
    subprocess.run(
        ["git", "config", "--global", "core.excludesfile", gitignore_path],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )


def run_deploy(project_path=None, target="all", apply=False, home_dir=None):
    """
    一键全自动部署：scan → compile → 文件部署。跨平台纯 Python 实现。
    """
    t0 = time.time()
    cli_info("启动 PGRMS 一键全自动部署流水线...")

    # 步骤 1：扫描重建索引
    print("\n\033[94m[步骤 1/3] 扫描规则源仓库...\033[0m")
    scan_repository()

    # 步骤 2：编译分发
    print("\n\033[94m[步骤 2/3] 编译规则至目标格式...\033[0m")
    try:
        from compiler import run_compilation
        run_compilation(target, project_path)
    except ImportError:
        cli_error("无法导入编译器模块 (compiler.py)")
        return

    # 步骤 3：全局配置文件部署（仅在不指定项目路径时执行）
    if not project_path:
        print("\n\033[94m[步骤 3/3] 全局部署计划...\033[0m")
        if not apply:
            print_deploy_plan(home_dir)
            elapsed = time.time() - t0
            cli_summary(f"Dry-run complete | No user-global files changed | 耗时 {elapsed:.2f}s")
            return

        explicit_home = home_dir is not None
        home_dir = home_dir or os.path.expanduser("~")
        log_lines = [f"PGRMS global deploy: {datetime.datetime.now().isoformat(timespec='seconds')}"]
        cli_warning(f"Applying global deployment under home: {home_dir}")

        # 部署 .gitignore_global
        gitignore_src = os.path.join(ROOT_DIR, ".gitignore_global")
        if os.path.exists(gitignore_src):
            gitignore_dst = os.path.join(home_dir, ".gitignore_global")
            os.makedirs(os.path.dirname(gitignore_dst), exist_ok=True)
            shutil.copy2(gitignore_src, gitignore_dst)
            if explicit_home:
                cli_warning("Skipping git config --global because --home was provided.")
            else:
                configure_global_gitignore(gitignore_dst)
                cli_success("Git 全局忽略规则已激活。")
            log_lines.append(f"{gitignore_src} -> {gitignore_dst}")

        # 部署 GEMINI.md
        gemini_src = os.path.join(ROOT_DIR, "GEMINI.md")
        if os.path.exists(gemini_src):
            gemini_dir = os.path.join(home_dir, ".gemini")
            os.makedirs(gemini_dir, exist_ok=True)
            gemini_dst = os.path.join(gemini_dir, "GEMINI.md")
            shutil.copy2(gemini_src, gemini_dst)
            cli_success("全局 AI 约束文件 (GEMINI.md) 已部署。")
            log_lines.append(f"{gemini_src} -> {gemini_dst}")

        vscode_file = run_sync_vscode(home_dir)
        if vscode_file:
            log_lines.append(f"VS Code instructions -> {vscode_file}")

        # 部署 Antigravity/Gemini 与 VS Code Copilot 全局技能包
        antigravity_dist_skills = os.path.join(DIST_DIR, "antigravity", "skills")
        deployed_dirs = deploy_global_skill_packages(
            antigravity_dist_skills,
            home_dir,
            target_dirs=get_global_skill_dirs(home_dir),
        )
        if deployed_dirs:
            cli_success("全局技能包已同步至 ~/.agent/skills/ 与 ~/.agents/skills/。")
            log_lines.extend([f"skills -> {d}" for d in deployed_dirs])

        # 部署 Codex 全局技能包
        codex_dist_skills = os.path.join(DIST_DIR, "codex", "skills")
        codex_target_dir = get_codex_skill_dir(home_dir)
        deployed_codex_dirs = deploy_global_skill_packages(
            codex_dist_skills,
            home_dir,
            target_dirs=[codex_target_dir],
        )
        if deployed_codex_dirs:
            cli_success("Codex 全局技能包已同步至 ~/.codex/skills/。")
            log_lines.extend([f"codex-skills -> {d}" for d in deployed_codex_dirs])
        log_file = write_deploy_log(home_dir, log_lines)
        cli_info(f"Global deployment log: {log_file}")
    else:
        print("\n\033[94m[步骤 3/3] 跳过全局部署（已直推至项目目录）\033[0m")

    elapsed = time.time() - t0
    cli_summary(f"一键部署完成 | 耗时 {elapsed:.2f}s")


def main():
    parser = argparse.ArgumentParser(
        description="PGRMS (个人全局规则管理系统) 核心控制 CLI 工具",
        formatter_class=argparse.RawTextHelpFormatter
    )

    subparsers = parser.add_subparsers(dest="command", help="支持的操作命令")

    # 1. scan 命令
    subparsers.add_parser("scan", help="扫描 source/ 目录重建 metadata.json 索引库")

    # 2. list 命令
    list_parser = subparsers.add_parser("list", help="列出当前所有的规则状态及健康评分")
    list_parser.add_argument("--sort", choices=["name", "score", "usage"], default="name", help="排序方式 (默认: name)")

    # 3. compile 命令
    compile_parser = subparsers.add_parser("compile", help="编译通用规则至指定 IDE 格式分发")
    compile_parser.add_argument(
        "--target",
        choices=["all", "cursor", "windsurf", "cline", "antigravity", "codex"],
        default="all",
        help="目标 IDE 编译器类型 (默认: all)"
    )
    compile_parser.add_argument("--path", help="绑定的项目路径，用于自适应过滤并直推分发规则")
    compile_parser.add_argument(
        "--family",
        action="append",
        dest="families",
        help="显式编译指定技能族；可重复使用，且不会按项目 tags 拆分技能族",
    )

    # 4. family 命令
    family_parser = subparsers.add_parser("family", help="查看和校验技能族清单")
    family_subparsers = family_parser.add_subparsers(dest="family_action")
    family_subparsers.add_parser("list", help="列出技能族")
    family_show_parser = family_subparsers.add_parser("show", help="显示技能族详情")
    family_show_parser.add_argument("family_id", help="技能族 ID")
    family_validate_parser = family_subparsers.add_parser("validate", help="校验技能族")
    family_validate_parser.add_argument("family_id", nargs="?", help="技能族 ID")
    family_validate_parser.add_argument("--all", action="store_true", dest="validate_all", help="校验全部技能族")

    # 5. fetch 命令
    fetch_parser = subparsers.add_parser("fetch", help="自动从第三方 GitHub 仓库拉取并标准化规则")
    fetch_parser.add_argument("--url", required=True, help="第三方的规则文件或 GitHub 仓库地址")
    fetch_parser.add_argument(
        "--category",
        default="engineering",
        help="导入规则的目标功能分类 (默认: engineering)"
    )
    fetch_parser.add_argument("--name", help="显式指定导入后的规则 ID（留空将从地址自动解析）")

    # 6. evaluate 命令
    subparsers.add_parser("evaluate", help="评估所有规则的健康度，结合使用统计和网络检索更新打分")

    # 7. prune 命令
    prune_parser = subparsers.add_parser("prune", help="自动清理或推荐替换评分低于 5.0 的亚健康规则")
    prune_parser.add_argument("--yes", "-y", action="store_true", help="跳过交互式确认，自动归档所有亚健康规则")
    prune_parser.add_argument("--dry-run", action="store_true", help="仅预览待清理的规则，不执行任何操作")

    # 8. bind 命令
    bind_parser = subparsers.add_parser("bind", help="自适应检测当前项目技术栈并进行规则绑定配置")
    bind_parser.add_argument("--path", default=".", help="需要绑定的项目路径 (默认: 当前路径)")
    bind_parser.add_argument("--tags", help="手动强制指定的技术标签 (以逗号分隔，留空则启动自动探测)")
    bind_parser.add_argument("--force", action="store_true", help="强制重新绑定覆盖原有配置")
    bind_parser.add_argument("--ide", choices=["cursor", "windsurf", "cline", "antigravity", "codex"], default="cursor",
                             help="首选 IDE 类型，直推分发时仅输出该格式 (默认: cursor)")

    # 9. touch 命令
    touch_parser = subparsers.add_parser("touch", help="静默增加指定规则的本地调用使用次数 (使用统计遥测)")
    touch_parser.add_argument("--rule", required=True, help="调用的规则标识 ID")

    # 10. deploy 命令 (一键全自动)
    deploy_parser = subparsers.add_parser("deploy", help="一键全自动: scan + compile + 部署全局配置（跨平台）")
    deploy_parser.add_argument("--path", help="指定项目路径，执行定向增量编译并直推分发")
    deploy_parser.add_argument("--target", choices=["all", "cursor", "windsurf", "cline", "antigravity", "codex"],
                               default="all", help="目标 IDE (默认: all)")
    deploy_parser.add_argument("--apply", action="store_true", help="执行真实全局写入；默认只做 dry-run")
    deploy_parser.add_argument("--home", help="覆盖全局部署使用的 HOME 目录，主要用于测试")

    # 11. sync-skills 命令
    sync_skills_parser = subparsers.add_parser("sync-skills", help="仅同步技能包，不修改其他全局配置")
    sync_skills_parser.add_argument("--family", action="append", dest="families", help="仅同步指定技能族；可重复使用")
    sync_skills_parser.add_argument("--apply", action="store_true", help="执行真实全局写入；默认 dry-run")
    sync_skills_parser.add_argument("--home", help="覆盖同步使用的 HOME 目录，主要用于测试")

    # 12. sync-vscode 命令
    subparsers.add_parser("sync-vscode", help="同步 VS Code Copilot 用户级全局 instructions")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    if args.command == "scan":
        scan_repository()
    elif args.command == "list":
        list_rules(sort_by=args.sort)
    elif args.command == "compile":
        try:
            from compiler import run_compilation
            run_compilation(args.target, args.path, family_ids=args.families)
        except ImportError:
            cli_error("无法导入编译器模块 (compiler.py)，请确认脚本是否存在。")
    elif args.command == "family":
        if not args.family_action:
            family_parser.print_help()
        elif args.family_action == "list":
            sys.exit(run_family_command("list"))
        elif args.family_action == "show":
            sys.exit(run_family_command("show", args.family_id))
        elif args.family_action == "validate":
            if not args.validate_all and not args.family_id:
                family_validate_parser.error("provide a family_id or --all")
            sys.exit(run_family_command("validate", "--all" if args.validate_all else args.family_id))
    elif args.command == "fetch":
        try:
            from fetcher import run_fetching
            run_fetching(args.url, args.category, args.name)
        except ImportError:
            cli_error("无法导入拉取器模块 (fetcher.py)，请确认脚本是否存在。")
    elif args.command == "evaluate":
        try:
            from evaluator import run_evaluation
            run_evaluation()
        except ImportError:
            cli_error("无法导入评估器模块 (evaluator.py)，请确认脚本是否存在。")
    elif args.command == "prune":
        try:
            from evaluator import run_pruning
            run_pruning(auto_yes=args.yes, dry_run=args.dry_run)
        except ImportError:
            cli_error("无法导入评估器模块进行清理，请确认脚本是否存在。")
    elif args.command == "bind":
        run_binding(args.path, args.tags, args.force, args.ide)
    elif args.command == "touch":
        run_touching(args.rule)
    elif args.command == "deploy":
        run_deploy(project_path=args.path, target=args.target, apply=args.apply, home_dir=args.home)
    elif args.command == "sync-skills":
        result = run_sync_skills(family_ids=args.families, apply=args.apply, home_dir=args.home)
        if result is None:
            sys.exit(1)
    elif args.command == "sync-vscode":
        run_sync_vscode()

if __name__ == "__main__":
    ensure_utf8_console()
    main()
