## Context

站点使用 Astro 静态路由和 `import.meta.glob` 在构建时加载报告。现有月、周、日、雷达报告都通过共享顶部周期导航进入，并使用归档栏选择历史日期。feasibility 目录包含日期 Markdown 与说明、日志等支持文件；日期报告由自动任务生成，一份报告可包含多个方案。

## Goals / Non-Goals

**Goals:**

- 把日期可行性 Markdown 变成可归档、可直达的静态页面。
- 在不改变原始数据格式的前提下提升摘要与组合表的可读性。
- 让第五个顶部标签和日期归档在桌面、移动端及键盘操作下保持可用。

**Non-Goals:**

- 不修改报告生成脚本和 feasibility 原始内容。
- 不把方案项目加入全局搜索，也不新增筛选、评分或交互编辑能力。
- 不对受版本控制的本地 Markdown 执行额外内容净化或远程抓取。

## Decisions

### Build-time loader with a strict filename glob

新增独立 loader，使用 `feasibility/20??-??-??.md` 的构建时 glob，并在加载后再次校验 ISO 日期文件名。相比读取整个目录后排除特殊文件，这能默认拒绝未来新增的说明文件。

### Hybrid parsing at stable heading and label boundaries

报告模型保留完整 Markdown/HTML，同时按 `## 可行性方案` 下的 `###` 边界拆分方案。每个方案只提取稳定的粗体标签摘要；正文其余部分继续交给 `marked`，避免为自动生成内容建立脆弱的完整 AST 映射。尾部 `## 单点项目机会` 和 `## 行动建议` 分别保留为 HTML。

### Reuse archive primitives and extend period links minimally

详情页复用 `DateRail`、`ArchiveTimeline` 和 `archive-shell.js`。`ReportPeriod` 增加 `feasibility`，`resolvePeriodLinks` 增加对应 slug 列表，并统一更新现有调用点。该方案与当前架构一致，避免引入第二套导航状态。

### Purpose-specific feasibility view within the existing visual system

新增视图使用现有字体、颜色和空间 token。特色元素是每个方案顶部的三栏“定位 / 客户 / 机会”决策摘要；其余内容保持克制的研究报告排版。宽表在正文容器内滚动，顶部五标签在移动端单行横向滚动。

## Risks / Trade-offs

- 自动生成器改变标题或粗体标签格式时摘要字段可能为空 → 正文 HTML 仍完整保留，页面不丢内容，并以解析测试锁定当前契约。
- 新增第五标签会超过窄屏宽度 → 导航容器显式提供横向滚动和可见焦点，不通过缩小触控目标解决。
- `marked` 输出来自仓库本地生成内容但不做净化 → 延续现有报告信任模型，不接受运行时用户输入。

## Migration Plan

静态增量发布即可，无数据迁移。回滚时移除新增路由和周期枚举即可；原始 feasibility 文件不受影响。

## Open Questions

无。展示方式、搜索范围、标签顺序和空状态均已在批准计划中确定。
