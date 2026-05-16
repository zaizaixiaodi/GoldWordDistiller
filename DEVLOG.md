# DEVLOG — 金词蒸馏器

> 按时间倒序排列。每次完成有意义的工作单元后追加。

---

## [2026-05-17 15:00] Phase 2.2 — tracker.py 趋势追踪实现

### 完成内容

- **创建 `goldword/tracker.py`**：金词 + 句式双路趋势追踪
  - `track_words(candidates)` → 比对飞书历史，精确/别名/子串三级匹配，输出 trend 标签
  - `track_patterns(candidates)` → skeleton 精确匹配，合并 examples
  - `upsert_words(tracked)` / `upsert_patterns(tracked)` → 新词 insert / 已有 update
  - `refresh_trends()` → 批次间衰减：上升→平稳
- **修复 `feishu.py` 的 `_list_records`**：`["bash", "-c", cmd]` → `shell=True`（Windows 兼容）
- **新增 `_unwrap()` 辅助函数**：飞书 single-select 字段返回 list（如 `['twist']`），需取首元素
- **测试验证**：179 条金词索引、15 条句式索引、update/insert/upsert 全通过

### 踩坑记录

#### 坑 1：Python subprocess 找不到 bash

- **现象**：`_list_records` 用 `subprocess.run(["bash", "-c", cmd])` 报 `FileNotFoundError`
- **原因**：Python subprocess 的 PATH 不含 Git Bash 的 bin 目录。Bash 工具（Claude Code 内置）运行在 Git Bash 环境中，但 Python 启动的子进程没有同样的 PATH
- **解决**：改用 `subprocess.run(cmd, shell=True, capture_output=True)`。`shell=True` 在 Windows 上用 cmd.exe，`lark-cli base +record-list` 命令在 cmd.exe 下正常工作
- **影响文件**：`goldword/feishu.py` 的 `_list_records` 函数

#### 坑 2：飞书 single-select 字段返回 list

- **现象**：`fields.get("category")` 返回 `['twist']` 而非 `'twist'`
- **原因**：lark-cli `base +record-list --format json` 的 tabular 输出中，单选/多选字段都是数组格式
- **解决**：tracker.py 新增 `_unwrap(val)` 辅助函数：如果值是长度 1 的 list，取第一个元素；否则原样返回。所有读取飞书数据的地方都经过 `_unwrap`

#### 坑 3：lark-cli DELETE 在 Git Bash 下需 MSYS_NO_PATHCONV=1

- **现象**：`lark-cli api DELETE "/open-apis/..."` 返回 404
- **原因**：Git Bash 自动把 `/open-apis/` 路径转换为 Git 安装目录下的路径（如 `C:/Program Files/Git/open-apis/`）
- **解决**：加 `MSYS_NO_PATHCONV=1` 环境变量，或改用 PowerShell 执行

#### 坑 4：Python 全路径 + PYTHONPATH

- **现象**：`python` 命令找不到，`import goldword` 报 ModuleNotFoundError
- **解决**：
  - Python 全路径：`C:\Users\Administrator\AppData\Local\Python\bin\python.exe`
  - PYTHONPATH：`PYTHONPATH="D:\AI Agent\金词挖掘机"`
  - 或者写 `sys.path.insert(0, "D:/AI Agent/金词挖掘机")` 到脚本头部

### 关键决策

- 匹配策略：精确 → 别名 → 双向子串（同 category 内），避免跨类误判
- 趋势标签：新词/新句式（首次）、上升（frequency+1），平稳和下降由 `refresh_trends()` 处理
- tracker 不自动调用 distill，而是接收蒸馏结果。Claude（或未来 skill化后）负责蒸馏→调用 tracker→upsert

### 产物文件

- `goldword/tracker.py`（新增）
- `goldword/feishu.py`（修复 `_list_records`）
- `scripts/test_tracker.py`、`scripts/test_tracker_upsert.py`（测试脚本）
- `CLAUDE.md` §6.5 新增 Windows 踩坑速查

### ⚠️ feishu.py 遗留问题（待 Opus 修复）

审计发现 `goldword/feishu.py` 仍有以下隐患，需要一次性在源头修干净：

#### 隐患 1：single-select 字段返回 list 未在源头处理

- **现状**：`_list_records` 返回的 fields 中，single-select 值是 `['twist']` 而非 `'twist'`。目前只有 `tracker.py` 的 `_unwrap()` 处理了，其他消费者（harvester、reporter 等）都没处理，遇到就会崩
- **应修**：在 `_list_records` 的解析循环里统一 unwrap——如果值是长度 1 的 list 且内容是字符串/数字，取首元素。这样所有上层调用者自动拿到干净数据，tracker.py 的 `_unwrap` 可以移除或保留为兼容层

