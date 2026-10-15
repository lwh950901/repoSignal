import { randomUUID } from 'node:crypto'

/**
 * 最小验证版插件：每天到点新建一个会话跑一次任务，跑完归档，并向指定会话发一条回执。
 *
 * 刻意不做的事（留给完整版 docs/superpowers/plans/2026-10-07-dsh-fresh-session-jobs.md）：
 * 幂等键、跨重启补发、并发保护、多任务与工具、运行历史、cron 规则。
 * 因此 lastDay 只存在内存里：宿主重启后当天可能再跑一次，这是已知且可接受的验证代价。
 *
 * 注意：**不要在这里 import 任何 @deepseek-ai/* 宿主包**。profile 里安装的插件是按自身
 * 目录解析依赖的，而宿主包在 app.asar 内，裸导入会以 ERR_MODULE_NOT_FOUND 导致
 * "failed to import"。需要宿主能力时只通过 apply(ctx) 注入进来的 ctx 使用。
 */

function deepFreeze(value) {
  if (value !== null && typeof value === 'object' && !Object.isFrozen(value)) {
    Object.freeze(value)
    for (const key of Object.keys(value)) deepFreeze(value[key])
  }
  return value
}

/** 等价于 @deepseek-ai/dsh-llm 的 createUserMessage，内联以免裸导入宿主包。 */
function createUserMessage(input) {
  return deepFreeze({ ...structuredClone(input), id: randomUUID(), role: 'user' })
}

export const name = 'fresh-session-min'
export const inject = ['sessionController', 'workspaceRegistry', 'sessionTitle', 'sessions']

/**
 * resolveAgent 返回的是包装对象：成功为 { agent, ... }，失败为 { error }。
 * 直接把它当 agent 用会得到 `agent.session === undefined`（实测踩过这个坑）。
 */
async function requireAgent(ctx, sessionId) {
  const resolved = await ctx.sessionController.resolveAgent(sessionId)
  if (resolved !== null && typeof resolved === 'object' && 'error' in resolved) throw resolved.error
  const agent = resolved?.agent
  if (agent === undefined) throw new Error(`resolveAgent(${sessionId}) returned no agent`)
  return agent
}


const TIME_ZONE = 'Asia/Shanghai'

function localDay(now) {
  return new Intl.DateTimeFormat('en-CA', { timeZone: TIME_ZONE }).format(now)
}

function minutesSinceMidnight(now) {
  return now.getHours() * 60 + now.getMinutes()
}

/**
 * skipToday 的判定：只有"今天的触发时刻已经过去"才把今天视为已跑。
 * 触发时刻还没到就返回 false——否则每天早上在 06:30 之前重启都会误跳过当天。
 */
export function shouldSkipToday(now, timeOfDay) {
  const [hour, minute] = String(timeOfDay).split(':').map(Number)
  if (!Number.isInteger(hour) || !Number.isInteger(minute) || hour > 23 || minute > 59) return false
  return minutesSinceMidnight(now) >= hour * 60 + minute
}

/** 两次轮询的墙钟间隔明显超过轮询周期 → 机器睡过（墙钟在走，进程没被调度）。 */
export function isSleepGap(gapMs, pollMs, factor = 4) {
  return gapMs > pollMs * factor
}

/** 按“清醒时间”判断停摆：lastProgressMs 只在有进展、或检测到睡眠之后前移。 */
export function isStalled(nowMs, lastProgressMs, stallMs) {
  return nowMs - lastProgressMs >= stallMs
}

function sleep(ms) {
  return new Promise((resolve) => {
    const handle = setTimeout(resolve, ms)
    if (typeof handle.unref === 'function') handle.unref()
  })
}

function countEvents(agent) {
  try {
    return agent.session?.snapshotEvents?.().length ?? 0
  } catch {
    return 0
  }
}

/**
 * 取会话里最后一条 assistant 文本，压平空白并截断，用作回执摘要。
 * 回执里的「完成」只说明会话跑完了；摘要才能让收件人一眼看出有没有产出方案。
 */
export function summarizeAssistantText(events, maxChars = 80) {
  for (let index = events.length - 1; index >= 0; index -= 1) {
    const event = events[index]
    if (event?.type !== 'assistant/message') continue
    const text = (event.data?.message?.content ?? [])
      .filter((block) => block?.type === 'text' && typeof block.text === 'string')
      .map((block) => block.text)
      .join(' ')
      .replace(/\s+/g, ' ')
      .trim()
    if (text === '') continue
    return text.length > maxChars ? `${text.slice(0, maxChars - 1)}…` : text
  }
  return ''
}

