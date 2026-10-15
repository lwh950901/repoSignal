import test from 'node:test'
import assert from 'node:assert/strict'
import { summarizeAssistantText } from '../index.js'

const assistant = (text) => ({ type: 'assistant/message', data: { message: { content: [{ type: 'text', text }] } } })

test('取最后一条 assistant 文本，压平空白', () => {
  const events = [assistant('第一段'), { type: 'turn/end' }, assistant('本轮无合格方案：\n两个方向均在冷却期。')]
  assert.equal(summarizeAssistantText(events), '本轮无合格方案： 两个方向均在冷却期。')
})

test('跳过没有文本的 assistant 消息', () => {
  const events = [assistant('有内容'), { type: 'assistant/message', data: { message: { content: [{ type: 'reasoning', text: 'x' }] } } }]
  assert.equal(summarizeAssistantText(events), '有内容')
})

test('没有可用文本时返回空串', () => {
  assert.equal(summarizeAssistantText([]), '')
  assert.equal(summarizeAssistantText([{ type: 'turn/end' }]), '')
})

test('超长截断到上限', () => {
  const long = '字'.repeat(200)
  const summary = summarizeAssistantText([assistant(long)], 80)
  assert.equal(summary.length, 80)
  assert.ok(summary.endsWith('…'))
})
