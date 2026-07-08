## 1. 类型与数据模型

- [x] 1.1 在 `ProjectKind` 中新增 `"额外发现"` 值
- [x] 1.2 在 `DigestReport` 中新增 `bonusProjects: ProjectRecord[]` 和 `bonusHtml: string` 字段

## 2. 解析逻辑

- [x] 2.1 实现 `parseBonusProjects()` 函数：从 Markdown 中提取 `## 额外发现` 章节，匹配 `### 额外发现：<repo> — <score>/100` 格式
- [x] 2.2 处理边界情况：无 `## 额外发现` 章节时返回空数组；有章节但无结构化项目时返回空数组并填充 `bonusHtml`
- [x] 2.3 修改 `parseDailyReport()`：调用 `parseBonusProjects()` 并填充 `bonusProjects` 和 `bonusHtml`

## 3. 搜索索引

- [x] 3.1 修改 `createSearchIndex()`：将 `bonusProjects` 也纳入搜索索引

## 4. 页面渲染

- [x] 4.1 在 `ReportView.astro` 中新增"额外发现"渲染区块，位于主推荐项目列表之后
- [x] 4.2 区块包含标题"额外发现"、bonusProjects 卡片列表（复用 `ProjectEntry` 组件）
- [x] 4.3 无额外发现时隐藏区块

## 5. 样式

- [x] 5.1 在 `global.css` 中为额外发现区块添加视觉区分样式

## 6. 验证

- [x] 6.1 运行测试确认现有测试不受影响
- [x] 6.2 运行 `astro build` 确认构建通过
