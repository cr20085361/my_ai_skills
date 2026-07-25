---
name: installer-version-naming
title: 离线安装包版本命名规范
description: 设计本地离线安装包时，强制程序显示名称包含版本号，并确保程序名称与软件内部版本信息一致。当用户提到"打包安装包""制作安装程序""离线部署包""Inno Setup""NSIS""安装包设计""程序快捷方式"时激活。
category: engineering
audience: codex-project
tags: [installer, packaging, versioning, windows]
status: active
score: 10.0
---

# 离线安装包版本命名规范

## 核心原则

用户通过桌面快捷方式或开始菜单中的程序名称即可判断当前安装的软件是否为最新版本。为此，所有本地离线安装包必须遵守以下版本可见性约束。

## 强制约束

### 1. 程序显示名称必须包含版本号

安装后在快捷方式、开始菜单、控制面板"程序和功能"中显示的程序名称，必须携带完整版本号。

**命名格式：**

```
<程序名> <主版本>.<次版本>.<修订号>
```

**示例：**

| ✅ 正确 | ❌ 错误 |
|---------|---------|
| `DataSync 2.3.1` | `DataSync` |
| `CST Antenna Tool 1.0.0` | `CST Antenna Tool` |
| `ReportGen 3.2.0` | `ReportGen v3` |

### 2. 程序名称与内部版本信息必须一致

以下所有位置的版本标识必须保持完全一致：

- **快捷方式名称**（桌面 / 开始菜单）
- **控制面板 → 程序和功能 → 显示名称**（`DisplayName`）
- **软件窗口标题栏**（如 `DataSync 2.3.1`）
- **软件"关于"对话框中的版本号**
- **安装包文件名**（如 `DataSync-Setup-2.3.1.exe`）
- **安装目录名称**（如 `C:\Program Files\DataSync 2.3.1\`）

### 3. 安装包文件命名

```
<程序名>-Setup-<版本号>.exe
```

示例：`DataSync-Setup-2.3.1.exe`

### 4. 版本升级时的行为

- 新版本安装后，旧版本的快捷方式应被替换或移除，不得残留。
- 若支持多版本并存，快捷方式必须各自携带版本号以区分。
- 控制面板中不得出现同名但不同版本的重复条目。

## 各打包工具的实现要点

### Inno Setup

```pascal
#define MyAppName "DataSync"
#define MyAppVersion "2.3.1"

[Setup]
AppName={#MyAppName} {#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
DefaultDirName={autopf}\{#MyAppName} {#MyAppVersion}
OutputBaseFilename={#MyAppName}-Setup-{#MyAppVersion}

[Icons]
Name: "{autodesktop}\{#MyAppName} {#MyAppVersion}"; Filename: "{app}\DataSync.exe"
Name: "{group}\{#MyAppName} {#MyAppVersion}"; Filename: "{app}\DataSync.exe"
```

### NSIS

```nsis
!define APP_NAME "DataSync"
!define APP_VERSION "2.3.1"

Name "${APP_NAME} ${APP_VERSION}"
OutFile "${APP_NAME}-Setup-${APP_VERSION}.exe"
InstallDir "$PROGRAMFILES\${APP_NAME} ${APP_VERSION}"

VIProductVersion "${APP_VERSION}.0"
VIAddVersionKey "ProductName" "${APP_NAME} ${APP_VERSION}"
VIAddVersionKey "FileVersion" "${APP_VERSION}"
```

### Python (PyInstaller + Inno Setup)

```python
# version.py — 唯一版本源
APP_NAME = "DataSync"
APP_VERSION = "2.3.1"
APP_DISPLAY = f"{APP_NAME} {APP_VERSION}"
```

窗口标题和"关于"对话框必须引用同一版本常量，禁止硬编码。

## 检查清单

每次发布安装包前，逐项确认：

- [ ] 快捷方式名称包含完整版本号
- [ ] 控制面板显示名称包含完整版本号
- [ ] 窗口标题栏显示版本号
- [ ] "关于"对话框版本号与名称一致
- [ ] 安装包文件名包含版本号
- [ ] 安装目录包含版本号
- [ ] 升级安装后旧快捷方式已清理
