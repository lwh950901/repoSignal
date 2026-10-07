import test from 'node:test'
import assert from 'node:assert/strict'
import { shouldSkipToday } from '../index.js'

const at = (hour, minute) => new Date(2026, 9, 7, hour, minute, 0)

test('触发时刻已过 → 今天视为已跑（切换/重启当天不补跑）', () => {
  assert.equal(shouldSkipToday(at(13, 6), '06:30'), true)
  assert.equal(shouldSkipToday(at(6, 30), '06:30'), true) // 正好到点也算已过
})

test('触发时刻未到 → 今天照常触发（早上重启不会误跳过当天）', () => {
  assert.equal(shouldSkipToday(at(5, 0), '06:30'), false)
  assert.equal(shouldSkipToday(at(6, 29), '06:30'), false)
})

test('时刻非法 → 不跳过', () => {
  assert.equal(shouldSkipToday(at(13, 0), '25:00'), false)
  assert.equal(shouldSkipToday(at(13, 0), 'abc'), false)
  assert.equal(shouldSkipToday(at(13, 0), undefined), false)
})
