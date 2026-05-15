# 金词蒸馏器 / GoldWord Distiller — DEVPLAN v1

> **本文件的定位**：把 PRD 拆解成"AI 可以独立执行 + 用户可以肉眼验收"的开发任务清单。每个任务都有明确的 DoD（Definition of Done），后续 AI 接手时按本文件顺序推进即可，无需重新通读 PRD 再做规划。
>
> **配套文件**：
> - 需求源头：[`项目需求和参考/金词蒸馏器_PRD_v1.md`](项目需求和参考/金词蒸馏器_PRD_v1.md)
> - 开发流水账：`DEVLOG.md`（每次 `/done` 追加，本文件创建后由 Phase 1.1 生成）

---

## 0. 如何使用本文件（写给后续 AI）

**会话开始时**：
1. 先读"§1 状态总览"，找到第一个未勾选 `[ ]` 的任务。
2. 跳到该任务，读它的"目标 / 前置 / 步骤 / DoD"。
3. 如果前置任务未完成，先回去做前置。
4. 如果步骤里写了"和用户确认 X"，就先 AskUserQuestion 而不是擅自决定。

**任务执行中**：
- 每个任务的"步骤"是建议路径，不是死板剧本。如果发现 PRD 假设不成立（例如某个 API 字段名错了），先修正再继续，并把发现写进 DEVLOG。
- 修改本文件 §1 的勾选状态（`[ ]` → `[x]`）和当前阶段标记。
- "产物文件"列出的文件如果不存在则创建，已存在则更新。

**任务结束时**：
1. 自检 DoD 每一条是否真的达成（不是"代码写完了"，而是"跑通了"）。
2. 调 `/done`（如果该命令已实现）；或手动追加 DEVLOG + git commit。
3. 在本文件的"状态总览"中把当前任务勾上，并把"当前进度"指针后移。

**何时该停下问用户**：
- 任务步骤里出现 ⚠️ 标记的地方，必须先确认。
- 发现 PRD 与现实冲突，且修正方案不止一种。
- 需要的密钥/账号/外部资源未就绪。

---

## 1. 状态总览（每次 /done 后更新）

**当前阶段**：Phase 1 — 管道打通（MVP）
**当前任务**：1.2 TikHub 接口联调（search + hotlist）
**最近一次更新**：2026-05-15（Phase 0 完成 + 1.1 脚手架搭建）

### Phase 0：准备工作（用户侧）
- [x] 0.1 收集环境变量与外部账号
- [x] 0.2 确认 Git 仓库地址

### Phase 1：管道打通（MVP）
- [x] 1.1 项目脚手架与开发工作流
- [ ] 1.2 TikHub 接口联调（search + hotlist）
- [ ] 1.3 飞书多维表搭建与读写封装
- [ ] 1.4 端到端采集管道（/harvest）

### Phase 2：蒸馏能力
- [ ] 2.1 金词提取（高频词 + 语义聚类）
- [ ] 2.2 趋势追踪（tracker.py）
- [ ] 2.3 简报与手动入口（/feed、/add、/report）

### Phase 3：体验打磨
- [ ] 3.1 定时任务（cron + /schedule）
- [ ] 3.2 管理命令（/list、/config）
- [ ] 3.3 飞书深度集成调优

---

## 2. Phase 0 — 准备工作（用户侧）

> 这一阶段 AI 不能自己完成，需要用户配合提供资源。AI 的工作是**逐项确认并把结果记录到本地**。

### 0.1 收集环境变量与外部账号

**目标**：把 TikHub API Key 收齐，完成 `lark-cli` 安装与 OAuth 登录。

**前置**：`lark-cli` 已安装（v1.0.32+）

**步骤**：
1. AskUserQuestion 确认 `TIKHUB_API_KEY` 是否已就绪。
2. 引导用户完成 `lark-cli` 认证（分两步，均需浏览器交互）：
   - `lark-cli config init --new`：创建飞书应用并配置凭据（AI 后台运行，提取授权 URL 给用户）
   - `lark-cli auth login --recommend`：OAuth 登录授权（AI 后台运行，提取授权 URL 给用户）
