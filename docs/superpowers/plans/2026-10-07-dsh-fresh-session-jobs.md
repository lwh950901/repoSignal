# DSH「每次投递新建会话」定时任务实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 交付一个 DSH profile bundle 插件，让定时任务每次触发都在指定工作区新建会话执行、结束后自动归档，并向原会话发一条结果回执。

**Architecture:** 独立宿主插件（旁路调度器），不修改内置 `@deepseek-ai/dsh-schedule`。纯逻辑（时间规则、幂等键、运行状态机、会话事件折叠、回执文本、裁剪、调度核心）与宿主适配层分离：纯逻辑用 `node --test` 全覆盖，宿主适配层集中在 `src/host.js` 一个文件里。

**Tech Stack:** 纯 ESM JavaScript（无构建步骤、**零依赖：不 import 任何 `@deepseek-ai/*` 宿主包**）、Node 内置测试运行器 `node --test`（本机 `/usr/local/bin/node` v24.14.1）、Cordis 插件（profile bundle）、运行状态用自有的 JSON 文件持久化（`node:fs`，不依赖 storage domain）。

**规格：** [docs/superpowers/specs/2026-10-07-dsh-fresh-session-jobs-design.md](../specs/2026-10-07-dsh-fresh-session-jobs-design.md)

---

## 已核对的宿主 API（来自 app.asar 内随发行版附带的编译产物，任务 9 会再次用 `cordis_inspect_query` 复核）

| 能力 | 调用面 | 核对来源 |
|---|---|---|
| 创建会话（含工作区归属） | `ctx.sessionController.create({ workspaceId })` → `{ sessionId, agentPreset? }`；内部会 `workspace.attachSession(sessionId)` | `@deepseek-ai/dsh-api-session-controller/lib/index.js` |
| 取会话 Agent | `ctx.sessionController.resolveAgent(sessionId)` → **包装对象**：成功 `{ agent, … }`，失败 `{ error }`；用 `resolved.agent`，别直接当 agent 使（实测踩过） | `@deepseek-ai/dsh-schedule/lib/index.js` |
| 投递消息 | `agent.followup(createUserMessage({ content: [{ type: 'text', text }], source: { kind: 'user' } }))`，随后 `await ctx.sessions.flush(agent.session)` 确认落盘；`followup` 会唤醒会话。**`createUserMessage` 用本仓库内联实现**（`src/message.js`），不要 `import` 宿主包 | `@deepseek-ai/dsh-schedule/lib/index.js`、`@deepseek-ai/dsh-subagent-in-process-driver/lib/index.js` |
| 等待回合结束 | `await agent.whenIdle()`，再用 `agent.session.snapshotEvents(boundary)` 读 `turn/end` | 同上 |
| 会话命名 | `ctx.sessionTitle.rename(session, title)`（session 取自 `agent.session`） | `@deepseek-ai/dsh-session-title/lib/index.js` |
| 归档会话 | `ctx.workspaceRegistry.archiveSession(sessionId)`；有活跃工作时会拒绝，故必须在回合结束后调用 | `@deepseek-ai/dsh-workspace/lib/index.js` |
| 运行状态持久化 | 插件自有的 JSON 文件：`$DSH_HOME/fresh-session-jobs/state.json`，写 `.tmp` 后 `rename` | 本计划 Task 7（不依赖 storage domain） |
| 插件形态 | `export function apply(ctx, config)` + 可选 `export const inject`；bundle 用 `dsh.bundle.patch`；**不 export `Config`**（配置自校验） | `cordis-plugin-development` 技能 `references/host-plugin.md` |

**读取 app.asar 内文件的方法（shell 不能直接读）：**

> **铁律：插件代码里不要出现任何 `@deepseek-ai/*` 的 `import`。** profile 里安装的插件按自身目录解析依赖，
> 而宿主包在 `app.asar` 内，裸导入会让插件以 `failed to import` 启用失败（最小验证版已实测过一次）。
> 需要的宿主能力只能走 `apply(ctx)` 的 `ctx`；需要的小工具在本仓库内联实现（见 `src/message.js`）。

```bash
python3 - <<'PY'
import json, struct, sys
p = "/Applications/DeepSeek Harness.app/Contents/Resources/app.asar"
inner = sys.argv[1] if len(sys.argv) > 1 else "/dsh/node_modules/@deepseek-ai/dsh-schedule/lib/index.js"
f = open(p, "rb")
_, _, _, jlen = struct.unpack("<4I", f.read(16))
d = json.loads(f.read(jlen).decode("utf-8"))
base = 16 + jlen
node = d
for part in inner.strip("/").split("/"):
    node = node["files"][part]
f.seek(base + int(node["offset"]))
sys.stdout.write(f.read(node["size"]).decode("utf-8", "replace"))
PY
```

## 文件结构

插件根目录：`/Users/elvis/Desktop/repo-signal/dsh-plugins/fresh-session-jobs/`（安装时用绝对路径；将来要搬家只需改安装命令）。

```text
dsh-plugins/fresh-session-jobs/
├── package.json          # bundle 清单：type=module、exports、dsh.bundle.patch
├── cordis.patch.yml      # 向 profile 插入一行插件
├── index.js              # 插件入口：apply/inject，装配 config+store+scheduler+runner
├── NOTES.md              # 任务 9 的 API 核对记录（唯一的事实来源）
├── src/
│   ├── rules.js          # 时间规则：daily / every / cron 的下一个与最近一个发生时点
│   ├── cron.js           # 五字段 cron 解析（Vixie 语义）
│   ├── keys.js           # 幂等键与同发生点查找
│   ├── run-state.js      # 运行状态机与 turn/end 原因归类
│   ├── session-fold.js   # 从会话事件里取 turn/end 与最后一条 assistant 文本
│   ├── message.js        # 内联的消息构造（替代 @deepseek-ai/dsh-llm 的 createUserMessage）
│   ├── receipt.js        # 回执文本组装与摘要截断
│   ├── retention.js      # 运行记录裁剪（200 条 / 30 天）
│   ├── config.js         # 配置装载与校验：任务来自 cordis.patch.yml 的 config.jobs
│   ├── job-store.js      # 运行状态存储：内存实现 + JSON 文件实现
│   ├── scheduler.js      # 调度核心：到点、幂等、并发跳过、只补发最近一次
│   ├── host.js           # 宿主适配层（唯一直接调用 ctx.* 的文件）
│   └── runner.js         # 编排一次运行：建会话→命名→投递→等结束→归档→回执
└── tests/
    ├── rules.test.js
    ├── cron.test.js
    ├── keys.test.js
    ├── run-state.test.js
    ├── session-fold.test.js
    ├── message.test.js
    ├── receipt.test.js
    ├── retention.test.js
    ├── job-store.test.js
    ├── scheduler.test.js
    ├── runner.test.js
    ├── config.test.js
    └── plugin-entry.test.js
```

职责边界：**所有 src 文件与 index.js 都不 import 任何 `@deepseek-ai/*`**，只有 `src/host.js` 通过 `apply(ctx)` 传进来的 `ctx` 访问宿主。

---

### Task 1: 插件骨架与 daily / every 规则

**Files:**
- Create: `dsh-plugins/fresh-session-jobs/package.json`
- Create: `dsh-plugins/fresh-session-jobs/src/rules.js`
- Test: `dsh-plugins/fresh-session-jobs/tests/rules.test.js`

- [ ] **Step 1: 建骨架**

`dsh-plugins/fresh-session-jobs/package.json`：

```json
{
  "name": "@local/dsh-fresh-session-jobs",
  "version": "1.0.0",
  "private": true,
  "type": "module",
  "exports": { ".": "./index.js" },
  "dsh": { "bundle": { "patch": "./cordis.patch.yml" } },
  "scripts": { "test": "node --test tests/*.test.js" }
}
```

- [ ] **Step 2: 写失败测试**

`dsh-plugins/fresh-session-jobs/tests/rules.test.js`：

```js
import test from 'node:test'
import assert from 'node:assert/strict'
import { nextOccurrence, nextDailyOccurrence, nextEveryOccurrence, occurrenceAtOrBefore } from '../src/rules.js'

const utc = (iso) => Date.parse(iso)

test('daily：取当天尚未到来的时刻', () => {
  const next = nextDailyOccurrence({ at: '06:30', timeZone: 'Asia/Shanghai' }, utc('2026-10-07T00:00:00Z'))
  assert.equal(new Date(next).toISOString(), '2026-10-06T22:30:00.000Z') // 上海 10-07 06:30 还有 6.5 小时
})

test('daily：当天时刻已过则顺延到次日', () => {
  const next = nextDailyOccurrence({ at: '06:30', timeZone: 'Asia/Shanghai' }, utc('2026-10-06T23:00:00Z'))
  assert.equal(new Date(next).toISOString(), '2026-10-07T22:30:00.000Z')
})

test('daily：夏令时不存在的时刻被跳过', () => {
  // 2026-03-08 02:30 在 America/New_York 不存在
  const next = nextDailyOccurrence({ at: '02:30', timeZone: 'America/New_York' }, utc('2026-03-08T05:00:00Z'))
  assert.equal(new Date(next).toISOString(), '2026-03-09T06:30:00.000Z')
})

test('daily：夏令时重复的时刻取较早者', () => {
  // 2026-11-01 01:30 在 America/New_York 出现两次，取 EDT（UTC-4）
  const next = nextDailyOccurrence({ at: '01:30', timeZone: 'America/New_York' }, utc('2026-11-01T04:00:00Z'))
  assert.equal(new Date(next).toISOString(), '2026-11-01T05:30:00.000Z')
})

test('every：至少 60 秒，按上次发生点顺延', () => {
  assert.equal(nextEveryOccurrence({ everySeconds: 3600 }, 1000), 1000 + 3600_000)
  assert.throws(() => nextEveryOccurrence({ everySeconds: 30 }, 1000), />= 60/)
})

test('nextOccurrence 按 kind 分派，occurrenceAtOrBefore 只补发最近一次', () => {
  const rule = { kind: 'daily', at: '06:30', timeZone: 'Asia/Shanghai' }
  const from = utc('2026-10-01T00:00:00Z')
  const now = utc('2026-10-05T12:00:00Z')
  assert.equal(new Date(occurrenceAtOrBefore(rule, from, now)).toISOString(), '2026-10-05T22:30:00.000Z')
  assert.equal(nextOccurrence(rule, from), utc('2026-10-01T22:30:00.000Z'))
})
```

- [ ] **Step 3: 运行测试，确认失败**

Run: `cd dsh-plugins/fresh-session-jobs && node --test tests/rules.test.js`
Expected: FAIL，`Cannot find module '../src/rules.js'`

- [ ] **Step 4: 实现 src/rules.js**

