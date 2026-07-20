## Why

RepoSignal 的日报负责持续发现、周报负责阶段筛选，但读者仍缺少跨项目比较、按角色选型和判断月度技术信号的入口。新增月度精选可以把现有候选账本、日报和周报转化为更有决策价值的长期静态档案，同时保持当前无数据库、构建期不访问外部 API 的发布方式。

## What Changes

- 新增结构化月报 Markdown、严格发布校验和 `/monthly/` 静态归档页面。
- 新增 Top 5 深度精选、三类读者的场景推荐、观察信号和行动建议模块。
- 新增基于候选账本、日报和周报的月度候选初稿生成器，初稿与发布目录隔离。
- 将顶部导航升级为“月 / 周 / 日”周期切换，并在切换时尽量保留当前时间上下文。
- 将月报项目加入现有本地搜索，增加月/周/日类型标记并优先展示月度精选记录。
- 发布第一份截至 2026-07-20 的七月月度精选，并补充响应式、无 JavaScript 降级和自动化测试。

## Capabilities

### New Capabilities

- `monthly-selection-reports`: 月报内容格式、校验、静态归档、Top 5、角色推荐、观察信号和行动建议。
- `period-navigation`: 全站月/周/日切换、时间锚点映射、缺失周期回退和无 JavaScript 导航。
- `monthly-editorial-drafts`: 从仓库内候选账本、日报和周报生成确定性的月度编辑初稿。
- `unified-report-search`: 月报项目进入搜索索引、类型标签和月报优先排序。

### Modified Capabilities

无。当前仓库没有已发布的基础 OpenSpec capability；日报与周报的现有行为保持兼容。

## Impact

- 数据：新增 `data/github-project-digest/monthly/` 发布目录和被忽略的 `monthly-drafts/` 初稿目录。
- 前端：新增月报解析器、月报组件、月报路由和共享周期切换器；更新基础布局、搜索面板和全局样式。
- 工具：新增 Python 3 标准库初稿生成脚本与 npm 自检命令，不新增运行时依赖。
- 发布：仍由 Astro 静态构建，构建阶段不访问 GitHub API；现有首页继续默认展示最新周报。