export function apply(ctx, config) {
  const log = (message) => {
    const text = `[fresh-session-min] ${message}`
    if (typeof ctx.logger?.warn === 'function') ctx.logger.warn(text)
    else console.warn(text)
  }

  let lastDay = null
  let busy = false
  let skippedNotifiedDay = null

  const timeOfDay = String(config.timeOfDay ?? '06:30')
  const [triggerHour, triggerMinute] = timeOfDay.split(':').map(Number)
  const triggerValid = Number.isInteger(triggerHour) && Number.isInteger(triggerMinute) && triggerHour <= 23 && triggerMinute <= 59
  // 停摆看门狗：按“清醒时间”计，机器睡过的间隔不计入（笔记本合盖一夜不该被误判超时）。
  const tickMs = Math.max(1, Number(config.tickSeconds ?? 30)) * 1000
  const pollMs = Math.max(1, Number(config.pollSeconds ?? 30)) * 1000
  const stallMs = Math.max(0.05, Number(config.stallMinutes ?? 30)) * 60 * 1000

  // skipToday：只压制"加载时今天那个时刻已经过去"的情况（切换/重启当天不补跑一次）。
  // 若加载时还没到触发时刻，今天照常触发——否则每天早上在 06:30 之前重启都会误跳过当天。
  if (config.skipToday === true && shouldSkipToday(new Date(), timeOfDay)) {
    lastDay = localDay(new Date())
  }

  async function sendReceipt(lines) {
    if (typeof config.receiptSessionId !== 'string' || config.receiptSessionId === '') return
    try {
      const owner = await requireAgent(ctx, config.receiptSessionId)
      owner.followup(createUserMessage({
        content: [{ type: 'text', text: lines.join('\n') }],
        source: { kind: 'user' },
      }))
      await ctx.sessions.flush(owner.session)
    } catch (error) {
      log(`回执发送失败：${String(error?.message ?? error)}`)
    }
  }

  /**
   * 等回合结束，但停摆预算只算"清醒时间"：
   * - 轮询间隔远超周期 → 判定为睡眠，重置计时（今天 06:31→21:15 那次就是被合盖挂起的）；
   * - 有新的会话事件 → 视为有进展，重置计时；
   * - 清醒状态下连续无进展超过 stallMs → 取消回合并按失败收尾。
   */
  async function waitForIdle(agent) {
    // 只订阅一次：若每次轮询都新建 whenIdle，短轮询会永远先返回，真正的 idle 永远观察不到。
    const idle = agent.whenIdle().then(() => true)
    let lastCheck = Date.now()
    let lastProgress = Date.now()
    let events = countEvents(agent)
    while (true) {
      const finished = await Promise.race([idle, sleep(pollMs).then(() => false)])
      if (finished) return
      const now = Date.now()
      const gap = now - lastCheck
      lastCheck = now
      if (isSleepGap(gap, pollMs)) {
        lastProgress = now
        log(`等待回合时检测到约 ${Math.round(gap / 60000)} 分钟的睡眠间隔，停摆计时重置`)
        continue
      }
      const next = countEvents(agent)
      if (next !== events) {
        events = next
        lastProgress = now
        continue
      }
      if (isStalled(now, lastProgress, stallMs)) {
        try {
          agent.cancel()
        } catch {
          // 取消失败不影响按停摆收尾
        }
        const budget = stallMs < 60_000 ? `${Math.round(stallMs / 1000)} 秒` : `${Math.round(stallMs / 60000)} 分钟`
        throw new Error(`回合停摆超过 ${budget}且无新事件，已取消`)
      }
    }
  }

  async function runOnce(reason) {
    if (busy) return
    busy = true
    const now = new Date()
    const day = localDay(now)
    let sessionId = null
    let agent = null
    let status = '失败'
    try {
      const created = await ctx.sessionController.create({ workspaceId: config.workspaceId })
      sessionId = created.sessionId
      agent = await requireAgent(ctx, sessionId)
      await ctx.sessionTitle.rename(agent.session, `${config.title} ${day}`)
      agent.followup(createUserMessage({ content: [{ type: 'text', text: config.prompt }], source: { kind: 'user' } }))
      // flush 之后这次投递才算落盘（内置 schedule 的投递也走这一步）
      await ctx.sessions.flush(agent.session)
      await waitForIdle(agent)
      status = '完成'
      try {
        await ctx.workspaceRegistry.archiveSession(sessionId)
      } catch (error) {
        status = `完成但未归档（${String(error?.message ?? error)}）`
      }
      log(`${reason}：已投递到 ${sessionId}，状态 ${status}`)
    } catch (error) {
      status = `失败（${String(error?.message ?? error)}）`
      log(`${reason}：出错，状态 ${status}`)
    } finally {
      busy = false
    }

    const receipt = [
      `[定时任务回执] ${config.title}`,
      `状态：${status}`,
      `新会话：${config.title} ${day}（${sessionId ?? '-'}）`,
    ]
    if (agent !== null) {
      let summary = ''
      try {
        summary = summarizeAssistantText(agent.session?.snapshotEvents?.() ?? [])
      } catch {
        // 读不到事件就不加摘要，回执照常发
      }
      if (summary !== '') receipt.push(`摘要：${summary}`)
    }
    await sendReceipt(receipt)
  }

  const timer = setInterval(() => {
    const now = new Date()
    const day = localDay(now)
    if (lastDay === day) return
    if (!triggerValid) {
      log(`timeOfDay 配置无效："${config.timeOfDay}"`)
      lastDay = day
      return
    }
    if (minutesSinceMidnight(now) < triggerHour * 60 + triggerMinute) return
    if (busy) {
      // 不再静默跳过：只提醒一次，并且不把今天标记为已跑——
      // 上一次跑完后当天还在窗口内就补跑，避免整天无声无息地丢掉。
      if (skippedNotifiedDay !== day) {
        skippedNotifiedDay = day
        log('上一次运行仍在进行，本轮暂缓；跑完后当天会补跑')
        sendReceipt([
          `[定时任务回执] ${config.title}`,
          '状态：暂缓（上一次运行仍在进行）',
          `说明：${day} 的运行会在上一次结束后自动补跑；若整天未补上，会再发一条回执。`,
        ]).catch((error) => log(String(error)))
      }
      return
    }
    lastDay = day
    runOnce('到点触发').catch((error) => log(String(error)))
  }, tickMs)

  ctx.effect(() => () => clearInterval(timer))

  if (config.runOnStart === true) {
    lastDay = localDay(new Date())
    // 延后 10 秒：应用刚启动时宿主可能还没完全就绪，避免在建会话这一步抢跑
    const kickoff = setTimeout(() => {
      runOnce('runOnStart 验证').catch((error) => log(String(error)))
    }, 10_000)
    ctx.effect(() => () => clearTimeout(kickoff))
  }
}
