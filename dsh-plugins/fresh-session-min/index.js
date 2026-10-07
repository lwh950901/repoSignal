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
export const inject = ['sessionController', 'workspaceRegistry', 'sessionTitle']

const TICK_MS = 30_000
const TIME_ZONE = 'Asia/Shanghai'

function localDay(now) {
  return new Intl.DateTimeFormat('en-CA', { timeZone: TIME_ZONE }).format(now)
}

function minutesSinceMidnight(now) {
  return now.getHours() * 60 + now.getMinutes()
}

export function apply(ctx, config) {
  const log = (message) => {
    const text = `[fresh-session-min] ${message}`
    if (typeof ctx.logger?.warn === 'function') ctx.logger.warn(text)
    else console.warn(text)
  }

  let lastDay = null
  let busy = false

  async function runOnce(reason) {
    if (busy) return
    busy = true
    const now = new Date()
    const day = localDay(now)
    let sessionId = null
    let status = '失败'
    try {
      const created = await ctx.sessionController.create({ workspaceId: config.workspaceId })
      sessionId = created.sessionId
      const agent = await ctx.sessionController.resolveAgent(sessionId)
      await ctx.sessionTitle.rename(agent.session, `${config.title} ${day}`)
      agent.followup(createUserMessage({ content: config.prompt, source: { kind: 'user' } }))
      await agent.whenIdle()
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

    if (typeof config.receiptSessionId === 'string' && config.receiptSessionId !== '') {
      try {
        const owner = await ctx.sessionController.resolveAgent(config.receiptSessionId)
        owner.followup(createUserMessage({
          content: [
            `[定时任务回执] ${config.title}`,
            `状态：${status}`,
            `新会话：${config.title} ${day}（${sessionId ?? '-'}）`,
          ].join('\n'),
          source: { kind: 'user' },
        }))
      } catch (error) {
        log(`回执发送失败：${String(error?.message ?? error)}`)
      }
    }
  }

  const timer = setInterval(() => {
    const now = new Date()
    const day = localDay(now)
    if (lastDay === day) return
    const [hour, minute] = String(config.timeOfDay ?? '06:30').split(':').map(Number)
    if (!Number.isInteger(hour) || !Number.isInteger(minute)) {
      log(`timeOfDay 配置无效："${config.timeOfDay}"`)
      lastDay = day
      return
    }
    if (minutesSinceMidnight(now) < hour * 60 + minute) return
    lastDay = day
    runOnce('到点触发').catch((error) => log(String(error)))
  }, TICK_MS)

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