3. 确认三个多维表 ID（可通过 `lark-cli base` 命令查看，或在飞书多维表 URL 中提取）：
   - `FEISHU_BITABLE_APP_TOKEN`
   - `FEISHU_HOTPOSTS_TABLE_ID` / `FEISHU_GOLDWORDS_TABLE_ID` / `FEISHU_CONFIG_TABLE_ID`
4. 创建 `.env.example` 文件（不含真实值），列出 4 个变量名（TikHub Key + 3 个飞表 ID）。
5. 提示用户在项目根目录创建 `.env`（加入 `.gitignore`）。
6. 写一个 `goldword/config.py` 的最小骨架：用 `python-dotenv` 加载 `.env`，对外暴露这些常量。

**DoD**：
- `lark-cli auth status` 显示已登录
- `.env.example` 已提交
- `.gitignore` 已加入 `.env`
- 在项目根跑 `python -c "from goldword.config import TIKHUB_API_KEY; print('ok' if TIKHUB_API_KEY else 'missing')"` 输出 `ok`

**产物文件**：`.env.example`、`.gitignore`、`goldword/config.py`、`requirements.txt`（加入 `python-dotenv`）

**风险**：
- `lark-cli config init --new` 需要用户在浏览器中完成应用创建，如果用户没有飞书企业管理员权限可能失败。
- 飞书 app_token 容易和文档 token 混淆，要确认是多维表的 token（在 bitable.feishu.cn URL 里）。

**换设备恢复开发**：`lark-cli` 是全局安装，不随 git 仓库走。新设备需：
1. `npx @larksuite/cli@latest install` 安装 CLI
2. `echo "<APP_SECRET>" | lark-cli config init --app-id cli_aa8d9918c778dbb4 --app-secret-stdin --brand feishu` 配置应用
3. `lark-cli auth login --recommend` 重新 OAuth 授权
4. 在项目根创建 `.env`（TikHub Key + 飞表 ID）
5. 注意：如果多维表嵌在 Wiki 中，`.env` 里的 `FEISHU_BITABLE_APP_TOKEN` 应填 wiki node 的 `obj_token`（通过 wiki API 查询获得），不是 URL 中的 wiki token。详见 DEVLOG 踩坑记录。

---

### 0.2 确认 Git 仓库地址

**目标**：拿到远程仓库 URL，准备 `git remote add origin`。

**步骤**：
1. AskUserQuestion 问用户：远程仓库地址是什么？（GitHub / GitLab / Gitee 都行）
2. 如果用户还没建，引导用户在 GitHub 创建私有仓库 `goldword-distiller`。
3. 把地址记到本任务下面的"已确认信息"区域。

**已确认信息**（AI 拿到后填进来）：
- 远程仓库 URL：`<待填写>`
- 主分支名：`main`

**DoD**：本节"已确认信息"已填写。

---

## 3. Phase 1 — 管道打通（MVP）

> Phase 1 的目标：跑通一次完整的"搜索 → 写入飞书 → 等飞书解析 → 读回数据"的数据管道。**不做蒸馏**，蒸馏放到 Phase 2。这一阶段结束时，飞书的"热贴库"里应该能看到一批由 agent 写入并已解析的真实数据。

### 1.1 项目脚手架与开发工作流

**目标**：把 `CLAUDE.md`、`DEVLOG.md`、`/done` 命令、目录结构都立起来，让后续每一步开发都能自动留痕。

**前置**：0.1、0.2 完成。

**步骤**：
1. `git init`，添加 `.gitignore`（Python 默认 + `.env` + `.claude/settings.local.json`）。
2. 添加远程：`git remote add origin <0.2 拿到的 URL>`。
3. 创建 `CLAUDE.md`，内容包含：
   - 项目一句话定位（抄 PRD §标题下的引用）
   - 三层词汇模型简要说明
   - 目录结构概览（抄 PRD §6.2）
   - **开发工作流**：每完成一个 Phase 子任务就调 `/done`
   - **权限约定**：python、pip、git、ls/cat、读写 .env 之外的项目文件都自动允许（在 `.claude/settings.json` 的 `permissions.allow` 里配置）
   - 环境变量列表（指向 `.env.example`）
   - 指向本 DEVPLAN.md，说明"开发进度看这里"
