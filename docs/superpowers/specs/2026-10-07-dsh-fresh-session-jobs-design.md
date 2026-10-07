# DSH 定时任务「每次投递新建会话」设计

- 状态：draft（待用户审阅）
- 日期：2026-10-07
- 归属：DeepSeek Harness（DSH）能力，不是 repo-signal 站点功能
- 交付形态：**独立宿主插件（profile bundle）**，不修改内置 `@deepseek-ai/dsh-schedule`
- 相关文档：`@deepseek-ai/dsh-schedule` README、`@deepseek-ai/dsh-workspace` README、`@deepseek-ai/dsh-agent-loop` README、`@deepseek-ai/dsh-storage-domain` README、`cordis-plugin-development` 技能

## 1. 背景与问题

内置 schedule 把提醒投递回**任务所属的原会话**：`delivery` 通过 `sessionController.resolveAgent` 解析原会话，再用插件来源的 `followup()` 把消息追加进该会话收件箱。

于是「任务的设计与调试对话」和「每天的运行记录」堆在同一个会话里。当前这台机器上的实测数据（会话 `session-0faa1c50`，18 轮 / 2320 条 / 1.8 MB）：

| 轮次 | 时间 | 记录数 | 内容 |
|---|---|---|---|
| 1–16 | 10-05 21:08–22:31 | 1737 | 与用户设计、调试该定时任务的讨论 |
| 17 | 10-06 06:30 | 105 | 一次每日运行 |
| 18 | 10-07 06:30 | 41 | 一次每日运行 |

后果：每天唤起都要带着全部历史；一天的运行记录无法单独审计、单独清理；失败的那天淹没在设计讨论里。

内置 schedule 明确不支持这个能力（`dsh-schedule` README：「不支持暂停、执行状态、原会话以外的投递或**每次运行新建会话**」）。因此本设计不改它，而是新增一种**旁路任务类型**：每次触发都新建会话执行，原会话只收结果回执。

## 2. 目标与非目标

**目标**

1. 定时任务每次触发，都在指定工作区新建一个会话执行该任务的提示词。
2. 运行结束（无论成功或失败）后自动归档该会话，侧边栏不被每日运行占满。
3. 任务所属会话（owner session）收到一条结果回执，作为「失败也会被归档」前提下唯一的异常提示渠道。
4. 与内置 schedule 完全并存：内置任务行为不变，两类任务可在同一个会话里共存。

**非目标**

- 不修改内置 schedule 的存储、投递语义与工具。
- 不做跨设备/云端调度；宿主不在线时的补发语义与内置保持一致。
- v1 不做客户端 UI（管理通过 agent 工具，观测通过回执）。
- 不做任务模板、任务依赖链、运行失败后的自动重试、任务级并发编排。（第 7 节中「归档失败后由启动对账重试一次」是对账修复，不是运行重试。）

## 3. 行为契约

### 3.1 任务字段

| 字段 | 必填 | 说明 |
|---|---|---|
| `id` | 是 | 宿主唯一 id |
| `title` | 是 | 任务名，同时用于新会话标题前缀与回执 |
| `prompt` | 是 | 投递给新会话的提示词正文 |
| `rule` | 是 | `daily` / `every` / `cron` 之一，含时区（默认 `Asia/Shanghai`） |
| `workspaceId` | 是 | 新会话所属工作区；创建任务时默认取 owner 会话所在工作区 |
| `ownerSessionId` | 是 | 回执投递目标；同时作为任务的管理入口 |
| `agentOptions` | 否 | 模型 / 推理档位覆盖；缺省时用 profile 默认 |
| `enabled` | 是 | 关闭后不再触发，记录保留 |
| `nextAt` | 由调度器维护 | 下一个发生时点 |

### 3.2 一次投递的时序

1. **到点**（按任务配置的时区计算）。
2. **幂等检查**：发生键 = `jobId + 发生时点`；已存在同键 run 则直接跳过，不重复投递。
3. **并发检查**：同一任务的上一次 run 仍为 `running` → 记一条 `skipped`（原因 `previous-running`），发回执，并推进 `nextAt`。**不排队**。
4. **新建会话**：在 `workspaceId` 对应工作区创建会话，工作目录取该工作区目录；模型/推理档位取 `agentOptions`，缺省用 profile 默认；权限预设与沙箱模式用 profile 默认。
5. **显式命名**：会话标题固定为 `{title} {YYYY-MM-DD}`（例如 `每日GitHub组合可行性方案 2026-10-07`）。使用显式重命名，避免自动标题随之改写。
6. **注入首条消息**：首行 `[定时任务] {title} · {YYYY-MM-DD HH:mm}`，空行后接 `prompt` 正文；来源标记为插件来源。
7. **等首轮 `turn/end`**：以该事件判定本次运行结果。
8. **归档会话**：成功、失败、中断**一律归档**。
9. **发回执**：向 `ownerSessionId` 追加回执消息。

