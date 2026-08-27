## MODIFIED Requirements

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
