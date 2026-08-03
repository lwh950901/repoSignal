## MODIFIED Requirements

### Requirement: Missing target periods have safe index fallbacks
当目标类型没有不晚于当前时间锚点的报告时，系统 MUST 链接到该类型无日期入口；该入口 MUST 临时重定向到目标类型当前最新一期的带日期详情页，且不得返回失效链接或重复正文。

#### Scenario: No target report exists at or before the anchor
- **WHEN** 读者切换周期且目标类型没有不晚于当前时间锚点的报告，但该类型存在已发布报告
- **THEN** 周期导航进入目标类型无日期入口，并最终以 `302` 到达该类型最新一期的带日期详情页
