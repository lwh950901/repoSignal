## ADDED Requirements

### Requirement: Build only dated feasibility reports
系统 SHALL 在构建时只把 `data/github-project-digest/feasibility/YYYY-MM-DD.md` 识别为可行性报告，并按日期倒序提供归档。

#### Scenario: Directory contains reports and supporting files
- **WHEN** feasibility 目录同时包含日期 Markdown、`KUN-TASK.md` 和日志文件
- **THEN** 系统只加载日期 Markdown，且最新日期排在归档首位

### Requirement: Provide feasibility index and dated routes
系统 SHALL 提供 `/feasibility/` 索引页和 `/feasibility/<YYYY-MM-DD>/` 详情页，并让索引页在有数据时链接最新一期、无数据时显示明确空状态。

#### Scenario: Reader opens feasibility index with reports available
- **WHEN** 仓库至少存在一份日期可行性报告
- **THEN** 页面提供指向最新日期详情页的链接

#### Scenario: Reader opens a dated feasibility report
- **WHEN** 读者访问一个已生成的日期路由
- **THEN** 页面显示该日方案并提供同类日期归档导航和 canonical 地址

### Requirement: Preserve research context with hybrid structured rendering
系统 MUST 保留源报告的研究草稿提示，并 SHALL 将每个三级标题方案独立展示，结构化呈现业务定位、目标客户和市场机会，同时保真呈现组合表、风险、MVP、验证路径、单点机会和行动建议。

#### Scenario: Report contains multiple feasibility plans
- **WHEN** 一份日期 Markdown 包含多个 `###` 方案
- **THEN** 页面按源文件顺序显示全部方案，且每个方案都有独立标题、摘要和正文

#### Scenario: Report contains wide component table
- **WHEN** 组合方案表格宽于移动视口
- **THEN** 表格所在内容区域可横向滚动而不挤压整页

### Requirement: Keep feasibility reports out of project search
系统 MUST 保持现有全局项目搜索范围，不将可行性方案里的重复仓库创建为搜索结果。

#### Scenario: Same repository appears in several feasibility reports
- **WHEN** 搜索索引在构建时生成
- **THEN** 不会因可行性报告产生额外重复搜索项
