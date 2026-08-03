## ADDED Requirements

### Requirement: Monthly Top 5 uses an independent evidence-backed ranking
系统 MUST 发布恰好五个单仓库 Top 5，并为每个项目展示本月变化、事实指标、核实日期、验证等级、六项评分、主要反对理由、最终判断和来源。Top 5 排名 MUST NOT 依赖项目是否进入业务组合。

#### Scenario: Reader inspects a ranked project
- **WHEN** 读者打开一份已发布月报
- **THEN** 每个 Top 5 项目显示 100 分评分的六个分项及其事实依据，并能访问外部来源

#### Scenario: Ranked project lacks evidence
- **WHEN** Top 5 项目缺少本月变化、核实日期、验证等级、任一评分、反对理由或来源
- **THEN** 发布校验 MUST 报告文件和项目位置并阻止构建

### Requirement: Monthly business opportunities remain separate from Top 5
系统 SHALL 在 Top 5 之后展示 0–3 个经过研究的商业产品、企业内部工具或新开源项目机会。业务方案成员 MAY 不属于 Top 5，Top 5 项目 MAY 不属于任何业务方案。

#### Scenario: No opportunity passes publication gates
- **WHEN** 当月没有业务方案达到需求与技术验证门槛
- **THEN** 页面明确说明未发现通过完整验证的新机会，并且不生成占位方案

#### Scenario: Opportunity uses a non-ranked repository
- **WHEN** 一个业务方案使用未进入 Top 5 的本月核心仓库或外部辅助仓库
- **THEN** 页面正常展示其角色和来源，不改变 Top 5 排名

### Requirement: Business opportunities expose decision-ready analysis
每个公开业务方案 MUST 展示摘要、真实问题、市场与替代方案、产品定义、仓库组合、组合链路、自行开发部分、MVP、业务判断和证据边界。

#### Scenario: Reader evaluates an opportunity
- **WHEN** 读者打开一个业务方案
- **THEN** 读者可以识别目标用户、需求状态、竞品、各仓库职责与接入方式、验证等级、未解决缺口、成功指标、停止条件和最终判断

### Requirement: Published monthly content distinguishes facts from inference
系统 MUST 为仓库事实和业务外部事实保存来源与核实日期，并 MUST 使用规定的需求状态、验证等级、组合结论和商业判断枚举。未知价格、收入、客户数量或市场规模不得被估算成事实。

#### Scenario: A claim is not fully verified
- **WHEN** 组合只获得官方文档支持但尚未运行连接实验
- **THEN** 页面 MUST 标记“文档层面可行”而不是“已验证可行”

### Requirement: Revised monthly pages preserve static archive behavior
新版月报 SHALL 继续通过 `/monthly/` 和 `/monthly/YYYY-MM/` 静态渲染，保留月份归档、相邻月份、月/周/日切换、本地搜索、SEO 元数据和无 JavaScript 导航。

#### Scenario: Site rebuilds after external facts change
- **WHEN** GitHub 或商业产品信息在发布后变化
- **THEN** Astro 构建仍只读取冻结的本地 Markdown，不访问外部 API 改写历史内容

### Requirement: Period navigation is centered and the desktop monthly archive is collapsible
共享页头 MUST 将月、周、日切换器相对页面内容区域居中，且不得因品牌或搜索控件宽度不同而偏移。桌面月报 MUST 允许读者将月份归档收起为保留展开按钮的窄栏；移动端 MUST 隐藏折叠按钮并继续显示月份选择器。

#### Scenario: Reader collapses the monthly archive on desktop
- **WHEN** 读者激活月度归档的收起按钮
- **THEN** 归档链接隐藏、主内容区域扩展、窄栏中仍保留可聚焦的展开按钮，且按钮通过 `aria-expanded` 暴露当前状态

#### Scenario: Reader opens a report on mobile
- **WHEN** 视口宽度不超过 768px
- **THEN** 归档折叠按钮不显示，月份选择器继续可用，月/周/日切换器保持居中

### Requirement: Report archives are period-specific and collapsible
周报页面 MUST 只展示周报归档，日报页面 MUST 只展示日报归档。桌面归档 MUST 可收起为保留展开按钮的窄栏；移动端 MUST 保留只含当前周期报告的选择器。

#### Scenario: Reader opens a weekly or daily report
- **WHEN** 读者打开周报或日报详情页
- **THEN** 归档链接与选择器只包含当前周期，且桌面折叠按钮通过 `aria-expanded` 暴露状态
