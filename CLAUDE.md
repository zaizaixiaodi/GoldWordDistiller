# 金词蒸馏器 / GoldWord Distiller

> 一个运行在 Claude Code 下的 CLI Agent，帮助自媒体博主从小红书热贴中蒸馏出**可按位组装的金词与句式**，为选题/标题/封面文案提供原料和模板。

## 0. 必读文档导航

后续模型接手开发前，按下表读取上下文：

| 用途 | 文件 | 说明 |
|------|------|------|
| **顶层指令**（本文件） | `CLAUDE.md` | 项目定位、核心模型、约定 |
| **需求源头** | `项目需求和参考/金词蒸馏器_PRD_v2.md` | 当前以 v2 为准 |
| 历史版本 | `项目需求和参考/金词蒸馏器_PRD_v1.md` | 已废弃，仅供溯源 |
| **开发计划** | `DEVPLAN.md` | 进度看这里，按未勾选任务顺序推进 |
| 开发日志 | `DEVLOG.md` | 按时间倒序，每次 `/done` 追加 |
| 蒸馏 prompt | `prompts/distill.md` | 标题/封面双路 prompt |
| 业务规范回写 | `prompts/observations.md` | 周报元认知反思的沉淀 |

**新会话第一步**：读 `DEVPLAN.md §1 状态总览`，找到第一个未勾选 `[ ]` 的任务执行。

---

## 1. 核心数据模型

### 1.1 输入侧 — 三层词汇模型

- **领域词**（~5个）：博主赛道（搞钱、职场、个人成长、AI 应用、自媒体方法论），手动设定
- **搜索词**（~15个）：每个领域词下 3 个搜索关键词，手动维护
- **金词**：从搜索结果中蒸馏出的高价值表达，agent 核心产出

**驱动链**：领域词 → 搜索词 → TikHub 搜索 → 飞书豆包识图 → agent 蒸馏 → 金词 + 句式

### 1.2 产物侧 — 三层产物模型（v2 核心）

| 层 | 产物 | 频率 | 受众 |
|---|------|------|------|
| **L1 原料层** | 金词库（标题/封面 × 8 功能位） | 每次 /harvest | AI 写手 RAG |
| **L2 骨架层** | 句式库 | 每次 /harvest | AI 写手 RAG |
| **L3 精炼层** | 周报（趋势 + TOP 金词 + 新句式 + 元认知反思） | 每周 | 人 + 回写 AI |

**AI 写手使用流程**：选句式骨架 → 按功能位填金词 → 输出标题/封面文案。

### 1.3 金词功能位（8 类 MECE）

每个金词必须打标 `category`：

| # | 功能位 | 锚 | 例子 |
|---|--------|----|------|
| 1 | 身份标签 | who | 独居女生、INFJ、普通人、学生党 |
| 2 | 场景锚点 | when/where | 下班后、凌晨三点、35 岁前、出租屋 |
| 3 | 痛点/欲望 | pain/want | 早点下班、攒下第一桶金、不想内卷 |
| 4 | 行动召唤 | do | 把手弄脏、立刻删掉、闭嘴去做 |
| 5 | 反常识钩子 | twist | 越懒越赚、3 个月赚 15w 但离职 |
| 6 | 量化锚 | number | 21 天、月入 5 万、第 7 次 |
| 7 | 情绪/状态词 | feel | 班味、松弛感、破防、上头、王炸 |
| 8 | 隐喻具象 | picture | 地毯起号、野路子、卡皮巴拉打工日记 |

**附加字段**：
- `source_field`：title / cover / both（来源字段）
- `vibe_score`：0-10，反常识/隐喻/情绪类天然高分；< 3 不入库
- `suggested_patterns`：关联到句式库

**待回测**（详见 PRD v2 §11）：必填位 vs 加分位分级、第 9 类"工具/IP 名"是否独立。

---

## 2. 目录结构

