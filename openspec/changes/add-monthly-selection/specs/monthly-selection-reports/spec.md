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

### Requirement: Monthly page remains usable across devices and script states
月报 SHALL 在 360px 及以上宽度无横向滚动，并在 JavaScript 禁用时保留正文、仓库链接、周期链接和月份链接。

#### Scenario: Reader disables JavaScript on mobile
- **WHEN** 读者在 360px 视口禁用 JavaScript 并打开月报
- **THEN** 正文可读，月/周/日和历史月份仍可通过普通链接访问
