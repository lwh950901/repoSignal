## ADDED Requirements

### Requirement: Undated report entrypoints redirect to the latest issue
系统 SHALL 将月报、周报、日报和开源雷达周刊的无日期入口临时重定向到各自按现有发现规则排序后的最新一期带日期路径，并更新浏览器地址栏。

#### Scenario: Reader opens the monthly entrypoint
- **WHEN** 读者访问 `/monthly` 或 `/monthly/`
- **THEN** 系统以 `302` 重定向到最新月报的 `/monthly/YYYY-MM/` 路径

#### Scenario: Reader opens the weekly entrypoint
- **WHEN** 读者访问 `/weekly` 或 `/weekly/`
- **THEN** 系统以 `302` 重定向到最新周报的 `/weekly/YYYY-Www/` 路径

#### Scenario: Reader opens the daily entrypoint
- **WHEN** 读者访问 `/daily` 或 `/daily/`
- **THEN** 系统以 `302` 重定向到最新日报的 `/daily/YYYY-MM-DD/` 路径

#### Scenario: Reader opens the radar entrypoint
- **WHEN** 读者访问 `/radar` 或 `/radar/`
- **THEN** 系统以 `302` 重定向到最新开源雷达周刊的 `/radar/YYYY-Www/` 路径

### Requirement: Production builds emit exact Cloudflare redirect rules
生产构建 MUST 在静态资产目录生成 Cloudflare `_redirects` 文件，为四类入口的有斜杠和无斜杠形式分别声明精确的 `302` 规则，并且规则 MUST NOT 匹配任何带日期详情页。

#### Scenario: Build contains all undated entrypoint rules
- **WHEN** 生产构建完成且四类详情页均存在
- **THEN** `dist/_redirects` 包含八条指向当前最新 slug 的精确 `302` 规则

#### Scenario: Reader opens a dated detail page
- **WHEN** 读者访问 `/weekly/2026-W31/` 等带日期详情路径
- **THEN** Cloudflare 直接提供该详情页且不应用无日期入口重定向

### Requirement: Redirect generation validates all report types
重定向生成器 MUST 只接受与各报告类型公开 slug 格式匹配且包含 `index.html` 的详情目录，并在任一类型没有合法详情页时以非零状态失败且指出缺失类型。

#### Scenario: Unrelated directories exist in a report output
- **WHEN** 报告输出目录同时包含合法详情目录和不符合 slug 格式的其他目录
- **THEN** 生成器忽略无关目录并选择最新的合法详情目录

#### Scenario: A report type has no valid detail page
- **WHEN** 任一报告类型不存在包含 `index.html` 的合法详情目录
- **THEN** 生成器终止构建并在错误中标明该报告类型

### Requirement: Dated report pages remain the sole content URLs
系统 MUST 保持所有带日期报告详情页及其 canonical URL 不变，无日期入口 MUST NOT 渲染报告正文、归档内容或独立 canonical 页面。

#### Scenario: Search engine follows an undated report entrypoint
- **WHEN** 搜索引擎或读者请求任一无日期报告入口
- **THEN** 请求被重定向到自带 canonical 的最新带日期详情页，而不是获得重复正文