4. 创建 `DEVLOG.md`，写入第一条记录（本次脚手架搭建）。
5. 创建 `.claude/commands/done.md`：
   - 输入：本次工作摘要（可选）
   - 行为：
     1. 读 DEVPLAN.md 找到当前任务编号
     2. 在 DEVLOG.md 顶部追加新条目（时间戳 + 阶段编号 + 工作摘要 + 关键决策 + 问题与解决）
     3. 更新 DEVPLAN.md：勾选当前任务，更新"当前阶段/当前任务/最近一次更新"
     4. `git add -A && git commit -m "[phase X.Y] <摘要>" && git push`
6. 创建 `.claude/settings.json`，配置 `permissions.allow`（参考 §5 工程约定）。
7. 按 PRD §6.2 创建空目录骨架：`goldword/`（加 `__init__.py`）、`prompts/`、`.claude/commands/`。

**DoD**：
- 在项目根敲 `/done "搭建脚手架"`，能自动追加 DEVLOG、勾选本任务、提交并推送。
- `git log --oneline` 至少有 1 条 commit，且远程有同步。
- CLAUDE.md 读完即可了解项目背景和开发约定，无需再翻 PRD。

**产物文件**：`CLAUDE.md`、`DEVLOG.md`、`.gitignore`、`.claude/commands/done.md`、`.claude/settings.json`、`goldword/__init__.py`、`prompts/.gitkeep`

**风险**：`/done` 命令实现质量直接决定后续节奏。如果它不能自动维护 DEVPLAN 的勾选状态，后面 AI 容易跑偏。第一版可以简单粗暴：让 AI 在执行 `/done` 时显式读 DEVPLAN、找到第一个 `[ ]` 替换为 `[x]`、再 commit。

---

### 1.2 TikHub 接口联调（search + hotlist）

**目标**：用真实 API 调用确认 PRD §2.1 的两个接口，把返回字段映射记到代码里。

**前置**：0.1（拿到 `TIKHUB_API_KEY`）、1.1。

**步骤**：
1. `pip install tikhub` 加入 `requirements.txt`。
2. 写一个临时脚本 `scripts/probe_tikhub.py`：
   - 用一个测试搜索词（例如"副业"）调 `search_notes`，sort=popularity_descending，取 1 页
   - 用 `fetch_hot_list` 拉热榜
   - 把两个接口的原始返回 JSON 各 dump 1 条到 `scripts/samples/`
3. 阅读 dump 出来的 JSON，确认以下字段都存在且名称是什么：
   - 帖子 ID、标题、链接、封面图 URL、点赞/收藏/评论数、note_type、hashtags
4. 在 `goldword/harvester.py` 创建一个 dataclass `RawPost`，字段对应 PRD §3.1 热贴库中"数据来源 = TikHub"的列。
5. 实现 `harvester.search(keyword: str) -> list[RawPost]` 和 `hotlist.fetch() -> list[RawPost]`，只做"调 API + 解析为 RawPost"，**不写飞书**（飞书是 1.3 的事）。
6. 写一个最小测试 `python -m goldword.harvester "副业"`，打印返回的 RawPost 列表。

**DoD**：
- 命令行跑 `python -m goldword.harvester "副业"` 输出 ≥10 条 RawPost
- `scripts/samples/search_notes.json` 和 `scripts/samples/hot_list.json` 已 commit，作为字段映射的活文档
- 在 DEVLOG 里记录：实际字段名 vs PRD 假设字段名的差异

**产物文件**：`goldword/harvester.py`、`goldword/hotlist.py`、`scripts/probe_tikhub.py`、`scripts/samples/*.json`

**风险**：
- TikHub SDK 的参数名可能和文档不一致（PRD §7.2 DEVLOG 示例就提到过 `sort_type` vs `sort`）
- 热榜接口可能需要不同的鉴权/参数

---

### 1.3 飞书多维表搭建与读写封装

**目标**：在飞书侧把三张表建好，并实现 `goldword/feishu.py` 的业务逻辑封装（基于 `lark-cli base` 命令）。

**前置**：0.1（`lark-cli` 已认证登录）、1.2（知道 RawPost 字段长什么样）。

**步骤**：

