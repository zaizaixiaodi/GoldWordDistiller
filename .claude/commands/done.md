记录本次工作到 DEVLOG 并提交 git。

参数: $ARGUMENTS

## 执行步骤

1. 读取 `DEVPLAN.md`，找到当前阶段和第一个未勾选的任务编号
2. 在 `DEVLOG.md` 顶部（第一个 `---` 分隔线之后）追加新条目：
   - 格式：`## [YYYY-MM-DD HH:MM] Phase X.Y - <简要标题>`
   - 包含：完成内容（3-5 条要点）、关键决策（如有）、问题与解决（如有）
   - 保持简洁，不要啰嗦
3. 更新 `DEVPLAN.md`：
   - 将当前任务从 `[ ]` 改为 `[x]`
   - 更新"当前阶段"和"当前任务"指针到下一个未完成的任务
   - 更新"最近一次更新"时间戳
4. 执行 git 操作：
   ```
   git add -A
   git commit -m "[phase X.Y] <简要描述>"
   git push origin main
   ```
   commit message 从本次工作内容中提取，使用 `[phase X.Y]` 前缀

如果用户提供了参数（$ARGUMENTS），将其作为本次工作摘要的核心内容。
