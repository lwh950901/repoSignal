# monthly-research-evidence Specification

## Purpose
定义月度研究证据在公开构建之外的版本化存储和核验规则，确保商业需求使用独立证据，机会判断先调查现有替代方案，并通过明确验证等级、许可证与维护检查约束核心仓库和辅助组件的组合结论。

## Requirements

### Requirement: Monthly research evidence is versioned outside the public build
系统 MUST 在 `data/github-project-digest/monthly-research/YYYY-MM/` 保存 Top 5 评分、业务调查和仓库验证摘要，并 MUST 排除该目录的页面加载和搜索索引。

#### Scenario: Production site is built
- **WHEN** Astro 执行生产构建
- **THEN** 构建产物不包含内部研究路径、原始命令日志、凭据或私有数据

### Requirement: Business demand uses independent evidence
正式业务方案 MUST 至少包含两类相互独立的真实需求证据，并 MUST 达到“有需求信号”或“已确认需求”。Stars、单篇趋势文章、项目作者声明和 AI 推断不得单独满足门槛。

#### Scenario: Hypothesis only has weak evidence
- **WHEN** 一个业务假设只有仓库热度和编辑推断
- **THEN** 研究文件将其标记为“推测需求”，公开月报不得发布该方案

### Requirement: Existing alternatives are investigated before opportunity claims
每个公开业务方案 MUST 调查至少一个商业产品、一个开源或可自托管方案，以及一个人工或企业内部现实流程，并记录服务对象、能力、公开价格、部署方式、采用证据、限制和差异。

#### Scenario: Public pricing is unavailable
- **WHEN** 官方来源没有提供价格
- **THEN** 研究和公开内容标记“未知”，不得推算价格或收入

### Requirement: Repository combinations use explicit verification levels
每个核心仓库 MUST 至少达到 L0，至少一个核心仓库 MUST 达到 L2。组合未达到 L3 时 MUST 标记为“文档层面可行”或“部分可行”，并列出输入、输出、接入方式和自行开发部分。

#### Scenario: Repositories are only conceptually related
- **WHEN** 两个仓库功能重叠、没有可用接口或只能人工复制数据
- **THEN** 它们不得被描述为已验证组合，研究结论 MUST 降级或拒绝发布

### Requirement: Monthly repository scope allows verified supporting components
每个业务方案 MUST 至少包含一个本月核心仓库，并 MAY 使用历史或外部辅助仓库。辅助仓库 MUST 明确标记且接受与本月仓库相同的许可证、维护和接口核实。

#### Scenario: A required component was not discovered this month
- **WHEN** 完成产品工作流需要一个稳定的历史或外部仓库
- **THEN** 研究可以将其作为“补充组件”加入，而不把它计作本月发现或 Top 5 候选
