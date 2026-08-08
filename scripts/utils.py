#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PGRMS (个人全局规则管理系统) - 共享工具函数模块
将各脚本中重复使用的通用工具函数统一收口至此，消除拷贝粘贴、确保签名一致。
"""

import os
import sys
import io
import json
import tempfile

# ─── Windows 控制台 UTF-8 编码强制重定向（仅在 CLI 直接运行时启用） ───
_utf8_initialized = False

def ensure_utf8_console():
    """在 Windows 环境下将 stdout/stderr 强制切换为 UTF-8 编码"""
    global _utf8_initialized
    if _utf8_initialized:
        return
    _utf8_initialized = True
    if sys.platform.startswith("win"):
        try:
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
        except Exception:
            pass

# ─── 全局路径常量 ───
SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(SCRIPTS_DIR)
SOURCE_DIR = os.path.join(ROOT_DIR, "source")
FAMILIES_DIR = os.path.join(SOURCE_DIR, "families")
METADATA_FILE = os.path.join(ROOT_DIR, "metadata.json")
DIST_DIR = os.path.join(ROOT_DIR, "dist")
ARCHIVE_DIR = os.path.join(ROOT_DIR, "archive")
DASHBOARD_FILE = os.path.join(ROOT_DIR, "dashboard.html")


# ─── 文件安全读取 ───
def read_file_safely(file_path):
    """
    自适应多编码安全读取文件内容。
    按 utf-8 → utf-8-sig → gbk → gb18030 → utf-16 的顺序尝试解码，
    最后兜底以二进制读取并忽略无法解码的字符。
    返回: (文件内容字符串, 实际使用的编码名称)
    """
    for enc in ["utf-8", "utf-8-sig", "gbk", "gb18030", "utf-16"]:
        try:
            with open(file_path, "r", encoding=enc) as f:
                return f.read(), enc
        except UnicodeDecodeError:
            continue
    # 兜底二进制读取
    try:
        with open(file_path, "rb") as f:
            return f.read().decode("utf-8", errors="ignore"), "utf-8-ignored"
    except Exception as e:
        return f"读取文件内容失败: {str(e)}", "error"


# ─── JSON 原子化安全写入 ───
def safe_write_json(filepath, data):
    """
    原子化安全写入 JSON 文件，防止中途崩溃导致数据损毁。
    策略: 先写入同目录的临时文件 → 备份原文件为 .bak → 原子重命名临时文件为目标文件。
    """
    dir_name = os.path.dirname(filepath)
    fd, tmp_path = tempfile.mkstemp(dir=dir_name, suffix=".json.tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        # 备份原文件
        if os.path.exists(filepath):
            backup = filepath + ".bak"
            if os.path.exists(backup):
                os.remove(backup)
            os.rename(filepath, backup)
        # 原子重命名
        os.rename(tmp_path, filepath)
    except Exception:
        # 回滚：清理临时文件，尝试从备份恢复
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        backup = filepath + ".bak"
        if not os.path.exists(filepath) and os.path.exists(backup):
            os.rename(backup, filepath)
        raise


# ─── CLI 色彩输出工具 ───
def cli_success(msg):
    """绿色成功信息"""
    print(f"\033[92m✓ {msg}\033[0m")

def cli_warning(msg):
    """黄色警告信息"""
    print(f"\033[93m⚠ {msg}\033[0m")

def cli_error(msg):
    """红色错误信息"""
    print(f"\033[91m✗ {msg}\033[0m")

def cli_info(msg):
    """蓝色提示信息"""
    print(f"\033[94mℹ {msg}\033[0m")

def cli_summary(msg):
    """紫色操作摘要"""
    print(f"\033[95m{'─'*60}\033[0m")
    print(f"\033[95m{msg}\033[0m")
    print(f"\033[95m{'─'*60}\033[0m")
