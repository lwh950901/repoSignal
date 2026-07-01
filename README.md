# RepoSignal

将 `data/github-project-digest` 中持续生成的日报与周报发布为静态项目档案库。网站使用 Astro 在构建阶段读取 Markdown，不需要数据库或服务端运行时。

## 本地运行

```bash
npm install
npm run dev
```

常用检查：

```bash
npm test
npm run check
npm run build
```

生产文件输出到 `dist/`。

## 数据来源

- 日报：`data/github-project-digest/daily/*.md`
- 周报：`data/github-project-digest/weekly/*.md`

提交新的报告后，下一次构建会自动生成对应日期或周次的静态页面，并更新首页、归档导航与本地搜索索引。

## Cloudflare Pages

在 Cloudflare Pages 中连接这个 GitHub 仓库，并使用以下设置：

- Framework preset：`Astro`
- Build command：`npm run build`
- Build output directory：`dist`
- Root directory：仓库根目录
- Node.js：22 或更新版本

首次部署完成后会获得一个 `*.pages.dev` 地址。此后推送到部署分支会自动重新构建；不需要在 Cloudflare 配置 GitHub API 密钥。

## 交互

- 桌面端使用左侧日期轴浏览历史报告。
- 移动端使用报告选择器切换日期。
- 按 `⌘K` 或 `Ctrl+K` 搜索仓库名、技术栈、推荐类型和使用场景。
- 禁用 JavaScript 后，报告正文、归档链接和 GitHub 链接仍可阅读。
