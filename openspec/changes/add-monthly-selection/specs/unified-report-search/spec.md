## ADDED Requirements

### Requirement: Search index identifies report periods
每个搜索项 MUST 包含 `monthly`、`weekly` 或 `daily` 报告类型，搜索面板 SHALL 以“月”“周”“日”徽标显示该类型。

#### Scenario: Monthly project appears in search
- **WHEN** 月报中的 Top 5 或分类推荐项目被索引并匹配查询
- **THEN** 搜索结果链接到对应月报锚点并显示“月”徽标

### Requirement: Monthly matches rank before weekly and daily history
对相同查询，系统 MUST 按月报、周报、日报的优先级排序，同类型项目保持输入顺序。

#### Scenario: Repository exists in all report types
- **WHEN** 同一仓库同时存在匹配的月报、周报和日报搜索项
- **THEN** 月报结果排第一、周报第二、日报第三

### Requirement: Report type is searchable
系统 SHALL 将本地化类型标签与报告标签加入搜索文本，同时保留仓库名、定位、技术栈和项目类型匹配。

#### Scenario: Reader searches by monthly type
- **WHEN** 查询包含“月”并存在月报项目
- **THEN** 搜索返回月报项目且不因新增类型字段破坏现有技术栈或仓库名匹配
