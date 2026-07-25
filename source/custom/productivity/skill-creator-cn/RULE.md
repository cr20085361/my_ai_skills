---
name: skill-creator-cn
description: 创建、修改、改进 skill，并衡量其表现。当用户想从零做一个 skill、改进/调试已有 skill、把刚才对话里的流程"变成 skill"、或说"我想做个 skill 但不知道怎么做""帮我做个 skill"时使用。也适用于优化 skill 的触发描述、跑评测。Use when the user wants to create, edit, debug, or evaluate a skill (Chinese or English).
category: productivity
audience: codex-project
tags: [skill, chinese]
status: active
score: 10.0
---

# Skill Creator

## 语言与水平指令

**默认用中文与用户交流，跟随用户的语言切换**（用户改用英文则跟着切换）。

全程自动识别用户的技术水平，**不要打断流程询问"你是什么水平"**——通过用户的措辞、上下文自动判断，并相应调整用词深度：
- 用户说"我不懂代码""帮我做一个自动化"→ 用日常语言，避免裸露的 JSON/assertion/eval 等术语（或用时简要解释）。
- 用户说"写个 SKILL.md""跑 eval"→ 可直接使用技术术语。
- 中间态：术语按需解释，不过度科普也不假设对方都懂。

详细的水平信号识别与提问节奏，见 `references/需求共创.md`。

---

## ① 前置 Triage（闸门）

在进入任何创建/改进流程之前，先做三个快速判断：

### 1. 这要不要做成 skill？

判断标准：
- **一次性任务**：用户只要做一次，做完就不用了 → 直接帮做，不必做成 skill。
- **普通 prompt 够用**：Claude 不需要任何 skill 也能胜任 → 直说，不必做 skill。
- **Claude 原生能干**：内置能力已覆盖，skill 不会带来额外价值 → 坦诚建议不必做。
- **更适合 slash command 或 subagent**：任务是一次性调度或编排多个步骤，而非可复用流程 → 说明区别，建议替代方案。

**命中后怎么做**：坦诚告诉用户"这种情况不一定需要做成 skill，因为……"，并提供直接帮助或替代建议。

### 2. 有没有现成类似的？

判断方法：扫一眼用户环境里已有的 skills 列表（`available_skills`），看有没有功能高度重叠的。

**命中后怎么做**：告知用户已有类似 skill，建议先试用，或在现有 skill 上改进，而非重新造轮子。

### 3. 范围太大？

判断标准：用户描述的需求实际上涵盖了多个独立的、可拆分的工作流程。

**命中后怎么做**：提醒用户"这其实是好几个 skill，建议拆开来做"，本工具不会自动批量生成多套 skill，每次聚焦一个。

---

## ② 入口识别与路由

通过用户的描述，判断属于哪个入口，然后跳转对应分支：

| 入口 | 用户大概这样说 | 跳转 |
|------|--------------|------|
| **E1 模糊想法** | "我想做个 skill""帮我自动化 XX""我有个想法但不知道怎么做" | → `references/需求共创.md` |
| **E2 从对话提取** | "把我们刚才做的变成 skill""提取这个流程""这次对话做成 skill" | → `references/需求共创.md`（从 transcript 抽步骤/工具/纠正 → 回填四要素） |
| **E3 现有材料** | "我有个文档/流程图/SOP""给你几对输入输出示例，照着做""参考这个来做 skill" | → `references/需求共创.md`（分析材料/示例 → 提炼四要素 → 补缺） |
| **E4 已有草稿** | "我写了个 SKILL.md 草稿""帮我完善这个 skill" | → `references/需求共创.md`（读懂草稿 → 补缺 → 进打磨循环） |
| **E5 改进/调试** | "这个 skill 不触发""触发错了""效果跑偏""太慢太重" | → `references/改进调试.md` |

**E1/E2/E3/E4** 均路由到 `references/需求共创.md`，按各自情境执行对应段落。**E5** 路由到 `references/改进调试.md`，按诊断 playbook 执行。

---

## 创建流程地图（全局视图）

以下是整体流程的全局视图，确保你在每个阶段都知道"下一步去哪"：