```js
const DAY_MS = 86_400_000
const MINUTE_MS = 60_000

/** 把某个 UTC 时刻渲染成指定时区的本地钟表时间。 */
function localParts(utcMs, timeZone) {
  const formatter = new Intl.DateTimeFormat('en-US', {
    timeZone, hour12: false,
    year: 'numeric', month: '2-digit', day: '2-digit',
    hour: '2-digit', minute: '2-digit', second: '2-digit',
  })
  const parts = {}
  for (const part of formatter.formatToParts(new Date(utcMs))) parts[part.type] = part.value
  return {
    year: Number(parts.year), month: Number(parts.month), day: Number(parts.day),
    hour: Number(parts.hour) % 24, minute: Number(parts.minute), second: Number(parts.second),
  }
}

function offsetMs(utcMs, timeZone) {
  const p = localParts(utcMs, timeZone)
  return Date.UTC(p.year, p.month - 1, p.day, p.hour, p.minute, p.second) - utcMs
}

/** 本地钟表时间 → UTC 毫秒。不存在的时刻返回 null；重复的时刻取较早者。 */
export function zonedTimeToUtc(parts, timeZone) {
  const naive = Date.UTC(parts.year, parts.month - 1, parts.day, parts.hour, parts.minute, parts.second ?? 0)
  const candidates = new Set([
    naive - offsetMs(naive, timeZone),
    naive - offsetMs(naive - DAY_MS, timeZone),
    naive - offsetMs(naive + DAY_MS, timeZone),
  ])
  const matches = []
  for (const candidate of candidates) {
    const p = localParts(candidate, timeZone)
    if (p.year === parts.year && p.month === parts.month && p.day === parts.day
      && p.hour === parts.hour && p.minute === parts.minute && p.second === (parts.second ?? 0)) {
      matches.push(candidate)
    }
  }
  return matches.length === 0 ? null : Math.min(...matches)
}

/** daily 规则在 fromMs 之后的下一个发生时点；不存在的时刻顺延到次日。 */
export function nextDailyOccurrence({ at, timeZone }, fromMs) {
  const [hour, minute] = String(at).split(':').map(Number)
  if (!Number.isInteger(hour) || !Number.isInteger(minute)) throw new Error(`invalid daily time "${at}"`)
  const start = localParts(fromMs, timeZone)
  for (let dayOffset = 0; dayOffset <= 3; dayOffset += 1) {
    const base = new Date(Date.UTC(start.year, start.month - 1, start.day) + dayOffset * DAY_MS)
    const candidate = zonedTimeToUtc({
      year: base.getUTCFullYear(), month: base.getUTCMonth() + 1, day: base.getUTCDate(), hour, minute,
    }, timeZone)
    if (candidate !== null && candidate > fromMs) return candidate
  }
  throw new Error(`no daily occurrence for ${at} ${timeZone}`)
}

/** every 规则：严格按间隔顺延，最短 60 秒。 */
export function nextEveryOccurrence({ everySeconds }, fromMs) {
  if (!Number.isSafeInteger(everySeconds) || everySeconds < 60) throw new Error('everySeconds must be an integer >= 60')
  return fromMs + everySeconds * 1000
}

/** 按 kind 分派到具体规则实现。 */
export function nextOccurrence(rule, fromMs) {
  if (rule.kind === 'daily') return nextDailyOccurrence(rule, fromMs)
  if (rule.kind === 'every') return nextEveryOccurrence(rule, fromMs)
  if (rule.kind === 'cron') {
    // Task 2 接入：先抛错，保证未实现的规则不会被静默跳过
    throw new Error('cron rule requires nextCronOccurrence from src/cron.js')
  }
  throw new Error(`unknown rule kind "${rule.kind}"`)
}

/** 从 fromMs 起、不晚于 nowMs 的最后一个发生时点；没有则返回 null。只补发最近一次靠它实现。 */
export function occurrenceAtOrBefore(rule, fromMs, nowMs, maxSteps = 10_000) {
  let cursor = nextOccurrence(rule, fromMs - 1)
  let last = null
  for (let step = 0; step < maxSteps && cursor <= nowMs; step += 1) {
    last = cursor
    cursor = nextOccurrence(rule, cursor)
  }
  return last
}

export const MINUTE = MINUTE_MS
```

- [ ] **Step 5: 运行测试，确认通过**

Run: `cd dsh-plugins/fresh-session-jobs && node --test tests/rules.test.js`
Expected: PASS（6 个 test 全绿）

- [ ] **Step 6: 提交**

```bash
cd /Users/elvis/Desktop/repo-signal
git add dsh-plugins/fresh-session-jobs
git commit -m "feat(dsh-plugin): add plugin skeleton and daily/every rule engine"
```

---

### Task 2: cron 规则

**Files:**
- Create: `dsh-plugins/fresh-session-jobs/src/cron.js`
- Modify: `dsh-plugins/fresh-session-jobs/src/rules.js`（`nextOccurrence` 的 cron 分支）
- Test: `dsh-plugins/fresh-session-jobs/tests/cron.test.js`

- [ ] **Step 1: 写失败测试**

```js
import test from 'node:test'
import assert from 'node:assert/strict'
import { parseCron, nextCronOccurrence } from '../src/cron.js'

test('解析：数字、列表、区间、步长、星号', () => {
  const cron = parseCron('*/15 6-8 1,15 * 1-5')
  assert.deepEqual([...cron.minute].sort((a, b) => a - b), [0, 15, 30, 45])
  assert.deepEqual([...cron.hour].sort((a, b) => a - b), [6, 7, 8])
  assert.deepEqual([...cron.dom].sort((a, b) => a - b), [1, 15])
  assert.equal(cron.month.size, 12)
  assert.deepEqual([...cron.dow].sort((a, b) => a - b), [1, 2, 3, 4, 5])
})

test('字段数不对或越界要报错', () => {
  assert.throws(() => parseCron('* * * *'), /5 fields/)
  assert.throws(() => parseCron('99 * * * *'), /out of range/)
})

test('下一个发生时点：上海时区的每天 06:30', () => {
  const next = nextCronOccurrence('30 6 * * *', Date.parse('2026-10-06T23:00:00Z'), 'Asia/Shanghai')
  assert.equal(new Date(next).toISOString(), '2026-10-07T22:30:00.000Z')
})

test('dom 与 dow 同时受限时取并集（Vixie 语义）', () => {
  // 每月 1 号 或 每周一
  const next = nextCronOccurrence('0 9 1 * 1', Date.parse('2026-10-07T00:00:00Z'), 'Asia/Shanghai')
  assert.equal(new Date(next).toISOString(), '2026-10-12T01:00:00.000Z') // 10-12 是周一
})
```

- [ ] **Step 2: 运行测试，确认失败**

Run: `cd dsh-plugins/fresh-session-jobs && node --test tests/cron.test.js`
Expected: FAIL，`Cannot find module '../src/cron.js'`

- [ ] **Step 3: 实现 src/cron.js**

```js
import { zonedTimeToUtc } from './rules.js'

const MINUTE_MS = 60_000
const DAY_MS = 86_400_000
const MAX_SCAN_MINUTES = 366 * 4 * 24 * 60 // 最多扫 4 年

function parseField(field, min, max) {
  const values = new Set()
  for (const chunk of String(field).split(',')) {
    const [range, stepText] = chunk.split('/')
    const step = stepText === undefined ? 1 : Number(stepText)
    if (!Number.isSafeInteger(step) || step < 1) throw new Error(`invalid step in "${chunk}"`)
    let start = min
    let end = max
    if (range !== '*') {
      const bounds = range.split('-')
      start = Number(bounds[0])
      end = bounds.length === 1 ? start : Number(bounds[1])
    }
    for (let value = start; value <= end; value += step) {
      if (!Number.isInteger(value) || value < min || value > max) throw new Error(`value ${value} out of range ${min}-${max}`)
      values.add(value)
    }
  }
  return values
}

export function parseCron(expression) {
  const fields = String(expression).trim().split(/\s+/)
  if (fields.length !== 5) throw new Error('cron expression must have 5 fields: minute hour day-of-month month day-of-week')
  const [minute, hour, dom, month, dow] = fields
  return {
    minute: parseField(minute, 0, 59),
    hour: parseField(hour, 0, 23),
    dom: parseField(dom, 1, 31),
    month: parseField(month, 1, 12),
    dow: parseField(dow, 0, 6),
    domRestricted: dom !== '*',
    dowRestricted: dow !== '*',
  }
}

function matchesDay(cron, day, weekday) {
  if (!cron.domRestricted && !cron.dowRestricted) return true
  if (cron.domRestricted && cron.dowRestricted) return cron.dom.has(day) || cron.dow.has(weekday)
  return cron.domRestricted ? cron.dom.has(day) : cron.dow.has(weekday)
}

export function nextCronOccurrence(expression, fromMs, timeZone, maxScanMinutes = MAX_SCAN_MINUTES) {
  const cron = typeof expression === 'string' ? parseCron(expression) : expression
  const start = new Date(fromMs)
  const localStart = new Intl.DateTimeFormat('en-CA', {
    timeZone, hour12: false, year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit',
  }).formatToParts(start).reduce((acc, part) => ({ ...acc, [part.type]: part.value }), {})
  let cursor = Date.UTC(
    Number(localStart.year), Number(localStart.month) - 1, Number(localStart.day),
    Number(localStart.hour) % 24, Number(localStart.minute),
  ) + MINUTE_MS
  for (let scanned = 0; scanned < maxScanMinutes; scanned += 1) {
    const date = new Date(cursor)
    const year = date.getUTCFullYear()
    const month = date.getUTCMonth() + 1
    const day = date.getUTCDate()
    const hour = date.getUTCHours()
    const minute = date.getUTCMinutes()
    const weekday = new Date(Date.UTC(year, month - 1, day)).getUTCDay()
    if (cron.month.has(month) && matchesDay(cron, day, weekday) && cron.hour.has(hour) && cron.minute.has(minute)) {
      const utc = zonedTimeToUtc({ year, month, day, hour, minute }, timeZone)
      if (utc !== null && utc > fromMs) return utc
    }
    cursor += MINUTE_MS
  }
  throw new Error(`no cron occurrence within ${maxScanMinutes} minutes for "${expression}"`)
}

export const DAY_MS_FOR_TESTS = DAY_MS
```

- [ ] **Step 4: 接入 rules.js 的 cron 分支（注入式，避免与 cron.js 循环依赖）**

把 `src/rules.js` 顶部的 `MINUTE` 导出之前加入：

```js
let cronImpl = null
/** 由 index.js 在装配时注入 cron 实现，避免 rules.js 与 cron.js 互相 import。 */
export function configureCron(impl) { cronImpl = impl }
```

并把 `nextOccurrence` 的 cron 分支替换为：

```js
  if (rule.kind === 'cron') {
    if (cronImpl === null) throw new Error('cron support not configured: call configureCron() during apply()')
    return cronImpl.nextCronOccurrence(rule.expression, fromMs, rule.timeZone)
  }
```

- [ ] **Step 5: 运行测试，确认通过**

Run: `cd dsh-plugins/fresh-session-jobs && node --test tests/cron.test.js tests/rules.test.js`
Expected: PASS（cron 4 个 + rules 6 个）

- [ ] **Step 6: 提交**

```bash
cd /Users/elvis/Desktop/repo-signal
git add dsh-plugins/fresh-session-jobs
git commit -m "feat(dsh-plugin): add five-field cron rule with Vixie day semantics"
```

---

### Task 3: 幂等键与运行状态机