### 3.3 回执

- 触发时机：该次会话首轮 `turn/end` 之后（一次运行一条）。
- 内容：任务名、发生时点、状态（完成 / 失败 / 中断 / 跳过）、新会话标题与会话 id、一句话摘要（取该会话最后一条 assistant 文本的前 200 字，超出截断）；归档失败时额外标注「未归档」。
- 写入方式：与内置 schedule 投递同一机制——插件来源消息追加到 owner 会话，待会话 flush 确认即视为已投递。
- 降级：owner 会话不存在或已被删除 → 记日志，run 标记 `receiptAt: null`，不影响任务状态与后续触发。

### 3.4 错过、重启与对账

- **宿主重启**：错过的发生时点**只补发最近一次**（与内置 schedule 一致）。
- **本地钟表语义**：与内置 schedule 相同——夏令时不存在的时刻跳过，重复的时刻取较早者。
- **运行中重启**：启动对账把仍为 `running`、但其会话已无活跃 turn 的 run 记为 `interrupted`，并补发回执。
- **归档未完成**：启动对账对 `completed` 但 `archived: false` 的 run 重试归档一次。

### 3.5 不变量

- 归档只发生在首轮结束之后（此时该会话无活跃工作，不触发工作区归档准入的拒绝）；不使用 `stopActivity` 强制归档。
- 会话标题只在创建时设定一次，运行期间不自动改写。
- 每个发生时点最多产生一个会话、一条回执。
- 本插件不写入内置 schedule 的任何存储域。

## 4. 架构与组件

一个宿主侧 Cordis 插件包，按 `cordis-plugin-development` 的 bundle 形态交付（`package.json` 声明 `dsh.bundle.patch`，用 `cordis.patch.yml` 插入一行）。

| 组件 | 职责 | 依赖的宿主能力 |
|---|---|---|
| `Scheduler` | 单定时器 + 到期计算；宿主重启后重算并对账 | 宿主定时器；自有 domain |
| `JobStore` | 任务与运行的持久化、上限裁剪、幂等键 | `ctx.storageDomain`（自有 domain） |
| `Runner` | 建会话 → 命名 → 注入提示词 → 等首轮结束 → 归档 | `ctx.agents.create`、`ctx.sessionTitle`、工作区归档 API、会话事件 |
| `Receipt` | 回执组装与投递 | `ctx.sessionController`（解析 owner 会话 + 插件来源 followup） |
| `Tools` | 供 agent 创建/查看/修改/删除任务 | 工具注册 API |
| `Client UI` | **v1 不做**：失败可见性已由回执覆盖，避免为重复信息再造一页 | — |

与既有系统的关系：

- 内置 schedule 不动；owner 会话可以同时持有内置提醒与本插件任务，互不干扰。
- 归档准入不需要改：本插件的会话在归档时首轮已结束，不产生活跃工作家族。
- 若将来要转上游实现，本契约可直接映射为内置 schedule 的投递模式字段，插件层退役。

## 5. 数据模型

自有 domain：`fresh-session-jobs`，version 1。

```text
jobs: {
  id, title, prompt,
  rule: { kind: 'daily'|'every'|'cron', timeZone,
          at?: 'HH:mm', everySeconds?: number, expression?: string },
  workspaceId, ownerSessionId, agentOptions?, enabled,
  createdAt, updatedAt, nextAt?, lastRunId?
}

runs: {
  id, jobId, occurrenceAt, sessionId?,
  status: 'running'|'completed'|'failed'|'interrupted'|'skipped',
  skipReason?, startedAt, endedAt?, endReason?, archived?, receiptAt?, receiptMessageId?,
  summaryText?
}
```

保留策略：每个任务保留最近 **200 条** run 或最近 **30 天**，先到为准（对齐内置 schedule 的 `deliveryHistoryDays: 30` / `deliveryHistoryRecords: 200` 默认值）。

## 6. 运行状态机

