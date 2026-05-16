查看金词列表。

参数: $ARGUMENTS

## 执行步骤

1. 解析 $ARGUMENTS 中的过滤参数，支持的选项：
   - `--category <功能位>` — 按 8 功能位过滤（who/when/pain/do/twist/number/feel/picture）
   - `--field <title|cover>` — 按来源字段过滤（both 会同时出现在两个结果中）
   - `--trend <up|down|stable|new>` — 按趋势过滤
   - `--status <pending|adopted|used|stale>` — 按状态过滤
   - `--domain <领域>` — 按领域词过滤
   - `--min-vibe <N>` — 最低 vibe_score 阈值
2. 运行 `python -m goldword.cli list` 加上解析出的参数
3. 将输出展示给用户