**Files:**
- Create: `dsh-plugins/fresh-session-jobs/src/keys.js`
- Create: `dsh-plugins/fresh-session-jobs/src/run-state.js`
- Test: `dsh-plugins/fresh-session-jobs/tests/keys.test.js`
- Test: `dsh-plugins/fresh-session-jobs/tests/run-state.test.js`

- [ ] **Step 1: 写失败测试**

```js
// tests/keys.test.js
import test from 'node:test'
import assert from 'node:assert/strict'
import { occurrenceKey, findRunForOccurrence } from '../src/keys.js'

test('同一任务同一发生时点得到同一个键', () => {
  const at = Date.parse('2026-10-07T22:30:00Z')
  assert.equal(occurrenceKey('job-1', at), 'job-1@2026-10-07T22:30:00.000Z')
  assert.equal(occurrenceKey('job-1', at), occurrenceKey('job-1', at))
  assert.notEqual(occurrenceKey('job-1', at), occurrenceKey('job-2', at))
})

test('按发生点查找已有运行记录', () => {
  const runs = [{ jobId: 'j', occurrenceAt: 1 }, { jobId: 'j', occurrenceAt: 2 }]
  assert.equal(findRunForOccurrence(runs, 'j', 2).occurrenceAt, 2)
  assert.equal(findRunForOccurrence(runs, 'j', 3), null)
})
```

```js
// tests/run-state.test.js
import test from 'node:test'
import assert from 'node:assert/strict'
import { classifyEndReason, isTerminal, RUN_STATUS } from '../src/run-state.js'

test('turn/end 原因归类', () => {
  assert.equal(classifyEndReason({ kind: 'completed' }), RUN_STATUS.COMPLETED)
  assert.equal(classifyEndReason({ kind: 'aborted' }), RUN_STATUS.INTERRUPTED)
  assert.equal(classifyEndReason({ kind: 'interrupted' }), RUN_STATUS.INTERRUPTED)
  assert.equal(classifyEndReason({ kind: 'error' }), RUN_STATUS.FAILED)
  assert.equal(classifyEndReason(null), RUN_STATUS.FAILED)
})

test('终态判定', () => {
  assert.equal(isTerminal(RUN_STATUS.RUNNING), false)
  assert.equal(isTerminal(RUN_STATUS.COMPLETED), true)
  assert.equal(isTerminal(RUN_STATUS.SKIPPED), true)
})
```

- [ ] **Step 2: 运行测试，确认失败**

Run: `cd dsh-plugins/fresh-session-jobs && node --test tests/keys.test.js tests/run-state.test.js`
Expected: FAIL，模块不存在

- [ ] **Step 3: 实现**

```js
// src/keys.js
/** 发生键：任务 id + 发生时点（UTC ISO）。 */
export function occurrenceKey(jobId, occurrenceAt) {
  return `${jobId}@${new Date(occurrenceAt).toISOString()}`
}

/** 在同一任务的运行记录里找该发生点的记录；没有则返回 null。 */
export function findRunForOccurrence(runs, jobId, occurrenceAt) {
  const key = occurrenceKey(jobId, occurrenceAt)
  return runs.find((run) => occurrenceKey(run.jobId, run.occurrenceAt) === key) ?? null
}
```

```js
// src/run-state.js
export const RUN_STATUS = Object.freeze({
  RUNNING: 'running',
  COMPLETED: 'completed',
  FAILED: 'failed',
  INTERRUPTED: 'interrupted',
  SKIPPED: 'skipped',
})

const TERMINAL = new Set([RUN_STATUS.COMPLETED, RUN_STATUS.FAILED, RUN_STATUS.INTERRUPTED, RUN_STATUS.SKIPPED])

export function isTerminal(status) {
  return TERMINAL.has(status)
}

/** 把 turn/end 的原因映射成运行状态。 */
export function classifyEndReason(reason) {
  const kind = reason?.kind
  if (kind === 'completed') return RUN_STATUS.COMPLETED
  if (kind === 'aborted' || kind === 'canceled' || kind === 'cancelled' || kind === 'interrupted') return RUN_STATUS.INTERRUPTED
  return RUN_STATUS.FAILED
}

/** 宿主重启对账：重启时仍标记为 running 的运行一定是被打断的。 */
export function reconcileAfterRestart(runs) {
  return runs.map((run) => (run.status === RUN_STATUS.RUNNING
    ? { ...run, status: RUN_STATUS.INTERRUPTED, endReason: 'host-restart', endedAt: run.endedAt ?? run.startedAt, archived: false, receiptAt: null }
    : run))
}
```

- [ ] **Step 4: 运行测试，确认通过**

Run: `cd dsh-plugins/fresh-session-jobs && node --test tests/keys.test.js tests/run-state.test.js`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
cd /Users/elvis/Desktop/repo-signal
git add dsh-plugins/fresh-session-jobs
git commit -m "feat(dsh-plugin): add occurrence keys and run state machine"
```

---

### Task 4: 会话事件折叠与消息构造

**Files:**
- Create: `dsh-plugins/fresh-session-jobs/src/session-fold.js`
- Create: `dsh-plugins/fresh-session-jobs/src/message.js`
- Test: `dsh-plugins/fresh-session-jobs/tests/session-fold.test.js`
- Test: `dsh-plugins/fresh-session-jobs/tests/message.test.js`

- [ ] **Step 1: 写失败测试**

```js
import test from 'node:test'
import assert from 'node:assert/strict'
import { lastTurnEnd, lastAssistantText } from '../src/session-fold.js'

test('取最后一个 turn/end', () => {
  const events = [
    { type: 'turn/start', data: {} },
    { type: 'turn/end', data: { reason: { kind: 'error' } } },
    { type: 'turn/start', data: {} },
    { type: 'turn/end', data: { reason: { kind: 'completed' } } },
  ]
  assert.equal(lastTurnEnd(events).data.reason.kind, 'completed')
  assert.equal(lastTurnEnd([{ type: 'turn/start', data: {} }]), null)
})

test('取最后一条有文本的 assistant 消息', () => {
  const events = [
    { type: 'assistant/message', data: { message: { content: [{ type: 'text', text: '第一段' }] } } },
    { type: 'assistant/message', data: { message: { content: [{ type: 'reasoning', text: 'ignored' }] } } },
    { type: 'assistant/message', data: { message: { content: [{ type: 'text', text: '最终结论 A' }, { type: 'text', text: '补充 B' }] } } },
  ]
  assert.equal(lastAssistantText(events), '最终结论 A\n补充 B')
  assert.equal(lastAssistantText([]), '')
})
// tests/message.test.js
import test from 'node:test'
import assert from 'node:assert/strict'
import { createUserMessage } from '../src/message.js'

test('产出冻结的 user 消息，带唯一 id 与 role', () => {
  const message = createUserMessage({ content: '你好', source: { kind: 'user' } })
  assert.equal(message.role, 'user')
  assert.equal(message.content, '你好')
  assert.deepEqual(message.source, { kind: 'user' })
  assert.equal(typeof message.id, 'string')
  assert.equal(Object.isFrozen(message), true)
  assert.notEqual(createUserMessage({ content: 'x' }).id, createUserMessage({ content: 'x' }).id)
})
```

- [ ] **Step 2: 运行测试，确认失败**

Run: `cd dsh-plugins/fresh-session-jobs && node --test tests/session-fold.test.js tests/message.test.js`
Expected: FAIL，模块不存在

- [ ] **Step 3: 实现 src/session-fold.js 与 src/message.js**

```js
/** 会话事件里最后一个 turn/end。 */
export function lastTurnEnd(events) {
  for (let index = events.length - 1; index >= 0; index -= 1) {
    if (events[index]?.type === 'turn/end') return events[index]
  }
  return null
}

/** 会话事件里最后一条含文本的 assistant 消息的纯文本。 */
export function lastAssistantText(events) {
  for (let index = events.length - 1; index >= 0; index -= 1) {
    const event = events[index]
    if (event?.type !== 'assistant/message') continue
    const blocks = event.data?.message?.content ?? []
    const text = blocks
      .filter((block) => block?.type === 'text' && typeof block.text === 'string')
      .map((block) => block.text)
      .join('\n')
      .trim()
    if (text !== '') return text
  }
  return ''
}
```

`src/message.js`（内联宿主工具，**不得**改为 `import` 宿主包）：

```js
import { randomUUID } from 'node:crypto'

function deepFreeze(value) {
  if (value !== null && typeof value === 'object' && !Object.isFrozen(value)) {
    Object.freeze(value)
    for (const key of Object.keys(value)) deepFreeze(value[key])
  }
  return value
}

/** 等价于 @deepseek-ai/dsh-llm 的 createUserMessage：造一个冻结的 user 消息并给唯一 id。 */
export function createUserMessage(input) {
  return deepFreeze({ ...structuredClone(input), id: randomUUID(), role: 'user' })
}
```

- [ ] **Step 4: 运行测试，确认通过**

Run: `cd dsh-plugins/fresh-session-jobs && node --test tests/session-fold.test.js tests/message.test.js`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
cd /Users/elvis/Desktop/repo-signal
git add dsh-plugins/fresh-session-jobs
git commit -m "feat(dsh-plugin): fold session events and inline user-message helper"
```

---

### Task 5: 回执文本

**Files:**
- Create: `dsh-plugins/fresh-session-jobs/src/receipt.js`
- Test: `dsh-plugins/fresh-session-jobs/tests/receipt.test.js`

- [ ] **Step 1: 写失败测试**

```js
import test from 'node:test'
import assert from 'node:assert/strict'
import { summarize, buildReceipt, wrapPrompt } from '../src/receipt.js'

test('摘要压平空白并截断到 200 字', () => {
  assert.equal(summarize('  第一行\n\n第二行  '), '第一行 第二行')
  const long = 'x'.repeat(300)
  assert.equal(summarize(long).length, 200)
  assert.ok(summarize(long).endsWith('…'))
})

test('回执包含任务名、时间、状态、会话与摘要', () => {
  const text = buildReceipt({
    job: { title: '每日GitHub组合可行性方案' },
    run: { occurrenceAt: Date.parse('2026-10-07T22:30:00Z'), status: 'completed', archived: true, summaryText: '本轮无合格方案' },
    sessionTitle: '每日GitHub组合可行性方案 2026-10-07',
    sessionId: 'session-abc',
    timeZone: 'Asia/Shanghai',
  })
  assert.match(text, /\[定时任务回执\] 每日GitHub组合可行性方案/)
  assert.match(text, /发生时点：2026-10-07 06:30/)
  assert.match(text, /状态：完成/)
  assert.match(text, /新会话：每日GitHub组合可行性方案 2026-10-07（session-abc）/)
  assert.match(text, /摘要：本轮无合格方案/)
})

test('失败、跳过与未归档都有明确措辞', () => {
  const text = buildReceipt({
    job: { title: '任务' },
    run: { occurrenceAt: 0, status: 'failed', archived: false, endReason: 'timeout', summaryText: '' },
    sessionTitle: '任务 1970-01-01',
    sessionId: 'session-x',
    timeZone: 'Asia/Shanghai',
  })
  assert.match(text, /状态：失败（timeout）/)
  assert.match(text, /未归档/)
  assert.match(text, /摘要：（无输出）/)
})

test('首条消息带任务来源首行', () => {
  const prompt = wrapPrompt({ title: '任务' }, Date.parse('2026-10-07T22:30:00Z'), 'Asia/Shanghai')
  assert.match(prompt, /^\[定时任务\] 任务 · 2026-10-07 06:30\n\n正文$/)
})
```