#### 隐患 2：无分页，超 limit 静默丢数据

- **现状**：`_list_records` 接受 `limit` 和 `offset` 参数，但 `query_words(limit=500)` 等调用方从不翻页。金词库现 179 条还好，但超过 500 条后查询结果会静默截断
- **应修**：`_list_records` 内部循环翻页直到取完所有数据，或者 `query_*` 函数自动分页。lark-cli 的 tabular 输出里应该有 `has_more` 或 `total` 字段可以判断

#### 隐患 3：`import platform` 死代码

- **现状**：第 10 行 `import platform` 是之前修复时加的，但实际没用到
- **应修**：删掉

#### 修复优先级

隐患 1（unwrap）和隐患 2（分页）都是"现在能跑、未来必崩"的类型。建议在下一次会话由 Opus 一次性修掉 `_list_records`，修完后重跑 `scripts/test_tracker.py` 验证。

---

## [2026-05-17 01:30] Phase 1.4+++ — 封面图本地备份 + 回填上传

### 完成内容

- **本地 JSON 备份**：harvest_all 写入飞书前自动 dump 到 `scripts/samples/harvest_YYYYMMDD_HHMMSS.json`，防止数据丢失
- **封面上传集成**：harvest_all 新增步骤 7，写入后自动下载封面→上传飞书 Drive→写回"封面"附件字段，不消耗 LLM token
- **封面对回填**：`backfill_covers()` 搜索 20 词匹配已存在的 496 条记录 post_id，成功回填 87 张封面，398 条未匹配（搜索结果是实时的，昨天的帖今天可能不在 top 20）
- **feishu.py 新增**：download_cover / upload_cover / update_cover_attachment
- **热贴库现状**：496 条记录，96 条有封面附件（9 + 87），400 条待后续 /harvest 积累

### 关键决策

- 封面上传不消耗 LLM token，纯本地 subprocess + HTTP
- 回填只调搜索 API（$0.01/次），不留详情 API——cover_url 在搜索结果中免费返回
- 未匹配的 398 条不单独追，后续每次 /harvest 自动补齐新帖封面

### 存量覆盖情况

| 状态 | 数量 |
|------|------|
| 有封面 | 96 条 |
| 待回填（搜索结果未匹配） | 400 条 |
| 总计 | 496 条 |

---

## [2026-05-16 23:00] Phase 1.3 — 飞书四表建好 + feishu.py 封装 + CRUD 联调

### 完成内容

- **句式库表新建**（`tbl7iu3g51uFw1Ci`）：skeleton/category/examples/frequency/first_seen/last_seen/trend/recommended_categories/user_note 共 9 字段
- **金词库字段补全**：v2 ★ 字段 category/source_field/vibe_score/suggested_patterns + domain/trend/status/source/related_posts/aliases/used_in 等 15 字段
- **配置表字段建立**：domain_word/search_keyword/is_active/priority/note
- **热贴库补 domain 字段**：单选（搞钱/职场/个人成长/AI应用/自媒体方法论）
- **`goldword/feishu.py` 双通道封装**：
  - 写入走 `lark-cli api` (shell=True / cmd.exe)，已验证 POST batch_create / PUT record 正常
  - 读取走 `lark-cli base +record-list` (bash -c)，解析 tabular JSON 输出
  - 覆盖热贴库/金词库/句式库/配置表 CRUD + 识图轮询 `wait_for_cover_text`
- **`scripts/probe_feishu.py`**：四表 insert/query/update 全通过（11/11）

### 关键踩坑

1. **`lark-cli base` 子命令需要 `+` 前缀**：`+record-list` 非 `record-list`；`--data` 只对 raw API 有效，base 命令用 `--json`
2. **`lark-cli api` GET/搜索端点权限不足**：99991679 Permission denied，但 POST/PUT 写入正常。读取改用 `bash -c` + `lark-cli base +record-list`
3. **`lark-cli base +record-list --format json` 输出 tabular**：需 `fields` + `record_id_list` + `data`（值二维数组）拼回 record dict
4. **Windows `shell=True` 用 cmd.exe**：`shlex.quote` 单引号不兼容 cmd.exe，改用拼字符串
5. **飞书 URL 字段格式**：必须 `{"link":"...","text":"..."}`，空字符串会导致 1254068 URLFieldConvFail
6. **表字段名必须一字不差**：`cover_url` 不在热贴库（封面是附件字段"封面"），需 pop 掉