```
① 前置 Triage（闸门）
   · 这要不要做成 skill？ → 一次性/普通 prompt 够/Claude 原生能干/
                            更适合 slash command·subagent → 直说不必
   · 有没有现成类似的？   → 扫一眼已有 skills，别重复造
   · 范围太大？          → 提醒"这其实是好几个 skill"
        │
        ▼
② 识别入口，跳对应分支（两类，分别走不同路）
   ▸ 创建类 E1 模糊想法 / E2 从对话 / E3 现有材料 / E4 已有草稿
        └─→ references/需求共创.md（四要素 / 水平信号 / 材料·输入输出例子分析）
                 │ 四要素挖掘完
                 ▼
            ✦ 确认门：把四要素回述给用户、获批才开写（见 需求共创.md 第六节）──┐
   ▸ 改进类 E5 改进/调试                                                        │
        └─→ references/改进调试.md（诊断：不触发/行为跑偏/过欠触发/太重；不经确认门）─┤
                                                                                 ▼
③ 共有打磨循环（见下文"起草 SKILL.md"及后续章节）
   起草 SKILL.md（含 description；顺带确认 依赖/工具/MCP 可用性）
   → 验证【分层：轻量"跑给你看"默认 / 重型量化评测可选】
   → 看结果 → 改 → 重跑 → 满意为止 → 打磨 description 触发
        │
        ▼
④ 最后一公里 → references/最后一公里.md（放哪/确认装上/自测触发/打包）
```

---

## ③ 共有打磨循环：起草、验证与迭代

### 起草 SKILL.md

根据需求共创的结果，填写以下几个核心部分：

- **name**：skill 的标识符，保持简洁。
- **description**：这是触发机制——写清楚"什么时候用、做什么"。把所有"何时使用"的信息都放在这里，不要藏在正文里。注意：Claude 有时会"触发不足"（明明适合用却没用），所以描述可以稍微主动一点。比如，别只写"如何构建仪表盘"，而是写"构建仪表盘。当用户提到仪表盘、数据可视化、内部指标、想展示任何公司数据时，即使没有明确说'仪表盘'，也应使用本 skill。"
- **compatibility**：所需工具、依赖（可选，大多数 skill 不需要）。
- **正文**：其余的 skill 说明。

#### skill 的结构

```
skill-name/
├── SKILL.md（必须）
│   ├── YAML frontmatter（name、description 必填）
│   └── Markdown 说明
└── 捆绑资源（可选）
    ├── scripts/    - 确定性/重复性任务的可执行代码
    ├── references/ - 按需加载到上下文的文档
    └── assets/     - 输出中用到的文件（模板、图标、字体）
```

#### 渐进加载机制

Skill 有三级加载层：
1. **元数据**（name + description）——始终在上下文中（约 100 词）
2. **SKILL.md 正文**——skill 触发时进入上下文（理想 <500 行）
3. **捆绑资源**——按需加载（不限大小，scripts 可直接执行无需加载）

关键原则：
- SKILL.md 尽量控制在 500 行以内；接近上限时，增加一层层级并写清楚"下一步去哪里"的指引。
- 在 SKILL.md 中明确引用 reference 文件，注明何时读取。
- reference 文件超过 300 行时，加目录索引。

多领域 skill 按变体组织：
```
cloud-deploy/
├── SKILL.md（流程 + 选择逻辑）
└── references/
    ├── aws.md
    ├── gcp.md
    └── azure.md
```
Claude 只读取相关的 reference 文件。

#### 内容安全

Skill 不得包含恶意代码、漏洞利用代码或任何可能损害系统安全的内容。Skill 的内容不应在描述说明的范围之外给用户带来意外。不要配合制作带有误导性、旨在未授权访问或数据泄露的 skill。角色扮演类需求（如"扮演某个角色"）通常没问题。

#### 写作风格

用祈使句写指令，这样模型更容易执行。

尽量说明"为什么"而不是堆砌 MUST/NEVER 等强制词——当今的 LLM 相当聪明，理解了背后的理由反而比死规定更灵活有效。用心揣摩用户真正想要什么，写出的 skill 要足够通用，不要只针对几个具体例子过拟合。

写完初稿之后，换个视角重读一遍再改——这一步经常能发现自己没意识到的问题。

**输出格式示例：**
```markdown
## 报告结构
始终使用以下模板：
# [标题]
## 执行摘要
## 关键发现
## 建议
```

**示例模式——**在 skill 里放例子很有用：
```markdown
## commit 消息格式
示例：
输入：Added user authentication with JWT tokens
输出：feat(auth): implement JWT-based authentication
```