- [ ] **Step 2: 运行测试，确认失败**

Run: `cd dsh-plugins/fresh-session-jobs && node --test tests/receipt.test.js`
Expected: FAIL，模块不存在

- [ ] **Step 3: 实现 src/receipt.js**

```js
const STATUS_LABEL = {
  completed: '完成',
  failed: '失败',
  interrupted: '中断',
  skipped: '跳过',
  running: '运行中',
}

/** 本地时间格式化为 YYYY-MM-DD HH:mm。 */
export function formatLocal(ms, timeZone) {
  const parts = new Intl.DateTimeFormat('en-CA', {
    timeZone, hour12: false, year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit',
  }).formatToParts(new Date(ms)).reduce((acc, part) => ({ ...acc, [part.type]: part.value }), {})
  return `${parts.year}-${parts.month}-${parts.day} ${String(Number(parts.hour) % 24).padStart(2, '0')}:${parts.minute}`
}

/** 压平空白并截断（默认 200 字）。 */
export function summarize(text, maxChars = 200) {
  const flat = String(text ?? '').replace(/\s+/g, ' ').trim()
  if (flat.length <= maxChars) return flat
  return `${flat.slice(0, maxChars - 1)}…`
}

/** 投递给新会话的首条消息：来源首行 + 任务提示词正文。 */
export function wrapPrompt(job, occurrenceAt, timeZone) {
  return `[定时任务] ${job.title} · ${formatLocal(occurrenceAt, timeZone)}\n\n${job.prompt}`
}

/** 回执文本。 */
export function buildReceipt({ job, run, sessionTitle, sessionId, timeZone }) {
  const status = STATUS_LABEL[run.status] ?? run.status
  const detail = run.endReason || run.reason
  const reason = detail ? `（${detail}）` : ''
  const archiveNote = run.archived === false ? '（未归档）' : ''
  return [
    `[定时任务回执] ${job.title}`,
    `发生时点：${formatLocal(run.occurrenceAt, timeZone)}`,
    `状态：${status}${reason}`,
    `新会话：${sessionTitle ?? '（未创建）'}（${sessionId ?? '-'}）${archiveNote}`,
    `摘要：${run.summaryText ? summarize(run.summaryText) : '（无输出）'}`,
  ].join('\n')
}
```

- [ ] **Step 4: 运行测试，确认通过**

Run: `cd dsh-plugins/fresh-session-jobs && node --test tests/receipt.test.js`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
cd /Users/elvis/Desktop/repo-signal
git add dsh-plugins/fresh-session-jobs
git commit -m "feat(dsh-plugin): build receipt text and prompt wrapper"
```

---

### Task 6: 运行记录裁剪

**Files:**
- Create: `dsh-plugins/fresh-session-jobs/src/retention.js`
- Test: `dsh-plugins/fresh-session-jobs/tests/retention.test.js`

- [ ] **Step 1: 写失败测试**

```js
import test from 'node:test'
import assert from 'node:assert/strict'
import { pruneRuns, RUN_KEEP, RUN_MAX_AGE_MS } from '../src/retention.js'

test('超过 30 天的记录被丢弃', () => {
  const now = Date.parse('2026-10-07T00:00:00Z')
  const runs = [
    { id: 'old', startedAt: now - RUN_MAX_AGE_MS - 1 },
    { id: 'fresh', startedAt: now - 1000 },
  ]
  assert.deepEqual(pruneRuns(runs, now).map((r) => r.id), ['fresh'])
})

test('超过 200 条时保留最新的 200 条，且顺序不变', () => {
  const now = 1_000_000_000
  const runs = Array.from({ length: RUN_KEEP + 25 }, (_, index) => ({ id: `r${index}`, startedAt: now - index * 1000 }))
  const kept = pruneRuns(runs, now)
  assert.equal(kept.length, RUN_KEEP)
  assert.equal(kept[0].id, 'r0')
  assert.equal(kept.at(-1).id, `r${RUN_KEEP - 1}`)
})
```

- [ ] **Step 2: 运行测试，确认失败**

Run: `cd dsh-plugins/fresh-session-jobs && node --test tests/retention.test.js`
Expected: FAIL，模块不存在

- [ ] **Step 3: 实现 src/retention.js**

```js
export const RUN_KEEP = 200
export const RUN_MAX_AGE_MS = 30 * 24 * 60 * 60 * 1000

/** 先按年龄丢弃，再按条数保留最新；返回仍按时间升序排列。 */
export function pruneRuns(runs, nowMs, { keep = RUN_KEEP, maxAgeMs = RUN_MAX_AGE_MS } = {}) {
  const alive = runs.filter((run) => nowMs - run.startedAt <= maxAgeMs)
  if (alive.length <= keep) return alive
  return [...alive]
    .sort((a, b) => b.startedAt - a.startedAt)
    .slice(0, keep)
    .sort((a, b) => a.startedAt - b.startedAt)
}
```

- [ ] **Step 4: 运行测试，确认通过**

Run: `cd dsh-plugins/fresh-session-jobs && node --test tests/retention.test.js`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
cd /Users/elvis/Desktop/repo-signal
git add dsh-plugins/fresh-session-jobs
git commit -m "feat(dsh-plugin): prune run history by age and count"
```

---

### Task 7: 运行状态存储（内存 + JSON 文件）

**Files:**
- Create: `dsh-plugins/fresh-session-jobs/src/job-store.js`
- Test: `dsh-plugins/fresh-session-jobs/tests/job-store.test.js`

任务定义来自配置（Task 11），这里只持久化**运行状态**：每个任务的上次发生点/下次目标，以及全部运行记录。
落盘位置由 Task 12 决定：`$DSH_HOME/fresh-session-jobs/state.json`。

- [ ] **Step 1: 写失败测试**

```js
import test from 'node:test'
import assert from 'node:assert/strict'
import { mkdtempSync, readFileSync, writeFileSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { join } from 'node:path'
import { createMemoryStore, createFileStore } from '../src/job-store.js'

const configJobs = [{
  id: 'daily-report', title: '每日报告', prompt: '跑一遍', enabled: true,
  rule: { kind: 'daily', at: '06:30', timeZone: 'Asia/Shanghai' },
  workspaceId: 'ws-1', ownerSessionId: 'owner-1',
}]

test('内存实现：任务与运行记录', async () => {
  const store = createMemoryStore({ jobs: configJobs })
  await store.putRun({ id: 'r1', jobId: 'daily-report', startedAt: 10, status: 'running' })
  await store.putRun({ id: 'r1', jobId: 'daily-report', startedAt: 10, status: 'completed' })
  assert.equal(store.listRuns('daily-report').length, 1)
  assert.equal(store.listRuns('daily-report')[0].status, 'completed')
  assert.deepEqual(await store.prune(10), [])
})

test('文件实现：运行记录与下次目标跨进程保留', async () => {
  const path = join(mkdtempSync(join(tmpdir(), 'fsj-')), 'state.json')
  const first = createFileStore({ path, jobs: configJobs })
  await first.putRun({ id: 'r1', jobId: 'daily-report', occurrenceAt: 100, startedAt: 100, status: 'completed' })
  await first.putJob({ ...first.getJob('daily-report'), nextAt: 999 })
  const second = createFileStore({ path, jobs: configJobs })
  assert.equal(second.listRuns('daily-report')[0].status, 'completed')
  assert.equal(second.getJob('daily-report').nextAt, 999)
  assert.equal(second.getJob('daily-report').title, '每日报告') // 任务定义来自配置
})

test('文件实现：未写过 nextAt 时不会落成 0', async () => {
  const path = join(mkdtempSync(join(tmpdir(), 'fsj-')), 'state.json')
  const store = createFileStore({ path, jobs: configJobs })
  await store.putJob(store.getJob('daily-report'))
  assert.equal(store.getJob('daily-report').nextAt, undefined)
  assert.equal(createFileStore({ path, jobs: configJobs }).getJob('daily-report').nextAt, undefined)
})

test('文件实现：文件损坏时告警并从空状态启动，随后可正常写入', async () => {
  const path = join(mkdtempSync(join(tmpdir(), 'fsj-')), 'state.json')
  writeFileSync(path, '{ 这不是 JSON')
  const warnings = []
  const store = createFileStore({ path, jobs: configJobs, log: (message) => warnings.push(message) })
  assert.equal(store.listRuns('daily-report').length, 0)
  assert.equal(warnings.length, 1)
  await store.putRun({ id: 'r1', jobId: 'daily-report', startedAt: 5, status: 'completed' })
  assert.equal(JSON.parse(readFileSync(path, 'utf8')).runs.length, 1)
})

test('文件实现：裁剪会删掉最旧记录并立即落盘', async () => {
  const path = join(mkdtempSync(join(tmpdir(), 'fsj-')), 'state.json')
  const store = createFileStore({ path, jobs: configJobs })
  const now = 1_000_000_000_000
  await store.putRun({ id: 'old', jobId: 'daily-report', startedAt: now - 40 * 24 * 3600 * 1000, status: 'completed' })
  await store.putRun({ id: 'new', jobId: 'daily-report', startedAt: now - 1000, status: 'completed' })
  assert.deepEqual(await store.prune(now), ['old'])
  assert.deepEqual(createFileStore({ path, jobs: configJobs }).listRuns('daily-report').map((run) => run.id), ['new'])
})
```

- [ ] **Step 2: 运行测试，确认失败**

Run: `cd dsh-plugins/fresh-session-jobs && node --test tests/job-store.test.js`
Expected: FAIL，模块不存在

- [ ] **Step 3: 实现 src/job-store.js**