**A. 飞书侧建表**（通过 `lark-cli base` 命令）：
1. 确认多维表是否已存在。如不存在，用 `lark-cli base` 命令或引导用户在飞书 UI 新建。
2. 确认三张表（热贴库、金词库、配置表）是否已创建。如未创建：
   - 可通过 `lark-cli base` + `lark-base` skill 按 PRD §3.1 / §3.2 / §3.3 的字段表创建
   - 也可引导用户在飞书 UI 手动创建，然后记下每张表的 `table_id`
3. 引导用户在飞书多维表上配置"链接深度解析"工具（PRD §9 待定事项 2 提到）：
   - ⚠️ 需要用户确认该工具的具体名称、触发方式、解析结果回填到哪几列
   - 把确认结果写到 CLAUDE.md 的"飞书集成"小节

**B. 代码侧**（薄封装）：
4. 实现 `goldword/feishu.py`，作为对 `lark-cli base` 命令的业务逻辑封装层，至少包含：
   - `insert_post(record: dict) -> str`（调用 `lark-cli base` 写入热贴库，返回 record_id）
   - `batch_insert_posts(records: list[dict]) -> list[str]`
   - `query_posts(filter: dict) -> list[dict]`
   - `update_post(record_id: str, fields: dict) -> None`
   - 金词库对应方法同上：`insert_word` / `update_word` / `query_words`
   - **解析等待轮询** `wait_for_parse(record_ids: list[str], initial_wait=90, retry_interval=30, max_retries=3) -> dict`：
     - 先 sleep 90s
     - 然后循环最多 3 次，每次用 `lark-cli base` 查询 `parse_status`，全部为"已解析"则返回数据
     - 超时则返回部分解析数据 + 失败列表
5. 写一个最小测试 `scripts/probe_feishu.py`：写入 1 条假数据 → 等 5 秒 → 读出来 → 更新 → 删除。

**DoD**：
- `lark-cli base` 命令能正常读写目标多维表（先 `--dry-run` 确认，再实际执行）
- `scripts/probe_feishu.py` 跑通，飞书后台能看到操作痕迹
- `goldword/feishu.py` 的关键方法都有 docstring
- CLAUDE.md 的"飞书集成"小节已经写清楚：三张表的 table_id 来源、解析工具如何触发、解析结果回填哪几列

**产物文件**：`goldword/feishu.py`、`scripts/probe_feishu.py`、CLAUDE.md（更新）

**优势**（相比手写 API 封装）：
- auth 管理（token 缓存、刷新）由 `lark-cli` 内置，不需要在 `feishu.py` 里处理
- 请求构建、分页、错误重试由 CLI 内置
- `--dry-run` 支持可先预览再执行
- `--format json` 直接返回结构化数据，无需手写 JSON 解析

**风险**：
- 飞书的"链接深度解析"是用户侧的现成工具，AI 没法直接验证它的行为，⚠️ 一定要让用户先手动喂一条数据观察解析效果
- `lark-cli base` 命令的参数格式需在联调中确认（用 `lark-cli schema` 查看接口定义）

---

### 1.4 端到端采集管道（/harvest）

**目标**：注册 `/harvest` 命令，能一键完成"读配置 → 遍历搜索词 → 写热贴库 → 等飞书解析 → 读回解析数据"。**这一步还不蒸馏**，只是把数据沉淀好。

**前置**：1.2、1.3 完成。

**步骤**：
1. 在配置表（PRD §3.3）里手动录入 1-2 个领域词 + 对应搜索词作为测试数据。
2. 在 `goldword/config.py` 增加 `load_search_config() -> list[dict]`，从飞书配置表读出 `is_active=True` 的领域/搜索词。
3. 在 `goldword/harvester.py` 增加 `harvest_all() -> HarvestResult` 流程：
   - 读配置 → 对每个搜索词调 `search()` → 去重（按 post_id 查飞书是否已存在）→ 批量写入热贴库 → 收集 record_ids
   - 调 `hotlist.fetch()` → 同样去重写入
   - 调 `feishu.wait_for_parse(record_ids)` → 拿到解析后的完整数据
   - 返回 HarvestResult（包含本次写入数、API 调用次数、解析成功/失败数）
4. 创建 `.claude/commands/harvest.md`：
   - 无参：执行完整流程
   - `--dry-run`：只读配置打印预期搜索词列表和预估 API 调用量，不实际调
