#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PGRMS (个人全局规则管理系统) - 第三方规则拉取与标准化引擎
"""

import os
import sys
import re
import shutil
import subprocess
import urllib.parse
from datetime import datetime

SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(SCRIPTS_DIR)
SOURCE_DIR = os.path.join(ROOT_DIR, "source")
REGISTRY_DIR = os.path.join(SOURCE_DIR, "registry")
TEMP_DIR = os.path.join(ROOT_DIR, "temp_git_fetch")

def parse_github_url(url):
    """
    解析 GitHub URL 提取作者、仓库名、分支和可能的文件路径
    """
    parsed = urllib.parse.urlparse(url)
    path_parts = [p for p in parsed.path.split("/") if p]
    
    if len(path_parts) < 2:
        raise ValueError("无效的 GitHub 链接结构！请提供 owner/repo 结构链接。")
        
    author = path_parts[0]
    repo = path_parts[1].replace(".git", "")
    
    # 提取分支或特定路径（如果是指向具体文件的链接）
    specific_file = None
    if "blob" in path_parts and len(path_parts) > 3:
        blob_index = path_parts.index("blob")
        specific_file = "/".join(path_parts[blob_index + 2:])
        
    return author, repo, specific_file

def smart_extract_metadata(content, fallback_name):
    """
    智能分析规则文本内容，提取 YAML 元数据。
    支持原生包含 YAML Frontmatter 的规则，也支持纯 Markdown 文档的启发式匹配提取。
    """
    metadata = {
        "name": fallback_name,
        "title": fallback_name,
        "description": "自动从第三方引入的规则配置。",
        "audience": "archive",
        "tags": []
    }
    
    # 1. 检查是否原生包含 YAML Frontmatter
    if content.strip().startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            yaml_text = parts[1]
            for line in yaml_text.strip().split("\n"):
                if ":" not in line:
                    continue
                k, v = line.split(":", 1)
                k = k.strip().lower()
                v = v.strip().strip('"').strip("'")
                if k == "name":
                    metadata["name"] = re.sub(r'[^a-z0-9\-]', '', v.lower())
                elif k == "title":
                    metadata["title"] = v
                elif k == "description":
                    metadata["description"] = v
                elif k == "audience":
                    metadata["audience"] = v
                elif k == "tags":
                    v = v.replace("[", "").replace("]", "")
                    metadata["tags"] = [t.strip() for t in v.split(",") if t.strip()]
            return metadata, parts[2].strip()

    # 2. 启发式解析纯 Markdown 文档
    # 提取第一个大标题作为标题
    title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
    if title_match:
        metadata["title"] = title_match.group(1).strip()
        metadata["name"] = re.sub(r'[^a-z0-9\-]', '', metadata["title"].lower().replace(" ", "-"))
        
    # 提取前几段有实际意义的文本作为描述
    paragraphs = [p.strip() for p in content.split("\n\n") if p.strip()]
    for p in paragraphs:
        # 跳过标题行
        if p.startswith("#"):
            continue
        # 取第一段非标题文本的前 80 个字作为描述
        metadata["description"] = p[:80] + ("..." if len(p) > 80 else "")
        break
        
    # 智能技术标签匹配
    tech_keywords = {
        "python": ["python", "django", "flask", "fastapi"],
        "javascript": ["javascript", "js", "node", "typescript", "ts"],
        "react": ["react", "next.js", "jsx", "tsx"],
        "vue": ["vue", "nuxt"],
        "css": ["css", "tailwind", "sass", "less", "html"],
        "matlab": ["matlab", "octave"],
        "git": ["git", "github", "gitlab"],
        "database": ["sql", "mysql", "postgresql", "mongodb", "redis"],
        "docker": ["docker", "k8s", "kubernetes", "devops"]
    }
    
    lower_content = content.lower()
    for tag, kw_list in tech_keywords.items():
        for kw in kw_list:
            if kw in lower_content:
                metadata["tags"].append(tag)
                break
                
    if not metadata["tags"]:
        metadata["tags"] = ["general"]
        
    # 剔除第一个大标题（因为它会被编译引擎以规范格式重新附加上去）
    clean_body = re.sub(r'^#\s+.+$', '', content, flags=re.MULTILINE).strip()
    
    return metadata, clean_body

def run_fetching(url, category="engineering", explicit_name=None):
    """
    拉取第三方仓库或文件的核心逻辑
    """
    print(f"正在启动规则自动拉取引擎...")
    print(f"原始链接: {url}")
    print(f"归类分类: {category}")
    
    try:
        author, repo, specific_file = parse_github_url(url)
    except Exception as e:
        print(f"错误: 无法解析输入的 URL: {str(e)}")
        return
        
    print(f"解析成功 -> 作者/所有者: {author} | 仓库名: {repo}")
    if specific_file:
        print(f"检测到指定特定的规则文件路径: {specific_file}")

    # 清理原有的临时拉取文件夹
    if os.path.exists(TEMP_DIR):
        try:
            shutil.rmtree(TEMP_DIR)
        except Exception as e:
            print(f"清理临时目录失败: {str(e)}")

    # 1. 克隆 GitHub 仓库到临时目录
    repo_url = f"https://github.com/{author}/{repo}.git"
    print(f"正在克隆远程 GitHub 仓库: {repo_url} ...")
    
    try:
        # 使用 git clone --depth 1 高效克隆
        subprocess.run(
            ["git", "clone", "--depth", "1", repo_url, TEMP_DIR],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
    except Exception as e:
        print(f"克隆远程仓库失败！请确认您的网络或链接是否正确。详情: {str(e)}")
        return

    # 2. 搜寻规则配置文件
    rule_content = ""
    rule_source_file = ""
    
    if specific_file:
        # 如果指定了特定文件，直接读取它
        target_path = os.path.join(TEMP_DIR, specific_file)
        if os.path.exists(target_path):
            rule_source_file = specific_file
            try:
                with open(target_path, "r", encoding="utf-8") as f:
                    rule_content = f.read()
            except Exception as e:
                print(f"读取指定文件失败: {str(e)}")
        else:
            print(f"错误: 在克隆的仓库中未找到指定文件: {specific_file}")
    else:
        # 否则，智能扫描通用的规则配置文件
        possible_files = [
            ".cursorrules",
            ".clinerules",
            ".roo-clinerules",
            ".windsurfrules",
            "SKILL.md",
            "RULE.md",
            "rules.md"
        ]
        
        for p_file in possible_files:
            target_path = os.path.join(TEMP_DIR, p_file)
            if os.path.exists(target_path):
                rule_source_file = p_file
                try:
                    with open(target_path, "r", encoding="utf-8") as f:
                        rule_content = f.read()
                    print(f"智能匹配成功！找到规则配置文件: {p_file}")
                    break
                except Exception as e:
                    print(f"读取匹配文件失败: {str(e)}")
                    
        # 兜底：如果没找到规则文件，寻找 README.md 并将其视作规则正文
        if not rule_content:
            readme_path = os.path.join(TEMP_DIR, "README.md")
            if os.path.exists(readme_path):
                rule_source_file = "README.md"
                try:
                    with open(readme_path, "r", encoding="utf-8") as f:
                        rule_content = f.read()
                    print("智能匹配: 未找到任何标准规则文件，将使用 README.md 进行标准化解析。")
                except Exception as e:
                    print(f"读取 README.md 失败: {str(e)}")

    # 如果依旧为空，则拉取失败
    if not rule_content:
        print("错误: 无法在克隆的仓库中识别出有效的规则文本或 README 说明！拉取中止。")
        # 清理临时目录
        shutil.rmtree(TEMP_DIR, ignore_errors=True)
        return

    # 3. 标准化元数据抽取
    fallback_id = explicit_name if explicit_name else f"{author}-{repo}".lower().replace("_", "-")
    metadata, clean_body = smart_extract_metadata(rule_content, fallback_id)
    
    # 强制将 category 设置为用户指定的参数
    metadata["category"] = category

    # 4. 创建 registry 入库目录
    rule_dir_name = metadata["name"]
    target_rule_dir = os.path.join(REGISTRY_DIR, author, rule_dir_name)
    os.makedirs(target_rule_dir, exist_ok=True)
    
    target_rule_file = os.path.join(target_rule_dir, "RULE.md")
    target_meta_file = os.path.join(target_rule_dir, "metadata.yml")

    # 5. 写入标准化后的 RULE.md
    rule_formatted_content = []
    rule_formatted_content.append("---")
    rule_formatted_content.append(f"name: {metadata['name']}")
    rule_formatted_content.append(f"title: {metadata['title']}")
    rule_formatted_content.append(f"description: {metadata['description']}")
    rule_formatted_content.append(f"category: {metadata['category']}")
    rule_formatted_content.append(f"audience: {metadata['audience']}")
    rule_formatted_content.append(f"tags: [{', '.join(metadata['tags'])}]")
    rule_formatted_content.append("status: active")
    rule_formatted_content.append("score: 10.0")
    rule_formatted_content.append("---")
    rule_formatted_content.append("\n# " + metadata["title"])
    rule_formatted_content.append("\n" + clean_body)
    
    try:
        with open(target_rule_file, "w", encoding="utf-8") as f:
            f.write("\n".join(rule_formatted_content))
        print(f"标准化规则正文已保存至: {target_rule_file}")
    except Exception as e:
        print(f"写入 RULE.md 失败: {str(e)}")
        return

    # 获取最新 commit 哈希
    commit_hash = "unknown"
    try:
        commit_res = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=TEMP_DIR,
            capture_output=True,
            text=True,
            check=True
        )
        commit_hash = commit_res.stdout.strip()
    except Exception as e:
        pass

    # 6. 写入辅助元数据记录 metadata.yml
    meta_yml_content = []
    meta_yml_content.append(f"original_url: {url}")
    meta_yml_content.append(f"repository: {author}/{repo}")
    meta_yml_content.append(f"author: {author}")
    meta_yml_content.append(f"ingestion_date: {datetime.now().strftime('%Y-%m-%d')}")
    meta_yml_content.append(f"commit_hash: {commit_hash}")
    
    try:
        with open(target_meta_file, "w", encoding="utf-8") as f:
            f.write("\n".join(meta_yml_content))
        print(f"拉取审计信息元数据已保存至: {target_meta_file}")
    except Exception as e:
        print(f"写入 metadata.yml 失败: {str(e)}")

    # 7. 清理临时目录
    try:
        shutil.rmtree(TEMP_DIR)
        print("临时克隆缓存目录已清理干净。")
    except Exception as e:
        print(f"清理临时目录时发生轻微异常（已忽略）: {str(e)}")

    # 8. 触发 scan 自动更新主索引 metadata.json
    print("正在自动扫描并更新全局规则索引库索引...")
    from pgrms import scan_repository
    scan_repository()
    
    print(f"恭喜！成功导入外部规则: [{author}] {metadata['name']} 并将其放入 [{category}] 分类中！")

if __name__ == "__main__":
    # 支持命令行独立调用测试
    if len(sys.argv) < 2:
        print("使用说明: python fetcher.py <github-url> [category]")
        sys.exit(0)
    url = sys.argv[1]
    cat = sys.argv[2] if len(sys.argv) > 2 else "engineering"
    run_fetching(url, cat)