```js
import { mkdirSync, readFileSync, renameSync, writeFileSync } from 'node:fs'
import { dirname } from 'node:path'
import { pruneRuns } from './retention.js'

const STATE_VERSION = 1

function emptyState() {
  return { version: STATE_VERSION, jobs: {}, runs: [] }
}

function normalize(raw) {
  if (raw === null || typeof raw !== 'object' || raw.version !== STATE_VERSION) throw new Error('unsupported state version')
  return { version: STATE_VERSION, jobs: raw.jobs ?? {}, runs: Array.isArray(raw.runs) ? raw.runs : [] }
}

/** 存储接口：listJobs / getJob / putJob / deleteJob / listRuns / putRun / prune。 */
export function createMemoryStore({ jobs = [], runs = [] } = {}) {
  const jobMap = new Map(jobs.map((job) => [job.id, { ...job }]))
  let runList = runs.map((run) => ({ ...run }))
  return {
    listJobs: () => [...jobMap.values()],
    getJob: (id) => jobMap.get(id),
    async putJob(job) { jobMap.set(job.id, { ...job }) },
    async deleteJob(id) {
      jobMap.delete(id)
      runList = runList.filter((run) => run.jobId !== id)
    },
    listRuns: (jobId) => runList.filter((run) => run.jobId === jobId).sort((a, b) => a.startedAt - b.startedAt),
    async putRun(run) { runList = [...runList.filter((item) => item.id !== run.id), { ...run }] },
    async prune(nowMs) {
      const kept = pruneRuns(runList, nowMs)
      const keptIds = new Set(kept.map((run) => run.id))
      const removed = runList.filter((run) => !keptIds.has(run.id)).map((run) => run.id)
      runList = kept
      return removed
    },
  }
}

/**
 * 文件实现：任务定义来自配置，运行状态落在 JSON 文件里。
 * 每次写入先写 .tmp 再 rename，避免读到半个文件。
 */
export function createFileStore({ path, jobs, log = () => {} }) {
  let state
  try {
    state = normalize(JSON.parse(readFileSync(path, 'utf8')))
  } catch (error) {
    if (error?.code !== 'ENOENT') log(`[fresh-session-jobs] state file unusable, starting empty: ${String(error?.message ?? error)}`)
    state = emptyState()
  }

  function persist() {
    mkdirSync(dirname(path), { recursive: true })
    const temporary = `${path}.tmp`
    writeFileSync(temporary, JSON.stringify(state, null, 2))
    renameSync(temporary, path)
  }

  const merged = (job) => ({ ...job, ...(state.jobs[job.id] ?? {}) })

  return {
    listJobs: () => jobs.map(merged),
    getJob: (id) => {
      const job = jobs.find((item) => item.id === id)
      return job === undefined ? undefined : merged(job)
    },
    async putJob(job) {
      const previous = state.jobs[job.id] ?? {}
      state.jobs[job.id] = {
        lastOccurrenceAt: job.lastOccurrenceAt ?? previous.lastOccurrenceAt ?? 0,
        ...(job.nextAt === undefined ? {} : { nextAt: job.nextAt }),
      }
      persist()
    },
    async deleteJob(id) {
      delete state.jobs[id]
      state.runs = state.runs.filter((run) => run.jobId !== id)
      persist()
    },
    listRuns: (jobId) => state.runs.filter((run) => run.jobId === jobId).sort((a, b) => a.startedAt - b.startedAt),
    async putRun(run) {
      state.runs = [...state.runs.filter((item) => item.id !== run.id), run]
      persist()
    },
    async prune(nowMs) {
      const kept = pruneRuns(state.runs, nowMs)
      const keptIds = new Set(kept.map((run) => run.id))
      const removed = state.runs.filter((run) => !keptIds.has(run.id)).map((run) => run.id)
      state.runs = kept
      persist()
      return removed
    },
  }
}
```

- [ ] **Step 4: 运行测试，确认通过**

Run: `cd dsh-plugins/fresh-session-jobs && node --test tests/job-store.test.js`
Expected: PASS（5 个 test）

- [ ] **Step 5: 提交**

```bash
cd /Users/elvis/Desktop/repo-signal
git add dsh-plugins/fresh-session-jobs
git commit -m "feat(dsh-plugin): add memory and json-file run-state stores"
```

---

### Task 8: 调度核心

**Files:**
- Create: `dsh-plugins/fresh-session-jobs/src/scheduler.js`
- Test: `dsh-plugins/fresh-session-jobs/tests/scheduler.test.js`

- [ ] **Step 1: 写失败测试**

```js
import test from 'node:test'
import assert from 'node:assert/strict'
import { createScheduler } from '../src/scheduler.js'
import { createMemoryStore } from '../src/job-store.js'

function makeRunner({ fail = false } = {}) {
  const calls = []
  return {
    calls,
    async runOnce(job, occurrenceAt) { calls.push({ kind: 'run', jobId: job.id, occurrenceAt }); if (fail) throw new Error('boom') },
    async recordSkipped(job, occurrenceAt, reason) { calls.push({ kind: 'skip', jobId: job.id, occurrenceAt, reason }) },
  }
}

const rule = { kind: 'daily', at: '06:30', timeZone: 'Asia/Shanghai' }
const baseJob = { id: 'j1', title: 'T', prompt: 'p', rule, enabled: true, createdAt: Date.parse('2026-10-01T00:00:00Z'), nextAt: Date.parse('2026-10-07T22:30:00Z') }

test('未到点不触发', async () => {
  const store = createMemoryStore({ jobs: [baseJob] })
  const runner = makeRunner()
  const scheduler = createScheduler({ store, runner, nextAtFor: () => 0 })
  await scheduler.tick(Date.parse('2026-10-07T22:00:00Z'))
  assert.equal(runner.calls.length, 0)
})

test('到点触发一次，并推进 nextAt', async () => {
  const store = createMemoryStore({ jobs: [baseJob] })
  const runner = makeRunner()
  const nextAtFor = () => Date.parse('2026-10-08T22:30:00Z')
  const scheduler = createScheduler({ store, runner, nextAtFor })
  await scheduler.tick(Date.parse('2026-10-07T23:00:00Z'))
  assert.deepEqual(runner.calls, [{ kind: 'run', jobId: 'j1', occurrenceAt: baseJob.nextAt }])
  assert.equal(store.getJob('j1').nextAt, nextAtFor())
})

test('错过多个发生时点只补发最近一次', async () => {
  const store = createMemoryStore({ jobs: [{ ...baseJob, nextAt: Date.parse('2026-10-01T22:30:00Z') }] })
  const runner = makeRunner()
  const scheduler = createScheduler({ store, runner, nextAtFor: (job, from) => from + 86_400_000 })
  await scheduler.tick(Date.parse('2026-10-07T23:00:00Z'))
  assert.equal(runner.calls.length, 1)
  assert.equal(new Date(runner.calls[0].occurrenceAt).toISOString(), '2026-10-07T22:30:00.000Z')
})

test('上一次仍在运行则跳过并记录原因', async () => {
  const store = createMemoryStore({
    jobs: [baseJob],
    runs: [{ id: 'r', jobId: 'j1', occurrenceAt: baseJob.nextAt - 86_400_000, startedAt: 1, status: 'running' }],
  })
  const runner = makeRunner()
  const scheduler = createScheduler({ store, runner, nextAtFor: () => 0 })
  await scheduler.tick(Date.parse('2026-10-07T23:00:00Z'))
  assert.deepEqual(runner.calls, [{ kind: 'skip', jobId: 'j1', occurrenceAt: baseJob.nextAt, reason: 'previous-running' }])
  assert.equal(runner.calls.some((call) => call.kind === 'run'), false)
})

test('同一发生点已经跑过就不再跑（幂等）', async () => {
  const store = createMemoryStore({
    jobs: [baseJob],
    runs: [{ id: 'r', jobId: 'j1', occurrenceAt: baseJob.nextAt, startedAt: 1, status: 'completed' }],
  })
  const runner = makeRunner()
  const scheduler = createScheduler({ store, runner, nextAtFor: () => 0 })
  await scheduler.tick(Date.parse('2026-10-07T23:00:00Z'))
  assert.equal(runner.calls.length, 0)
})

test('runner 抛错不阻塞其他任务', async () => {
  const store = createMemoryStore({ jobs: [baseJob, { ...baseJob, id: 'j2' }] })
  const runner = { calls: [], async runOnce(job) { this.calls.push(job.id); if (job.id === 'j1') throw new Error('boom') }, async recordSkipped() {} }
  const errors = []
  const scheduler = createScheduler({ store, runner, nextAtFor: () => 0, log: (message) => errors.push(message) })
  await scheduler.tick(Date.parse('2026-10-07T23:00:00Z'))
  assert.deepEqual(runner.calls, ['j1', 'j2'])
  assert.equal(errors.length, 1)
})
```

- [ ] **Step 2: 运行测试，确认失败**

Run: `cd dsh-plugins/fresh-session-jobs && node --test tests/scheduler.test.js`
Expected: FAIL，模块不存在

- [ ] **Step 3: 实现 src/scheduler.js**

```js
import { nextOccurrence, occurrenceAtOrBefore } from './rules.js'
import { findRunForOccurrence } from './keys.js'
import { RUN_STATUS } from './run-state.js'

/**
 * 调度核心。
 * @param store 任务/运行存储
 * @param runner { runOnce(job, occurrenceAt), recordSkipped(job, occurrenceAt, reason) }
 * @param nextAtFor (job, fromMs) => number
 * @param clock 注入时钟（测试用）
 */
export function createScheduler({ store, runner, nextAtFor, clock = () => Date.now(), log = () => {}, tickMs = 20_000 }) {
  async function tick(nowMs) {
    for (const job of store.listJobs()) {
      try {
        if (!job.enabled) continue
        // 没有持久化目标时，以"现在"为起点算下一个未来发生点：
        // 新装插件不会去补跑历史上的发生点（首次运行不惊吓用户）
        const nextAt = job.nextAt ?? nextAtFor(job, clock())
        if (nextAt > nowMs) continue

        // 只补发最近一次：从 nextAt 起、不晚于现在的最后一个发生时点
        const occurrenceAt = occurrenceAtOrBefore(job.rule, nextAt, nowMs) ?? nextAt

        const runs = store.listRuns(job.id)
        if (findRunForOccurrence(runs, job.id, occurrenceAt) !== null) {
          job.nextAt = nextAtFor(job, occurrenceAt)
          await store.putJob(job)
          continue
        }
        const stillRunning = runs.some((run) => run.status === RUN_STATUS.RUNNING)
        if (stillRunning) await runner.recordSkipped(job, occurrenceAt, 'previous-running')
        else await runner.runOnce(job, occurrenceAt)

        job.nextAt = nextAtFor(job, occurrenceAt)
        await store.putJob(job)
      } catch (error) {
        log(`[fresh-session-jobs] job ${job.id} tick failed: ${String(error?.message ?? error)}`)
      }
    }
  }

  let timer = null
  return {
    tick,
    start() {
      if (timer !== null) return
      timer = setInterval(() => { tick(clock()).catch(log) }, tickMs)
      if (typeof timer.unref === 'function') timer.unref()
      tick(clock()).catch(log)
    },
    stop() {
      if (timer !== null) { clearInterval(timer); timer = null }
    },
    nextAtFor,
    nextOccurrence,
  }
}
```

- [ ] **Step 4: 运行测试，确认通过**

Run: `cd dsh-plugins/fresh-session-jobs && node --test tests/scheduler.test.js`
Expected: PASS（6 个 test）

- [ ] **Step 5: 提交**

```bash
cd /Users/elvis/Desktop/repo-signal
git add dsh-plugins/fresh-session-jobs
git commit -m "feat(dsh-plugin): add scheduler with idempotency and catch-up rules"
```

---

### Task 9: 宿主适配层与 API 核对

**Files:**
- Create: `dsh-plugins/fresh-session-jobs/src/host.js`
- Create: `dsh-plugins/fresh-session-jobs/NOTES.md`

这个任务没有单元测试：它只做两件事——把已核对的 API 固化成适配层，并用宿主自带的检查工具复核一遍。

- [ ] **Step 1: 用 `cordis_inspect_query` 复核（在 `cordis` preset 的会话里执行；本会话没有该工具）**

