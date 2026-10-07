# fresh-session-min：定时任务「每次触发新建会话」最小验证版

验证四件事是否按规格发生：**新建会话 → 命名 `{任务名} {日期}` → 注入提示词 → 跑完归档 → 回执**。

完整版（幂等、跨重启补发、并发保护、多任务与工具、运行历史）见
[docs/superpowers/plans/2026-10-07-dsh-fresh-session-jobs.md](../../docs/superpowers/plans/2026-10-07-dsh-fresh-session-jobs.md)。

## 安装

首选：GUI 左侧 **插件** 页 → 安装 → 选择本目录
`/Users/elvis/Desktop/repo-signal/dsh-plugins/fresh-session-min`。

备选（需要同时写 profile 层的 patch，属于手工改动，先确认再动）：

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
| `runOnStart` | **验证开关**：`true` 时插件加载后立刻跑一次 |
| `receiptSessionId` | 回执投递目标；留空则不发回执 |
| `prompt` | 投递给新会话的提示词 |

## 验证清单

1. 新会话出现在 repo-signal 工作区，标题为 `{title} {YYYY-MM-DD}`
2. 该会话首条消息是 `prompt` 内容
3. 跑完后该会话从活跃列表消失、出现在归档里
4. `receiptSessionId` 指定的会话收到一条 `[定时任务回执]`

## 已知限制（验证版刻意不做）

- `lastDay` 只在内存：宿主重启后当天可能重复触发
- 没有幂等键、没有错过补发、没有并发保护
- 只能配一个任务，没有工具与运行历史
- 归档失败只记日志，不改状态

## 卸载

插件页里移除该 bundle 即可；`dsh-plugins/fresh-session-min/` 目录可直接删除。