### 产物文件

- `goldword/feishu.py`（241 行）
- `scripts/probe_feishu.py`
- `CLAUDE.md`（飞书集成更新到四张表）
- `.env` / `.env.example` / `config.py`（加 PATTERNS_TABLE_ID）

---

## [2026-05-17 00:30] Phase 1.4 — 端到端采集管道（/harvest）跑通

### 完成内容

- **配置表录入测试数据**：搞钱→副业(P1)+自由职业(P2)、AI应用→AI(P3)
- **`config.py` 加 `load_search_config()`**：从飞书读取 active 配置，按 priority 排序
- **`harvester.py` 加 `HarvestResult` + `harvest_all()`**：
  - 读配置 → 去重（按 post_id 查飞书已有）→ 遍历搜索词 → 补详情 → 拉热榜 → 批量写飞书
  - `--dry-run` 模式只打印计划
  - 连接重试（WinError 10054 自动 2 次重试）+ 详情获取逐条 try-except
- **实际采集跑通**：3 个搜索词 → 60 条搜索 + 20 条热榜 → 去重 43 条 → 写入 37 条，共 19 次 API 调用
- **`/harvest` 命令注册**（`.claude/commands/harvest.md`）

### 关键踩坑

1. **空 URL → URLFieldConvFail**：热榜记录无链接，需传 `None` 而非空字符串
2. **`cover_url` 字段不存在热贴库**：`to_dict()` 含 cover_url 但表里没有对应字段，需 pop 掉
3. **TikHub 连接中断（WinError 10054）**：connection reset，加 `requests.ConnectionError` 捕获 + 重试
4. **详情 API 间隔太短触发限流**：0.5s → 0.8s，加 try-except 跳过单个失败

### 费用

- 本次采集：搜索 3 次($0.01) + 详情 15 次($0.02) + 热榜 1 次($0.01) ≈ $0.34
- 前几次踩坑调测额外消耗 ~$1.20

### 热贴库现状

- 已有 ~105 条记录（副业+自由职业+AI），含封面附件
- 豆包识图等待验证（Phase 1.4 只收数据，不蒸馏）

---

## [2026-05-16 16:30] Phase 1.3-pre — PRD/DEVPLAN/CLAUDE 升级到 v2

### 完成内容

- **PRD v1.1 标注废弃**：顶部加废弃声明，全文保留供溯源
- **新建 PRD v2.0**（`项目需求和参考/金词蒸馏器_PRD_v2.md`）：核心增量
  - **三层产物模型**：L1 金词库（原料）/ L2 句式库（骨架，新第 4 张表）/ L3 周报（精炼，含元认知反思）
  - **金词 8 功能位 MECE**：who / when / pain / do / twist / number / feel / picture
  - **标题/封面分别打标**：新增 `source_field` 字段（title/cover/both）
  - **vibe_score**：0-10 分，反常识/隐喻/情绪类天然高分，< 3 不入库
  - **周报含 7 节模板**：数据概览 + 功能位分布 + TOP 推荐 + 新句式 + 趋势 + 选题建议 + ⭐元认知反思（对 prompt/分词/功能位模型本身的反思）
  - **业务规范回写**：`prompts/observations.md` 沉淀人审周报后的判断，下次蒸馏 prompt 引用形成闭环
  - **飞书架构保持不变**：识图继续走豆包（成本可接受，进度优先）
- **DEVPLAN 对齐 v2**：1.3 收尾 + 2.1/2.2/2.3 + 3.2/3.3 全部改写，新增"v2 专项回测"（必填/加分位分级、第 9 类工具/IP）
- **CLAUDE.md 重写**：新增"必读文档导航"区，让任意后续模型拿到 CLAUDE+PRDv2+DEVPLAN 三件套即可独立执行
- **首轮回测**：用飞书现有 23 条数据（副业+AI）回测 8 功能位，无空桶；样本太小，结论作为大方向参考

### 关键决策

- **本次只动顶层设计，不动代码**：Opus 做架构，后续具体执行交给更便宜的模型
- **飞书识图不替换**：用户已验证豆包识图成本可接受，进度优先，不再纠结本地化
- **句式独立成表（而非金词的属性）**：句式是骨架，金词是肉，AI 写手的写作流程是"选句式 → 按位填金词"，绑死会丧失复用性
- **周报必须含元认知区**：对功能位模型/prompt/分词策略本身做反思，避免长期跑偏

