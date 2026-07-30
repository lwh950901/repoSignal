## Why

RepoSignal 的档案式视觉方向已经清晰，但少数界面细节削弱了信息表达：无评分周选被渲染成类似分数的 `W/EEKLY`，移动端搜索入口缺少可识别语义，月报长内容缺少快速定位方式，间距令牌也无法表达真实层级。现在应在不改变既有品牌语言的前提下完成一轮聚焦精修，让日报、周报和月报更容易扫描与导航。

## What Changes

- 将无数字评分的周选状态改为明确、低干扰的文本标识，不再伪装成分数。
- 为移动端搜索入口保留可识别的搜索图标和无障碍名称，同时维持紧凑页头。
- 为月报增加页内章节导航，并允许次要研究证据按项目折叠展开，缩短默认阅读路径。
- 重建有实际层级差异的间距令牌，并将受影响布局迁移到新的节奏尺度。
- 保留现有纸张色、苔绿色、标记黄色、时间轨、细分隔线和克制动效，不引入卡片化重设计。

## Capabilities

### New Capabilities

- `report-interface-refinement`: 规定周选状态、移动端搜索入口、月报长内容导航与披露方式，以及跨页面间距层级的可观察界面行为。

### Modified Capabilities

<!-- No existing main capability requirements are changed. -->

## Impact

- 主要影响 `ProjectEntry.astro`、`BaseLayout.astro`、`MonthlyReportView.astro` 和 `global.css`。
- 需要扩展布局契约测试，覆盖新的语义标识、章节导航、折叠内容和移动端搜索表现。
- 不改变 Markdown 数据格式、报告解析逻辑、路由、搜索索引或外部依赖。
