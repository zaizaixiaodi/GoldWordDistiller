浏览或管理句式库。

参数: $ARGUMENTS

## 执行步骤

1. 如果 $ARGUMENTS 包含 `--add`：
   - 解析 `--add "<骨架>"` 和 `--category <类型>` 参数
   - 构造句式数据并写入飞书：
     ```
     python -c "
     import sys,io;sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding='utf-8',errors='replace')
     from datetime import datetime
     from goldword.feishu import insert_pattern
     now_ms=int(datetime.now().timestamp()*1000)
     rid=insert_pattern({
       'skeleton':'SKELETON','category':'CATEGORY',
       'frequency':1,'first_seen':now_ms,'last_seen':now_ms,'trend':'新句式'
     })
     print(f'已写入句式库: {rid}')
     "
     ```
     替换 SKELETON / CATEGORY 为实际值
2. 否则（无参数或浏览模式）：
   - 运行 `python -m goldword.cli patterns`
   - 将输出展示给用户
