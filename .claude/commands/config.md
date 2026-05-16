查看或编辑搜索配置（领域词 / 搜索词）。

参数: $ARGUMENTS

## 执行步骤

1. 如果 $ARGUMENTS 包含 `--add`：
   - 解析 `--domain <领域>` 和 `--keyword <搜索词>` 参数
   - 写入飞书配置表：
     ```
     python -c "
     import sys,io;sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding='utf-8',errors='replace')
     from goldword.feishu import insert_config
     rid=insert_config('DOMAIN','KEYWORD')
     print(f'已添加: {rid}')
     "
     ```
     替换 DOMAIN / KEYWORD 为实际值
2. 如果 $ARGUMENTS 包含 `--deactivate`：
   - 先运行 `python -m goldword.cli config` 展示当前配置
   - 确认要停用哪条，然后通过飞书 update 将 is_active 设为 false
3. 否则（查看模式）：
   - 运行 `python -m goldword.cli config`
   - 将输出展示给用户
