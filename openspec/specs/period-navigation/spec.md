# period-navigation Specification

## Purpose
定义所有报告页面共享的月、周、日周期导航契约，使当前周期具有明确的可访问状态，并在跨周期切换时依据当前报告时间锚点选择最近且不晚于锚点的内容；目标周期缺失时必须安全回退到可读的索引页而非产生失效链接。

## Requirements

### Requirement: Site header provides month week and day navigation
系统 SHALL 在所有报告页面顶部按“月 / 周 / 日”顺序展示周期导航，并用 `aria-current` 与视觉状态标明当前周期。

#### Scenario: Reader views a monthly report
- **WHEN** 当前页面为月报
- **THEN** “月”导航项处于激活状态，“周”和“日”为可访问的普通链接

### Requirement: Period switching preserves time context
系统 MUST 使用当前报告的时间锚点解析目标链接：月报使用月末、周报使用 ISO 周末、日报使用报告日期，并选择不晚于锚点的最近目标报告。

#### Scenario: Switch from July month to week and day
- **WHEN** 读者从 2026-07 月报切换到周报或日报
- **THEN** 系统链接到七月范围内不晚于月末的最近周报和日报

#### Scenario: Switch from daily report to containing periods
- **WHEN** 读者从 2026-07-18 日报切换到周报或月报
- **THEN** 系统链接到包含该日期的 2026-W29 周报和 2026-07 月报（若已发布）

### Requirement: Missing target periods have safe index fallbacks
当目标类型没有不晚于当前时间锚点的报告时，系统 MUST 链接到该类型无日期入口；该入口 MUST 临时重定向到目标类型当前最新一期的带日期详情页，且不得返回失效链接或重复正文。

#### Scenario: No target report exists at or before the anchor
- **WHEN** 读者切换周期且目标类型没有不晚于当前时间锚点的报告，但该类型存在已发布报告
- **THEN** 周期导航进入目标类型无日期入口，并最终以 `302` 到达该类型最新一期的带日期详情页
