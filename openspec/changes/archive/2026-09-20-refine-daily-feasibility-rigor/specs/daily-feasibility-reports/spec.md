## MODIFIED Requirements

### Requirement: Preserve research context with hybrid structured rendering
系统 MUST 保留源报告的研究草稿提示，并 SHALL 将每个三级标题方案独立展示：新格式方案结构化呈现方案判断、双评分（技术组合成熟度 / 需求证据强度）与摘要字段（方案判断 / 目标客户 / 需求证据），历史格式方案继续以业务定位 / 目标客户 / 市场机会与单一评分呈现；两种格式的组合表、风险、MVP、验证路径正文均保真呈现。

#### Scenario: Report contains multiple feasibility plans
- **WHEN** 一份日期 Markdown 包含多个 `###` 方案
- **THEN** 页面按源文件顺序显示全部方案，且每个方案都有独立标题、摘要和正文

#### Scenario: Report contains wide component table
- **WHEN** 组合方案表格宽于移动视口
- **THEN** 表格所在内容区域可横向滚动而不挤压整页

#### Scenario: New format plan exposes judgment and dual scores
- **WHEN** 方案含 `**方案判断**` 与 `**双评分**` 行
- **THEN** 页面显示判断徽标与两块评分面板（含各自分项），且 `**双评分**` 行不出现在正文 Markdown 中

#### Scenario: Legacy plan keeps single score rendering
- **WHEN** 方案只含 `**方案评分**` 行
- **THEN** 页面按原有单一评分面板呈现，不要求双评分字段

## ADDED Requirements

### Requirement: Require a connected component data flow for every plan
生成器 MUST 只把通过闭环门槛的组合写成方案：组件数量 ≥3、每个组件都有源报告中的接口依据、组合内能力面不重复、除部署形态外的组件按交接表构成弱连通且无环的数据流，并且存在至少一个上游与一个下游。报告 SHALL 输出每个组件的输入、输出、上下游关系与整体接入方式。

#### Scenario: Combination carries capability tags only
- **WHEN** 组合中某个组件只命中能力标签、源报告里没有任何接口或用途描述
- **THEN** 该组合被判为“仅标签相关”，不进入方案列表，并在今日结论里说明原因

#### Scenario: Combination cannot be connected into a data flow
- **WHEN** 组合的能力面之间没有允许的交接关系，或组件少于三个
- **THEN** 该组合不进入方案列表，今日结论按闭环门槛未过计数

#### Scenario: Qualified plan documents inputs and outputs
- **WHEN** 组合通过闭环门槛
- **THEN** 方案包含组件数据流表格（顺序 / 组件 / 角色 / 输入 / 输出 / 上下游）与接入方式行

### Requirement: Split feasibility scoring into technical maturity and demand evidence
系统 MUST 分别给出两个 0-100 评分且不得合并：`技术组合成熟度`（组件可靠度 40 · 组件供给 20 · 风险敞口 20 · 许可证 10 · 完整度 10）与 `需求证据强度`（证据等级 40 · 用户明确表态 25 · 独立来源 20 · 新鲜度 15）。报告 SHALL 展示两者的档位与分项明细，且分项之和等于总分。

#### Scenario: Technically mature plan without demand evidence
- **WHEN** 组合的组件可靠、供给充足，但需求侧只有项目方自述
- **THEN** 技术组合成熟度高、需求证据强度低，两者不被合并成单一“方案评分”

#### Scenario: Reader inspects the score details
- **WHEN** 读者查看方案的双评分行
- **THEN** 两个评分各自显示 `N/100（档位）` 与分项明细，且分项之和等于总分

### Requirement: Classify demand and market statements by evidence level
需求与市场表述 MUST 标注证据等级之一：已确认事实 / 项目方自述 / 待验证假设 / 无证据。只有 `feedback.jsonl` 中 `source=user` 且点名组件的记录可以标为“已确认事实”；源报告的接口与亮点描述最高标为“项目方自述”；由能力面推导的客户问题标为“待验证假设”；付费意愿、采购预算与市场规模在没有来源时标为“无证据”。生成文本 MUST NOT 出现“刚需、愿意付费、市场已验证”等无来源断言。

