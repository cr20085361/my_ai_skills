#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PGRMS (个人全局规则管理系统) - 看板式 HTML 交互控制大屏生成引擎
"""

import os
import json

from utils import ROOT_DIR, METADATA_FILE, DASHBOARD_FILE, read_file_safely as _read_file_safely

def read_file_safely(file_path):
    """兼容层：dashboard 内部仅需 content 字符串，忽略编码名"""
    content, _ = _read_file_safely(file_path)
    return content

def get_rule_full_content(rule_path):
    """
    读取 RULE.md 的完整文本内容（包括 YAML 头部和 Markdown），用于在前端 Modal 弹窗中展示
    """
    absolute_rule_path = os.path.join(ROOT_DIR, rule_path, "RULE.md")
    if not os.path.exists(absolute_rule_path):
        return "未找到该规则的物理源文件 RULE.md！"
    return read_file_safely(absolute_rule_path)

def generate_html_dashboard(metadata_file=METADATA_FILE, output_file=DASHBOARD_FILE):
    """
    读取规则元数据索引，生成精美的暗色毛玻璃风格交互看板 dashboard.html
    """
    print("正在启动 PGRMS 看板生成引擎，正在渲染交互大屏...")
    
    if not os.path.exists(metadata_file):
        print("错误: 规则索引库不存在，请先运行 scan 扫描命令。")
        return
        
    try:
        with open(metadata_file, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"读取索引库失败: {str(e)}")
        return
        
    rules = data.get("rules", {})
    families = data.get("families", {})
    
    # 动态将每条规则的完整 Markdown 源码注入到元数据中，便于前端弹窗直接渲染
    rules_list = []
    for r_id, r_info in rules.items():
        # 复制一份以防污染内存
        info_copy = dict(r_info)
        info_copy["full_content"] = get_rule_full_content(r_info["path"])
        
        # 预先生成维护建议文本，方便前端直接调取
        score = info_copy.get("score", 10.0)
        status = info_copy.get("status", "active")
        
        if status == "disabled" or score < 0.1:
            info_copy["health_status"] = "archived"
            info_copy["health_badge"] = "已停用/归档"
            info_copy["suggestion"] = "该规则已失效并已移入 archive/ 目录。建议运行 clean 或寻找同类替代规则。"
        elif score >= 8.5:
            info_copy["health_status"] = "healthy"
            info_copy["health_badge"] = "状态极佳"
            info_copy["suggestion"] = "优秀规则：评分在安全线以上，状态极佳，无需任何改动。"
        elif score >= 5.0:
            info_copy["health_status"] = "warning"
            info_copy["health_badge"] = "正常运行"
            info_copy["suggestion"] = "正常规则：运行状态平稳。可定期关注其 GitHub 原仓库的更新状态。"
        else:
            info_copy["health_status"] = "critical"
            info_copy["health_badge"] = "亚健康/过时"
            info_copy["suggestion"] = "严重警告：评分低于 5.0！针对技术栈可能已过时，强烈建议运行 'python scripts/pgrms.py prune' 进行淘汰与同类更优替代！"
            
        rules_list.append(info_copy)

    # 计算全局大屏统计指标 (KPIs)
    total_count = len(rules_list)
    active_count = sum(1 for r in rules_list if r["status"] == "active")
    avg_score = sum(r["score"] for r in rules_list) / total_count if total_count > 0 else 0.0
    critical_count = sum(1 for r in rules_list if r["status"] == "active" and r["score"] < 5.0)

    # 序列化为 JSON 并对 HTML 敏感标签尖括号进行 Unicode 转义，防止 HTML 解析器提前截断 script 标签
    rules_json = json.dumps(rules_list, ensure_ascii=False).replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
    families_json = json.dumps(list(families.values()), ensure_ascii=False).replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")

    # HTML 网页源码模板 (使用高拟真暗色毛玻璃 UI 风格，全部原生 HTML+CSS+JS 编写)
    html_template = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PGRMS - 个人全局规则智能管理看板</title>
    <!-- 引入 Google Outfit 现代科技感字体与 FontAwesome 图标 -->
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&family=Noto+Sans+SC:wght@300;400;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    
    <style>
        :root {{
            --bg-gradient: linear-gradient(135deg, #0f172a 0%, #1e1b4b 50%, #020617 100%);
            --glass-bg: rgba(15, 23, 42, 0.45);
            --glass-border: rgba(255, 255, 255, 0.08);
            --glass-hover-border: rgba(255, 255, 255, 0.18);
            --text-primary: #f8fafc;
            --text-secondary: #94a3b8;
            --accent-glow: rgba(99, 102, 241, 0.15);
            
            /* 健康度状态色彩体系 */
            --color-healthy: #10b981;
            --color-healthy-glow: rgba(16, 185, 129, 0.2);
            --color-warning: #f59e0b;
            --color-warning-glow: rgba(245, 158, 11, 0.2);
            --color-critical: #ef4444;
            --color-critical-glow: rgba(239, 68, 68, 0.2);
            --color-archived: #64748b;
            --color-archived-glow: rgba(100, 116, 139, 0.2);
        }}

        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: 'Outfit', 'Noto Sans SC', sans-serif;
            background: var(--bg-gradient);
            color: var(--text-primary);
            min-height: 100vh;
            overflow-x: hidden;
            padding-bottom: 50px;
        }}

        /* 顶部毛玻璃导航条 */
        header {{
            position: sticky;
            top: 0;
            z-index: 100;
            background: rgba(15, 23, 42, 0.6);
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            border-bottom: 1px solid var(--glass-border);
            padding: 15px 40px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}

        .logo-section {{
            display: flex;
            align-items: center;
            gap: 12px;
        }}

        .logo-icon {{
            font-size: 24px;
            background: linear-gradient(135deg, #6366f1 0%, #a855f7 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            filter: drop-shadow(0 2px 8px rgba(99, 102, 241, 0.5));
        }}

        .logo-title {{
            font-size: 20px;
            font-weight: 800;
            letter-spacing: 1px;
            background: linear-gradient(to right, #ffffff, #c7d2fe);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}

        .logo-badge {{
            background: rgba(99, 102, 241, 0.15);
            border: 1px solid rgba(99, 102, 241, 0.3);
            color: #818cf8;
            font-size: 11px;
            font-weight: 600;
            padding: 2px 8px;
            border-radius: 20px;
        }}

        /* 搜索和过滤控制器 */
        .controls-section {{
            display: flex;
            align-items: center;
            gap: 20px;
        }}

        .search-wrapper {{
            position: relative;
        }}

        .search-input {{
            background: rgba(15, 23, 42, 0.6);
            border: 1px solid var(--glass-border);
            color: var(--text-primary);
            padding: 10px 16px 10px 40px;
            border-radius: 30px;
            font-size: 14px;
            width: 280px;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        }}

        .search-input:focus {{
            outline: none;
            border-color: #6366f1;
            box-shadow: 0 0 15px rgba(99, 102, 241, 0.25);
            width: 340px;
        }}

        .search-wrapper i {{
            position: absolute;
            left: 15px;
            top: 50%;
            transform: translateY(-50%);
            color: var(--text-secondary);
            pointer-events: none;
        }}

        .select-filter {{
            background: rgba(15, 23, 42, 0.6);
            border: 1px solid var(--glass-border);
            color: var(--text-primary);
            padding: 10px 16px;
            border-radius: 30px;
            font-size: 14px;
            cursor: pointer;
            outline: none;
            transition: all 0.3s ease;
        }}

        .select-filter:focus {{
            border-color: #6366f1;
        }}

        /* 维度分类切换控制器样式 */
        .dimension-switcher {{
            display: flex;
            background: rgba(15, 23, 42, 0.4);
            border: 1px solid var(--glass-border);
            padding: 3px;
            border-radius: 30px;
            gap: 4px;
            margin-right: 15px;
        }}

        .dimension-btn {{
            background: transparent;
            border: none;
            color: var(--text-secondary);
            padding: 8px 16px;
            border-radius: 20px;
            font-size: 13px;
            font-weight: 600;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 8px;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        }}

        .dimension-btn:hover {{
            color: var(--text-primary);
            background: rgba(255, 255, 255, 0.05);
        }}

        .dimension-btn.active {{
            background: linear-gradient(135deg, #6366f1 0%, #a855f7 100%);
            color: #ffffff;
            box-shadow: 0 4px 12px rgba(99, 102, 241, 0.3);
        }}

        /* 主体布局大屏容器 */
        .main-container {{
            max-width: 1600px;
            margin: 30px auto 0 auto;
            padding: 0 40px;
        }}

        .family-overview {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}

        .family-card {{
            background: var(--glass-bg);
            border: 1px solid rgba(99, 102, 241, 0.25);
            border-radius: 18px;
            padding: 20px;
        }}

        .family-card h3 {{ margin-bottom: 8px; }}
        .family-card p {{ color: var(--text-secondary); font-size: 13px; line-height: 1.5; }}
        .family-meta {{ margin-top: 14px; display: grid; gap: 8px; font-size: 12px; color: #cbd5e1; }}
        .family-member {{ padding: 7px 9px; background: rgba(0, 0, 0, 0.18); border-radius: 8px; }}
        .family-owner {{ color: #a5b4fc; }}

        /* 仪表盘统计面板 (KPIs Deck) */
        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 24px;
            margin-bottom: 40px;
        }}

        .metric-card {{
            background: var(--glass-bg);
            backdrop-filter: blur(10px);
            -webkit-backdrop-filter: blur(10px);
            border: 1px solid var(--glass-border);
            border-radius: 20px;
            padding: 24px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            transition: all 0.4s ease;
            position: relative;
            overflow: hidden;
        }}

        .metric-card:hover {{
            transform: translateY(-5px);
            border-color: var(--glass-hover-border);
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3), 0 0 20px var(--accent-glow);
        }}

        .metric-card::after {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: linear-gradient(45deg, transparent, rgba(255, 255, 255, 0.03), transparent);
            transform: translateX(-100%);
            transition: 0.6s;
        }}

        .metric-card:hover::after {{
            transform: translateX(100%);
        }}

        .metric-label {{
            font-size: 14px;
            color: var(--text-secondary);
            font-weight: 600;
            margin-bottom: 6px;
        }}

        .metric-value {{
            font-size: 32px;
            font-weight: 800;
            color: #ffffff;
            letter-spacing: -0.5px;
        }}

        .metric-icon {{
            font-size: 36px;
            background: linear-gradient(135deg, #818cf8 0%, #c084fc 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            opacity: 0.8;
        }}

        .metric-icon.warn {{
            background: linear-gradient(135deg, #f59e0b 0%, #ef4444 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}

        /* 看板布局主干 (Kanban Board Columns) */
        .kanban-board {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 24px;
            align-items: start;
        }}

        .kanban-column {{
            background: rgba(15, 23, 42, 0.3);
            border: 1px solid rgba(255, 255, 255, 0.03);
            border-radius: 24px;
            padding: 20px;
            min-height: 600px;
            transition: border-color 0.3s ease;
        }}

        .kanban-column-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
            padding-bottom: 12px;
            border-bottom: 1px dashed rgba(255, 255, 255, 0.08);
        }}

        .column-title-wrapper {{
            display: flex;
            align-items: center;
            gap: 10px;
        }}

        .column-icon {{
            font-size: 16px;
            color: #818cf8;
        }}

        .column-title {{
            font-size: 16px;
            font-weight: 700;
            letter-spacing: 0.5px;
            color: #f1f5f9;
        }}

        .column-badge {{
            background: rgba(255, 255, 255, 0.06);
            color: var(--text-secondary);
            font-size: 12px;
            font-weight: 600;
            padding: 2px 8px;
            border-radius: 12px;
        }}

        /* 规则卡片 (Rule Card CSS) */
        .cards-list {{
            display: flex;
            flex-direction: column;
            gap: 16px;
            min-height: 100px;
        }}

        .rule-card {{
            background: var(--glass-bg);
            backdrop-filter: blur(10px);
            -webkit-backdrop-filter: blur(10px);
            border: 1px solid var(--glass-border);
            border-radius: 16px;
            padding: 18px;
            cursor: pointer;
            transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
            position: relative;
        }}

        .rule-card:hover {{
            transform: translateY(-4px) scale(1.02);
            border-color: var(--glass-hover-border);
            box-shadow: 0 12px 24px rgba(0, 0, 0, 0.4), 0 0 10px rgba(99, 102, 241, 0.1);
        }}

        /* 卡片头部 */
        .card-header {{
            display: flex;
            justify-content: space-between;
            align-items: start;
            gap: 10px;
            margin-bottom: 12px;
        }}

        .card-title {{
            font-size: 14px;
            font-weight: 700;
            color: #f1f5f9;
            line-height: 1.4;
            display: -webkit-box;
            -webkit-line-clamp: 1;
            -webkit-box-orient: vertical;
            overflow: hidden;
        }}

        .source-badge {{
            font-size: 10px;
            font-weight: 600;
            padding: 2px 6px;
            border-radius: 6px;
            white-space: nowrap;
        }}

        .source-badge.custom {{
            background: rgba(99, 102, 241, 0.15);
            color: #818cf8;
            border: 1px solid rgba(99, 102, 241, 0.2);
        }}

        .source-badge.registry {{
            background: rgba(168, 85, 247, 0.15);
            color: #c084fc;
            border: 1px solid rgba(168, 85, 247, 0.2);
        }}

        /* 卡片功能描述 */
        .card-desc {{
            font-size: 12px;
            color: var(--text-secondary);
            line-height: 1.5;
            margin-bottom: 14px;
            display: -webkit-box;
            -webkit-line-clamp: 2;
            -webkit-box-orient: vertical;
            overflow: hidden;
        }}

        /* 健康评分条 */
        .score-bar-section {{
            margin-bottom: 14px;
        }}

        .score-row {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 11px;
            font-weight: 600;
            margin-bottom: 5px;
        }}

        .score-label {{
            color: var(--text-secondary);
        }}

        .score-value-text {{
            font-weight: 700;
        }}

        .score-progress-bg {{
            height: 6px;
            background: rgba(255, 255, 255, 0.05);
            border-radius: 4px;
            overflow: hidden;
        }}

        .score-progress-fill {{
            height: 100%;
            border-radius: 4px;
            transition: width 1s ease-in-out;
        }}

        /* 维护建议区域 */
        .suggestion-box {{
            background: rgba(0, 0, 0, 0.15);
            border-radius: 8px;
            padding: 8px 10px;
            font-size: 11px;
            line-height: 1.4;
            display: flex;
            gap: 6px;
            align-items: flex-start;
        }}

        .suggestion-indicator {{
            width: 8px;
            height: 8px;
            border-radius: 50%;
            margin-top: 3px;
            flex-shrink: 0;
        }}

        .suggestion-text {{
            color: #cbd5e1;
        }}

        /* 标签集 */
        .tags-wrapper {{
            display: flex;
            flex-wrap: wrap;
            gap: 6px;
            margin-top: 12px;
        }}

        .tag-pill {{
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid rgba(255, 255, 255, 0.05);
            color: var(--text-secondary);
            font-size: 10px;
            padding: 1px 6px;
            border-radius: 4px;
        }}

        /* 对健康度颜色的专属应用 */
        /* Healthy (>=8.5) */
        .rule-card.healthy .score-value-text {{ color: var(--color-healthy); }}
        .rule-card.healthy .score-progress-fill {{
            background: var(--color-healthy);
            box-shadow: 0 0 8px var(--color-healthy-glow);
        }}
        .rule-card.healthy .suggestion-indicator {{
            background: var(--color-healthy);
            box-shadow: 0 0 6px var(--color-healthy);
        }}
        .rule-card.healthy:hover {{ border-color: rgba(16, 185, 129, 0.3); }}

        /* Warning (>=5.0) */
        .rule-card.warning .score-value-text {{ color: var(--color-warning); }}
        .rule-card.warning .score-progress-fill {{
            background: var(--color-warning);
            box-shadow: 0 0 8px var(--color-warning-glow);
        }}
        .rule-card.warning .suggestion-indicator {{
            background: var(--color-warning);
            box-shadow: 0 0 6px var(--color-warning);
        }}
        .rule-card.warning:hover {{ border-color: rgba(245, 158, 11, 0.3); }}

        /* Critical (<5.0) */
        .rule-card.critical .score-value-text {{ color: var(--color-critical); }}
        .rule-card.critical .score-progress-fill {{
            background: var(--color-critical);
            box-shadow: 0 0 8px var(--color-critical-glow);
        }}
        .rule-card.critical .suggestion-indicator {{
            background: var(--color-critical);
            box-shadow: 0 0 6px var(--color-critical);
        }}
        .rule-card.critical:hover {{
            border-color: rgba(239, 68, 68, 0.4);
            box-shadow: 0 12px 24px rgba(0, 0, 0, 0.4), 0 0 15px var(--color-critical-glow);
        }}

        /* Archived (Status = disabled) */
        .rule-card.archived .score-value-text {{ color: var(--color-archived); }}
        .rule-card.archived .score-progress-fill {{
            background: var(--color-archived);
            box-shadow: 0 0 8px var(--color-archived-glow);
        }}
        .rule-card.archived .suggestion-indicator {{
            background: var(--color-archived);
            box-shadow: 0 0 6px var(--color-archived);
        }}
        .rule-card.archived:hover {{ border-color: rgba(100, 116, 139, 0.3); }}
        .rule-card.archived {{ opacity: 0.65; }}

        /* 规则查看器 Modal 弹窗 */
        .modal-overlay {{
            position: fixed;
            top: 0;
            left: 0;
            width: 100vw;
            height: 100vh;
            background: rgba(2, 6, 23, 0.7);
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            z-index: 1000;
            display: flex;
            justify-content: center;
            align-items: center;
            opacity: 0;
            pointer-events: none;
            transition: opacity 0.3s ease;
        }}

        .modal-overlay.active {{
            opacity: 1;
            pointer-events: all;
        }}

        .modal-container {{
            background: rgba(15, 23, 42, 0.85);
            border: 1px solid var(--glass-hover-border);
            border-radius: 24px;
            width: 900px;
            max-width: 95%;
            height: 80vh;
            display: flex;
            flex-direction: column;
            box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.6), 0 0 40px rgba(99, 102, 241, 0.15);
            transform: scale(0.9);
            transition: transform 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
        }}

        .modal-overlay.active .modal-container {{
            transform: scale(1);
        }}

        .modal-header {{
            padding: 24px 30px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.08);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}

        .modal-title-area {{
            display: flex;
            align-items: center;
            gap: 15px;
        }}

        .modal-title {{
            font-size: 20px;
            font-weight: 700;
            color: #ffffff;
        }}

        .close-btn {{
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.08);
            color: var(--text-primary);
            width: 40px;
            height: 40px;
            border-radius: 50%;
            display: flex;
            justify-content: center;
            align-items: center;
            cursor: pointer;
            transition: all 0.2s ease;
        }}

        .close-btn:hover {{
            background: rgba(239, 68, 68, 0.15);
            border-color: rgba(239, 68, 68, 0.4);
            color: #ef4444;
            transform: rotate(90deg);
        }}

        .modal-body {{
            flex-grow: 1;
            overflow-y: auto;
            padding: 30px;
        }}

        .modal-meta-grid {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 20px;
            margin-bottom: 30px;
            background: rgba(0, 0, 0, 0.2);
            border-radius: 16px;
            padding: 16px 24px;
        }}

        .meta-item-label {{
            font-size: 11px;
            color: var(--text-secondary);
            font-weight: 600;
            margin-bottom: 4px;
            text-transform: uppercase;
        }}

        .meta-item-value {{
            font-size: 14px;
            font-weight: 700;
            color: #cbd5e1;
        }}

        .modal-content-markdown {{
            background: rgba(0, 0, 0, 0.3);
            border: 1px solid rgba(255, 255, 255, 0.03);
            border-radius: 16px;
            padding: 24px;
            font-family: 'Courier New', Courier, monospace;
            font-size: 13px;
            line-height: 1.6;
            color: #cbd5e1;
            white-space: pre-wrap;
            overflow-x: auto;
        }}

        /* 隐藏的空白信息状态 */
        .empty-state {{
            display: none;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            padding: 40px 20px;
            color: var(--text-secondary);
            text-align: center;
        }}

        .empty-state i {{
            font-size: 40px;
            margin-bottom: 12px;
            color: rgba(255, 255, 255, 0.15);
        }}
    </style>
</head>
<body>

    <!-- 顶部导航栏 -->
    <header>
        <div class="logo-section">
            <i class="fa-solid fa-brain logo-icon"></i>
            <span class="logo-title">PGRMS</span>
            <span class="logo-badge">规则看板</span>
        </div>
        
        <div class="controls-section">
            <!-- 维度分类选择器 -->
            <div class="dimension-switcher">
                <button class="dimension-btn active" id="btn-func" onclick="switchDimension('functions')">
                    <i class="fa-solid fa-folder-tree"></i> 功能分类
                </button>
                <button class="dimension-btn" id="btn-src" onclick="switchDimension('sources')">
                    <i class="fa-solid fa-code-branch"></i> 来源分类
                </button>
                <button class="dimension-btn" id="btn-family" onclick="switchDimension('families')">
                    <i class="fa-solid fa-diagram-project"></i> 技能族
                </button>
            </div>

            <!-- 模糊搜索框 -->
            <div class="search-wrapper">
                <i class="fa-solid fa-magnifying-glass"></i>
                <input type="text" id="searchInput" class="search-input" placeholder="输入技术标签或关键字模糊过滤...">
            </div>
            
            <!-- 状态过滤器 -->
            <select id="statusFilter" class="select-filter">
                <option value="all">所有激活状态</option>
                <option value="active">仅显示已启用</option>
                <option value="disabled">仅显示已停用</option>
            </select>

            <select id="familyFilter" class="select-filter">
                <option value="all">全部技能族</option>
                <option value="ungrouped">未分组</option>
            </select>

            <!-- 评分排序器 -->
            <select id="scoreSort" class="select-filter">
                <option value="default">默认规则ID排序</option>
                <option value="desc">按健康评分由高到低</option>
                <option value="asc">按健康评分由低到高</option>
            </select>
        </div>
    </header>

    <div class="main-container">
        <!-- 仪表盘统计面板 (KPIs Deck) -->
        <section class="metrics-grid">
            <div class="metric-card">
                <div>
                    <div class="metric-label">已注册规则总数</div>
                    <div class="metric-value" id="kpiTotal">{total_count}</div>
                </div>
                <i class="fa-solid fa-layer-group metric-icon"></i>
            </div>
            <div class="metric-card">
                <div>
                    <div class="metric-label">当前已启用规则</div>
                    <div class="metric-value" id="kpiActive">{active_count}</div>
                </div>
                <i class="fa-solid fa-circle-check metric-icon"></i>
            </div>
            <div class="metric-card">
                <div>
                    <div class="metric-label">全库平均健康分</div>
                    <div class="metric-value" id="kpiAvgScore">{avg_score:.2f}</div>
                </div>
                <i class="fa-solid fa-gauge-high metric-icon"></i>
            </div>
            <div class="metric-card">
                <div>
                    <div class="metric-label">严重警告亚健康数</div>
                    <div class="metric-value" id="kpiCritical" style="color: { '#ef4444' if critical_count > 0 else '#ffffff' }">{critical_count}</div>
                </div>
                <i class="fa-solid fa-triangle-exclamation metric-icon warn"></i>
            </div>
        </section>

        <section class="family-overview" id="familyOverview"></section>

        <!-- 看板大屏主体（动态渲染容器） -->
        <main class="kanban-board" id="kanbanBoard"></main>
    </div>

    <!-- 规则查看器 Modal 弹窗 -->
    <div class="modal-overlay" id="modalOverlay">
        <div class="modal-container">
            <div class="modal-header">
                <div class="modal-title-area">
                    <i class="fa-solid fa-book-open-reader logo-icon"></i>
                    <span class="modal-title" id="modalTitle">规则标题</span>
                    <span class="source-badge" id="modalSourceBadge">原创</span>
                </div>
                <div class="close-btn" id="modalCloseBtn">
                    <i class="fa-solid fa-xmark"></i>
                </div>
            </div>
            
            <div class="modal-body">
                <div class="modal-meta-grid">
                    <div>
                        <div class="meta-item-label">规则标识 (Identifier)</div>
                        <div class="meta-item-value" id="metaId">unknown</div>
                    </div>
                    <div>
                        <div class="meta-item-label">健康评分 (Score)</div>
                        <div class="meta-item-value" id="metaScore">10.0 / 10.0</div>
                    </div>
                    <div>
                        <div class="meta-item-label">维护建议 (Suggestion)</div>
                        <div class="meta-item-value" id="metaSuggestion">暂无建议</div>
                    </div>
                </div>
                <div class="modal-content-markdown" id="modalMarkdown">
                    加载中...
                </div>
            </div>
        </div>
    </div>

    <!-- 插入规则数据与核心逻辑 -->
    <script>
        // 从 Python 端注入序列化好的全量规则 JSON 数组
        const rulesData = {rules_json};
        const familiesData = {families_json};
        
        // 简易安全 HTML 转义工具函数，防范源文件注入 XSS
        function escapeHTML(str) {{
            if (!str) return '';
            return str.replace(/[&<>'"]/g, 
                tag => ({{
                    '&': '&amp;',
                    '<': '&lt;',
                    '>': '&gt;',
                    "'": '&#39;',
                    '"': '&quot;'
                }}[tag] || tag)
            );
        }}

        // 获取 DOM 节点
        const searchInput = document.getElementById('searchInput');
        const statusFilter = document.getElementById('statusFilter');
        const familyFilter = document.getElementById('familyFilter');
        const scoreSort = document.getElementById('scoreSort');
        const modalOverlay = document.getElementById('modalOverlay');
        const modalCloseBtn = document.getElementById('modalCloseBtn');
        
        let currentDimension = 'functions';
        
        const COLUMN_CONFIGS = {{
            functions: [
                {{ id: 'engineering', title: '软件工程 (Engineering)', icon: 'fa-code' }},
                {{ id: 'design', title: '艺术设计 (Design)', icon: 'fa-palette' }},
                {{ id: 'productivity', title: '办公效率 (Productivity)', icon: 'fa-bolt' }},
                {{ id: 'registry', title: '外部引入 (Registry)', icon: 'fa-globe' }}
            ],
            sources: [
                {{ id: 'custom', title: '个人自建规则 (Custom Rules)', icon: 'fa-user-gear' }},
                {{ id: 'registry', title: '第三方引入规则 (Third-Party Rules)', icon: 'fa-cloud-arrow-down' }}
            ],
            families: [
                ...familiesData.map(family => ({{ id: family.id, title: family.title, icon: 'fa-diagram-project' }})),
                {{ id: 'ungrouped', title: '未分组技能 (Ungrouped)', icon: 'fa-layer-group' }}
            ]
        }};

        function initializeFamilyUI() {{
            familiesData.forEach(family => {{
                const option = document.createElement('option');
                option.value = family.id;
                option.textContent = family.title;
                familyFilter.appendChild(option);
            }});

            const overview = document.getElementById('familyOverview');
            overview.innerHTML = familiesData.map(family => {{
                const memberHtml = family.members.map(member => {{
                    const dependencies = member.depends_on.length ? ' → ' + member.depends_on.join(', ') : '';
                    return '<div class="family-member"><strong>' + escapeHTML(member.skill) + '</strong> [' + escapeHTML(member.kind) + '] — ' + escapeHTML(member.role) + escapeHTML(dependencies) + '</div>';
                }}).join('');
                const owners = Object.entries(family.ownership).map(([topic, owner]) => escapeHTML(topic) + ': ' + escapeHTML(owner)).join(' · ');
                return '<article class="family-card"><h3>' + escapeHTML(family.title) + '</h3><p>' + escapeHTML(family.description) + '</p><div class="family-meta">' + memberHtml + '<div class="family-owner">知识归属：' + owners + '</div><div>校验：' + escapeHTML(family.validation.status) + '</div></div></article>';
            }}).join('');
        }}
        
        function switchDimension(dimension) {{
            if (currentDimension === dimension) return;
            currentDimension = dimension;
            
            document.getElementById('btn-func').classList.toggle('active', dimension === 'functions');
            document.getElementById('btn-src').classList.toggle('active', dimension === 'sources');
            document.getElementById('btn-family').classList.toggle('active', dimension === 'families');
            document.getElementById('familyOverview').style.display = dimension === 'families' ? 'grid' : 'none';
            
            renderBoard();
        }}
        
        // 渲染与交互机制核心
        function renderBoard() {{
            const searchKeyword = searchInput.value.toLowerCase().trim();
            const selectedStatus = statusFilter.value;
            const selectedFamily = familyFilter.value;
            const sortOrder = scoreSort.value;
            
            const board = document.getElementById('kanbanBoard');
            board.innerHTML = '';
            
            const cols = COLUMN_CONFIGS[currentDimension];
            board.style.gridTemplateColumns = "repeat(" + cols.length + ", 1fr)";
            
            // 1. 动态生成列容器 DOM 结构
            cols.forEach(col => {{
                const colSec = document.createElement('section');
                colSec.className = 'kanban-column';
                colSec.id = 'col-' + col.id;
                colSec.innerHTML = '<div class="kanban-column-header"><div class="column-title-wrapper"><i class="fa-solid ' + col.icon + ' column-icon"></i><span class="column-title">' + col.title + '</span></div><span class="column-badge" id="badge-' + col.id + '">0</span></div><div class="cards-list" id="list-' + col.id + '"></div><div class="empty-state" id="empty-' + col.id + '"><i class="fa-solid fa-box-open"></i><div>当前分类下无匹配规则</div></div>';
                board.appendChild(colSec);
            }});
            
            // 2. 规则数据过滤与排序
            let filteredRules = [...rulesData];
            
            // 过滤：关键词检索
            if (searchKeyword) {{
                filteredRules = filteredRules.filter(rule => {{
                    const titleMatch = rule.title.toLowerCase().includes(searchKeyword);
                    const descMatch = rule.description.toLowerCase().includes(searchKeyword);
                    const idMatch = rule.name.toLowerCase().includes(searchKeyword);
                    const tagsMatch = rule.tags.some(tag => tag.toLowerCase().includes(searchKeyword));
                    const familyMatch = (rule.family || 'ungrouped').toLowerCase().includes(searchKeyword);
                    return titleMatch || descMatch || idMatch || tagsMatch || familyMatch;
                }});
            }}

            if (selectedFamily !== 'all') {{
                filteredRules = filteredRules.filter(rule => (rule.family || 'ungrouped') === selectedFamily);
            }}
            
            // 过滤：状态筛选
            if (selectedStatus !== 'all') {{
                filteredRules = filteredRules.filter(rule => rule.status === selectedStatus);
            }}
            
            // 排序：健康分
            if (sortOrder === 'desc') {{
                filteredRules.sort((a, b) => b.score - a.score);
            }} else if (sortOrder === 'asc') {{
                filteredRules.sort((a, b) => a.score - b.score);
            }} else {{
                // 默认按 ID 字母表排序
                filteredRules.sort((a, b) => a.name.localeCompare(b.name));
            }}
            
            // 3. 更新总体 KPI 大屏
            const activeRules = filteredRules.filter(r => r.status === 'active');
            document.getElementById('kpiTotal').innerText = filteredRules.length;
            document.getElementById('kpiActive').innerText = activeRules.length;
            
            let sumScore = 0;
            let criticalCount = 0;
            filteredRules.forEach(r => {{
                sumScore += r.score;
                if (r.status === 'active' && r.score < 5.0) {{
                    criticalCount++;
                }}
            }});
            const avg = filteredRules.length > 0 ? (sumScore / filteredRules.length).toFixed(2) : "0.00";
            document.getElementById('kpiAvgScore').innerText = avg;
            
            const kpiCritical = document.getElementById('kpiCritical');
            kpiCritical.innerText = criticalCount;
            kpiCritical.style.color = criticalCount > 0 ? '#ef4444' : '#ffffff';
            
            // 4. 将卡片分配入动态创建的列中
            let colCounts = {{}};
            cols.forEach(col => colCounts[col.id] = 0);
            
            filteredRules.forEach(rule => {{
                let targetColId = '';
                if (currentDimension === 'functions') {{
                    targetColId = rule.source_type === 'registry' ? 'registry' : rule.category;
                }} else if (currentDimension === 'sources') {{
                    targetColId = rule.source_type; // 'custom' or 'registry'
                }} else {{
                    targetColId = rule.family || 'ungrouped';
                }}
                
                const colList = document.getElementById('list-' + targetColId);
                if (colList) {{
                    colCounts[targetColId]++;
                    const card = createRuleCard(rule);
                    colList.appendChild(card);
                }}
            }});
            
            // 5. 更新每列徽章与空白状态显示
            cols.forEach(col => {{
                document.getElementById('badge-' + col.id).innerText = colCounts[col.id];
                const emptyState = document.getElementById('empty-' + col.id);
                if (colCounts[col.id] === 0) {{
                    emptyState.style.display = 'flex';
                }} else {{
                    emptyState.style.display = 'none';
                }}
            }});
        }}
        
        // 动态创建卡片 DOM 元素
        function createRuleCard(rule) {{
            const div = document.createElement('div');
            let healthClass = rule.health_status; // healthy, warning, critical, archived
            div.className = 'rule-card ' + healthClass;
            
            const srcText = rule.source_type === 'custom' ? '原创' : '第三方';
            const srcClass = rule.source_type;
            const progressWidth = rule.status === 'disabled' ? 0 : rule.score * 10;
            
            const familyTag = '<span class="tag-pill">family: ' + escapeHTML(rule.family || 'ungrouped') + '</span>';
            const tagsHtml = familyTag + rule.tags.map(tag => '<span class="tag-pill">' + escapeHTML(tag) + '</span>').join('');
            
            div.innerHTML = '<div class="card-header"><span class="card-title" title="' + escapeHTML(rule.title) + '">' + escapeHTML(rule.title) + '</span><span class="source-badge ' + srcClass + '">' + srcText + '</span></div><div class="card-desc">' + escapeHTML(rule.description) + '</div><div class="score-bar-section"><div class="score-row"><span class="score-label">健康评分</span><span class="score-value-text">' + rule.score.toFixed(1) + '</span></div><div class="score-progress-bg"><div class="score-progress-fill" style="width: ' + progressWidth + '%"></div></div></div><div class="suggestion-box"><div class="suggestion-indicator"></div><div class="suggestion-text">' + escapeHTML(rule.suggestion) + '</div></div><div class="tags-wrapper">' + tagsHtml + '</div>';
            
            div.addEventListener('click', () => showRuleDetail(rule));
            
            return div;
        }}
        
        // 呼出 Modal 详情弹窗并填充内容
        function showRuleDetail(rule) {{
            document.getElementById('modalTitle').innerText = rule.title;
            document.getElementById('metaId').innerText = rule.name;
            
            const scoreVal = document.getElementById('metaScore');
            scoreVal.innerText = rule.score.toFixed(2) + " / 10.0";
            
            if (rule.status === 'disabled') {{
                scoreVal.style.color = 'var(--color-archived)';
            }} else if (rule.score >= 8.5) {{
                scoreVal.style.color = 'var(--color-healthy)';
            }} else if (rule.score >= 5.0) {{
                scoreVal.style.color = 'var(--color-warning)';
            }} else {{
                scoreVal.style.color = 'var(--color-critical)';
            }}
            
            document.getElementById('metaSuggestion').innerText = rule.suggestion;
            document.getElementById('modalMarkdown').textContent = rule.full_content;
            
            const srcText = rule.source_type === 'custom' ? '原创' : '第三方';
            const badge = document.getElementById('modalSourceBadge');
            badge.innerText = srcText;
            badge.className = 'source-badge ' + rule.source_type;
            
            modalOverlay.classList.add('active');
        }}
        
        // 关闭 Modal 详情
        function closeModal() {{
            modalOverlay.classList.remove('active');
        }}
        
        // 注册控制监听事件
        searchInput.addEventListener('input', renderBoard);
        statusFilter.addEventListener('change', renderBoard);
        familyFilter.addEventListener('change', renderBoard);
        scoreSort.addEventListener('change', renderBoard);
        modalCloseBtn.addEventListener('click', closeModal);
        
        // 点击弹窗遮罩空白处，关闭弹窗
        modalOverlay.addEventListener('click', (e) => {{
            if (e.target === modalOverlay) {{
                closeModal();
            }}
        }});
        
        // 按 ESC 键关闭弹窗
        document.addEventListener('keydown', (e) => {{
            if (e.key === 'Escape' && modalOverlay.classList.contains('active')) {{
                closeModal();
            }}
        }});

        // 首次加载看板渲染
        window.addEventListener('DOMContentLoaded', () => {{
            initializeFamilyUI();
            document.getElementById('familyOverview').style.display = 'none';
            renderBoard();
        }});
    </script>
</body>
</html>
"""
    
    # 写入 dashboard.html 文件中
    try:
        with open(output_file, "w", encoding="utf-8-sig") as f:
            f.write(html_template)
        print(f"看板大屏生成成功！已成功输出并同步至: {output_file}")
    except Exception as e:
        print(f"写入看板 dashboard.html 失败: {str(e)}")

if __name__ == "__main__":
    import sys
    import io
    if sys.platform.startswith("win"):
        # 强制将标准输出和错误输出指定为 UTF-8 编码，防止 Windows 控制台因 GBK 代码页打印中文或特殊符号报错、乱码
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
    generate_html_dashboard()
