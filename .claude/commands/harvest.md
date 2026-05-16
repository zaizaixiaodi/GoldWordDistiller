执行一次完整的金词采集管道。

参数: $ARGUMENTS

## 执行步骤

1. 如果 $ARGUMENTS 包含 `--dry-run`：运行 `python -c "from goldword.harvester import harvest_all; harvest_all(dry_run=True)"` 只需打印计划。
2. 否则运行完整采集：`python -c "from goldword.harvester import harvest_all; r = harvest_all(); print(f'写入 {r.total_inserted} 条 / 重复 {r.total_duplicates} 条 / API {r.api_calls} 次')"`
3. 将输出原样展示给用户。
4. 如果写入数 > 0，询问用户是否需要在飞书热贴库肉眼确认数据。
