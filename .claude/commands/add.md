手动添加金词到飞书金词库（真人甄选，PRD v2 §3.4）。

参数: $ARGUMENTS

## 语法

`/add "<金词>" --field <title|cover> --category <功能位> --domain <领域> --note "<备注>"`

- `--field`、`--category`、`--domain`、`--note` 均为可选
- 不指定 `--category` 时，由 Claude 推断功能位
- `--field` 默认 `title`

## 执行步骤

1. 从 $ARGUMENTS 解析出金词和各参数
2. 如果未指定 `--category`，根据金词内容推断 8 功能位之一（who/when/pain/do/twist/number/feel/picture）
3. 如果未指定 `--field`，默认为 `title`
4. 构造写入数据并调用飞书：
   ```
   python -c "
   import sys,io;sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding='utf-8',errors='replace')
   from datetime import datetime
   from goldword.feishu import insert_word
   now_ms=int(datetime.now().timestamp()*1000)
   rid=insert_word({
     'word':'WORD','category':'CATEGORY','source_field':'FIELD',
     'domain':'DOMAIN','vibe_score':VIBE,'frequency':1,
     'first_seen':now_ms,'last_seen':now_ms,'trend':'新词',
     'source':'人工精选','status':'待审','user_note':'NOTE'
   })
   print(f'已写入飞书金词库: {rid}')
   "
   ```
   替换 WORD / CATEGORY / FIELD / DOMAIN / VIBE / NOTE 为实际值
5. 展示写入结果给用户
