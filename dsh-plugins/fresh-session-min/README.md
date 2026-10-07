# fresh-session-min：定时任务「每次触发新建会话」

最小可用插件，**已接入真实任务**：每天 06:30 新建一个会话执行「每日 GitHub 组合可行性分析」，跑完自动归档，
并向指定会话发一条结果回执。机制清单：**新建会话 → 命名 `{任务名} {日期}` → 注入提示词 → 跑完归档 → 回执**。

完整版（幂等、跨重启补发、并发保护、多任务与运行历史）见
[docs/superpowers/plans/2026-10-07-dsh-fresh-session-jobs.md](../../docs/superpowers/plans/2026-10-07-dsh-fresh-session-jobs.md)。

## 现状（2026-10-07 起）

- 任务：`每日GitHub组合可行性方案`，`06:30`（Asia/Shanghai），工作区 repo-signal
- 提示词只指向契约文件 `data/github-project-digest/feasibility/FEASIBILITY-TASK.md`，不复制内容
- 回执发到 `receiptSessionId` 指定的会话；留空则不发
- **切换时旧的定时任务必须停掉**：内置 schedule 里那个也属于同一任务、每天 06:30 投递到
  `session-0faa1c50`。两个都开会双跑、争同一个 `feasibility/` 目录。请在 GUI 的定时任务页删除旧任务。

## 安装

首选：GUI 左侧 **插件** 页 → 安装 → 选择本目录
`/Users/elvis/Desktop/repo-signal/dsh-plugins/fresh-session-min`。

备选（会写 profile 层，属于手工改动，先确认再动）：

```bash
dsh plugin --profile desktop add /Users/elvis/Desktop/repo-signal/dsh-plugins/fresh-session-min
```

## 配置

改 [cordis.patch.yml](./cordis.patch.yml) 里的 `config`，然后重装插件或重启应用：

| 字段 | 说明 |
|---|---|
| `title` | 任务名，同时是新会话标题前缀 |
| `workspaceId` | 新会话所属工作区（repo-signal 为 `3d0269e2-3e85-4e5e-b784-30f1837184f2`） |
| `timeOfDay` | 每天触发时刻，本机时区 |
| `skipToday` | 加载时若今天的触发时刻已过，就当作今天跑过（切换/重启当天不补跑）；未到点则不影响今天 |
| `runOnStart` | **验证开关**：`true` 时加载后 10 秒立刻跑一次 |
| `receiptSessionId` | 回执投递目标；留空则不发回执 |
| `prompt` | 投递给新会话的提示词 |

## 验证清单

1. 新会话出现在 repo-signal 工作区，标题为 `{title} {YYYY-MM-DD}`
2. 该会话首条消息是 `prompt` 内容
3. 跑完后该会话从活跃列表消失、出现在归档里
4. `receiptSessionId` 指定的会话收到一条 `[定时任务回执]`

（2026-10-07 已在隔离 profile 与桌面 profile 各实测一遍，四条全部通过。）

## 已知限制（最小版刻意不做）

- `lastDay` 只在内存：宿主重启后当天可能重复触发
- 没有幂等键、没有错过补发、没有并发保护
- 只能配一个任务，没有工具与运行历史
- 归档失败只记日志，不改状态

### `skipToday` 的取舍

因为"今天跑没跑"只在内存里，重启后无法区分"今天已经跑过"和"今天还没跑"，只能二选一：

| 取值 | 好处 | 代价 |
|---|---|---|
| `true`（当前） | 重启不会重复跑 | 若 06:30 时应用没开、之后才打开，当天会被跳过 |
| `false` | 应用晚开也会补跑当天 | 06:30 跑过之后再重启，当天会**再跑一次**（重复写 runs.log） |

当前选 `true`：重复跑会污染 `feasibility/runs.log` 与冷却判断，比偶尔漏一天更麻烦。
这个取舍在完整版里由持久化的幂等键消除（见计划 Task 3/7/8）。

## 踩过的坑（写 DSH 插件必看）

**不要在插件里 `import` 任何 `@deepseek-ai/*` 宿主包。** profile 里安装的插件是按自身目录解析依赖的，
而宿主包在 `app.asar` 内，裸导入会让插件以 `failed to import` / `Cannot find package '@deepseek-ai/dsh-llm'`
启用失败（本插件第一版就是这样挂的）。宿主能力只能通过 `apply(ctx)` 拿到的 `ctx` 使用；
需要的小工具（如 `createUserMessage`）自己内联实现。

**`ctx.sessionController.resolveAgent(id)` 返回的是包装对象**：成功是 `{ agent, … }`，失败是 `{ error }`。
把它直接当 agent 用会得到 `agent.session === undefined`，随后 `sessionTitle.rename` 抛错、整个 run 静默失败
（现象：会话建出来了，但没有标题、没有投递、也没有归档）。正确写法：

```js
const resolved = await ctx.sessionController.resolveAgent(sessionId)
if ('error' in resolved) throw resolved.error
const agent = resolved.agent
```

**投递后要 flush 才算落盘**：`agent.followup(message)` 之后 `await ctx.sessions.flush(agent.session)`，
并且 `inject` 里要加上 `'sessions'`（内置 schedule 的投递同样走这一步）。

## 卸载

插件页里移除该 bundle 即可；`dsh-plugins/fresh-session-min/` 目录可直接删除。
