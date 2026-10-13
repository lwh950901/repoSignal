import test from 'node:test'
import assert from 'node:assert/strict'
import { isSleepGap, isStalled } from '../index.js'

test('睡眠间隔判定：轮询 30 秒，间隔超过 4 倍才算机器睡过', () => {
  assert.equal(isSleepGap(30_000, 30_000), false)
  assert.equal(isSleepGap(119_000, 30_000), false)
  assert.equal(isSleepGap(121_000, 30_000), true)
  // 今天真实发生的那次：06:31 → 21:15，约 884 分钟
  assert.equal(isSleepGap(884 * 60_000, 30_000), true)
})

test('停摆判定：按清醒时间累计，达到门槛才算停摆', () => {
  const now = 1_000_000_000
  assert.equal(isStalled(now, now - 29 * 60_000, 30 * 60_000), false)
  assert.equal(isStalled(now, now - 30 * 60_000, 30 * 60_000), true)
})