依次查询并记录到 `NOTES.md`：`Service` 列出 `sessionController`、`workspaceRegistry`、`sessionTitle` 的方法签名（`agents` 也一并记录，便于核对会话 id 的读取路径）；`Event` 里确认是否存在可订阅的会话事件（用于替代 `whenIdle` 的精确等待，可选）。

- [ ] **Step 2: 写 NOTES.md**

把这一步的查询结果原样贴进去，并逐条标注「与计划一致 / 有出入（出入内容）」。**有出入时以 NOTES.md 为准修改本任务 Step 3 的代码，不要改规格。**

- [ ] **Step 3: 实现 src/host.js**

```js
import { createUserMessage } from './message.js'
import { lastTurnEnd, lastAssistantText } from './session-fold.js'

const DEFAULT_TIMEOUT_MS = 60 * 60 * 1000

function waitForTurnEnd(agent, boundary, timeoutMs) {
  return new Promise((resolve, reject) => {
    const timer = setTimeout(() => {
      try { agent.cancel() } catch { /* 取消失败不影响后续标记 */ }
      reject(new Error(`run timeout after ${timeoutMs} ms`))
    }, timeoutMs)
    Promise.resolve(agent.whenIdle()).then(() => {
      clearTimeout(timer)
      const end = lastTurnEnd(agent.session.snapshotEvents(boundary))
      if (end === null) reject(new Error('turn did not settle'))
      else resolve(end)
    }, (error) => {
      clearTimeout(timer)
      reject(error)
    })
  })
}

/**
 * resolveAgent 返回的是包装对象：成功为 { agent, ... }，失败为 { error }。
 * 直接把它当 agent 用会得到 `agent.session === undefined`（最小验证版实测踩过，
 * 随后 rename 抛错、整个 run 静默失败）。这里统一解包。
 */
async function requireAgent(ctx, sessionId) {
  const resolved = await ctx.sessionController.resolveAgent(sessionId)
  if (resolved !== null && typeof resolved === 'object' && 'error' in resolved) throw resolved.error
  const agent = resolved?.agent
  if (agent === undefined) throw new Error(`resolveAgent(${sessionId}) returned no agent`)
  return agent
}

/** 唯一直接依赖 ctx.* 的模块；其余模块保持纯净可测。 */
export function createHostAdapter(ctx) {
  return {
    async createSession({ workspaceId }) {
      const created = await ctx.sessionController.create({ workspaceId })
      return created.sessionId
    },
    async renameSession(sessionId, title) {
      const agent = await requireAgent(ctx, sessionId)
      await ctx.sessionTitle.rename(agent.session, title)
    },
    async drivePrompt({ sessionId, prompt, timeoutMs = DEFAULT_TIMEOUT_MS }) {
      const agent = await requireAgent(ctx, sessionId)
      const boundary = agent.session.snapshotEvents().length
      agent.followup(createUserMessage({ content: [{ type: 'text', text: prompt }], source: { kind: 'user' } }))
      // flush 之后这次投递才算落盘；内置 schedule 的投递同样走这一步
      await ctx.sessions.flush(agent.session)
      const end = await waitForTurnEnd(agent, boundary, timeoutMs)
      const events = agent.session.snapshotEvents(boundary)
      return { endReason: end?.data?.reason ?? null, finalText: lastAssistantText(events) }
    },
    async archiveSession(sessionId) {
      await ctx.workspaceRegistry.archiveSession(sessionId)
    },
    async notifyOwner(sessionId, text) {
      const agent = await requireAgent(ctx, sessionId)
      agent.followup(createUserMessage({ content: [{ type: 'text', text }], source: { kind: 'user' } }))
      await ctx.sessions.flush(agent.session)
    },
    workspaceIdForSession(sessionId) {
      const record = ctx.workspaceRegistry.list().find((workspace) => workspace.sessionIds?.includes(sessionId))
      return record?.id
    },
    /** 取 Agent 所属会话 id（会话 id 的字段位置以 NOTES.md 的核对结果为准）。 */
    sessionId(agent) {
      return agent.session?.header?.id ?? agent.session?.id
    },
  }
}
```

- [ ] **Step 4: 提交**

```bash
cd /Users/elvis/Desktop/repo-signal
git add dsh-plugins/fresh-session-jobs
git commit -m "feat(dsh-plugin): add host adapter for sessions, titles, archive and receipts"
```

---

### Task 10: 运行编排

**Files:**
- Create: `dsh-plugins/fresh-session-jobs/src/runner.js`
- Test: `dsh-plugins/fresh-session-jobs/tests/runner.test.js`

- [ ] **Step 1: 写失败测试（假宿主，不碰 DSH）**

```js
import test from 'node:test'
import assert from 'node:assert/strict'
import { createRunner } from '../src/runner.js'
import { createMemoryStore } from '../src/job-store.js'

const job = {
  id: 'j1', title: '每日可行性方案', prompt: '跑一遍',
  rule: { kind: 'daily', at: '06:30', timeZone: 'Asia/Shanghai' },
  workspaceId: 'ws-1', ownerSessionId: 'owner-1', enabled: true, createdAt: 0,
  nextAt: Date.parse('2026-10-07T22:30:00Z'),
}
const occurrenceAt = job.nextAt

function makeHost({ endReason = { kind: 'completed' }, finalText = '结论', archiveFails = false, notifyFails = false } = {}) {
  const calls = []
  return {
    calls,
    async createSession(args) { calls.push(['createSession', args]); return 'session-new' },
    async renameSession(id, title) { calls.push(['renameSession', id, title]) },
    async drivePrompt(args) { calls.push(['drivePrompt', args]); return { endReason, finalText } },
    async archiveSession(id) { calls.push(['archiveSession', id]); if (archiveFails) throw new Error('archive refused') },
    async notifyOwner(id, text) { calls.push(['notifyOwner', id, text]); if (notifyFails) throw new Error('owner gone') },
  }
}

test('成功路径：建会话→命名→投递→归档→回执', async () => {
  const store = createMemoryStore({ jobs: [job] })
  const host = makeHost()
  const runner = createRunner({ store, host, clock: () => 1000 })
  const run = await runner.runOnce(job, occurrenceAt)
  assert.equal(run.status, 'completed')
  assert.equal(run.sessionId, 'session-new')
  assert.equal(run.archived, true)
  assert.equal(run.summaryText, '结论')
  assert.deepEqual(host.calls.map((call) => call[0]), ['createSession', 'renameSession', 'drivePrompt', 'archiveSession', 'notifyOwner'])
  assert.equal(host.calls[1][2], '每日可行性方案 2026-10-07')
  assert.match(host.calls[4][2], /\[定时任务回执\] 每日可行性方案/)
  assert.equal(store.listRuns('j1').length, 1)
})

test('首轮失败也归档，回执状态为失败', async () => {
  const store = createMemoryStore({ jobs: [job] })
  const host = makeHost({ endReason: { kind: 'error' }, finalText: '' })
  const run = await createRunner({ store, host, clock: () => 1000 }).runOnce(job, occurrenceAt)
  assert.equal(run.status, 'failed')
  assert.equal(run.archived, true)
})

test('建会话失败：无 sessionId，不归档，回执仍发出', async () => {
  const store = createMemoryStore({ jobs: [job] })
  const host = makeHost()
  host.createSession = async () => { throw new Error('workspace/not-found') }
  const run = await createRunner({ store, host, clock: () => 1000 }).runOnce(job, occurrenceAt)
  assert.equal(run.status, 'failed')
  assert.equal(run.sessionId, undefined)
  assert.equal(host.calls.some((call) => call[0] === 'archiveSession'), false)
  assert.equal(host.calls.some((call) => call[0] === 'notifyOwner'), true)
})

test('归档失败：回执标注未归档', async () => {
  const store = createMemoryStore({ jobs: [job] })
  const host = makeHost({ archiveFails: true })
  const run = await createRunner({ store, host, clock: () => 1000 }).runOnce(job, occurrenceAt)
  assert.equal(run.archived, false)
  assert.match(host.calls.at(-1)[2], /未归档/)
})

test('跳过：写一条 skipped 记录并发回执', async () => {
  const store = createMemoryStore({ jobs: [job] })
  const host = makeHost()
  const run = await createRunner({ store, host, clock: () => 1000 }).recordSkipped(job, occurrenceAt, 'previous-running')
  assert.equal(run.status, 'skipped')
  assert.equal(run.reason, 'previous-running')
  assert.match(host.calls.at(-1)[2], /状态：跳过（previous-running）/)
})

test('宿主重启对账：running 变 interrupted 并补发回执', async () => {
  const store = createMemoryStore({ jobs: [job], runs: [{ id: 'r1', jobId: 'j1', occurrenceAt, startedAt: 5, status: 'running', sessionId: 'session-new', archived: false }] })
  const host = makeHost()
  const done = await createRunner({ store, host, clock: () => 1000 }).reconcile()
  assert.deepEqual(done, ['r1'])
  const stored = store.listRuns('j1')[0]
  assert.equal(stored.status, 'interrupted')
  assert.equal(stored.archived, true)
  assert.equal(host.calls.some((call) => call[0] === 'notifyOwner'), true)
})
```

- [ ] **Step 2: 运行测试，确认失败**

Run: `cd dsh-plugins/fresh-session-jobs && node --test tests/runner.test.js`
Expected: FAIL，模块不存在

- [ ] **Step 3: 实现 src/runner.js**

```js
import { randomUUID } from 'node:crypto'
import { classifyEndReason, reconcileAfterRestart, RUN_STATUS } from './run-state.js'
import { buildReceipt, summarize, wrapPrompt, formatLocal } from './receipt.js'

/**
 * 一次运行的编排。
 * @param store 见 src/job-store.js
 * @param host 见 src/host.js
 * @param clock 注入时钟
 * @param runTimeoutMs 单次运行上限
 */
export function createRunner({ store, host, clock = () => Date.now(), log = () => {}, runTimeoutMs = 60 * 60 * 1000, tickMs = 20_000 }) {
  async function deliverReceipt(job, run) {
    try {
      await host.notifyOwner(job.ownerSessionId, buildReceipt({
        job,
        run,
        sessionTitle: run.sessionTitle,
        sessionId: run.sessionId,
        timeZone: job.rule.timeZone,
      }))
      run.receiptAt = clock()
    } catch (error) {
      run.receiptAt = null
      log(`[fresh-session-jobs] receipt for run ${run.id} failed: ${String(error?.message ?? error)}`)
    }
  }

  async function runOnce(job, occurrenceAt) {
    const run = {
      id: randomUUID(), jobId: job.id, occurrenceAt,
      status: RUN_STATUS.RUNNING, startedAt: clock(), archived: false,
    }
    await store.putRun(run)

    try {
      run.sessionId = await host.createSession({ workspaceId: job.workspaceId })
      run.sessionTitle = `${job.title} ${formatLocal(occurrenceAt, job.rule.timeZone).slice(0, 10)}`
      await host.renameSession(run.sessionId, run.sessionTitle)
      const outcome = await host.drivePrompt({
        sessionId: run.sessionId,
        prompt: wrapPrompt(job, occurrenceAt, job.rule.timeZone),
        timeoutMs: runTimeoutMs,
      })
      run.status = classifyEndReason(outcome.endReason)
      run.endReason = outcome.endReason?.kind ?? null
      run.summaryText = summarize(outcome.finalText)
    } catch (error) {
      run.status = RUN_STATUS.FAILED
      run.endReason = String(error?.message ?? error)
    }

    run.endedAt = clock()
    if (run.sessionId !== undefined) {
      try {
        await host.archiveSession(run.sessionId)
        run.archived = true
      } catch (error) {
        run.archived = false
        log(`[fresh-session-jobs] archive of ${run.sessionId} failed: ${String(error?.message ?? error)}`)
      }
    }

    await deliverReceipt(job, run)
    await store.putRun(run)
    await store.prune(clock())
    return run
  }

  async function recordSkipped(job, occurrenceAt, reason) {
    const run = {
      id: randomUUID(), jobId: job.id, occurrenceAt, reason,
      status: RUN_STATUS.SKIPPED, startedAt: clock(), endedAt: clock(), archived: false, summaryText: '',
    }
    await store.putRun(run)
    await deliverReceipt(job, run)
    await store.putRun(run)
    return run
  }

  /** 宿主重启对账：仍为 running 的运行标记为 interrupted，补归档与回执。 */
  async function reconcile() {
    const done = []
    for (const job of store.listJobs()) {
      for (const run of store.listRuns(job.id)) {
        if (run.status !== RUN_STATUS.RUNNING) continue
        const [reconciled] = reconcileAfterRestart([run])
        Object.assign(run, reconciled)
        if (run.sessionId !== undefined) {
          try { await host.archiveSession(run.sessionId); run.archived = true } catch { run.archived = false }
        }
        await deliverReceipt(job, run)
        await store.putRun(run)
        done.push(run.id)
      }
    }
    return done
  }

  return { runOnce, recordSkipped, reconcile, tickMs }
}
```

