#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PGRMS (个人全局规则管理系统) - 多目标规则编译器
"""

import os
import json
import shutil
import time

from utils import (
    ROOT_DIR, METADATA_FILE, DIST_DIR,
    read_file_safely, safe_write_json,
    cli_success, cli_warning, cli_error, cli_info, cli_summary
)

EXCLUDED_PACKAGE_NAMES = {
    ".git",
    ".agent",
    ".agents",
    "__pycache__",
    ".pytest_cache",
    "temp_git_fetch",
    "dist",
}

CODEX_ALLOWED_AUDIENCES = {"codex-core", "codex-project"}


def load_active_rules(project_tags=None):
    """
    加载所有处于激活状态且健康评分 >= 5.0 的规则。
    自适应过滤逻辑：
    - 若规则 tags 为空或含 "general" → 始终放行（通用规则）
    - 否则，必须其 tags 与 project_tags 存在交集才允许加载
    注意：此逻辑对原创和第三方规则一视同仁，真正实现按需精准注入。
    """
    if not os.path.exists(METADATA_FILE):
        cli_warning("规则索引库不存在，正在尝试自动生成...")
        from pgrms import scan_repository
        scan_repository()

    try:
        with open(METADATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        cli_error(f"读取规则索引库失败: {str(e)}")
        return []

    rules = data.get("rules", {})
    active_rules = []
    filtered_count = 0

    p_tags = set(t.lower() for t in project_tags) if project_tags else set()

    for r_id, r_info in rules.items():
        if r_info.get("status") == "active" and r_info.get("score", 10.0) >= 5.0:
            if not project_tags:
                # 无项目标签 → 全量加载
                active_rules.append(r_info)
            else:
                r_tags = set(t.lower() for t in r_info.get("tags", []))

                # 通用规则始终放行：tags 为空 或 含 "general"
                if "general" in r_tags:
                    active_rules.append(r_info)
                elif r_tags & p_tags:
                    active_rules.append(r_info)
                else:
                    filtered_count += 1

    if project_tags:
        cli_info(f"自适应过滤: 加载 {len(active_rules)} 条 | 过滤 {filtered_count} 条无关规则")
    else:
        cli_info(f"全量加载: 共 {len(active_rules)}/{len(rules)} 条有效规则")
    return active_rules


def get_rule_body_content(rule_path):
    """
    读取 RULE.md 的内容，剔除顶部的 YAML Frontmatter，仅保留 Markdown 正文。
    如果同级目录下存在 override.md，则采用追加图层策略，并在尾部追加个人专属修正。
    """
    absolute_rule_dir = os.path.join(ROOT_DIR, rule_path)
    absolute_rule_path = os.path.join(absolute_rule_dir, "RULE.md")

    if not os.path.exists(absolute_rule_path):
        return ""

    try:
        content, _ = read_file_safely(absolute_rule_path)
        content = content.lstrip("\ufeff")

        body = ""
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                body = parts[2].strip()
            else:
                body = content.strip()
        else:
            body = content.strip()

        # 检测并合并个人专属覆盖图层 override.md
        override_file_path = os.path.join(absolute_rule_dir, "override.md")
        if os.path.exists(override_file_path):
            override_content, _ = read_file_safely(override_file_path)
            override_content = override_content.strip()
            if override_content:
                body += f"\n\n## 🛠️ 个人专属修正 (User Personal Override)\n\n{override_content}"

        return body
    except Exception as e:
        cli_warning(f"读取规则正文或专属修正失败 [{rule_path}]: {str(e)}")
        return ""


def compile_to_single_file(rules, filename):
    """
    将多个规则合并输出为一个单一的规则配置文件（适用于 Cursor, Windsurf, Cline）
    """
    compiled_content = []
    compiled_content.append("#" * 80)
    compiled_content.append(f"# 个人全局规则统一配置库 (由 PGRMS 编译器自动生成)")
    compiled_content.append(f"# 包含已激活有效规则数: {len(rules)} 条")
    compiled_content.append("#" * 80 + "\n")

    for rule in rules:
        body = get_rule_body_content(rule["path"])
        if not body:
            continue

        compiled_content.append("=" * 80)
        compiled_content.append(f"## 📌 规则标识: [{rule['name']}] | 标题: {rule['title']}")
        compiled_content.append(f"## 功能描述: {rule['description']}")
        compiled_content.append("=" * 80 + "\n")
        compiled_content.append(body)
        compiled_content.append("\n\n")

    return "\n".join(compiled_content)


def compile_for_cursor(rules, output_dir=None):
    target_dir = output_dir if output_dir else os.path.join(DIST_DIR, "cursor")
    os.makedirs(target_dir, exist_ok=True)
    target_file = os.path.join(target_dir, ".cursorrules")
    content = compile_to_single_file(rules, ".cursorrules")
    with open(target_file, "w", encoding="utf-8") as f:
        f.write(content)
    cli_success(f"Cursor 规则文件: {target_file}")


def compile_for_windsurf(rules, output_dir=None):
    target_dir = output_dir if output_dir else os.path.join(DIST_DIR, "windsurf")
    os.makedirs(target_dir, exist_ok=True)
    target_file = os.path.join(target_dir, ".windsurfrules")
    content = compile_to_single_file(rules, ".windsurfrules")
    with open(target_file, "w", encoding="utf-8") as f:
        f.write(content)
    cli_success(f"Windsurf 规则文件: {target_file}")


def compile_for_cline(rules, output_dir=None):
    target_dir = output_dir if output_dir else os.path.join(DIST_DIR, "cline")
    os.makedirs(target_dir, exist_ok=True)
    clinerules_file = os.path.join(target_dir, ".clinerules")
    rooclinerules_file = os.path.join(target_dir, ".roo-clinerules")
    content = compile_to_single_file(rules, ".clinerules")
    with open(clinerules_file, "w", encoding="utf-8") as f:
        f.write(content)
    with open(rooclinerules_file, "w", encoding="utf-8") as f:
        f.write(content)
    cli_success(f"Cline 规则文件: {clinerules_file}")
    cli_success(f"Roo-Cline 规则文件: {rooclinerules_file}")


def compile_for_antigravity(rules, output_dir=None):
    """
    编译并生成 Antigravity/Gemini 全局技能包。
    """
    if output_dir:
        antigravity_dist = os.path.join(output_dir, ".gemini", "antigravity", "skills")
    else:
        antigravity_dist = os.path.join(DIST_DIR, "antigravity", "skills")

    if os.path.exists(antigravity_dist):
        try:
            shutil.rmtree(antigravity_dist)
        except Exception as e:
            cli_warning(f"清空旧的 antigravity 编译文件夹失败: {str(e)}")

    os.makedirs(antigravity_dist, exist_ok=True)

    success_count = 0
    for rule in rules:
        src_dir = os.path.join(ROOT_DIR, rule["path"])
        src_rule_file = os.path.join(src_dir, "RULE.md")

        if not os.path.exists(src_rule_file):
            continue

        dst_rule_dir = os.path.join(antigravity_dist, rule["name"])
        os.makedirs(dst_rule_dir, exist_ok=True)

        dst_skill_file = os.path.join(dst_rule_dir, "SKILL.md")
        try:
            shutil.copy2(src_rule_file, dst_skill_file)

            for item in os.listdir(src_dir):
                if item in ("RULE.md", "override.md") or item in EXCLUDED_PACKAGE_NAMES:
                    continue
                item_src = os.path.join(src_dir, item)
                item_dst = os.path.join(dst_rule_dir, item)
                if os.path.isdir(item_src):
                    shutil.copytree(item_src, item_dst, ignore=package_ignore)
                else:
                    shutil.copy2(item_src, item_dst)
            success_count += 1
        except Exception as e:
            cli_warning(f"编译 Antigravity 技能 {rule['name']} 失败: {str(e)}")

    cli_success(f"Antigravity 技能包: {success_count} 个 → {antigravity_dist}")


def package_ignore(dir_path, names):
    ignored = set()
    for name in names:
        if name in EXCLUDED_PACKAGE_NAMES or name.endswith(".pyc"):
            ignored.add(name)
    return ignored


def filter_rules_for_codex(rules):
    codex_rules = []
    skipped_count = 0
    for rule in rules:
        audience = (rule.get("audience") or "archive").strip().lower()
        if audience in CODEX_ALLOWED_AUDIENCES:
            codex_rules.append(rule)
        else:
            skipped_count += 1
    cli_info(f"Codex audience filter: include {len(codex_rules)} | skip {skipped_count}")
    return codex_rules


def compile_for_codex(rules, output_dir=None):
    """
    Build a local Codex skill bundle without touching user-global directories.
    """
    rules = filter_rules_for_codex(rules)
    if output_dir:
        codex_dist = os.path.join(output_dir, ".codex", "skills")
    else:
        codex_dist = os.path.join(DIST_DIR, "codex", "skills")
    if os.path.exists(codex_dist):
        shutil.rmtree(codex_dist)
    os.makedirs(codex_dist, exist_ok=True)

    success_count = 0
    for rule in rules:
        src_dir = os.path.join(ROOT_DIR, rule["path"])
        src_rule_file = os.path.join(src_dir, "RULE.md")
        if not os.path.exists(src_rule_file):
            continue

        dst_rule_dir = os.path.join(codex_dist, rule["name"])
        os.makedirs(dst_rule_dir, exist_ok=True)
        shutil.copy2(src_rule_file, os.path.join(dst_rule_dir, "SKILL.md"))

        for item in os.listdir(src_dir):
            if item in ("RULE.md", "override.md") or item in EXCLUDED_PACKAGE_NAMES:
                continue
            item_src = os.path.join(src_dir, item)
            item_dst = os.path.join(dst_rule_dir, item)
            if os.path.isdir(item_src):
                shutil.copytree(item_src, item_dst, ignore=package_ignore)
            else:
                shutil.copy2(item_src, item_dst)
        success_count += 1

    cli_success(f"Codex local skills: {success_count} -> {codex_dist}")


# 编译器映射表，用于 IDE 偏好控制
COMPILER_MAP = {
    "cursor": compile_for_cursor,
    "windsurf": compile_for_windsurf,
    "cline": compile_for_cline,
    "antigravity": compile_for_antigravity,
    "codex": compile_for_codex,
}


def run_compilation(target="all", project_path=None):
    """
    执行规则的编译分发工作。
    支持 project_path 参数：
    1. 读取 .pgrms.json 提取 project_tags 自适应过滤
    2. 读取 preferred_ide 决定仅输出哪种格式（除非 target 显式覆盖）
    3. 将编译输出直推到项目根目录
    """
    t0 = time.time()
    cli_info(f"启动规则编译引擎，目标: [{target}]")

    project_tags = None
    output_dir = None
    preferred_ide = None

    if project_path:
        abs_project_path = os.path.abspath(project_path)
        config_file = os.path.join(abs_project_path, ".pgrms.json")
        if os.path.exists(config_file):
            try:
                with open(config_file, "r", encoding="utf-8") as f:
                    config_data = json.load(f)
                project_tags = config_data.get("tags", [])
                preferred_ide = config_data.get("preferred_ide", None)
                output_dir = abs_project_path
                cli_info(f"项目路径: {abs_project_path}")
                cli_info(f"关联标签: {project_tags}")
                if preferred_ide:
                    cli_info(f"首选 IDE: {preferred_ide}")
            except Exception as e:
                cli_warning(f"读取项目绑定配置失败: {str(e)}，将采用全量编译。")
        else:
            cli_info(f"项目路径 '{abs_project_path}' 未包含 .pgrms.json，将输出至默认 dist 目录。")

    rules = load_active_rules(project_tags=project_tags)
    if not rules:
        cli_warning("没有可供编译的有效激活规则！编译终止。")
        return

    if not output_dir:
        os.makedirs(DIST_DIR, exist_ok=True)

    # 确定实际编译目标
    if target == "all" and output_dir and preferred_ide and preferred_ide in COMPILER_MAP:
        # 直推模式 + 有首选 IDE → 仅输出首选格式，避免目录污染
        actual_targets = [preferred_ide]
        cli_info(f"直推模式: 仅输出首选 IDE ({preferred_ide}) 格式")
    elif target == "all":
        actual_targets = list(COMPILER_MAP.keys())
    else:
        actual_targets = [target]

    for t in actual_targets:
        if t in COMPILER_MAP:
            COMPILER_MAP[t](rules, output_dir)

    elapsed = time.time() - t0
    target_desc = output_dir or "dist/"
    cli_summary(f"编译完成 | {len(rules)} 条规则 | {len(actual_targets)} 个目标 | 输出: {target_desc} | 耗时 {elapsed:.2f}s")


if __name__ == "__main__":
    import sys
    target = sys.argv[1] if len(sys.argv) > 1 else "all"
    project_path = sys.argv[2] if len(sys.argv) > 2 else None
    run_compilation(target, project_path)
