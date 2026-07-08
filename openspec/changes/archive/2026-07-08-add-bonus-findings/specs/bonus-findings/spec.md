## ADDED Requirements

### Requirement: 解析额外发现结构化项目

系统 SHALL 从每日发现 Markdown 文件的 `## 额外发现` 章节中，解析 `### 额外发现：<repository> — <score>/100` 格式的结构化项目。

#### Scenario: 解析带评分的额外发现项目

- **WHEN** Markdown 中包含 `### 额外发现：asgeirtj/system_prompts_leaks — 74/100` 格式的标题
- **THEN** 系统将其解析为 `ProjectRecord`，其中 `repository` 为 `asgeirtj/system_prompts_leaks`，`score` 为 `74`
- **AND** 项目应包含仓库 URL、定位、技术栈、风险、推荐理由等字段，与主推荐项目一致的解析规则

#### Scenario: 无额外发现章节时不影响正常解析

- **WHEN** Markdown 中不存在 `## 额外发现` 章节
- **THEN** 系统正常返回已有的主推荐项目列表
- **AND** bonusProjects 为空数组

#### Scenario: 有章节但无结构化项目

- **WHEN** `## 额外发现` 章节下没有 `### 额外发现：` 格式的子标题（仅有文本说明）
- **THEN** 系统不产生解析错误，bonusHtml 包含章节的原始 HTML 渲染内容
- **AND** bonusProjects 为空数组

### Requirement: 展示额外发现区块

系统 SHALL 在每日发现页面中展示额外发现项目区块，与主推荐项目视觉区分。

#### Scenario: 有额外发现项目时展示区块

- **WHEN** `report.bonusProjects` 数组不为空
- **THEN** 页面在"主推荐"列表之后渲染"额外发现"区块
- **AND** 区块包含标题"额外发现"和所有 bonusProjects 的卡片列表
- **AND** 卡片内容包含仓库名称、定位、技术栈、风险、推荐理由

#### Scenario: 无额外发现时隐藏区块

- **WHEN** `report.bonusProjects` 数组为空且 `report.bonusHtml` 为空
- **THEN** 页面不渲染额外发现区块

### Requirement: 搜索索引包含额外发现项目

系统 SHALL 将额外发现项目纳入搜索索引，使用户能通过搜索找到它们。

#### Scenario: 额外发现项目可被搜索

- **WHEN** 用户在搜索框中输入额外发现项目的仓库名或关键词
- **THEN** 搜索结果中显示对应的额外发现项目
- **AND** 搜索结果链接正确指向对应报告的页面锚点
