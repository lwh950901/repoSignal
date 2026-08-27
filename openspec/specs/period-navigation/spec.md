# period-navigation Specification

## Purpose
定义所有报告页面共享的月、周、日周期导航契约，使当前周期具有明确的可访问状态，并在跨周期切换时依据当前报告时间锚点选择最近且不晚于锚点的内容；目标周期缺失时必须安全回退到可读的索引页而非产生失效链接。
## Requirements
### Requirement: Site header provides month week and day navigation
系统 SHALL 在所有报告页面顶部按“月度洞察 / 每周精选 / 每日发现 / 每日可行性方案 / 开源雷达周刊”顺序展示周期导航，并用 `aria-current` 与视觉状态标明当前周期。

#### Scenario: Reader views a monthly report
- **WHEN** 当前页面为月报
- **THEN** “月度洞察”导航项处于激活状态，其余周期为可访问的普通链接

#### Scenario: Reader views a feasibility report
- **WHEN** 当前页面为每日可行性方案
- **THEN** “每日可行性方案”导航项处于激活状态，其余周期为可访问的普通链接

#### Scenario: Reader uses navigation on a narrow screen
- **WHEN** 五个导航项宽于可用视口
- **THEN** 导航保持单行并可横向滚动，每个标签仍可点击和获得键盘焦点

### Requirement: Period switching preserves time context
系统 MUST 使用当前报告的时间锚点解析目标链接：月报使用月末、周报使用 ISO 周末、日报使用报告日期，并选择不晚于锚点的最近目标报告。

#### Scenario: Switch from July month to week and day
- **WHEN** 读者从 2026-07 月报切换到周报或日报
- **THEN** 系统链接到七月范围内不晚于月末的最近周报和日报

#### Scenario: Switch from daily report to containing periods
- **WHEN** 读者从 2026-07-18 日报切换到周报或月报
- **THEN** 系统链接到包含该日期的 2026-W29 周报和 2026-07 月报（若已发布）

### Requirement: Missing target periods have safe index fallbacks
当目标类型没有不晚于锚点的报告时，系统 MUST 链接到该类型索引页，并由索引页显示最新一期或明确空状态。

#### Scenario: No weekly reports exist
- **WHEN** 读者点击“周”且仓库没有周报
- **THEN** 系统进入 `/weekly/` 并显示周报空状态，不返回 404
