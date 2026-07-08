## Context

当前每日发现页面的数据流：Markdown → `digests.ts` 解析 → `DigestReport` → `ReportView.astro` 渲染。`parseProjects()` 只解析 `## 主推荐` 下的 `### N. 类型：repo — score/100` 格式项目。`## 额外发现` 章节完全被忽略。

需要新增一个解析通道，提取 `### 额外发现：repo — score/100` 格式的结构化项目，并在页面底部展示。

## Goals / Non-Goals

**Goals:**
- 解析 `## 额外发现` 下的结构化项目，存入 `DigestReport.bonusProjects`
- 在页面底部渲染额外发现区块，视觉上与主推荐区分
- 向后兼容：无额外发现的报告不受影响
- 额外发现项目纳入搜索索引

**Non-Goals:**
- 不修改主推荐项目的解析逻辑
- 不修改 `ProjectEntry` 组件（复用现有卡片布局）
- 不新增外部依赖

## Decisions

### Decision 1: 复用 `ProjectRecord` 类型，新增 `ProjectKind` 值

额外发现项目与主推荐项目共享同样的数据结构（仓库、定位、技术栈、风险、推荐理由），因此直接复用 `ProjectRecord` 类型，在 `ProjectKind` 中新增 `"额外发现"` 值。

替代方案：创建独立的 `BonusProject` 类型。否决原因：字段完全一致，引入新类型只会增加转换成本。

### Decision 2: `bonusProjects` 作为独立字段存储在 `DigestReport` 中

在主推荐 `projects` 数组中追加额外发现的问题是改变现有索引编号逻辑。独立字段 `bonusProjects` 和 `bonusHtml` 更清晰，渲染时按需展示。

### Decision 3: 解析使用独立函数 `parseBonusProjects()`

与 `parseProjects()` 分离而非修改它，因为：
- 匹配的正则不同（`### 额外发现：` vs `### N. 爆发型/实用型/潜力型：`）
- 额外发现项目没有"类型标签"，需要硬编码 kind 为 `"额外发现"`
- 独立函数更易测试

## Risks / Trade-offs

- [低] 额外发现项目没有类型标签（爆发型/实用型/潜力型），卡片上的 stamp 标签固定显示"额外发现"
- [低] 部分报告 `## 额外发现` 下只有纯文本说明而非结构化项目（如 2026-07-07），此时 `bonusProjects` 为空但 `bonusHtml` 包含渲染后的 HTML
- [低] 目前只有 2026-07-08 一份报告有结构化额外发现项目，改动影响范围小
