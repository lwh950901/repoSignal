## Why

每日发现报告中"额外发现"（Bonus Findings）章节虽然已在 Markdown 源文件中结构化存在，但解析器和前端页面完全没有展示这部分内容。读者无法看到有价值的额外项目推荐，内容被浪费。

## What Changes

- 在 `DigestReport` 类型中新增 `bonusProjects` 和 `bonusHtml` 字段，存储额外发现项目数据
- 新增 `parseBonusProjects()` 函数，从 Markdown 中解析 `### 额外发现：` 格式的结构化项目
- 在 `ReportView.astro` 中新增"额外发现"展示区块，与主推荐视觉区分
- 向后兼容：没有 `## 额外发现` 章节或其中没有结构化项目的报告不受影响

## Capabilities

### New Capabilities
- `bonus-findings`: 解析并展示每日 GitHub 项目发现报告中"额外发现"章节的结构化项目列表，包含项目仓库、定位、技术栈、风险、推荐理由等字段

### Modified Capabilities

<!-- 无现有 spec 行为变更 -->

## Impact

- `src/lib/digests.ts` — 新增 `bonusProjects` 字段到 `DigestReport`；新增 `parseBonusProjects()` 解析函数；修改 `parseDailyReport()` 以集成额外发现解析
- `src/components/ReportView.astro` — 新增额外发现渲染区块
- `src/styles/global.css` — 可能增加少量额外发现专属样式
