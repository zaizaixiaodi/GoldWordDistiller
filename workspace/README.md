# workspace/ — 数据资产与业务产物

这里是「点进去就能看到能用的东西」的入口。代码在 `goldword/`，prompt 在 `prompts/`，开发工具在 `scripts/`，**数据和报告在这里**。

## 目录速查

| 子目录 | 装什么 | 来源 / 触发 |
|---|---|---|
| `raw_api/` | TikHub 每次搜索 / 详情 / 热榜的原始 JSON 返回 | `harvester.py:_save_raw` 自动落盘，永久存档避免重复查询 |
| `harvest_backups/` | 每次 `/harvest` 写入飞书前的全量备份 | `harvester.harvest_all` 自动 dump 为 `harvest_YYYYMMDD_HHMMSS.json` |
| `distilled/` | 蒸馏中间产物（候选金词 / 句式 / 摘要骨架等） | 历史 dump + 未来 distiller 落盘的中间结果 |
| `reports/` | 周报 / 简报（人审用） | `/report` 命令生成 `weekly_YYYY-WNN.md` |

## 跟代码的关系

- **写入端**：`goldword/harvester.py` 写 `raw_api/` 和 `harvest_backups/`，`goldword/reporter.py`（尚未实现）写 `reports/`
- **读取端**：基本上是给人看的；除了 `raw_api/` 有时用于回测 / 重跑蒸馏不再调 TikHub

## 不该出现在这里的东西

- 一次性调试脚本 → `scripts/_archive/`
- 临时下载的图片、临时 JSON dump → 系统 temp 或 gitignore
- 开发期联调脚本 → `scripts/probe/`
