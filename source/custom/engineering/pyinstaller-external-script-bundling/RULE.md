---
name: pyinstaller-external-script-bundling
title: PyInstaller 打包外部解释器脚本的必备模式
description: 当 PyInstaller 应用需要在运行时通过 subprocess 调用外部解释器（CST Python、MATLAB、自定义 Python 等）执行 .py 脚本时，必须使用 --add-data 打包脚本并用 sys._MEIPASS 解析路径。当用户提到"PyInstaller 打包""CST 联动""外部脚本调用""subprocess 调用 worker""打包后脚本找不到""_MEIPASS"时激活。
category: engineering
audience: codex-project
tags: [pyinstaller, packaging, cst, subprocess, worker-script, meipass]
status: active
score: 10.0
---

# PyInstaller 打包外部解释器脚本的必备模式

## 问题场景

主程序（PyQt6 / Tkinter / CLI）通过 `subprocess.run([external_python, worker_script, ...])` 调用外部解释器执行一个 `.py` 脚本。典型场景：

- CST Studio Suite 参数化建模（CST 捆绑的 Python 执行 `cst_worker.py`）
- MATLAB Engine 调用（MATLAB 的 Python 接口执行桥接脚本）
- 任何"主程序用系统 Python，worker 用另一个解释器"的架构

**开发模式下一切正常**，因为 `Path(__file__).parents[N] / "scripts" / "worker.py"` 能正确定位源码树中的脚本。

**PyInstaller 打包后崩溃**，因为 `__file__` 指向 `_MEIPASS` 临时解压目录，该目录不包含源码树的 `scripts/` 子目录。

## 强制规则

### 规则 1：PyInstaller 构建必须包含 --add-data

```powershell
# Windows 语法：--add-data "源路径;目标子目录"
pyinstaller --onefile --windowed `
    --add-data "scripts\cst_worker.py;slant_polarizer\cst" `
    ...
```

```bash
# Linux/macOS 语法：--add-data "源路径:目标子目录"
pyinstaller --onefile --windowed \
    --add-data "scripts/cst_worker.py:slant_polarizer/cst" \
    ...
```

**目标子目录**必须与运行时路径解析代码中的相对路径一致。

### 规则 2：运行时路径解析必须兼容两种模式

```python
import sys
from pathlib import Path


def resolve_worker_script() -> Path:
    """Locate worker script in both PyInstaller bundles and source trees."""
    # PyInstaller onefile: 脚本被解压到 _MEIPASS/<目标子目录>/
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        candidate = Path(meipass) / "slant_polarizer" / "cst" / "cst_worker.py"
        if candidate.is_file():
            return candidate
    # 开发模式 / editable install：从源码树相对路径定位
    return Path(__file__).resolve().parents[3] / "scripts" / "cst_worker.py"
```

**禁止**仅使用 `Path(__file__).parents[N]` 而不检查 `_MEIPASS`。

### 规则 3：构建脚本必须同步更新

`build_installer.ps1`、`Makefile`、`pyproject.toml` 中的 PyInstaller 命令必须包含 `--add-data`。如果构建脚本使用变量拼接参数，确保 `--add-data` 不被条件跳过。

### 规则 4：worker 脚本的 source_root 参数

如果 worker 脚本接收 `source_root` 参数用于 `sys.path.insert()`，在 PyInstaller 模式下应传入 `worker_script.parent` 而非源码树路径：

```python
job = {
    "source_root": str(worker_script.parent),  # ✅ 两种模式都有效
    # "source_root": str(source_root / "src"),  # ❌ PyInstaller 下路径不存在
}
```

## 架构设计阶段的检查清单

创建新项目时，如果架构涉及"主程序 + 外部解释器执行脚本"，**在写第一行代码前**确认：

- [ ] worker 脚本路径解析函数已设计为双模式（`_MEIPASS` + 源码树）
- [ ] PyInstaller 构建命令已包含 `--add-data`
- [ ] 构建脚本（`.ps1` / `Makefile` / CI workflow）已包含 `--add-data`
- [ ] worker 脚本不依赖源码树中其他未打包的文件
- [ ] 打包后立即测试外部脚本调用路径（不要等到安装后才测）

## 常见错误模式

| 错误 | 症状 | 修复 |
|------|------|------|
| 仅用 `Path(__file__).parents[N]` | 安装版报 `FileNotFoundError: worker.py` | 添加 `_MEIPASS` 检查 |
| 忘记 `--add-data` | `_MEIPASS` 下找不到脚本 | 构建命令添加 `--add-data` |
| `--add-data` 目标路径与代码不一致 | 脚本存在但路径拼接错误 | 统一目标子目录名 |
| worker 依赖源码树其他模块 | worker 执行时 `ImportError` | 将依赖也打包，或让 worker 自包含 |
| `--collect-data` 替代 `--add-data` | `.py` 文件不被 collect-data 收集 | `.py` 必须用 `--add-data` |