### 待回测（落入 PRD v2 §11）

- 必填位 vs 加分位 vs 辅助位分级：样本量 ≥200 条多赛道后判断
- 第 9 类"工具/IP 名"是否独立：Phase 2 跑通后专项回测

### 顺手清理

- `.gitignore` 新增：`scripts/covers/*.webp`、`scripts/covers/*.json`、`scripts/samples/batch_create.json`（phase 1.2++ 临时调试产物）

### 备注

本次不勾选 1.3 任务——1.3 的实际"建表 + 飞书读写封装"代码工作尚未做，只是把 v2 的字段要求落入 DEVPLAN。下次会话从 1.3 实操开始。

---

## [2026-05-16 11:30] Phase 1.2++ — 视频封面修正 + AI 联调测试

### 完成内容

- **发现并修正视频封面提取逻辑**：`video_info_v2.image.thumbnail` 是小红书自动截取的视频帧（URL 含 `/frame/`），不是博主上传的封面。正确封面统一在 `images_list[cover_image_index]`，和图文笔记完全一致
- **修正 `harvester.py` 和 `upload_covers.py`**：去掉 video 分支，统一用 `images_list` 取封面
- **验证修正效果**：对 post `6a01f9f90000000008032f4b`（视频"副业经验分享喂饭版"）用 `images_list[0].original`（5000px 原图）重新下载上传，确认封面正确
- **AI 关键词联调测试**：搜索 "AI" top 3 视频，完整写入飞书热贴库（含封面附件、URL、互动数据等全部字段）

### 踩坑记录

#### 坑 1：视频封面是视频帧截图，不是博主上传的封面

- **现象**：视频帖子的封面图看起来像"时间点截图拼在一起的图片"
- **原因**：之前代码对 video 类型取 `video_info_v2.image.thumbnail`，这个字段是小红书自动从视频截取的帧（URL 路径含 `/frame/110/0/`），不是博主上传的封面
- **正确做法**：视频帖子也有 `images_list`，博主上传的封面就在 `images_list[cover_image_index]`，和图文笔记完全一致
- **修正**：删除 video 分支，统一用 `images_list` 取封面
  ```
  # 旧逻辑（错误）
  if note.get("type") == "video":
      cover_url = note["video_info_v2"]["image"]["thumbnail"]  # 视频帧截图
  
  # 新逻辑（正确）
  images_list = note.get("images_list", [])
  cover_idx = note.get("cover_image_index", 0)
  cover_url = images_list[cover_idx].url_size_large  # 博主上传的封面
  ```

#### 坑 2：飞书附件字段 `allowed_edit_modes` 阻止 API 上传

- **现象**：更新记录返回 1254027 `UploadAttachNotAllowed`
- **原因**：旧"封面"字段 `allowed_edit_modes.manual=false`，只允许手机扫码上传
- **解决**：删除旧字段 `fld83jGdX6`，重建新字段 `fld3h2c2Pw`（默认允许所有上传方式）

#### 坑 3：飞书 URL 字段格式

- **现象**：创建记录时包含 url 字段返回 1254068 `URLFieldConvFail`
- **原因**：飞书 URL 字段（type 15）通过 lark-cli 创建时不接受纯字符串，需要 `{"link": "url", "text": "显示文本"}` 格式
- **解决**：先创建记录（不含 url），再单独更新 url 字段

#### 坑 4：Windows subprocess 中文编码

- **现象**：Python `subprocess.run(text=True)` 用 GBK 解码 lark-cli 输出，遇到 emoji（❤️😈）报 `UnicodeDecodeError`
- **解决**：改用 `capture_output=True`（返回 bytes）+ `output.decode('utf-8', errors='replace')`

#### 坑 5：视频详情 API 数据结构与图文不同

- **现象**：`get_video_note_detail` 返回的数据取不到 `images_list`
- **原因**：图文详情是 `data.data[0].note_list[0]`（有 note_list 包裹），视频详情是 `data.data[0]` 直接就是笔记数据（无 note_list 包裹）
- **解决**：视频详情直接从 `data.data[0]` 取字段

### 联调测试结果

搜索关键词 "AI"，按热度排序，取 top 3 视频：

| 帖子 | 点赞 | 收藏 | 封面 |
|------|------|------|------|
| DeepSeek+即梦+剪映做视频，真的王炸组合 | 58,326 | 81,317 | 130 KB |
| 沉浸式IP 爆款卡皮巴拉的打工日记！ | 57,750 | 15,776 | 315 KB |
| 红色是毁灭❤️😈 蓝色是冷漠 | 45,693 | 12,396 | 302 KB |

