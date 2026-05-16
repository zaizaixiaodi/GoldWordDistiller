批量重蒸馏飞书热贴库的金词与句式（4 步手动流水线）。

参数: $ARGUMENTS

## 何时用此命令

- 用户说"重新蒸馏全量帖子"、"对某领域重做蒸馏"、"把飞书帖子再过一遍金词"等
- 与 `/harvest` 流程的区别：`/harvest` 是采集 → 写热贴 → 立即蒸馏；本命令是**只对飞书里已存在的热贴**做（再）蒸馏，不调 TikHub

## 4 步流水线

```
[Step 1] python scripts/export_posts.py
   ↓ workspace/distilled/posts_for_redistill.json （按 domain 分组）

[Step 2] python scripts/format_batch.py <domain> [start] [limit]
   ↓ stdout 蒸馏 prompt 输入文本
   ↓ AI 把它存到 workspace/distilled/batch_<标签>_input.txt

[Step 3] AI 按 prompts/distill.md + prompts/patterns_reference.md 蒸馏
   ↓ workspace/distilled/batch_<标签>_result.json （gold_words + patterns）

[Step 4] python scripts/write_distill.py --input workspace/distilled/batch_<标签>_result.json
   ↓ 经 tracker upsert 到飞书金词库 + 句式库（自动打趋势标签）
```

辅助：`python scripts/check_posts.py` 看各 domain 帖子数量分布，用于规划批次大小。

## 执行步骤（AI 按此推进）

### 解析参数

- 无参 → 把以下内容原样回给用户：本文件的 4 步流水线说明 + 各 domain 帖子数（先跑 Step 1 再跑 check_posts.py）
- `<domain>` 或 `<domain> <start> <limit>` → 直接从 Step 2 开始（假设用户已有最近的 posts_for_redistill.json，若文件不存在则先跑 Step 1）
- `--all` → 全量重蒸：对每个 domain 自动切分批次（每批 50 条）依次执行 Step 2-4

### Step 1：导出飞书帖子

```bash
python scripts/export_posts.py
```

产物：`workspace/distilled/posts_for_redistill.json`，结构：
```json
{
  "搞钱": [{"record_id": "...", "title": "...", "desc": "...", "cover_text": "...", "like": N, "collect": N, "domain": "搞钱"}, ...],
  "AI 应用": [...],
  ...
}
```

### Step 2：切批次并格式化

```bash
python scripts/format_batch.py 搞钱 0 50
```

stdout 形如：
```
domain: 搞钱  batch: [0-50]  total available: 153

[recvjHJK...] 标题 | 点赞: 1234 | 收藏: 567 | 关键词: 搞钱
正文（摘要）: ...
封面文案: ...
```

把 stdout 内容保存到 `workspace/distilled/batch_<domain拼音简写>_<序号>_input.txt`（命名约定见下方"批次标签"）。

### Step 3：AI 蒸馏

读 `prompts/distill.md`（规则） + `prompts/patterns_reference.md`（句式抽象参考） + 上一步 input.txt（数据）。

按 prompt 规则输出严格 JSON：

```json
{
  "gold_words": [
    {"word": "死磕", "aliases": "狠下心来死磕", "category": "do", "source_field": "title", "vibe_score": 7, "frequency": 1, "related_post_ids": ["rec..."], "vibe_reason": "..."}
  ],
  "patterns": [
    {"skeleton": "A 的 N 种 B", "category": "清单", "examples": ["36种可以躺赢的收入"], "from_post_ids": ["rec..."]}
  ]
}
```

**关键约束**（来自 DEVLOG 2026-05-16 踩坑）：
- `aliases` 必须是字符串（用 `", "` 连接多个），**不要**输出数组 → 否则飞书 TextFieldConvFail
- 还要默认带 `"domain": "<本批领域>"` 字段（否则 tracker 写飞书时 domain 会落空字符串）
- vibe_score < 3 的词不要出现在输出中
- patterns 的 skeleton 要抽象（参考 patterns_reference.md 的 15 个样例的抽象度）

保存为 `workspace/distilled/batch_<标签>_result.json`。

### Step 4：写回飞书

```bash
python scripts/write_distill.py --input workspace/distilled/batch_<标签>_result.json
```

控制台输出形如：
```
[batch_gq_01_result] 追踪 29 金词 + 7 句式 ...
  金词: insert 26 / update 3 / error 0
  句式: insert 5 / update 2 / error 0
  [batch_gq_01_result] 完成
```

## 批次标签约定

| domain | 拼音简写 |
|---|---|
| 搞钱 | gq |
| AI 应用 | ai |
| 个人成长 | gr |
| 人生务虚 | rswx |
| 职场 | zc |
| 自媒体 | mt |
| 未分类 | wfl |

格式：`batch_<拼音简写>_<两位序号>_{input.txt | result.json}`，如 `batch_gq_01_input.txt`、`batch_ai_02_result.json`。

## 完成后

执行完一批或全量后，建议跑：

```bash
python -m goldword.cli list --min-vibe 7 --domain 搞钱
```

肉眼校验本次新增的金词是否合理。如果有明显错检 / 漏检，把案例补到 `prompts/observations.md`，下次蒸馏 prompt 迭代时使用。

## 历史背景

本命令是 DEVLOG 2026-05-16「问题 3」的修复 —— 上一轮蒸馏 496 条帖子时不得不手工切 batch、产生临时脚本。本流水线把那些脚本扶正为正式工具，让后续会话不必重新摸索。
