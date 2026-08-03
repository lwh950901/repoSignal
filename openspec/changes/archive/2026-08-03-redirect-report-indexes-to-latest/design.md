## Context

RepoSignal 使用 Astro 静态输出并通过 Cloudflare Workers Static Assets 部署。四类报告加载器已经按 slug 倒序返回报告，但对应的无日期入口行为不一致：月报直接渲染最新内容，周报、日报和雷达显示手动入口链接。静态 Astro 路由可以在本地表达重定向意图，但线上必须由 Cloudflare `_redirects` 规则返回真实 HTTP 302。

该变化跨越页面路由、构建产物和托管平台配置，因此需要一套共享且可验证的最新目标解析规则。项目保证月报、周报、日报和雷达四类数据始终存在。

## Goals / Non-Goals

**Goals:**

- 四类无日期入口都将浏览器导航到最新一期的带日期详情页。
- Cloudflare Workers Static Assets 对入口请求返回真实 `302`。
- 每次构建自动从实际静态详情目录确定最新目标。
- 本地开发入口与线上 Cloudflare 规则指向相同的 slug。
- 缺少任一类型详情页时阻止生产构建成功。

**Non-Goals:**

- 不修改报告 Markdown、详情页路由、报告排序函数或页面视觉设计。
- 不保留无日期入口的正文、归档列表或空状态。
- 不增加客户端跳转、永久重定向或 Worker 运行时代码。

## Decisions

### 1. 无日期 Astro 路由返回临时重定向

四个 `src/pages/<period>/index.astro` 分别使用现有加载器取得第一条记录，并返回到 `/<period>/<slug>/` 的 `302`。这保证本地开发和不解析 `_redirects` 的静态预览仍表达相同导航意图。

备选方案是在索引页直接渲染最新正文；这会保留重复 URL、拆分统计并让分享链接随时间变义，因此不采用。客户端 JavaScript 或 meta refresh 依赖浏览器执行且会受 CSP 影响，也不采用。

### 2. 构建后从 `dist` 详情目录生成 Cloudflare 规则

新增 Node 脚本，在 `astro build` 成功后扫描：

- `dist/monthly/YYYY-MM/`
- `dist/weekly/YYYY-Www/`
- `dist/daily/YYYY-MM-DD/`
- `dist/radar/YYYY-Www/`

脚本按各类型的严格 slug 正则过滤目录，再按字典序降序选择最新值。合法 ISO 日期与周 slug 的字典序等于时间顺序，因此无需第二套 Markdown 解析器。脚本只写 `dist/_redirects`，不修改源数据或 `public/`。

备选方案是在 `public/_redirects` 保存具体日期；这需要每期人工更新，容易过期。让脚本重新解析 Markdown 则会重复现有 Astro 数据规则，增加漂移风险。

### 3. 同时覆盖有斜杠和无斜杠入口

每个类型生成两条精确规则，例如：

```text
/weekly /weekly/2026-W31/ 302
/weekly/ /weekly/2026-W31/ 302
```

共生成八条静态规则。精确源路径不会匹配 `/weekly/2026-W31/`，因此不会形成循环或拦截详情页。Cloudflare 在静态资产响应前处理 `_redirects`，所以线上请求不会先渲染 Astro 的索引 HTML。

### 4. 构建脚本是生产构建的一部分

`package.json` 的 `build` 命令先执行 Astro，再运行重定向生成器。生成器导出纯函数供 Vitest 使用，并提供 CLI 入口；任一类型没有合法详情目录时抛出包含类型名称的错误并以非零状态退出。

## Risks / Trade-offs

- [Cloudflare 规则与本地 Astro 行为由两处代码表达] → 用同一组 period/slug 契约测试目标，并在生产构建后核对 `dist/_redirects`。
- [构建目录中混入非报告子目录导致目标错误] → 每个类型使用严格 slug 正则，只接受目录且要求其中存在 `index.html`。
- [字典序假设被未来 slug 格式破坏] → 正则固定当前公开格式；格式变化必须同步修改测试和生成器。
- [Cloudflare Worker 代码配置为优先运行时 `_redirects` 可能不生效] → 当前部署直接使用 Static Assets，继续通过线上响应测试验证；若未来启用 `run_worker_first`，需要把相同规则迁移到 Worker 代码。
- [302 不会被长期缓存，可能比 301 多一次入口请求] → “最新一期”目标会变化，避免永久缓存比减少一次请求更重要。

## Migration Plan

1. 增加失败优先测试，覆盖四个入口和重定向生成器。
2. 实现 Astro 路由重定向和构建后 `_redirects` 生成。
3. 运行完整测试、Astro check、生产构建和 OpenSpec 严格校验。
4. 检查 `dist/_redirects` 的八条规则与当前最新 slug。
5. 部署后以无斜杠和有斜杠入口各抽查一次 302 与 `Location`。

回滚时恢复四个 index 页面和原构建命令，并删除生成脚本；带日期详情页始终保持可用。

## Open Questions

无。入口状态码、目标解析、无数据约束和部署机制均已确认。