#### 草稿自检

写完初稿，换个视角重读一遍再交给验证——重点扫四件事：
- **占位与含糊**："TBD""按需处理""适当地……"这类没说清的要求，说清它。
- **自相矛盾**：前后指令、description 与正文有没有打架。
- **范围蔓延**：有没有混进需求里没确认过的功能？砍掉，或回去确认。
- **歧义**：某条要求会不会被理解成两种意思？挑一种、写明确。

发现问题就地改掉，不必反复评审。

---

### 分层验证：默认轻量，进阶可选

验证的目的是确认 skill 的行为是否符合用户预期。根据用户的技术水平和需求，有两条路：

#### 默认：轻量"跑给你看"

起草完 skill 之后，设计 2–3 个真实用户会说出的测试提示词，和用户确认："这几个测试用例看起来对吗？有想加的吗？" 然后**直接运行**，把产出展示给用户看，问"这样对吗？"

这条路零术语、零 JSON——用户看到真实结果，给出直觉反馈，就可以进入下一轮改进。

保存测试用例到 `evals/evals.json`（只保存 prompt，assertion 留给进阶阶段）：

```json
{
  "skill_name": "example-skill",
  "evals": [
    {
      "id": 1,
      "prompt": "用户实际会说的任务描述",
      "expected_output": "期望结果的简要描述",
      "files": []
    }
  ]
}
```

完整 schema（含 `assertions` 字段）见 `references/schemas.md`。

#### 进阶 · 可选：重型量化评测

需要严格的量化对比（benchmark/assertion，跨版本比较）时，读 `references/重型评测.md` 的「重型量化评测」一节。默认绝不把 JSON assertion、benchmark 等概念主动抛给初学用户。

---

### 改进 skill

这是循环的核心。你已经跑完测试用例，用户已经看过结果，现在根据反馈改进 skill。

**怎么思考改进方向：**

- **从反馈里归纳共性**。我们在做的事情是：创建一个能被用一百万次的 skill，而现在只是在几个例子上快速迭代。如果改出来的 skill 只对这几个例子有效，就失去了意义。遇到顽固问题，与其加死规定，不如换个比喻或换种工作模式——代价低，说不定能找到更好的方案。

- **保持 prompt 精简**。去掉没有实际作用的内容。读运行的完整对话记录（transcript），不要只看最终输出——如果 skill 让模型做了很多无效工作，试着删掉导致这些行为的指令，看看结果是否更好。

- **解释"为什么"**。尽量说明你要求模型做某件事背后的理由。今天的 LLM 很聪明，给出了充分理由，它们能举一反三、灵活应对，效果往往比死规定更好。如果你发现自己在写"ALWAYS"或"NEVER"这样的全大写词，那是一个警示信号——尝试改写成解释理由的方式。

- **发现跨用例的重复工作**。读各测试用例的运行记录，看看子代理有没有各自独立写了类似的辅助脚本（比如 3 个用例都写了 `create_docx.py`）。如果有，这是强信号：把这个脚本写好放进 `scripts/`，让 skill 直接调用，省去每次重新造轮子。

改进后，**按你当前走的验证档重跑**（别无脑上重型）：
1. 应用改动到 skill
2. 重新验证：
   - **轻量档（默认）**：重跑那 2–3 个测试提示词，把新产出摆给用户看，问"这版好点了吗？"——不建目录、不跑 baseline。
   - **重型档（进阶）**：跑全部测试用例放入新的 `iteration-<N+1>/` 目录（含 baseline run），启动 eval viewer（`eval-viewer/generate_review.py`）并加 `--previous-workspace` 指向上一轮——细节见 `references/重型评测.md`。
3. 等用户看完反馈
4. 读新反馈，再改，循环

直到：用户说满意、反馈全为空、或已经没有实质进展，停止循环。

---

### 进阶 · 可选：盲评对比

需要更严格地对比两个版本的 skill 时（例如"新版本真的更好吗"），读 `references/重型评测.md` 的「盲评对比」一节。

---

## Description 触发优化

description 字段是 Claude 决定是否调用 skill 的核心机制——它决定 skill 会不会被调用。skill 整体打磨满意后，可以主动提出优化 description 以提升触发准确率。优化时会生成触发评测查询集、让用户确认，然后用 `scripts/run_loop.py` 在后台跑优化循环，自动选出最优 description。

