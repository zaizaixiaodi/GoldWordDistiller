喂入外部素材（他山之石），走蒸馏流程后写入金词库。

参数: $ARGUMENTS

## 输入格式

- `/feed <url>` — 喂入 URL（小红书链接走 TikHub，其他走通用抓取）
- `/feed --text "一段文案内容"` — 直接喂入文本
- `/feed --file <path>` — 喂入本地文件

## 执行步骤

1. 判断输入类型并提取内容：
   - URL：运行 `python -c "import sys,io,json;sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding='utf-8',errors='replace');from goldword.feeder import feed_url;print(json.dumps(feed_url('URL'),ensure_ascii=False))"`（替换 URL）
   - 文本：运行 `python -c "import sys,io,json;sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding='utf-8',errors='replace');from goldword.feeder import feed_text;print(json.dumps(feed_text('TEXT'),ensure_ascii=False))"`（替换 TEXT）
   - 文件：运行 `python -c "import sys,io,json;sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding='utf-8',errors='replace');from goldword.feeder import feed_file;print(json.dumps(feed_file('PATH'),ensure_ascii=False))"`（替换 PATH）
2. 如果返回结果包含 `error` 字段，展示错误并停止
3. 读取 `prompts/distill.md` 蒸馏 prompt 模板
4. 对提取到的内容执行蒸馏分析：
   - 标题路 + 封面路（如有）分别处理
   - 按 8 功能位打标（category）
   - 给 vibe_score（< 3 丢弃）
   - 识别句式骨架
   - 所有提取结果标记 source="他山之石"
5. 将蒸馏结果格式化为 JSON（gold_words + patterns）
6. 调用 tracker 追踪趋势并写入飞书：
   - `python -c "import sys,io,json;sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding='utf-8',errors='replace');from goldword.tracker import track_words,upsert_words;td=json.loads('TRACKED_JSON');r=upsert_words(td);print(f'金词: insert {r[\"inserted\"]} update {r[\"updated\"]} error {r[\"errors\"]}')"`
   - 同样处理 patterns（track_patterns + upsert_patterns）
7. 展示蒸馏结果摘要给用户
