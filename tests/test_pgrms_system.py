#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PGRMS 个人全局规则管理系统 - 自动化集成测试脚本 (第二轮迭代版)
"""

import os
import sys
import json
import shutil
import unittest

SCRIPTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts")
sys.path.insert(0, SCRIPTS_DIR)

from pgrms import (
    run_binding, run_touching, scan_repository,
    deploy_global_skill_packages, deploy_vscode_global_instructions,
    run_deploy
)
from compiler import run_compilation, get_rule_body_content
from utils import METADATA_FILE, safe_write_json, read_file_safely


class TestPGRMSSystem(unittest.TestCase):

    def setUp(self):
        self.root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.temp_project_dir = os.path.join(self.root_dir, "temp_test_project")
        self.metadata_file = METADATA_FILE

        if os.path.exists(self.temp_project_dir):
            shutil.rmtree(self.temp_project_dir)
        os.makedirs(self.temp_project_dir, exist_ok=True)

        self.metadata_backup = None
        if os.path.exists(self.metadata_file):
            with open(self.metadata_file, "r", encoding="utf-8") as f:
                self.metadata_backup = f.read()

    def tearDown(self):
        if os.path.exists(self.temp_project_dir):
            shutil.rmtree(self.temp_project_dir)

        if self.metadata_backup:
            with open(self.metadata_file, "w", encoding="utf-8") as f:
                f.write(self.metadata_backup)

        override_file = os.path.join(self.root_dir, "source", "registry", "cr20085361", "antigravity-", "override.md")
        if os.path.exists(override_file):
            try:
                os.remove(override_file)
            except Exception:
                pass

    def test_1_smart_binding_with_ide_preference(self):
        """测试自适应绑定与 IDE 偏好"""
        print("\n=== 测试 1：自适应智能绑定 + IDE 偏好 ===")
        pkg_data = {
            "name": "mock-frontend",
            "dependencies": {"react": "^18.2.0", "tailwindcss": "^3.0.0"}
        }
        with open(os.path.join(self.temp_project_dir, "package.json"), "w", encoding="utf-8") as f:
            json.dump(pkg_data, f, indent=2)
        os.makedirs(os.path.join(self.temp_project_dir, ".git"), exist_ok=True)

        run_binding(self.temp_project_dir, force=True, preferred_ide="windsurf")

        config_path = os.path.join(self.temp_project_dir, ".pgrms.json")
        self.assertTrue(os.path.exists(config_path))

        with open(config_path, "r", encoding="utf-8") as f:
            config_data = json.load(f)

        tags = config_data.get("tags", [])
        self.assertIn("react", tags)
        self.assertIn("tailwind", tags)
        self.assertIn("git", tags)
        self.assertEqual(config_data.get("preferred_ide"), "windsurf")
        print(f"标签: {tags}, 首选IDE: {config_data['preferred_ide']}")
        print("=== 测试 1 通过 ===")

    def test_2_override_merge(self):
        """测试双层 override.md 追加合并功能"""
        print("\n=== 测试 2：Override.md 追加合并 ===")
        rule_dir = os.path.join(self.root_dir, "source", "registry", "cr20085361", "antigravity-")
        self.assertTrue(os.path.exists(rule_dir))

        override_file = os.path.join(rule_dir, "override.md")
        with open(override_file, "w", encoding="utf-8") as f:
            f.write("### 测试特调指令\n个人特调参数 X = True。")

        body = get_rule_body_content("source/registry/cr20085361/antigravity-")

        self.assertIn("个人专属修正 (User Personal Override)", body)
        self.assertIn("测试特调指令", body)
        print("=== 测试 2 通过 ===")

    def test_3_adaptive_filtering_now_filters_custom_rules(self):
        """测试修正后的过滤逻辑：有明确 tags 的原创规则也会被过滤"""
        print("\n=== 测试 3：原创规则也参与标签过滤 ===")
        binding_info = {
            "bound_at": "2026-05-20 13:00:00",
            "project_path": self.temp_project_dir.replace("\\", "/"),
            "tags": ["matlab"],
            "preferred_ide": "cursor"
        }
        config_path = os.path.join(self.temp_project_dir, ".pgrms.json")
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(binding_info, f, indent=2)

        run_compilation(target="cursor", project_path=self.temp_project_dir)

        cursorrules_path = os.path.join(self.temp_project_dir, ".cursorrules")
        self.assertTrue(os.path.exists(cursorrules_path))

        with open(cursorrules_path, "r", encoding="utf-8") as f:
            content = f.read()

        # matlab 原创规则应包含
        self.assertIn("matlab", content.lower())
        # general 标签的规则（如 chinese-output-constraint）应包含
        self.assertIn("chinese-output-constraint", content)
        # frontend-design 的 tags 是 ["react","vue","css","javascript","tailwind"]，与 ["matlab"] 无交集，应被过滤
        self.assertNotIn("frontend-design", content, "frontend-design 应被过滤但未被过滤！")
        # slack-gif-creator 与 matlab 无标签交集，且空 tags 不再全局放行
        self.assertNotIn("slack-gif-creator", content)

        print("=== 测试 3 通过 ===")

    def test_4_touch_with_atomic_write(self):
        """测试使用频次自增 + 原子写入（应产生 .bak 备份）"""
        print("\n=== 测试 4：使用频次自增 + 原子写入 ===")
        with open(self.metadata_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.assertIn("matlab", data["rules"])
        original_count = data["rules"]["matlab"].get("usage_count", 0)

        run_touching("matlab")

        # 验证 .bak 备份文件是否产生
        bak_file = self.metadata_file + ".bak"
        self.assertTrue(os.path.exists(bak_file), "原子写入未产生 .bak 备份文件！")

        with open(self.metadata_file, "r", encoding="utf-8") as f:
            updated_data = json.load(f)

        new_count = updated_data["rules"]["matlab"].get("usage_count", 0)
        self.assertEqual(new_count, original_count + 1)
        print(f"使用统计: {original_count} -> {new_count}, .bak 备份已生成")
        print("=== 测试 4 通过 ===")

    def test_5_ide_preference_in_compilation(self):
        """测试直推模式下 preferred_ide 仅输出单一格式"""
        print("\n=== 测试 5：IDE 偏好直推 ===")
        binding_info = {
            "bound_at": "2026-05-20 13:00:00",
            "project_path": self.temp_project_dir.replace("\\", "/"),
            "tags": ["general"],
            "preferred_ide": "windsurf"
        }
        config_path = os.path.join(self.temp_project_dir, ".pgrms.json")
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(binding_info, f, indent=2)

        # 执行 target=all，但 preferred_ide=windsurf 应只输出 windsurf
        run_compilation(target="all", project_path=self.temp_project_dir)

        self.assertTrue(os.path.exists(os.path.join(self.temp_project_dir, ".windsurfrules")),
                        "首选 IDE 文件未生成！")
        self.assertFalse(os.path.exists(os.path.join(self.temp_project_dir, ".cursorrules")),
                         ".cursorrules 不应生成（不是首选IDE）！")
        self.assertFalse(os.path.exists(os.path.join(self.temp_project_dir, ".clinerules")),
                         ".clinerules 不应生成（不是首选IDE）！")

        print("=== 测试 5 通过 ===")

    def test_6_safe_write_json_rollback(self):
        """测试 safe_write_json 的备份机制"""
        print("\n=== 测试 6：原子写入备份验证 ===")
        test_file = os.path.join(self.temp_project_dir, "test_atomic.json")

        # 第一次写入
        safe_write_json(test_file, {"version": 1})
        self.assertTrue(os.path.exists(test_file))

        # 第二次写入应产生 .bak
        safe_write_json(test_file, {"version": 2})
        bak_file = test_file + ".bak"
        self.assertTrue(os.path.exists(bak_file))

        with open(bak_file, "r", encoding="utf-8") as f:
            bak_data = json.load(f)
        self.assertEqual(bak_data["version"], 1, ".bak 应保存上一版本内容")

        with open(test_file, "r", encoding="utf-8") as f:
            cur_data = json.load(f)
        self.assertEqual(cur_data["version"], 2, "当前文件应是最新版本")

        print("=== 测试 6 通过 ===")

    def test_7_global_skill_deploy_syncs_agent_and_agents_dirs(self):
        """测试全局部署同时覆盖 .agent 与 .agents 目录"""
        print("\n=== 测试 7：全局技能双目录同步 ===")
        dist_skills = os.path.join(self.temp_project_dir, "dist", "antigravity", "skills")
        sample_skill_dir = os.path.join(dist_skills, "sample-skill")
        fake_home_dir = os.path.join(self.temp_project_dir, "fake_home")

        os.makedirs(sample_skill_dir, exist_ok=True)
        with open(os.path.join(sample_skill_dir, "SKILL.md"), "w", encoding="utf-8") as f:
            f.write("---\nname: sample-skill\n---\n")

        deployed_dirs = deploy_global_skill_packages(dist_skills, fake_home_dir)

        singular_skill = os.path.join(fake_home_dir, ".agent", "skills", "sample-skill", "SKILL.md")
        plural_skill = os.path.join(fake_home_dir, ".agents", "skills", "sample-skill", "SKILL.md")

        self.assertEqual(len(deployed_dirs), 2)
        self.assertTrue(os.path.exists(singular_skill), ".agent 目录未同步技能！")
        self.assertTrue(os.path.exists(plural_skill), ".agents 目录未同步技能！")
        print("=== 测试 7 通过 ===")

    def test_8_vscode_global_instructions_sync(self):
        """测试 VS Code Copilot 用户级全局 instructions 同步"""
        print("\n=== 测试 8：VS Code 全局指令同步 ===")
        fake_prompts_dir = os.path.join(self.temp_project_dir, "fake_vscode_prompts")
        source_rule = os.path.join(
            self.root_dir,
            "source", "custom", "productivity", "chinese-output-constraint", "RULE.md"
        )

        target_file = deploy_vscode_global_instructions(fake_prompts_dir, source_rule)

        self.assertTrue(os.path.exists(target_file), "VS Code 全局 instructions 未生成！")

        with open(target_file, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn("applyTo: '**'", content)
        self.assertIn("全局中文输出约束规则", content)
        self.assertIn("description:", content)
        print("=== 测试 8 通过 ===")

    def test_9_deploy_dry_run_does_not_write_fake_home(self):
        """deploy 默认 dry-run，不应写入 fake HOME。"""
        fake_home_dir = os.path.join(self.temp_project_dir, "fake_home_dry_run")

        run_deploy(target="codex", apply=False, home_dir=fake_home_dir)

        self.assertFalse(os.path.exists(fake_home_dir), "dry-run 不应创建 fake HOME")

    def test_10_deploy_apply_fake_home_writes_only_fake_home(self):
        """deploy --apply --home 写入 fake HOME 并生成日志。"""
        fake_home_dir = os.path.join(self.temp_project_dir, "fake_home_apply")

        run_deploy(target="antigravity", apply=True, home_dir=fake_home_dir)

        self.assertTrue(os.path.exists(os.path.join(fake_home_dir, ".agent", "skills")))
        self.assertTrue(os.path.exists(os.path.join(fake_home_dir, ".agents", "skills")))
        self.assertTrue(os.path.exists(os.path.join(fake_home_dir, ".gitignore_global")))
        self.assertTrue(os.path.exists(os.path.join(fake_home_dir, ".gemini", "GEMINI.md")))
        self.assertTrue(os.path.exists(os.path.join(fake_home_dir, ".pgrms-deploy-logs")))

    def test_11_codex_compile_outputs_local_bundle(self):
        """compile --target codex 输出项目局部 .codex/skills。"""
        binding_info = {
            "bound_at": "2026-05-20 13:00:00",
            "project_path": self.temp_project_dir.replace("\\", "/"),
            "tags": ["general"],
            "preferred_ide": "codex"
        }
        config_path = os.path.join(self.temp_project_dir, ".pgrms.json")
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(binding_info, f, indent=2)

        run_compilation(target="codex", project_path=self.temp_project_dir)

        codex_skills_dir = os.path.join(self.temp_project_dir, ".codex", "skills")
        self.assertTrue(os.path.exists(codex_skills_dir))
        self.assertTrue(os.path.exists(os.path.join(codex_skills_dir, "chinese-output-constraint", "SKILL.md")))


    def test_12_scan_repository_includes_audience_metadata(self):
        """scan 后的 metadata.json 应包含 audience 字段。"""
        scan_repository()

        with open(self.metadata_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.assertEqual(data["rules"]["chinese-output-constraint"]["audience"], "codex-core")
        self.assertEqual(data["rules"]["internal-comms"]["audience"], "archive")

    def test_13_codex_compile_skips_archive_rules(self):
        """codex 编译默认只保留 codex-core 和 codex-project。"""
        binding_info = {
            "bound_at": "2026-05-20 13:00:00",
            "project_path": self.temp_project_dir.replace("\\", "/"),
            "tags": ["general", "react", "javascript", "tailwind", "web", "testing"],
            "preferred_ide": "codex"
        }
        config_path = os.path.join(self.temp_project_dir, ".pgrms.json")
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(binding_info, f, indent=2)

        run_compilation(target="codex", project_path=self.temp_project_dir)

        codex_skills_dir = os.path.join(self.temp_project_dir, ".codex", "skills")
        self.assertTrue(os.path.exists(os.path.join(codex_skills_dir, "frontend-design", "SKILL.md")))
        self.assertFalse(os.path.exists(os.path.join(codex_skills_dir, "ui-ux-pro-max")))
        self.assertFalse(os.path.exists(os.path.join(codex_skills_dir, "internal-comms")))


    def test_14_doc_coauthoring_not_injected_without_docs_tags(self):
        """doc-coauthoring 不应再因 general 标签默认注入。"""
        binding_info = {
            "bound_at": "2026-05-20 13:00:00",
            "project_path": self.temp_project_dir.replace("\\", "/"),
            "tags": ["git", "python", "mcp", "release", "skill"],
            "preferred_ide": "codex"
        }
        config_path = os.path.join(self.temp_project_dir, ".pgrms.json")
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(binding_info, f, indent=2)

        run_compilation(target="codex", project_path=self.temp_project_dir)

        codex_skills_dir = os.path.join(self.temp_project_dir, ".codex", "skills")
        self.assertFalse(os.path.exists(os.path.join(codex_skills_dir, "doc-coauthoring")))
        self.assertTrue(os.path.exists(os.path.join(codex_skills_dir, "mcp-builder", "SKILL.md")))

    def test_15_doc_coauthoring_injected_with_docs_tag(self):
        """doc-coauthoring 只在 docs/writing 项目中注入。"""
        binding_info = {
            "bound_at": "2026-05-20 13:00:00",
            "project_path": self.temp_project_dir.replace("\\", "/"),
            "tags": ["docs", "writing"],
            "preferred_ide": "codex"
        }
        config_path = os.path.join(self.temp_project_dir, ".pgrms.json")
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(binding_info, f, indent=2)

        run_compilation(target="codex", project_path=self.temp_project_dir)

        codex_skills_dir = os.path.join(self.temp_project_dir, ".codex", "skills")
        self.assertTrue(os.path.exists(os.path.join(codex_skills_dir, "doc-coauthoring", "SKILL.md")))


if __name__ == "__main__":
    unittest.main()