3 条全部成功写入飞书热贴库（post_id、标题、正文、URL、作者、互动数据、搜索关键词、采集时间、封面附件）。

### 备注：新增"封面文案"字段

- 用户在飞书热帖表新增了"封面文案输出结果"字段，用于存储 AI 识图后的封面文字识别结果
- 封面文案和帖子正文（desc）一样，是金词、金句分析的重要素材来源
- 后续蒸馏流程需要同时读取 desc 和封面文案

---

## [2026-05-16 10:50] Phase 1.2+ — 封面图采集 + 飞书附件上传

### 完成内容

- **封面 URL 提取**：在 `harvester.py` 的 `RawPost` 中新增 `cover_url` 字段，搜索接口零成本获取
  - 图文笔记：`images_list[cover_image_index].url_size_large`（1440px）
  - 视频笔记：`video_info_v2.image.thumbnail`（最高 5000px）
- **封面图下载**：`scripts/upload_covers.py` 搜索 TikHub → 匹配飞书记录 → 下载到 `scripts/covers/`
- **飞书附件上传**：`scripts/covers/batch_upload_larkcli.py` 通过 lark-cli UAT 批量上传封面图到飞书多维表附件字段
- **最终结果**：6/20 条热帖成功挂载封面图附件（其余 14 条因 TikHub 搜索结果不确定未匹配）

### 踩坑记录

#### 坑 1：Drive 上传 API 参数名

- **现象**：`upload_all` 返回 1061002 `params error`
- **原因**：参数名是 `file_name`，不是 `filename`。飞书 API 文档明确写的 `file_name`
- **解决**：改 data dict key

#### 坑 2：tenant_access_token 无 Drive 权限

- **现象**：修好参数名后返回 1061004 `forbidden`
- **原因**：应用的 tenant token 只有 `bitable:app` 权限，Drive 媒体上传需要 `drive:file:upload` scope
- **解决**：改用 lark-cli 的 user_access_token（有 `drive:file:upload` scope），通过 Python subprocess 调用 `lark-cli api`

#### 坑 3：附件字段 allowed_edit_modes 阻止 API 上传

- **现象**：写入 file_token 时返回 1254027 `UploadAttachNotAllowed`
- **原因**：旧"封面"字段 `allowed_edit_modes.manual=false`，只允许手机扫码上传，不允许 API 写入
- **解决**：删除旧字段，重新创建 `type=17` 附件字段（默认允许所有上传方式）。新字段 ID：`fld3h2c2Pw`

#### 坑 4：Windows 中文路径 + lark-cli 路径限制

- **现象**：Python subprocess 调 lark-cli 时中文路径（`金词挖掘机`）被编码为乱码（`閲戣瘝鎸栨帢鏈篭`）
- **原因**：Windows 子进程编码 + lark-cli 要求 `--data` 和 `--file` 必须是相对于 cwd 的相对路径
- **解决**：在 `%TEMP%\feishu_upload` 目录（纯 ASCII 路径）执行 lark-cli，JSON 文件和图片都复制到该目录后用相对路径引用

### 可沉淀为 Skill 的流程

> 飞书多维表附件上传（用户原话："以后考虑沉淀 skill"）

核心流程：
1. 上传文件到 Drive：`lark-cli api POST /open-apis/drive/v1/medias/upload_all --as user --data @req.json --file file=cover.jpg`
   - `parent_type: "bitable_image"`（图片）或 `"bitable_file"`（文件）
   - `parent_node: <bitable_app_token>`
   - 返回 `file_token`
2. 更新记录：`lark-cli api PUT /open-apis/bitable/v1/apps/{app}/tables/{table}/records/{record} --as user --data @update.json`
   - `fields: {"字段名": [{"file_token": "xxx"}]}`
3. 注意事项：
   - 附件字段创建时不要设置 `allowed_edit_modes`，保持默认（manual=true）
   - lark-cli 的 `--data @file` 和 `--file` 必须用相对路径（相对 cwd）
   - Windows 环境用纯 ASCII 临时目录执行 lark-cli，避免中文路径编码问题
   - lark-cli 在 Git Bash 下有 `/open-apis/` 路径转换问题，需用 PowerShell 或加 `MSYS_NO_PATHCONV=1`

### 下一步