5. 跑一次 `/harvest`，飞书后台肉眼确认：
   - 热贴库里多了真实数据
   - 这些数据的 `cover_text`、`content_full` 字段被飞书解析填充了

**DoD**：
- `/harvest --dry-run` 输出预期搜索词列表 + 预估 API 调用次数
- `/harvest` 跑完，飞书热贴库里 ≥1 条数据是已解析状态（`parse_status=已解析`）
- CLI 输出一个简单的本次汇总（写入 N 条 / 解析成功 M 条 / 失败 K 条）
- DEVLOG 记录解析等待的实际时长（用于校准 PRD §2.1 第 5 步的等待策略）

**产物文件**：`.claude/commands/harvest.md`、`goldword/harvester.py`（增强）、`goldword/config.py`（增强）

**风险**：
- 飞书解析时间可能超过 PRD 设定的 90s + 3×30s = 3 分钟。如果常常超时，需要把策略调整为"写入后异步标记，下次 /harvest 时回收上一批"。在 DEVLOG 中记录实际表现再决定。
- 去重逻辑：第一次跑去重表是空的，所有数据都入；第二次开始要按 post_id 过滤。注意 post_id 在飞书里的查询效率，可能需要本地维护一个 SQLite 索引。

---

## 4. Phase 2 — 蒸馏能力

> Phase 2 的目标：把 Phase 1 沉淀的原始数据真正"蒸"成金词。这一阶段结束时，金词库里应该自动出现一批带"新词/上升/平稳/下降"标签的金词，并能产出 PRD §4.2 那样的简报。

### 2.1 金词提取（高频词 + 语义聚类）

**目标**：实现 `distiller.py`，输入"一批已解析热贴"，输出"候选金词列表"。

**前置**：1.4 完成（飞书热贴库里已有真实解析数据）。

**步骤**：
1. 在 `prompts/distill.md` 写一版蒸馏 prompt，输入是一组帖子的（标题 + 封面文字 + 完整文案 + 互动数据），输出是 JSON 格式的候选金词列表，每个候选词包含：
   - `word`：主词（最有画面感的表述）
   - `aliases`：同义变体
   - `frequency`：在本批次出现的频次
   - `related_post_ids`：关联帖子 ID
   - `vibe`：画面感/力量感/反差感的简短描述
2. 实现 `goldword/distiller.py`：
   - `distill(posts: list[dict]) -> list[CandidateWord]`：
     - 预处理：拼接所有帖子的文本
     - 调 Claude（agent 本身的能力，不用额外 API）按 `prompts/distill.md` 分析
     - 过滤 PRD §4.1 的筛选条件（频次 ≥3、互动数据高于中位数、画面感、新鲜度）
3. 在 `harvester.py` 的 `harvest_all()` 末尾调 distill，但**先不写金词库**（写金词库是 2.2 的事），先 dump 到 `scripts/samples/candidate_words.json` 供肉眼审。

**DoD**：
- `python -m goldword.distiller --from-feishu` 能读飞书最近一批热贴并输出候选金词 JSON
- 用户肉眼审 candidate_words.json，确认至少 50% 候选词"看起来像金词"（不是通用停用词）
- prompt 里的停用词表已经覆盖 PRD §4.1 提到的"绝绝子/yyds/姐妹们"等

**产物文件**：`prompts/distill.md`、`goldword/distiller.py`、`scripts/samples/candidate_words.json`

**风险**：
- 第一版蒸馏质量大概率不行，需要 2-3 轮 prompt 迭代。⚠️ 不要追求一步到位，先跑通管道，迭代放在 3.3。
- LLM 输出的 JSON 可能不合法，需要 try-except + 重试逻辑。

---

### 2.2 趋势追踪（tracker.py）

**目标**：实现 `tracker.py`，把 2.1 产出的候选金词与金词库历史数据比对，打上趋势标签后写回金词库。

**前置**：2.1 完成。

**步骤**：
1. 实现 `goldword/tracker.py`：
   - `compare_with_history(candidates: list[CandidateWord]) -> list[TrackedWord]`：
     - 对每个候选词查金词库（按 `word` + `aliases` 模糊匹配）
     - 按 PRD §4.1 第四步规则打标签：新词 / 上升 / 平稳 / 下降
     - 计算 first_seen、last_seen、frequency 变化
