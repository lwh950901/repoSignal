## ADDED Requirements

### Requirement: Published monthly Markdown is strictly validated
系统 MUST 从 `data/github-project-digest/monthly/YYYY-MM.md` 加载月报，并要求有效月份、主题、数据截止日期以及恰好五个包含仓库、主要角色、入选依据、最佳使用场景和主要风险的 Top 5 项目。

#### Scenario: Valid monthly report is loaded
- **WHEN** 月报包含全部必填元数据、恰好五个 Top 5、分类推荐、观察信号和行动建议
- **THEN** 系统生成结构化 `MonthlyReport` 并按月份倒序返回

#### Scenario: Invalid published report is rejected
- **WHEN** 月报缺少必填字段、包含非法 GitHub URL、Top 5 数量不是五个或仓库名大小写归一化后重复
- **THEN** 系统 MUST 以包含文件名和问题位置的校验错误阻止发布构建

### Requirement: Monthly archive presents the approved editorial structure
系统 SHALL 在 `/monthly/` 和 `/monthly/YYYY-MM/` 静态页面展示月度封面、速览指标、三条结论、Top 5、三类角色推荐、观察信号、行动建议和方法说明。

#### Scenario: Reader opens a published month
- **WHEN** 读者访问已发布月份
- **THEN** 页面按照结论、Top 5、场景推荐、观察信号、行动建议的顺序渲染内容，并提供月份归档和相邻月链接

#### Scenario: No monthly reports exist
- **WHEN** 发布目录中没有月报
- **THEN** `/monthly/` MUST 显示解释月报用途的空状态而不是伪造项目

### Requirement: Monthly signals expose evidence boundaries
系统 MUST 展示观察信号的方向、支撑项目和证据强度；支撑项目少于三个时 MUST 将信号降级为“编辑观察”和“观察”强度。

#### Scenario: Signal has insufficient support
- **WHEN** 一个信号只列出两个独立支撑项目
- **THEN** 页面将其标记为“编辑观察”且不展示高或中置信

### Requirement: Monthly editorial scale follows the approved content policy
系统 MUST 发布恰好五个 Top 5 项目，并 SHALL 以 8–12 个分类推荐、2–4 条观察信号以及每类读者 2–3 条行动建议作为编辑目标；实际候选不足时 MUST 只展示真实内容而不生成占位项目。

#### Scenario: Fewer than eight credible recommendations are available
- **WHEN** 编辑审核后只有六个分类推荐满足入选条件
- **THEN** 页面展示六个真实推荐且不创建两个占位项目

### Requirement: Published monthly judgments are dated and frozen
系统 MUST 在月报页面显示数据截止日期，并 SHALL 把发布内容视为当时判断；后续项目变化通过新月报或明确的重新发布流程说明，不在构建时实时改写历史月报。

#### Scenario: Repository metrics change after publication
- **WHEN** 已发布月报中的仓库在之后发生 Star、维护状态或接口变化
- **THEN** 静态重建仍使用仓库中的月报 Markdown，不请求外部 API 改写历史判断

### Requirement: Monthly page remains usable across devices and script states
月报 SHALL 在 360px 及以上宽度无横向滚动，并在 JavaScript 禁用时保留正文、仓库链接、周期链接和月份链接。

#### Scenario: Reader disables JavaScript on mobile
- **WHEN** 读者在 360px 视口禁用 JavaScript 并打开月报
- **THEN** 正文可读，月/周/日和历史月份仍可通过普通链接访问

### Requirement: Monthly pages expose stable metadata
每个历史月报页面 SHALL 生成独立标题、描述、canonical 路径和 Open Graph 标题与描述，并保持正确的标题层级和月份时间语义。

#### Scenario: Search engine reads a historical month
- **WHEN** `/monthly/2026-07/` 被构建
- **THEN** 页面包含与该月份主题对应的 title、description、canonical 与 Open Graph 元信息