- 考虑多页搜索或按 post_id 精确查询来补全剩余 14 条封面
- Phase 1.3 飞书读写封装

---

## [2026-05-15 23:20] Phase 1.2 — TikHub 接口联调完成

### 完成内容

- **搜索接口调通**：`GET /api/v1/xiaohongshu/app_v2/search_notes`，关键词"副业"，按热度排序，返回 20 条
- **笔记详情接口调通**：`GET /api/v1/xiaohongshu/app_v2/get_image_note_detail`（图文）和 `get_video_note_detail`（视频），可获取完整正文 + 分享链接
- **热榜接口调通**：`GET /api/v1/xiaohongshu/web_v2/fetch_hot_list`，返回 9 条热榜
- **创建 `goldword/harvester.py`**：实现 `RawPost` dataclass + `search_notes()` + `fetch_note_detail()` + `search_with_detail()` + `fetch_hotlist()`
- **飞书热贴库建好字段**：post_id, title, desc, url, author, note_type, like/collect/comment/share_count, search_keyword, source, harvested_at（共 13 个字段）
- **测试数据写入飞书**：20 条"副业"搜索结果（前 5 条含完整正文和链接）已写入热贴库 `tblg2nOd7LvMZCKC`

### 踩坑记录

#### 坑 1：搜索端点不对

- **现象**：`web_v2/fetch_search_notes` 返回 404
- **原因**：PRD 里写的是 web_v2，但实际 TikHub 推荐用 `app_v2/search_notes`，参数名也从 `keywords` 变为 `keyword`
- **解决**：改用 `app_v2/search_notes`

#### 坑 2：笔记详情端点 404

- **现象**：`app_v2/get_mixed_note_detail` 和 `web_v2/fetch_one_note` 都返回 404
- **原因**：不确定，可能是端点路径问题或需要额外参数
- **解决**：改用 `get_image_note_detail`（对图文和视频都有效），数据结构是 `data.data[0].note_list[0]`

#### 坑 3：详情接口偶发超时

- **现象**：连续调 10 条详情时，第 5-6 条容易超时（30s）
- **解决**：调用量大时需逐条 try-except，跳过失败的；后续可增大 timeout 到 60s 或加 retry

#### 坑 4：视频笔记无链接

- **现象**：视频笔记的详情接口不返回 `share_info.link`，且部分视频笔记 `note_list` 为空
- **原因**：视频笔记的内容在视频里，API 不一定返回文字详情
- **解决**：所有笔记的链接统一用 `https://www.xiaohongshu.com/explore/{note_id}` 拼接，不依赖详情接口的 share_info。只对图文笔记调详情接口拿完整正文，视频笔记跳过（省 API 费用）

#### 坑 5：表创建时默认空行

- **现象**：第一次写入数据后，飞书表前 5 行为空行，数据从第 6 行开始
- **原因**：新建表时飞书自动插入了几行空记录
- **解决**：写入前先清空表

#### 坑 6：链接缺 xsec_token 导致"帖子不存在"

- **现象**：用 `https://www.xiaohongshu.com/explore/{note_id}` 拼接的链接在浏览器中打开显示"帖子不存在"
- **原因**：小红书需要 `xsec_token` 参数才能访问帖子页，裸链接会被拦截
- **解决**：搜索接口返回的 `note.xsec_token` 字段里就有 token，直接拼到 URL：`/explore/{id}?xsec_token=xxx&xsec_source=pc_search`。零成本，不需要额外调 API
- **已重写飞书数据**：清掉旧数据，20 条全部用带 xsec_token 的链接重新写入

### 费用记录

- 搜索接口：~$0.01/次（20 条结果）
- 笔记详情接口：~$0.02/次（每条笔记）
- 热榜接口：~$0.01/次
- 本次联调总花费：约 $0.47（含多次调试 + 最终写入 20 条）

### 搜索策略确认（与用户讨论后）

- **前期（数据积累）**：时间不限，按点赞排序，每词 1 页 ~20 条，图文笔记补详情
- **后期（稳定运行）**：一周内，每词 top 10，可尝试收藏排序
- 视频笔记只保留摘要 + 拼接链接，不浪费详情 API

### 字段映射（实际 API 字段 → RawPost 字段）