2. 实现 `tracker.upsert_to_feishu(words: list[TrackedWord])`：
   - 新词 → insert，状态=待审
   - 已有词 → update（更新 frequency、last_seen、trend）
   - 关联热贴 → 写入 `related_posts` 字段
3. 在 `harvester.harvest_all()` 中把 distill + tracker 串起来：搜索 → 写热贴 → 等解析 → distill → tracker → 写金词库。
4. 跑一次完整 `/harvest`，飞书金词库里应该自动出现新词。

**DoD**：
- `/harvest` 跑完后，飞书金词库新增至少 5 个候选词，状态=待审
- 连续跑 2 次 `/harvest`（中间换搜索词），第二次能看到至少 1 个词的 trend 从"新词"变为"上升"或"平稳"

**产物文件**：`goldword/tracker.py`、`goldword/harvester.py`（串联调整）

**风险**：
- 模糊匹配的阈值需要调（用编辑距离？子串匹配？语义相似度？）。先用最简单的：完全相等或互为子串。
- "下降"标签需要从历史读取"上次出现但本次消失"的词，逻辑稍复杂，注意只比对同一领域内的词。

---

### 2.3 简报与手动入口（/feed、/add、/report）

**目标**：把 PRD §2.2、§2.4、§4.2 三个面向用户的功能实现，让博主真正能用起来。

**前置**：2.2 完成。

**步骤**：
1. 实现 `goldword/reporter.py`，按 PRD §4.2 的格式生成简报（CLI 文本输出）。
2. 创建 `.claude/commands/report.md`：调 reporter，输出最近一期简报。
3. 在 `harvester.harvest_all()` 末尾自动调 reporter。
4. 实现 `goldword/feeder.py`（PRD §2.2 他山之石）：
   - `feed_url(url: str)`：调 TikHub 提取分享链接 → 拉详情 → 走 distill → 写金词库（source=他山之石）
   - `feed_text(text: str, domain: str | None)`：纯文本直接走 distill
   - `feed_file(path: str)`：读文件后走 feed_text
5. 创建 `.claude/commands/feed.md`，支持 `/feed <url>`、`/feed --text`、`/feed --file <path>`。
6. 创建 `.claude/commands/add.md`，实现 PRD §2.4 的语法 `/add "<金词>" --domain "<领域>" --note "<备注>"`，写入金词库时 source=人工精选，status=已采纳（跳过"待审"）。

**DoD**：
- `/report` 能产出一份格式正确的简报
- `/feed <小红书链接>` 能成功喂入一篇外部素材
- `/add "测试金词" --domain "搞钱" --note "调试"` 能在飞书金词库看到新行

**产物文件**：`goldword/reporter.py`、`goldword/feeder.py`、`.claude/commands/{report,feed,add}.md`

---

## 5. Phase 3 — 体验打磨

### 3.1 定时任务（cron + /schedule）

**目标**：把 `/harvest` 挂上 cron，实现 PRD §2.1 的"周二+周六自动跑"。

**前置**：Phase 2 完成。

**步骤**：
1. 写一个 `scripts/run_harvest.sh`（或 `.ps1`，因为是 Windows）作为 cron 入口，里面激活虚拟环境 → 调 python 入口。
2. ⚠️ Windows 没有 cron，要用任务计划程序（Task Scheduler）。和用户确认：
   - 走 Windows Task Scheduler？
   - 还是这台机器其实是常开的，可以用 Python 的 `apscheduler` 在后台守护？
   - 还是部署到服务器/云函数？
3. 实现 `.claude/commands/schedule.md`：查看/启用/禁用定时任务，能写入/修改任务计划程序的注册项（或 apscheduler 配置）。

**DoD**：用户能通过 `/schedule` 查看下次执行时间、暂停任务、立即触发一次。

---

### 3.2 管理命令（/list、/config）

**目标**：实现 PRD §5 中"查看与管理"分类下的命令。

**前置**：Phase 2 完成。