```
goldword-distiller/
├── CLAUDE.md                       # 本文件 — agent 全局指令
├── DEVLOG.md                       # 开发日志（/done 自动追加）
├── DEVPLAN.md                      # 开发计划（进度看这里）
├── .env                            # 环境变量（不提交 git）
├── .env.example                    # 环境变量模板
├── 项目需求和参考/
│   ├── 金词蒸馏器_PRD_v2.md         # 当前 PRD（v2，以此为准）
│   └── 金词蒸馏器_PRD_v1.md         # 已废弃，仅供溯源
├── .claude/
│   ├── settings.json               # Claude Code 权限配置
│   └── commands/                   # Slash commands
│       ├── done.md                 # /done — DEVLOG + DEVPLAN + git commit & push
│       ├── harvest.md              # /harvest — 立即执行一次完整采集
│       ├── feed.md                 # /feed — 喂入外部素材
│       ├── add.md                  # /add — 手动添加金词（--field/--category）
│       ├── list.md                 # /list — 查看金词（--category/--field/--min-vibe）
│       ├── report.md               # /report — 简报（无参）/ 周报（--weekly）
│       ├── patterns.md             # /patterns — 句式库浏览/管理
│       ├── config.md               # /config — 查看编辑配置
│       ├── sync.md                 # /sync — 手动飞书同步
│       └── schedule.md             # /schedule — 定时任务
├── goldword/
│   ├── config.py                   # 配置管理（环境变量、飞表 ID）
│   ├── harvester.py                # 平台直出：TikHub 搜索 + 表层数据采集 + 封面下载
│   ├── hotlist.py                  # 官方榜单：热榜采集
│   ├── feeder.py                   # 他山之石：手动素材输入
│   ├── distiller.py                # 金词蒸馏（标题/封面双路 + 8 功能位 + vibe_score）
│   ├── tracker.py                  # 趋势追踪（金词 + 句式双路）
│   ├── reporter.py                 # 简报 + 周报（含元认知反思）
│   └── feishu.py                   # 飞书多维表薄封装层（基于 lark-cli）
├── prompts/
│   ├── distill.md                  # 蒸馏 prompt 模板（标题路 + 封面路）
│   └── observations.md             # 业务规范回写文档（人审周报沉淀）
├── reports/                        # 本地周报存档（reports/weekly_YYYY-WNN.md）
├── scripts/
│   ├── probe_tikhub.py             # TikHub 联调脚本
│   ├── probe_feishu.py             # 飞书联调脚本
│   ├── covers/                     # 封面图临时下载与上传脚本
│   └── samples/                    # API 原始返回样本 + 候选金词/句式 dump
└── tests/                          # 单元测试
```

---

## 3. 飞书集成（v2：四张表）

- **工具**：`lark-cli` v1.0.32（飞书官方 CLI，通过 `lark-base` skill 操作多维表）
- **应用**：`cli_aa8d9918c778dbb4`（用户自建「金词」应用）
- **Bitable app_token**：`Z5DubZ9DMaPkgDsbMWScnrgknSz`（嵌在 Wiki 中，**非** URL 中的 wiki token）
- **四张表**：
  - 热贴库 `tblg2nOd7LvMZCKC`（含封面附件 + 封面文案输出结果）
  - 金词库 `tblqAKnCwubtFS0y`（v2 字段已补全：category / source_field / vibe_score / suggested_patterns / domain / trend / status 等 16 字段）
  - 配置表 `tbl7nJSXfjTkreFM`（domain_word / search_keyword / is_active / priority / note）
  - 句式库 `tbl7iu3g51uFw1Ci`（v2 新增：skeleton / category / examples / frequency / trend / recommended_categories 等 9 字段）
- **封面识图**：飞书侧已配置豆包多模态识图字段，对附件 OCR + 语义识别后回填到"封面文案输出结果"字段，agent 侧只需轮询等待
- **Windows 注意**：Git Bash 下使用 lark-cli raw API 需加 `MSYS_NO_PATHCONV=1`（详见 DEVLOG 2026-05-15 踩坑）