详细流程见 `references/重型评测.md` 的「Description 触发优化」一节。

---

## 打包发布

检查是否有 `present_files` 工具可用。有则打包 skill 并发给用户；没有则跳过。

```bash
python -m scripts.package_skill <path/to/skill-folder>
```

打包后，告知用户 `.skill` 文件的路径。

---

## 平台差异说明

### Claude.ai

核心流程相同（起草 → 测试 → 审阅 → 改进 → 重复），但 Claude.ai 没有子代理，部分机制需要调整：

- **跑测试用例**：不能并发，逐条执行。读 skill 的 SKILL.md，按其指令自己完成测试任务。这不如独立子代理严格（你既写了 skill 又在运行它），但作为合理性检查是有效的——人工审阅可以弥补。跳过 baseline run，只跑带 skill 的版本。
- **展示结果**：如果无法打开浏览器，直接在对话里展示。每个用例显示 prompt 和输出；如果输出是文件（.docx、.xlsx），告知文件位置让用户下载查看；内联征求反馈："这样看起来怎么样？有什么想改的？"
- **量化评测**：跳过——没有子代理就无法做有意义的 baseline 对比。以用户的定性反馈为准。
- **Description 优化**：需要 `claude -p`（仅 Claude Code 可用），Claude.ai 上跳过。
- **盲评对比**：需要子代理，跳过。
- **打包**：`scripts/package_skill.py` 只需 Python 和文件系统，在 Claude.ai 上可用。用户可下载生成的 `.skill` 文件。
- **更新已有 skill**：保留原始 name（目录名和 frontmatter 的 `name` 字段不变）；已安装的 skill 路径可能只读，先复制到 `/tmp/skill-name/` 再编辑，打包时从副本运行。

### Cowork

- 有子代理，主流程（并发测试用例、baseline、评分等）完全可用。遇到严重超时问题可以改串行。
- 没有浏览器/显示器：生成 eval viewer 时用 `--static <output_path>` 输出独立 HTML 文件，给用户提供可点击的链接。
- Cowork 环境下 Claude 有时会跳过生成 viewer 直接评估输出——请务必在让用户审阅结果之前生成 viewer（用 `eval-viewer/generate_review.py`，不要自己写 HTML）。把结果第一时间展示给用户，而不是自己先下结论。
- Feedback：没有运行中的服务器，viewer 的"Submit All Reviews"会下载 `feedback.json`，从那里读取（可能需要先请求访问权限）。
- 打包：`scripts/package_skill.py` 只需 Python 和文件系统，正常工作。
- Description 优化（`scripts/run_loop.py`）在 Cowork 下通过 `claude -p` 子进程运行，不依赖浏览器，应该正常工作；请在 skill 整体完成、用户确认满意后再运行。
- 更新已有 skill：同 Claude.ai 一节的指引。

---

## 内部文件说明

`agents/*.md`、`scripts/*.py`、`references/schemas.md` 是供本 skill 内部使用的子代理指令、脚本和 schema 定义，保持英文原样；它们输出的自由文本（evidence/reasoning/笔记等）由各 agent 文件自身的语言指令控制（默认跟随用户语言）。

`eval-viewer/viewer.html` 和 `assets/eval_review.html` 是**用户可见的 UI**，已中文化，不属于"内部文件"。同理 `scripts/` 里生成用户可见报告的部分（`generate_report.py` 等）也已中文化；脚本里给开发者看的 `print` 状态/错误同样已中文化。

- `agents/grader.md` — 评估 assertion 是否通过
- `agents/comparator.md` — 对两份输出做盲评 A/B 对比
- `agents/analyzer.md` — 分析某版本为何胜出
- `references/schemas.md` — evals.json、grading.json 等的 JSON schema
- `references/需求共创.md` — 需求挖掘引擎（E1–E4 入口）
- `references/改进调试.md` — 改进与调试 playbook（E5 入口）
- `references/最后一公里.md` — 安装、激活、自测、打包
- `references/重型评测.md` — 重型量化评测、盲评对比、Description 触发优化详细流程（进阶可选）

---

## 收尾：最后一公里

当 skill 内容打磨满意、description 触发调优完成后，进入 `references/最后一公里.md`，完成安装激活、自测触发验证和打包发布。
