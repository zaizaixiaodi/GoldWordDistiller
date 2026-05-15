# DEVLOG — 金词蒸馏器

> 按时间倒序排列。每次完成有意义的工作单元后追加。

---

## [2026-05-15 22:30] Phase 0 — 飞书连接调通 + 环境变量就位

### 完成内容

- **收到用户提供的凭据**：TikHub API Key、Git 仓库地址、飞书自建应用（金词 app）、多维表
- **初始化 Git 仓库**：`git init` + `git remote add origin https://github.com/zaizaixiaodi/GoldWordDistiller.git`
- **创建 `.env` / `.env.example` / `.gitignore`**
- **解决 lark-cli 多维表访问问题**（详见下方踩坑记录）
- **确认最终飞书应用**：使用用户自建的「金词」应用（`cli_aa8d9918c778dbb4`），lark-cli 已切换到该应用并重新授权

### 飞书连接完整流程（可 skill 化）

以下是本次跑通的完整流程，未来可作为"飞书多维表项目初始化"skill 模板：

```
步骤 1：安装 lark-cli
  $ npx @larksuite/cli@latest install

步骤 2：配置飞书应用凭据
  $ echo "<APP_SECRET>" | lark-cli config init --app-id <APP_ID> --app-secret-stdin --brand feishu
  注意：--app-secret-stdin 通过 stdin 传入密钥，避免进程列表泄露

步骤 3：OAuth 授权
  $ lark-cli auth login --recommend
  → 输出授权链接 → 用户在浏览器中打开并确认
  → 授权成功后 token 自动存储到 OS keychain

步骤 4：获取正确的 bitable app_token（关键！）
  如果多维表是嵌在 Wiki 里的（URL 格式：my.feishu.cn/wiki/xxx）：
    wiki_token = URL 中 /wiki/ 后面的部分（不是 bitable token！）
    真正的 bitable_token 需要通过 wiki API 获取：
    $ lark-cli wiki node get --token <wiki_token> --format json
    → 返回的 obj_token 才是 bitable API 需要的 app_token
  如果多维表是独立的（URL 格式：xxx.feishu.cn/base/xxx）：
    URL 中 /base/ 后面的部分直接就是 bitable token

步骤 5：验证连通性
  $ lark-cli base +table-list --base-token <BITABLE_TOKEN>
  能列出表名即成功
```

### 踩坑记录

#### 坑 1：wiki token ≠ bitable token

**现象**：lark-cli base 命令报 `param baseToken is invalid`（800004006），但 MCP 工具用同一个 token 能正常访问。

**原因**：用户的多维表是嵌在 Wiki 页面里的。URL `my.feishu.cn/wiki/SlpTwR15riqIuakaeomc4tbEnAb` 中的 `SlpTwR...` 是 **wiki node token**，不是 bitable app_token。lark-cli 的 base v3 shortcut 不认 wiki token，但 MCP 工具内部做了转换所以能工作。

**解决**：通过 wiki API（`lark-cli wiki node get --token <wiki_token>`）查出真正的 `obj_token`（`Z5DubZ9DMaPkgDsbMWScnrgknSz`），这才是 bitable API 的正确 token。

**预防**：以后遇到飞书多维表，先看 URL 格式。如果是 `/wiki/` 开头，必须先查 wiki node 拿 obj_token；如果是 `/base/` 开头，URL 里的 token 直接可用。

#### 坑 2：Windows Git Bash 路径转换

**现象**：lark-cli 的 `api` 子命令调用 raw API 时返回 HTTP 404。

**原因**：Windows 上的 Git Bash 会自动把以 `/` 开头的路径参数转换为 Git 安装目录（如 `/open-apis/xxx` → `C:/Program Files/Git/open-apis/xxx`）。通过 `--dry-run` 发现了实际发送的 URL 被篡改。

**解决**：在命令前加 `MSYS_NO_PATHCONV=1` 环境变量：
```bash
MSYS_NO_PATHCONV=1 lark-cli api GET "/open-apis/bitable/v1/apps/..."
```

**预防**：在 Windows Git Bash 环境下，所有以 `/` 开头的 CLI 参数都需要加 `MSYS_NO_PATHCONV=1`。或者改用 PowerShell 执行。

#### 坑 3：lark-cli 创建的应用无多维表权限