| RawPost 字段 | 搜索接口来源 | 详情接口来源 |
|-------------|-------------|-------------|
| post_id | `note.id` | `note_list[0].id` |
| title | `note.title` | `note_list[0].title` |
| desc | `note.abstract_show`（摘要） | `note_list[0].desc`（完整正文） |
| url | 搜索结果无链接 | `note_list[0].share_info.link` |
| author | `note.user.nickname` | `note_list[0].user.nickname` |
| note_type | `note.type` | 同 |
| like_count | `note.liked_count` | `note_list[0].liked_count` |
| collect_count | `note.collected_count` | `note_list[0].collected_count` |
| comment_count | `note.comments_count` | `note_list[0].comments_count` |
| share_count | `note.shared_count` | `note_list[0].share_info` 中无此字段 |

### 下一步

- 用户去飞书检验写入的数据
- 1.3 飞书读写封装

---

## [2026-05-15 22:30] Phase 0 — 飞书连接调通 + 环境变量就位

### 完成内容

- **收到用户提供的凭据**：TikHub API Key、Git 仓库地址、飞书自建应用（金词 app）、多维表
- **初始化 Git 仓库**：`git init` + `git remote add origin https://github.com/zaizaixiaodi/GoldWordDistiller.git`
- **创建 `.env` / `.env.example` / `.gitignore`**
- **解决 lark-cli 多维表访问问题**（详见下方踩坑记录）
- **确认最终飞书应用**：使用用户自建的「金词」应用（`cli_aa8d9918c778dbb4`），lark-cli 已切换到该应用并重新授权

### 飞书连接完整流程（可 skill 化）

以下是本次跑通的完整流程，未来可作为"飞书多维表项目初始化"skill 模板：

```
步骤 1：安装 lark-cli
  $ npx @larksuite/cli@latest install

步骤 2：配置飞书应用凭据
  $ echo "<APP_SECRET>" | lark-cli config init --app-id <APP_ID> --app-secret-stdin --brand feishu
  注意：--app-secret-stdin 通过 stdin 传入密钥，避免进程列表泄露

步骤 3：OAuth 授权
  $ lark-cli auth login --recommend
  → 输出授权链接 → 用户在浏览器中打开并确认
  → 授权成功后 token 自动存储到 OS keychain

步骤 4：获取正确的 bitable app_token（关键！）
  如果多维表是嵌在 Wiki 里的（URL 格式：my.feishu.cn/wiki/xxx）：
    wiki_token = URL 中 /wiki/ 后面的部分（不是 bitable token！）
    真正的 bitable_token 需要通过 wiki API 获取：
    $ lark-cli wiki node get --token <wiki_token> --format json
    → 返回的 obj_token 才是 bitable API 需要的 app_token
  如果多维表是独立的（URL 格式：xxx.feishu.cn/base/xxx）：
    URL 中 /base/ 后面的部分直接就是 bitable token

步骤 5：验证连通性
  $ lark-cli base +table-list --base-token <BITABLE_TOKEN>
  能列出表名即成功
```

### 踩坑记录

#### 坑 1：wiki token ≠ bitable token

**现象**：lark-cli base 命令报 `param baseToken is invalid`（800004006），但 MCP 工具用同一个 token 能正常访问。

**原因**：用户的多维表是嵌在 Wiki 页面里的。URL `my.feishu.cn/wiki/SlpTwR15riqIuakaeomc4tbEnAb` 中的 `SlpTwR...` 是 **wiki node token**，不是 bitable app_token。lark-cli 的 base v3 shortcut 不认 wiki token，但 MCP 工具内部做了转换所以能工作。

**解决**：通过 wiki API（`lark-cli wiki node get --token <wiki_token>`）查出真正的 `obj_token`（`Z5DubZ9DMaPkgDsbMWScnrgknSz`），这才是 bitable API 的正确 token。

**预防**：以后遇到飞书多维表，先看 URL 格式。如果是 `/wiki/` 开头，必须先查 wiki node 拿 obj_token；如果是 `/base/` 开头，URL 里的 token 直接可用。

#### 坑 2：Windows Git Bash 路径转换

**现象**：lark-cli 的 `api` 子命令调用 raw API 时返回 HTTP 404。

**原因**：Windows 上的 Git Bash 会自动把以 `/` 开头的路径参数转换为 Git 安装目录（如 `/open-apis/xxx` → `C:/Program Files/Git/open-apis/xxx`）。通过 `--dry-run` 发现了实际发送的 URL 被篡改。

**解决**：在命令前加 `MSYS_NO_PATHCONV=1` 环境变量：
```bash
MSYS_NO_PATHCONV=1 lark-cli api GET "/open-apis/bitable/v1/apps/..."
```

**预防**：在 Windows Git Bash 环境下，所有以 `/` 开头的 CLI 参数都需要加 `MSYS_NO_PATHCONV=1`。或者改用 PowerShell 执行。