**步骤**：
1. `/list`：默认最近 2 周的金词，支持 `--trend up/down/stable/new`、`--status pending/adopted/used/stale`、`--domain <领域>`。
2. `/config`：查看/编辑领域词和搜索词（直接调飞书 API 改配置表，或本地编辑后同步飞书）。
3. `/sync`：手动触发飞书同步（在哪些场景需要单独同步？要和用户确认。如果 /harvest 已经端到端跑通，这个命令可能多余。）

**DoD**：用户 `/list --trend up` 能看到当前上升趋势的金词列表。

---

### 3.3 飞书深度集成调优

**目标**：把 Phase 1 / 2 中遇到的体验问题集中收尾。

**前置**：实际使用一周以上，DEVLOG 里有积累的反馈。

**步骤**：
1. 调蒸馏 prompt（参考 DEVLOG 里记录的"漏检"和"误检"案例）。
2. 校准飞书解析等待策略（如果发现常常超时，改成异步回收策略）。
3. 调金词筛选阈值（频次门槛、互动数据中位数权重）。
4. 优化 CLI 输出格式（简报的视觉表达）。

**DoD**：用户主观评价"现在产出的金词清单一半以上都直接能用"。

---

## 6. 附录

### 6.1 工程约定（写进 CLAUDE.md，本节是源头）

- **Python 版本**：3.10+（用 `match-case` 和 `|` 类型联合）
- **依赖管理**：`requirements.txt`（不上 poetry，保持简单）
- **代码风格**：black + isort，行宽 100
- **测试**：核心模块（distiller、tracker）写单测，放 `tests/`；I/O 模块（harvester、feishu）用 `scripts/probe_*.py` 做联调脚本，不强制单测
- **commit message 格式**：`[phase X.Y] <简要描述>`，由 `/done` 自动生成
- **`.claude/settings.json` permissions.allow**（用 Claude Code 的权限规则语法）：
  - `Bash(python:*)`、`Bash(pip:*)`、`Bash(git:*)`、`Bash(ls:*)`、`Bash(cat:*)`
  - `Read(./**)`、`Write(./**)`、`Edit(./**)`（项目目录内自由读写）
  - 不放进白名单的：`Bash(rm:*)`（删除操作仍需确认）、`.env` 的读取（避免泄露）

### 6.2 飞书 parse_status 状态机

```
[新写入] ──→ 待解析 ──飞书工具触发──→ 解析中 ──成功──→ 已解析
                                            └─失败──→ 解析失败
```

Agent 的 `wait_for_parse` 轮询条件：`parse_status in ("已解析", "解析失败")`。

### 6.3 常见调试动作

- **想看 TikHub 原始数据**：`python scripts/probe_tikhub.py "<搜索词>"`
- **想看飞书写入是否成功**：飞书多维表 UI 直接看，或 `python scripts/probe_feishu.py --query <post_id>`
- **想重跑蒸馏但不重新采集**：`python -m goldword.distiller --from-feishu --since <日期>`
- **想清掉一次错误的采集**：在飞书 UI 里筛选 `harvest_date=<今天>` 然后手动删除（agent 不主动删数据）

### 6.4 PRD 待定事项与本计划的对应

PRD §9 的 7 项待定事项对应到本计划的处理位置：

| PRD §9 项 | 在 DEVPLAN 哪里处理 |
|-----------|---------------------|
| 1. 飞书应用权限 | 0.1 |
| 2. 飞书解析工具 | 1.3 步骤 A2 |
| 3. 解析时序校准 | 1.4 风险点 + 3.3 |
| 4. Git 仓库地址 | 0.2 |
| 5. TikHub 字段确认 | 1.2 步骤 3 |
| 6. 播客 ASR | 不在 v1 范围，记在 PRD §9 即可 |
| 7. 蒸馏 prompt 迭代 | 2.1 + 3.3 |

---

## 7. 变更记录

- 2026-05-15：DEVPLAN v1 创建，对齐 PRD v1.1。
- 2026-05-15：DEVPLAN v1.1 — 飞书集成方案从"手写 `lark-oapi` 封装"升级为"基于 `lark-cli`（v1.0.32）的薄封装层"。影响范围：§0.1（环境变量减少，增加 lark-cli 认证步骤）、§1.3（飞书搭建与封装方案重写）。