**现象**：用 `lark-cli config init --new` 创建的应用（`cli_aa8d94a223b99bdb`）无法访问用户的多维表。

**原因**：CLI 自动创建的应用没有被添加为多维表的协作者，且通过 API 添加协作者时参数格式不对。

**解决**：改用用户自建的飞书应用（`cli_aa8d9918c778dbb4`），该应用已在飞书后台配置好多维表权限。通过 `lark-cli config init --app-id ... --app-secret-stdin` 切换应用后重新授权即可。

**预防**：如果用 `--new` 创建应用，需要额外把该应用添加为多维表协作者。推荐直接复用已有应用。

### 最终确认的配置

| 配置项 | 值 |
|--------|-----|
| 飞书应用 | `cli_aa8d9918c778dbb4`（用户自建「金词」应用） |
| Bitable app_token | `Z5DubZ9DMaPkgDsbMWScnrgknSz`（wiki 内嵌，非 URL 中的 wiki token） |
| 热贴库 table_id | `tblg2nOd7LvMZCKC`（当前为空，待建字段） |
| 金词库 table_id | `tblqAKnCwubtFS0y`（当前为空，待建字段） |
| 配置表 table_id | `tbl7nJSXfjTkreFM`（当前为空，待建字段） |
| Git 远程仓库 | `https://github.com/zaizaixiaodi/GoldWordDistiller.git` |

### 下一步

- 按 PRD §3.1 / §3.2 / §3.3 给三张表建字段
- 创建 `goldword/config.py` 骨架
- Phase 0.1 DoD 自检

---

## [2026-05-15 22:15] Phase 0 — 飞书 CLI 方案升级 + 环境搭建

### 完成内容

- **技术方案变更**：飞书集成从"手写 `lark-oapi` SDK 封装"升级为"基于 `lark-cli`（飞书官方 CLI 工具 v1.0.32）的薄封装层"
- **安装 `lark-cli`**：通过 `npx @larksuite/cli@latest install` 全局安装，版本 1.0.32
- **创建飞书应用**：`lark-cli config init --new` → App ID: `cli_aa8d94a223b99bdb`
- **OAuth 授权**：`lark-cli auth login --recommend` → 用户王亚辉授权成功，获得全部 `base:*` 权限
- **更新 PRD v1.1**：修改 §6.1 技术栈、§6.2 模块划分、§7.5 环境变量、Phase 1.3 概述
- **更新 DEVPLAN v1.1**：修改 §0.1（环境变量减少，增加 lark-cli 认证步骤）、§1.3（飞书搭建方案重写）、新增变更记录

### 关键决策

- **为什么选 lark-cli 而不是手写封装**：
  - lark-cli 是飞书官方维护的 CLI 工具，专门为 AI Agent 设计
  - 内置 auth 管理（OAuth 登录、token 缓存/刷新）、分页、dry-run、结构化输出
  - `lark-base` skill 覆盖多维表全部 CRUD，不需要手写请求构建和错误重试
  - `feishu.py` 从"完整的 API 客户端"降级为"调用 lark-cli 的薄封装层"，代码量减少约 80%
- **环境变量减少**：`FEISHU_APP_ID` / `FEISHU_APP_SECRET` 不再需要写在 `.env` 中，改由 `lark-cli auth` 管理，凭证存储在 OS 原生 keychain，更安全

### 换设备须知

`lark-cli` 是全局安装的工具，不随项目仓库走。在另一台设备上恢复开发时：

1. 安装 lark-cli：`npx @larksuite/cli@latest install`
2. 配置应用：`echo "<APP_SECRET>" | lark-cli config init --app-id cli_aa8d9918c778dbb4 --app-secret-stdin --brand feishu`
3. OAuth 登录：`lark-cli auth login --recommend`
4. 项目代码中的 `.env` 仍需在新设备上创建（TikHub Key + 飞表 ID，注意 wiki token ≠ bitable token）

### 问题与解决

- 无阻塞问题，安装和授权均一次通过

---

## [2026-05-15] Phase 0.1 前 — PRD v1.1 + DEVPLAN v1 创建

- PRD v1.1 初版完成，定义了三层词汇模型、四个数据入口、飞书多维表结构、蒸馏流程
- DEVPLAN v1 初版完成，按 PRD 拆解为 Phase 0-3 共 12 个任务，每个任务含 DoD 和产物文件