#### 坑 3：lark-cli 创建的应用无多维表权限

**现象**：用 `lark-cli config init --new` 创建的应用（`cli_aa8d94a223b99bdb`）无法访问用户的多维表。

**原因**：CLI 自动创建的应用没有被添加为多维表的协作者，且通过 API 添加协作者时参数格式不对。

**解决**：改用用户自建的飞书应用（`cli_aa8d9918c778dbb4`），该应用已在飞书后台配置好多维表权限。通过 `lark-cli config init --app-id ... --app-secret-stdin` 切换应用后重新授权即可。

**预防**：如果用 `--new` 创建应用，需要额外把该应用添加为多维表协作者。推荐直接复用已有应用。

### 最终确认的配置

| 配置项 | 值 |
|--------|-----|
| 飞书应用 | `cli_aa8d9918c778dbb4`（用户自建「金词」应用） |
| Bitable app_token | `Z5DubZ9DMaPkgDsbMWScnrgknSz`（wiki 内嵌，非 URL 中的 wiki token） |
| 热贴库 table_id | `tblg2nOd7LvMZCKC`（当前为空，待建字段） |
| 金词库 table_id | `tblqAKnCwubtFS0y`（当前为空，待建字段） |
| 配置表 table_id | `tbl7nJSXfjTkreFM`（当前为空，待建字段） |
| Git 远程仓库 | `https://github.com/zaizaixiaodi/GoldWordDistiller.git` |

### 下一步

- 按 PRD §3.1 / §3.2 / §3.3 给三张表建字段
- 创建 `goldword/config.py` 骨架
- Phase 0.1 DoD 自检

---

## [2026-05-15 22:15] Phase 0 — 飞书 CLI 方案升级 + 环境搭建

### 完成内容

- **技术方案变更**：飞书集成从"手写 `lark-oapi` SDK 封装"升级为"基于 `lark-cli`（飞书官方 CLI 工具 v1.0.32）的薄封装层"
- **安装 `lark-cli`**：通过 `npx @larksuite/cli@latest install` 全局安装，版本 1.0.32
- **创建飞书应用**：`lark-cli config init --new` → App ID: `cli_aa8d94a223b99bdb`
- **OAuth 授权**：`lark-cli auth login --recommend` → 用户王亚辉授权成功，获得全部 `base:*` 权限
- **更新 PRD v1.1**：修改 §6.1 技术栈、§6.2 模块划分、§7.5 环境变量、Phase 1.3 概述
- **更新 DEVPLAN v1.1**：修改 §0.1（环境变量减少，增加 lark-cli 认证步骤）、§1.3（飞书搭建方案重写）、新增变更记录

### 关键决策

- **为什么选 lark-cli 而不是手写封装**：
  - lark-cli 是飞书官方维护的 CLI 工具，专门为 AI Agent 设计
  - 内置 auth 管理（OAuth 登录、token 缓存/刷新）、分页、dry-run、结构化输出
  - `lark-base` skill 覆盖多维表全部 CRUD，不需要手写请求构建和错误重试
  - `feishu.py` 从"完整的 API 客户端"降级为"调用 lark-cli 的薄封装层"，代码量减少约 80%
- **环境变量减少**：`FEISHU_APP_ID` / `FEISHU_APP_SECRET` 不再需要写在 `.env` 中，改由 `lark-cli auth` 管理，凭证存储在 OS 原生 keychain，更安全

### 换设备须知

`lark-cli` 是全局安装的工具，不随项目仓库走。在另一台设备上恢复开发时：

1. 安装 lark-cli：`npx @larksuite/cli@latest install`
2. 配置应用：`echo "<APP_SECRET>" | lark-cli config init --app-id cli_aa8d9918c778dbb4 --app-secret-stdin --brand feishu`
3. OAuth 登录：`lark-cli auth login --recommend`
4. 项目代码中的 `.env` 仍需在新设备上创建（TikHub Key + 飞表 ID，注意 wiki token ≠ bitable token）

### 问题与解决

- 无阻塞问题，安装和授权均一次通过

---

## [2026-05-15] Phase 0.1 前 — PRD v1.1 + DEVPLAN v1 创建

- PRD v1.1 初版完成，定义了三层词汇模型、四个数据入口、飞书多维表结构、蒸馏流程
- DEVPLAN v1 初版完成，按 PRD 拆解为 Phase 0-3 共 12 个任务，每个任务含 DoD 和产物文件
