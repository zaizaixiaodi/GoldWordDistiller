查看简报或周报。

参数: $ARGUMENTS

## 执行步骤

### 无参数：实时简报

1. 运行 `python -c "import sys,io;sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding='utf-8',errors='replace');from goldword.reporter import generate_brief;print(generate_brief())"` 
2. 将输出的简报展示给用户

### `--weekly`：周报

1. 提取 `--week` 参数（格式 `YYYY-WNN`，如 `2026-W20`）。无此参数则默认本周。
2. 运行 `python -c "import sys,io;sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding='utf-8',errors='replace');from goldword.reporter import generate_weekly_report;print(generate_weekly_report())"` （如有 --week 参数，在括号内传入 week 字符串）
3. 将生成的周报展示给用户
4. **补充 §6 选题建议**：从本周高 vibe 金词 + 升温句式中组合生成 5 个候选标题/封面，追加到周报的 §6 节
5. **检查 §7 元认知反思**：确认功能位分布是否均衡，有无空桶或异常聚集；如有人审反馈，标注漏检/误检案例
6. 更新后的完整周报保存回 `workspace/reports/weekly_*.md`
