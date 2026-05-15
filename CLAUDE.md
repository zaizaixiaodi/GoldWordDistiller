# 金词蒸馏器 / GoldWord Distiller

> 一个运行在 Claude Code 下的 CLI Agent，帮助自媒体博主从小红书热贴中蒸馏出"金词"，为选题提供弹药。

## 三层词汇模型

- **领域词**（~5个）：博主的内容赛道（搞钱、职场、个人成长、AI 应用、自媒体方法论），手动设定，长期稳定
- **搜索词**（~15个）：每个领域词下 3 个搜索关键词，手动维护
- **金词**：从搜索结果中蒸馏出的高价值表达（有画面感、有力量感、有传播力），agent 核心产出物

关系：领域词 → 驱动搜索词 → TikHub API 获取热贴 → 热贴经 agent 分析蒸馏出金词

## 目录结构

```
goldword-distiller/
├── CLAUDE.md              # 本文件 — agent 全局指令
├── DEVLOG.md              # 开发日志（/done 自动追加）
├── DEVPLAN.md             # 开发计划（进度看这里）
├── .env                   # 环境变量（不提交 git）
├── .env.example           # 环境变量模板
├── .claude/
│   ├── settings.json      # Claude Code 权限配置
│   └── commands/          # Slash commands
│       ├── done.md        # /done — DEVLOG + git commit & push
│       ├── harvest.md     # /harvest — 立即执行一次完整采集
│       ├── feed.md        # /feed — 喂入外部素材
│       ├── add.md         # /add — 手动添加金词
│       ├── list.md        # /list — 查看金词
│       ├── report.md      # /report — 生成蒸馏简报
│       ├── config.md      # /config — 查看编辑配置
│       ├── sync.md        # /sync — 手动飞书同步
│       └── schedule.md    # /schedule — 定时任务
├── goldword/
│   ├── config.py          # 配置管理（环境变量、飞表 ID）
│   ├── harvester.py       # 平台直出：TikHub 搜索 + 表层数据采集
│   ├── hotlist.py         # 官方榜单：热榜采集
│   ├── feeder.py          # 他山之石：手动素材输入
│   ├── distiller.py       # 金词蒸馏核心逻辑
│   ├── tracker.py         # 趋势追踪
│   ├── reporter.py        # 简报生成
│   └── feishu.py          # 飞书多维表薄封装层（基于 lark-cli）
├── prompts/
│   └── distill.md         # 蒸馏分析 prompt 模板
├── scripts/
│   ├── probe_tikhub.py    # TikHub 联调脚本
│   ├── probe_feishu.py    # 飞书联调脚本
│   └── samples/           # API 原始返回样本
└── tests/                 # 单元测试
```

## 开发工作流

每完成一个 Phase 子任务就调 `/done`，它会自动：追加 DEVLOG → 勾选 DEVPLAN → git commit & push

## 飞书集成

- **工具**：`lark-cli` v1.0.32（飞书官方 CLI，通过 `lark-base` skill 操作多维表）
- **应用**：`cli_aa8d9918c778dbb4`（用户自建「金词」应用）
- **Bitable app_token**：`Z5DubZ9DMaPkgDsbMWScnrgknSz`（嵌在 Wiki 中，非 URL 中的 wiki token）
- **三张表**：热贴库 `tblg2nOd7LvMZCKC`、金词库 `tblqAKnCwubtFS0y`、配置表 `tbl7nJSXfjTkreFM`
- **Windows 注意**：Git Bash 下使用 lark-cli raw API 需加 `MSYS_NO_PATHCONV=1`

## 环境变量

见 `.env.example`。所有密钥通过 `.env` 管理，不硬编码。

## 技术栈

- Python 3.10+ | requirements.txt | black + isort（行宽 100）
- TikHub Python SDK（`pip install tikhub`）
- lark-cli（飞书集成）
- Claude LLM（蒸馏分析，agent 自身能力）