- [ ] **Step 4: 运行测试，确认通过**

Run: `cd dsh-plugins/fresh-session-jobs && node --test tests/runner.test.js`
Expected: PASS（6 个 test）

- [ ] **Step 5: 全量测试 + 提交**

Run: `cd dsh-plugins/fresh-session-jobs && node --test tests/*.test.js`
Expected: PASS（10 个文件全绿）

```bash
cd /Users/elvis/Desktop/repo-signal
git add dsh-plugins/fresh-session-jobs
git commit -m "feat(dsh-plugin): orchestrate one run with archive and receipt"
```

---

### Task 11: 配置装载与校验（替代工具）

**Files:**
- Create: `dsh-plugins/fresh-session-jobs/src/config.js`
- Test: `dsh-plugins/fresh-session-jobs/tests/config.test.js`

v1 不提供 agent 工具，任务全部写在 bundle 的 `cordis.patch.yml` 的 `config.jobs` 里。
任务 id 必须**跨重启稳定**（幂等键依赖它），所以缺省 id 由标题派生而不是随机生成。

- [ ] **Step 1: 写失败测试**

```js
import test from 'node:test'
import assert from 'node:assert/strict'
import { parseConfig, slugId } from '../src/config.js'

const valid = {
  jobs: [{
    title: '每日GitHub组合可行性方案',
    prompt: '执行每日分析',
    rule: { kind: 'daily', at: '06:30' },
    workspaceId: 'ws-1',
    ownerSessionId: 'owner-1',
  }],
}

test('缺省值：时区、tick、超时、派生 id', () => {
  const parsed = parseConfig(valid)
  assert.equal(parsed.tickSeconds, 20)
  assert.equal(parsed.runTimeoutSeconds, 3600)
  const [job] = parsed.jobs
  assert.equal(job.rule.timeZone, 'Asia/Shanghai')
  assert.equal(job.enabled, true)
  assert.equal(job.id, 'job-1-每日github组合可行性方案'.toLowerCase())
})

test('id 稳定：同配置两次解析得到同一 id', () => {
  assert.deepEqual(parseConfig(valid).jobs.map((job) => job.id), parseConfig(valid).jobs.map((job) => job.id))
})

test('显式 id 优先，重复 id 报错', () => {
  const parsed = parseConfig({ jobs: [{ ...valid.jobs[0], id: 'mine' }] })
  assert.equal(parsed.jobs[0].id, 'mine')
  assert.throws(() => parseConfig({ jobs: [valid.jobs[0], valid.jobs[0]] }), /duplicate job id/)
})

test('必填与规则校验', () => {
  assert.throws(() => parseConfig({}), /jobs/)
  assert.throws(() => parseConfig({ jobs: [] }), /at least one job/)
  assert.throws(() => parseConfig({ jobs: [{ ...valid.jobs[0], title: '' }] }), /title/)
  assert.throws(() => parseConfig({ jobs: [{ ...valid.jobs[0], prompt: undefined }] }), /prompt/)
  assert.throws(() => parseConfig({ jobs: [{ ...valid.jobs[0], workspaceId: undefined }] }), /workspaceId/)
  assert.throws(() => parseConfig({ jobs: [{ ...valid.jobs[0], rule: { kind: 'daily', at: '25:00' } }] }), /invalid daily time/)
  assert.throws(() => parseConfig({ jobs: [{ ...valid.jobs[0], rule: { kind: 'every', everySeconds: 30 } }] }), />= 60/)
  assert.throws(() => parseConfig({ jobs: [{ ...valid.jobs[0], rule: { kind: 'cron', expression: '* * * *' } }] }), /5 fields/)
  assert.throws(() => parseConfig({ jobs: [{ ...valid.jobs[0], rule: { kind: 'hourly' } }] }), /unknown rule kind/)
})

test('slugId：保留中文，去掉空白与标点', () => {
  assert.equal(slugId('每日 GitHub 组合方案!'), '每日-github-组合方案')
})
```

- [ ] **Step 2: 运行测试，确认失败**

Run: `cd dsh-plugins/fresh-session-jobs && node --test tests/config.test.js`
Expected: FAIL，模块不存在

- [ ] **Step 3: 实现 src/config.js**

```js
import { nextOccurrence } from './rules.js'

const DEFAULT_TIME_ZONE = 'Asia/Shanghai'

/** 标题 → 稳定 id：小写、空白转连字符、去掉标点，保留中文。 */
export function slugId(title) {
  return String(title)
    .toLowerCase()
    .replace(/[\s_]+/g, '-')
    .replace(/[^\p{Letter}\p{Number}-]+/gu, '')
    .replace(/-{2,}/g, '-')
    .replace(/^-|-$/g, '')
}

function requireText(value, field) {
  if (typeof value !== 'string' || value.trim() === '') throw new Error(`job field "${field}" must be a non-empty string`)
  return value.trim()
}

function parseRule(rule, field) {
  if (rule === null || typeof rule !== 'object') throw new Error(`job field "${field}" must be an object`)
  const timeZone = rule.timeZone ?? DEFAULT_TIME_ZONE
  const base = { timeZone }
  if (rule.kind === 'daily') {
    const at = requireText(rule.at, `${field}.at`)
    if (!/^\d{1,2}:\d{2}$/.test(at)) throw new Error(`invalid daily time "${at}"`)
    const [hour, minute] = at.split(':').map(Number)
    if (hour > 23 || minute > 59) throw new Error(`invalid daily time "${at}"`)
    return { kind: 'daily', at, timeZone }
  }
  if (rule.kind === 'every') {
    if (!Number.isSafeInteger(rule.everySeconds) || rule.everySeconds < 60) throw new Error(`job field "${field}.everySeconds" must be an integer >= 60`)
    return { kind: 'every', everySeconds: rule.everySeconds, timeZone }
  }
  if (rule.kind === 'cron') {
    const expression = requireText(rule.expression, `${field}.expression`)
    if (expression.split(/\s+/).length !== 5) throw new Error(`cron expression must have 5 fields: "${expression}"`)
    return { kind: 'cron', expression, timeZone }
  }
  throw new Error(`unknown rule kind "${rule.kind}"`)
}

/** 校验并规范化整份插件配置；任何问题都抛出带字段名的错误，绝不带病启动。 */
export function parseConfig(raw) {
  if (raw === null || typeof raw !== 'object') throw new Error('plugin config must be a mapping with a "jobs" list')
  if (!Array.isArray(raw.jobs)) throw new Error('plugin config must declare a "jobs" list')
  if (raw.jobs.length === 0) throw new Error('plugin config must declare at least one job')

  const seen = new Set()
  const jobs = raw.jobs.map((entry, index) => {
    if (entry === null || typeof entry !== 'object') throw new Error(`jobs[${index}] must be a mapping`)
    const title = requireText(entry.title, 'title')
    const id = entry.id === undefined ? `job-${index + 1}-${slugId(title)}` : requireText(entry.id, 'id')
    if (seen.has(id)) throw new Error(`duplicate job id "${id}"`)
    seen.add(id)
    const job = {
      id,
      title,
      prompt: requireText(entry.prompt, 'prompt'),
      rule: parseRule(entry.rule, 'rule'),
      workspaceId: requireText(entry.workspaceId, 'workspaceId'),
      enabled: entry.enabled !== false,
    }
    if (entry.ownerSessionId !== undefined) job.ownerSessionId = requireText(entry.ownerSessionId, 'ownerSessionId')
    // 规则合法性在这里就用一次 nextOccurrence 兜底验证（cron 必须已 configureCron）
    nextOccurrence(job.rule, Date.now())
    return job
  })

  return {
    tickSeconds: raw.tickSeconds ?? 20,
    runTimeoutSeconds: raw.runTimeoutSeconds ?? 3600,
    jobs,
  }
}
```

- [ ] **Step 4: 运行测试，确认通过**

Run: `cd dsh-plugins/fresh-session-jobs && node --test tests/config.test.js`
Expected: PASS（5 个 test）

- [ ] **Step 5: 提交**

```bash
cd /Users/elvis/Desktop/repo-signal
git add dsh-plugins/fresh-session-jobs
git commit -m "feat(dsh-plugin): parse and validate config-declared jobs"
```

---

### Task 12: 插件入口与 bundle 清单

**Files:**
- Create: `dsh-plugins/fresh-session-jobs/index.js`
- Create: `dsh-plugins/fresh-session-jobs/cordis.patch.yml`
- Test: `dsh-plugins/fresh-session-jobs/tests/plugin-entry.test.js`

入口**不得 import 任何宿主包**（见文首铁律），所以没有 `Config` schema：配置由 `src/config.js` 自己校验。

- [ ] **Step 1: 写失败测试（用桩 ctx 验证装配与配置失败路径）**