---

## 4. 开发工作流

- 每完成一个 Phase 子任务就调 `/done`：自动追加 DEVLOG → 勾选 DEVPLAN → `git add` + commit + push
- commit message 格式：`[phase X.Y] <简要描述>`
- 不要绕过 `/done`，所有改动必须留痕

---

## 5. 环境变量

见 `.env.example`。所有密钥通过 `.env` 管理，不硬编码：
- `TIKHUB_API_KEY`
- `FEISHU_BITABLE_APP_TOKEN`
- `FEISHU_HOTPOSTS_TABLE_ID` / `FEISHU_GOLDWORDS_TABLE_ID` / `FEISHU_PATTERNS_TABLE_ID` / `FEISHU_CONFIG_TABLE_ID`

飞书凭证由 `lark-cli auth` 管理，存在 OS keychain，不进 `.env`。

---

## 6. 技术栈

- Python 3.10+ | `requirements.txt` | black + isort（行宽 100）
- TikHub Python SDK（`pip install tikhub`）
- lark-cli（飞书集成）
- Claude LLM（蒸馏分析，agent 自身能力，无需额外 API）
- 飞书豆包多模态（封面识图，由飞书侧自动触发）

---

## 6.5 Windows 开发踩坑速查

> **本节是 DEVLOG 踩坑记录的浓缩版。遇到问题先查这里，再查 DEVLOG。**

### Python 路径与模块

- **Python 全路径**：`C:\Users\Administrator\AppData\Local\Python\bin\python.exe`（`python` 命令不可用）
- **PYTHONPATH**：运行脚本时需 `PYTHONPATH="D:\AI Agent\金词挖掘机"`，或在脚本头部加 `sys.path.insert(0, "D:/AI Agent/金词挖掘机")`
- **Bash 工具 vs Python subprocess**：Claude Code 的 Bash 工具运行在 Git Bash 中（PATH 含 Git/bin），但 Python `subprocess` 不继承这个 PATH。所以 `bash -c` 在 Bash 工具里能跑，但在 Python subprocess 里找不到 bash

### lark-cli 调用

- **写入**（`_api`）：`subprocess.run(cmd, shell=True)` → cmd.exe 执行，已验证可写
- **读取**（`_list_records`）：同样用 `shell=True`（不要用 `["bash", "-c", cmd]`，Windows 找不到 bash）
- **Git Bash 路径转换**：`lark-cli api DELETE/GET "/open-apis/..."` 在 Git Bash 下路径被篡改，需 `MSYS_NO_PATHCONV=1`。PowerShell 无此问题
- **`--data @file` 和 `--file`**：必须用相对路径（相对 cwd），且 cwd 不能含中文。代码中用纯 ASCII 临时目录 `%TEMP%\feishu_cli`
- **中文编码**：`subprocess.run(text=True)` 用 GBK 解码会报错，统一用 `capture_output=True` + `.decode('utf-8', errors='replace')`

### 飞书数据格式

- **single-select 字段**：lark-cli `base +record-list --format json` 的 tabular 输出中，单选字段返回数组（如 `['twist']`），不是字符串。用 `_unwrap(val)` 取首元素
- **date 字段**：传 Unix 时间戳毫秒数（`int(datetime.now().timestamp() * 1000)`），不要传字符串
- **URL 字段**：格式必须是 `{"link": "url", "text": "显示文本"}`，空字符串会导致 URLFieldConvFail
- **附件字段**：创建时不要设 `allowed_edit_modes`，保持默认（manual=true）

### PowerShell here-string 注意

- PowerShell `-c @"..."@` 里的 f-string 如果包含 `w['fields']` 这种方括号，会被解析错误。解决办法：先赋值给变量，再在 f-string 中用变量