#### Scenario: Plan has no external demand source
- **WHEN** 方案的需求侧只能引用组件定位与能力面推导
- **THEN** 需求证据块列出“项目方自述”“待验证假设”“无证据”三档，并注明本轮无访谈证据

#### Scenario: Unfounded claim appears in generated text
- **WHEN** 生成的方案文本中出现被禁用的无来源断言
- **THEN** 渲染时清洗该措辞，且测试校验模板与报告都不含这些断言

### Requirement: Use four feasibility judgments and allow zero plans
系统 MUST 用“值得用户访谈 / 值得技术试验 / 继续观察 / 暂不建议”四档判断替代“优先推进最高分方案”，按确定性阶梯赋值：需求等级为无证据或风险敞口 ≤5/20 → 暂不建议；需求证据强度 ≥60 → 值得用户访谈；技术组合成熟度 ≥80 → 值得技术试验；否则继续观察。被判断为“暂不建议”的候选 MUST NOT 出现在方案列表中，只在今日结论里计数说明；每天允许 0 个合格方案。

#### Scenario: No plan qualifies on a given day
- **WHEN** 所有候选都被冷却跳过、判为暂不建议或未过闭环门槛
- **THEN** 报告写明“本轮无合格方案”并列出候选数量与原因，不补写方案

#### Scenario: Reader reads the judgment per plan
- **WHEN** 方案通过门槛并进入列表
- **THEN** 方案块首个字段为 `**方案判断**`，取值属于四档之一，并给出判断依据

### Requirement: Make every plan's MVP experiment falsifiable
每个方案 MUST 给出可证伪的 MVP 实验：测试场景、测试数据、周期、成功指标、失败指标与停止条件。成功指标与失败指标 SHALL 带可核对的阈值或判定方式；停止条件 SHALL 明确“未达成功指标即停止”与“命中失败指标立即停止”。

#### Scenario: Reader evaluates whether the experiment can fail
- **WHEN** 读者查看方案的 MVP 实验块
- **THEN** 六项内容齐备，且能看到具体阈值、失败判定与停止条件

### Requirement: Cool down plan families for 7 to 14 days
同一 `plan_family` MUST 跨日冷却 7–14 天：最近一次出现不足 7 天时无条件跳过；7–13 天之间只有新增关键组件、证据等级提升或客户问题/预期结果变化才允许提前重现；达到 14 天后自然重新合格。报告 SHALL 在今日结论里说明被跳过与提前重现的方向及理由。

#### Scenario: Same family appears again within the cooldown
- **WHEN** 某 `plan_family` 在最近 7 天内已出现过
- **THEN** 本轮跳过该方向，并在今日结论的“冷却与重现”里说明

#### Scenario: Family returns early with new material
- **WHEN** 某 `plan_family` 在 7–13 天前出现过，且本轮组合新增了关键组件、证据等级提升或客户问题变化
- **THEN** 允许出现，并在今日结论里写明提前重现的具体理由

### Requirement: Retire low-value sections and fix the reading order
报告 MUST NOT 自动生成“单点项目机会”与笼统“行动建议”章节。报告结构 SHALL 为：报告级 `## 今日结论`（方案数与轨道分布、判断分布、冷却/暂不建议/门槛未过计数、原则），随后每个方案按 `方案判断 → 客户问题 → 组件数据流 → 双评分 → MVP 实验 → 最大不确定性 → 下一步动作` 的顺序组织。

#### Scenario: Reader opens a new report
- **WHEN** 生成任意一天的新格式报告
- **THEN** 报告不含单点项目机会与行动建议章节，且方案块按约定顺序排列

#### Scenario: Reader opens a historical report
- **WHEN** 站点加载 2026-09-20 之前生成的报告
- **THEN** 旧章节（单一评分、单点机会、行动建议）继续按原格式渲染，不显示双评分面板
