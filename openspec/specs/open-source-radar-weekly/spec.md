# open-source-radar-weekly Specification

## Purpose
定义公开开源雷达周刊从冻结 Markdown 到静态站点的完整公开契约，涵盖内容与内部传播草稿的隔离、稳定静态路由、共享导航、周期归档、连续文章呈现、首期内容约束、发布校验以及搜索去重边界。

## Requirements

### Requirement: 公开雷达周刊必须与内部草稿分离

系统 SHALL 只从 `data/github-project-digest/radar/` 发现公开雷达周刊，并 MUST NOT 从 `distribution-drafts/` 自动发布内容。每个公开文件 MUST 使用 `YYYY-Www.md` ISO 周文件名，包含一个一级标题和一张封面图片；构建结果 SHALL 按 slug 从新到旧排序。

#### Scenario: 发现有效冻结文章
- **WHEN** `radar/` 中存在标题、封面和正文完整的 `2026-W31.md`
- **THEN** 系统将其解析为 slug 为 `2026-W31` 的雷达周刊
- **THEN** 系统从一级标题读取页面标题，从首张图片读取封面，并从首个正文段落生成页面描述

#### Scenario: 排除内部传播草稿
- **WHEN** `distribution-drafts/` 中存在公众号草稿但 `radar/` 中没有对应冻结文件
- **THEN** 系统不为该草稿生成雷达周刊页面或归档条目

#### Scenario: 拒绝无效公开文件
- **WHEN** 公开文件名不符合 ISO 周格式，或文件缺少一级标题或封面图片
- **THEN** 构建期解析 MUST 抛出包含文件名与缺失字段的明确错误

### Requirement: 每期雷达周刊必须具有稳定静态路由

系统 SHALL 为每个有效冻结文件生成 `/radar/YYYY-Www/` 静态页面，并 SHALL 提供 `/radar/` 归档入口。页面 canonical、标题和 description MUST 对应该期雷达文章。

#### Scenario: 构建单期页面
- **WHEN** 公开目录包含 `2026-W31.md`
- **THEN** 生产构建生成 `/radar/2026-W31/index.html`
- **THEN** 页面标题包含文章标题，canonical 指向 `/radar/2026-W31/`

#### Scenario: 打开雷达归档入口
- **WHEN** 读者访问 `/radar/`
- **THEN** 页面提供指向最新雷达周刊的静态链接
- **THEN** 在没有任何雷达文章时页面显示可读的空状态而不构建失败

### Requirement: 共享顶部导航必须新增完整雷达周刊 Tab

系统 SHALL 在月报、周报、日报、雷达周刊和各自归档入口的共享顶部导航中显示“开源雷达周刊”Tab。该 Tab SHALL 链接到最新雷达文章；没有文章时 SHALL 回退到 `/radar/`。当前雷达页面 MUST 将该 Tab 标记为当前项。

#### Scenario: 从现有报告进入最新雷达周刊
- **WHEN** 雷达文章列表包含 `2026-W31` 且读者在月报、周报或日报页面查看顶部导航
- **THEN** “开源雷达周刊”Tab 链接到 `/radar/2026-W31/`

#### Scenario: 标记当前雷达 Tab
- **WHEN** 读者位于任一 `/radar/` 页面
- **THEN** “开源雷达周刊”Tab 使用 `aria-current` 表达当前内容类型

#### Scenario: 移动端显示完整 Tab
- **WHEN** 视口宽度不大于 768px
- **THEN** 页头将品牌与搜索放在第一行、周期导航放在第二行
- **THEN** “开源雷达周刊”保持完整可见并具有至少 2.75rem 的触控高度

### Requirement: 雷达周刊必须提供按周日期归档

每个雷达单期页面 SHALL 在桌面端左侧显示按 ISO 周从新到旧排序的归档时间线，并 SHALL 复用现有圆点、当前项和“最新”标记语义。归档 SHALL 支持现有折叠行为、移动端期数选择器和无脚本链接列表。

#### Scenario: 显示桌面日期列表
- **WHEN** 公开目录包含多期雷达周刊且读者打开其中一期
- **THEN** 左侧时间线从新到旧显示所有 `YYYY-Www` 标签
- **THEN** 当前期使用 `aria-current="page"`，第一项显示“最新”

#### Scenario: 使用移动端选择器
- **WHEN** 视口宽度不大于 768px
- **THEN** 桌面时间线切换为包含全部期数的选择器
- **THEN** 选择其他期数后浏览器导航到对应 `/radar/YYYY-Www/` 页面

#### Scenario: 禁用 JavaScript 浏览归档
- **WHEN** JavaScript 被禁用
- **THEN** 页面仍显示可点击的雷达周刊归档链接
- **THEN** 正文和项目链接保持完整可读

### Requirement: 雷达页面必须以连续文章形式呈现

系统 SHALL 使用专用文章视图呈现封面、文章标题、ISO 周标识和按原顺序渲染的 Markdown 正文。系统 MUST NOT 将雷达文章重新拆成日报或研究周报的评分项目卡片。

#### Scenario: 渲染完整文章
- **WHEN** 读者打开有效雷达周刊
- **THEN** 页面在正文顶部显示文章封面、标题和该期 ISO 周
- **THEN** 分组标题、段落、项目 GitHub 链接、风险与试用建议按照冻结 Markdown 顺序呈现

#### Scenario: 保持现有视觉身份
- **WHEN** 雷达文章被渲染
- **THEN** 页面使用既有纸张色、苔绿色、标记黄色、细分隔线和直角边界
- **THEN** 封面保持约 2.35:1 宽高比，正文使用受限阅读宽度和清晰章节间距

### Requirement: 首期公开内容必须清除草稿占位符

首期 `2026-W31` 雷达周刊 SHALL 使用已批准的“开源雷达周刊”文章和固定“仓库雷达｜每周开源项目精选”封面。公开 Markdown MUST NOT 包含 `SITE_BASE_URL` 占位符或传播 UTM，阅读全文入口 SHALL 使用站内周报相对路径。

#### Scenario: 发布首期文章
- **WHEN** `2026-W31.md` 被加入公开雷达目录
- **THEN** 封面引用 `/covers/repository-radar-weekly-subtitle.png`
- **THEN** 正文包含 10 个本周推荐项目及对应 GitHub 链接
- **THEN** 阅读全文入口指向 `/weekly/2026-W31/`

#### Scenario: 阻止占位内容进入公开构建
- **WHEN** 公开雷达 Markdown 包含 `SITE_BASE_URL` 或 `utm_` 参数
- **THEN** 内容验证 MUST 失败并指出对应文件

### Requirement: 雷达周刊不得重复项目搜索结果

首版系统 MUST NOT 将雷达文章中的项目添加到现有月报、周报和日报项目搜索索引。雷达文章 SHALL 通过顶部 Tab、归档时间线和静态 URL 被发现。

#### Scenario: 搜索同周推荐项目
- **WHEN** 同一仓库同时出现在 `2026-W31` 研究周报和雷达周刊正文中
- **THEN** 项目搜索结果只保留现有研究报告产生的条目
- **THEN** 雷达文章不会创建第二条重复项目搜索结果