```js
import test from 'node:test'
import assert from 'node:assert/strict'
import { mkdtempSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { join } from 'node:path'
import { apply, inject, name } from '../index.js'

// 让插件的状态文件落在临时目录，别污染真实的 $DSH_HOME
process.env.DSH_HOME = mkdtempSync(join(tmpdir(), 'fsj-home-'))

function makeCtx() {
  const calls = []
  const disposers = []
  return {
    calls, disposers,
    logger: { warn: (message) => calls.push(['warn', message]) },
    effect: (factory) => { disposers.push(factory()) },
    sessionController: {
      create: async () => { calls.push(['create']); return { sessionId: 'session-new' } },
      resolveAgent: async () => ({ agent: { session: { id: 'session-new' }, whenIdle: async () => {}, followup: () => {} } }),
    },
    sessions: { flush: async () => {} },
    sessionTitle: { rename: async () => {} },
    workspaceRegistry: { archiveSession: async () => {}, list: () => [] },
  }
}

test('插件导出名与注入服务', () => {
  assert.equal(name, 'fresh-session-jobs')
  assert.deepEqual(inject, ['sessionController', 'workspaceRegistry', 'sessionTitle', 'sessions'])
})

test('配置无效时不启动，只记一条告警', () => {
  const ctx = makeCtx()
  apply(ctx, { jobs: [] })
  assert.equal(ctx.disposers.length, 0)
  assert.match(ctx.calls[0][1], /配置无效/)
})

test('配置有效时注册一个 effect，卸载时调用 disposer', () => {
  const ctx = makeCtx()
  apply(ctx, {
    jobs: [{
      id: 'daily-x', title: '每日X', prompt: 'p',
      rule: { kind: 'every', everySeconds: 3600, timeZone: 'Asia/Shanghai' },
      workspaceId: 'ws-1', ownerSessionId: 'owner-1', enabled: false,
    }],
    tickSeconds: 999,
  })
  assert.equal(ctx.disposers.length, 1)
  assert.equal(typeof ctx.disposers[0], 'function')
  ctx.disposers[0]()
})
```

（`enabled: false` 让这次装配不会真的触发运行；定时器用 `tickSeconds: 999` 拉开。）

- [ ] **Step 2: 运行测试，确认失败**

Run: `cd dsh-plugins/fresh-session-jobs && node --test tests/plugin-entry.test.js`
Expected: FAIL，`Cannot find module '../index.js'`

- [ ] **Step 3: 实现 index.js**

```js
import { homedir } from 'node:os'
import { join } from 'node:path'
import { parseConfig } from './src/config.js'
import { createFileStore } from './src/job-store.js'
import { createScheduler } from './src/scheduler.js'
import { createRunner } from './src/runner.js'
import { createHostAdapter } from './src/host.js'
import { nextOccurrence, configureCron } from './src/rules.js'
import { nextCronOccurrence } from './src/cron.js'

configureCron({ nextCronOccurrence })

export const name = 'fresh-session-jobs'
export const inject = ['sessionController', 'workspaceRegistry', 'sessionTitle', 'sessions']

export function apply(ctx, rawConfig) {
  const log = (message) => {
    const text = `[fresh-session-jobs] ${message}`
    if (typeof ctx.logger?.warn === 'function') ctx.logger.warn(text)
    else console.warn(text)
  }

  let config
  try {
    config = parseConfig(rawConfig)
  } catch (error) {
    log(`配置无效，插件不启动：${String(error?.message ?? error)}`)
    return
  }

  const host = createHostAdapter(ctx)
  const statePath = join(process.env.DSH_HOME ?? join(homedir(), '.dsh'), 'fresh-session-jobs', 'state.json')

  ctx.effect(() => {
    const store = createFileStore({ path: statePath, jobs: config.jobs, log })
    const runner = createRunner({ store, host, log, runTimeoutMs: config.runTimeoutSeconds * 1000 })
    const scheduler = createScheduler({
      store,
      runner,
      tickMs: config.tickSeconds * 1000,
      nextAtFor: (job, fromMs) => nextOccurrence(job.rule, fromMs),
      log,
    })

    runner.reconcile()
      .then((ids) => { if (ids.length > 0) log(`重启对账：${ids.length} 次运行标记为中断并补发回执`) })
      .catch((error) => log(`重启对账失败：${String(error?.message ?? error)}`))
      .finally(() => scheduler.start())

    return () => scheduler.stop()
  })
}
```

- [ ] **Step 4: 建 cordis.patch.yml**

```yaml
- insert:
    - id: fresh-session-jobs
      name: '@local/dsh-fresh-session-jobs'
      config:
        tickSeconds: 20
        runTimeoutSeconds: 3600
        jobs:
          - id: daily-feasibility
            title: 每日GitHub组合可行性方案
            workspaceId: 3d0269e2-3e85-4e5e-b784-30f1837184f2
            ownerSessionId: session-0faa1c50-8901-47dd-90d3-519208fe40aa
            rule:
              kind: daily
              at: '06:30'
              timeZone: Asia/Shanghai
            prompt: |-
              按工作区契约文件 data/github-project-digest/feasibility/FEASIBILITY-TASK.md 执行今日的
              GitHub 组合可行性分析：先读该文件并遵守其中的步骤、边界与核验清单，完成后简要汇报
              本轮组合数、业务名、判断与报告路径。
```

（提示词只写"按契约文件执行"，不复制那份长契约，避免两处漂移。）

- [ ] **Step 5: 全量测试与语法检查**

Run: `cd dsh-plugins/fresh-session-jobs && node --test tests/*.test.js && node --check index.js && node --check src/host.js && grep -rn "@deepseek-ai/" index.js src/ || echo "无宿主包导入 ✅"`
Expected: 测试全绿、`node --check` 无输出、grep 无命中

- [ ] **Step 6: 提交**

```bash
cd /Users/elvis/Desktop/repo-signal
git add dsh-plugins/fresh-session-jobs
git commit -m "feat(dsh-plugin): add dependency-free plugin entry and bundle manifest"
```

---

### Task 13: 安装与验收

**Files:**
- Modify: `dsh-plugins/fresh-session-jobs/NOTES.md`（记录安装与验收结果）

- [ ] **Step 1: 安装 bundle**

在 `cordis` preset 的会话里调用 `plugin_manager`（`action: install_bundle`，`target` 为 `/Users/elvis/Desktop/repo-signal/dsh-plugins/fresh-session-jobs`）；
若该工具不可用，则在 GUI 插件页安装同一目录，或 `dsh plugin --profile desktop add /Users/elvis/Desktop/repo-signal/dsh-plugins/fresh-session-jobs`（后两者都要确认后执行）。
判定标准：安装结果 `application: applied`，且 `list_plugins` 里出现 `fresh-session-jobs` 行。

**注意**：改完插件源码（含 `index.js`、`src/*.js`、`cordis.patch.yml` 里的 jobs 配置）后必须重启应用或重装 bundle，
loader 缓存的是上一次的模块代际；只改 patch 配置时重装 bundle 即可。

- [ ] **Step 2: 冒烟：先用测试任务跑通机制**

把 `cordis.patch.yml` 的 jobs 临时换成一个轻量任务（`rule: { kind: 'every', everySeconds: 60 }`、提示词只回一句话），
重启后确认：新会话出现、标题为 `{title} {YYYY-MM-DD}`、首条消息带 `[定时任务]` 首行、跑完进归档、owner 会话收到回执。

- [ ] **Step 3: 逐条执行规格 §9 的验收清单**

1. 到点触发 → 新会话标题严格等于 `{title} {YYYY-MM-DD}`
2. 首条消息是提示词正文且带 `[定时任务]` 来源首行
3. 首轮结束后会话进入 `archivedSessionIds`
4. owner 会话收到回执，含任务名/发生时点/状态/新会话标题与 id/摘要
5. 首轮失败时同样归档，回执状态为「失败」并带原因
6. 宿主重启后：错过只补发最近一次；被打断的运行记为 `interrupted` 且有回执
7. 上次未结束时下次到点 → `skipped(previous-running)` 且不产生第二个会话
8. 卸载插件后内置 schedule 任务行为与存储不变（回归）
9. 手工验收：把「每日GitHub组合可行性方案」迁到本插件跑一天，对照原会话只收到一条回执、归档里能找到该会话

第 6 条验证方式：把某个任务设成 2 分钟后触发，触发后 10 秒内 `kill` 宿主进程并重启应用，
检查 `state.json` 里该 run 变成 `interrupted` 且 owner 会话收到回执。

第 7 条验证方式：给任务配一个足够长的提示词（或用 `every` 60 秒 + 长任务），让上一次运行跨过下一次发生时点。

- [ ] **Step 4: 记录结果并提交**

```bash
cd /Users/elvis/Desktop/repo-signal
git add dsh-plugins/fresh-session-jobs/NOTES.md
git commit -m "docs(dsh-plugin): record install and acceptance results"
```

---

## 自检

**实测状态（2026-10-07）**：最小验证版已在隔离 profile（`web` 模板 + 独立 `$DSH_HOME`）里跑通完整链路——
新会话创建并挂到工作区、标题 `{title} {YYYY-MM-DD}`、提示词投递、模型应答（`turn/end: completed`）、
失败也归档、回执送达 owner 会话。裸导入宿主包、`resolveAgent` 返回包装对象、缺 `sessions.flush`
这三个坑都已在实测中暴露并修进本计划。

**规格覆盖**：§3.1 任务字段 → Task 7/11/12；§3.2 时序 → Task 10；§3.3 回执 → Task 5/10；§3.4 错过与重启 → Task 8/10；§3.5 不变量 → Task 8（归档在结束后）/10（幂等）/12（不写内置域）；§4 组件 → Task 7–12；§5 数据模型 → Task 7/11（任务来自配置、运行状态落 JSON）；§6 状态机 → Task 3/10；§7 失败降级 → Task 10；§9 验收 → Task 13；§11 开放问题 1 → Task 9，问题 3 → Task 11（v1 明确不做工具），问题 4 → Task 2（五字段 Vixie）。

**照规格的偏离（已确认，均因宿主限制或 YAGNI）**：

1. **零依赖**：插件不得 `import` 任何 `@deepseek-ai/*`。profile 里安装的插件按自身目录解析依赖，宿主包在 app.asar 内，裸导入会 `failed to import`（最小验证版实测）；npm 上的 `@deepseek-ai/dsh-tools` / `dsh-llm` 只有 `0.0.1-rc.1` 占位版本，不能当依赖装。因此规格 §4 里的"Tools"组件与 storage domain 持久化都被替换。
2. **任务由配置声明**（`cordis.patch.yml` 的 `config.jobs`），不提供 `fresh_job_*` 工具，也没有客户端 UI。改任务 = 改配置 + 重装/重启。
3. **持久化自管**：`$DSH_HOME/fresh-session-jobs/state.json`（只存每任务的上次发生点/下次目标 + 运行记录），不写内置 schedule 的任何域，也不用 storage domain。
4. **`agentOptions` 未接线**：`ctx.sessionController.create()` 不接受模型参数，新会话用 profile 默认，与规格 §8「v1 已知限制」一致。

**已知取舍**：

- 不实现 `cron` 的名称别名（`MON`/`JAN`），只支持数字、`*`、列表、区间与步长。
- `runTimeoutSeconds` 超时归类为 `failed`（规格未单列该项，回执里带 `run timeout` 原因）。
- 归档一律不使用 `stopActivity`，因此归档失败只会在回执里标注「未归档」，不会强杀会话。
- 会话 id 的读取路径（`agent.session.header.id` vs `agent.session.id`）由任务 9 用 `cordis_inspect_query` 核对后以 NOTES.md 为准调整，取值已集中在 `src/host.js` 一处。
- 配置文件里没有 `ownerSessionId` 的任务不会发回执（规格假定 owner 必填；实现里降级为可省略 + 记日志）。