```text
（到点，且无同键 run）
        ├─ 上次仍 running ──→ skipped(previous-running) ──→ 回执
        └─ 建会话成功 ──→ running ──┬─ turn/end 正常 ──→ completed ──→ 归档 ──→ 回执
                                    ├─ turn/end 失败 ──→ failed    ──→ 归档 ──→ 回执
                                    └─ 宿主重启中断 ──→ interrupted（启动对账）──→ 归档 ──→ 回执
建会话失败 ──→ failed（无 sessionId）──→ 回执
```

## 7. 失败与降级

| 失败点 | 处理 | 用户可见性 |
|---|---|---|
| 创建会话失败 | run 记 `failed`，`nextAt` 正常推进；不自动重试 | 回执（含错误码） |
| 首轮执行失败 | 照常归档；run 记 `failed` 与结束原因 | 回执（状态 failed + 摘要） |
| 归档被拒或失败 | run 保留 `archived: false`，回执标注「未归档」；启动对账重试一次 | 回执 + 日志 |
| owner 会话不可用 | 记日志，`receiptAt: null`，任务与后续触发不受影响 | 日志；可在任务工具里查看 run 记录 |
| 宿主重启打断运行 | 启动对账记 `interrupted` 并补发回执 | 回执 |
| 插件被禁用/卸载 | 内置 schedule 行为不变；已建任务不再触发，记录保留 | 重新启用后按「只补发最近一次」继续 |

## 8. 兼容性与已知限制

- 新会话不继承 owner 会话的临时权限/模型设置，只使用 profile 默认（v1 限制；如需要可后续加 `sessionTemplate` 快照）。
- 插件未安装或不启用时，不得写入任何自有存储域。
- 回执只落在 owner 会话；`runs` 运行记录属于宿主侧数据，不进入任何会话的模型上下文，新会话也不会看到它。
- 会话列表会出现「已归档的每日会话」，归档集合的检索体验由现有归档 UI 承担。

## 9. 验收标准

1. 到点触发后，目标工作区出现一个新会话，标题严格等于 `{title} {YYYY-MM-DD}`。
2. 该会话首条消息是提示词正文，且带 `[定时任务]` 来源首行。
3. 首轮结束后该会话进入工作区的归档集合（`archivedSessionIds`），不再属于活跃会话列表。
4. owner 会话收到回执，包含任务名、发生时点、状态、新会话标题与 id、摘要。
5. 首轮失败时同样归档，且回执状态为「失败」并带结束原因。
6. 宿主重启后：错过的发生时点只补发最近一次；被打断的运行记为 `interrupted` 且补发回执。
7. 上一次运行未结束时下一次到点 → 记 `skipped(previous-running)` 并回执，不产生第二个会话。
8. 回归：安装或卸载本插件都不改变内置 schedule 任务的投递行为与存储。
9. 手工验收：把「每日GitHub组合可行性方案」按本契约迁移一天，对照原会话确认只收到一条回执、归档里能找到该会话。

## 10. 交付与安装路径

- 载体：在工作区目录编写 bundle（`package.json` + `cordis.patch.yml` + `index.js`），再用 `plugin_manager` 的 `install_bundle` 安装到 `desktop` profile。
- 当前限制：本会话可用的 37 个工具里没有 `plugin_manager`，安装需在 GUI 的插件页操作，或把会话切到 `cordis` preset 后再装。
- 不采用「直接改 app.asar」作为正式交付方式：升级即被覆盖、且会破坏应用签名，只可作为一次性验证手段（本次不采用）。

## 11. 开放问题

1. **宿主侧创建会话的确切 API**：是否必须经 `ctx.sessionController` 的创建路径，才能正确加入工作区 `sessionIds`、写入 preset 与 cwd；实现首日先用 `cordis_inspect_query` 核实，再定 `Runner` 的调用面。
2. 回执能否附带可点击的会话跳转（GUI 是否支持按会话 id 打开），影响回执措辞。
3. 工具命名（`fresh_job_*` 或 `job_*`）与是否需要 `run_now` 手动触发。
4. `cron` 表达式是否沿用内置 schedule 的五字段 Vixie 语义（建议沿用，避免第二套时间方言）。

## 12. 决策记录（本轮已确认）

| 决策 | 结论 |
|---|---|
| 开关粒度 | 任务级：内置 schedule 任务保持原行为，本插件的任务即「每次新建会话」 |
| 归档策略 | 一律自动归档，成功与失败都归档 |
| 回执 | owner 会话收到一条，在结束时发出，含完成/失败与摘要 |
| 架构 | 独立插件（旁路调度器），不改内置 schedule |
| 实现载体 | 暂不决定：先完成本规格，再定交付路径 |
