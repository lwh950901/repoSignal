# 本地事务邮件验收证据包｜内部调查

> 核实与组合实验日期：2026-08-01。结论：有需求信号；新开源项目；合成组合达到 L3，未达到真实任务 L4。

## 问题与目标用户

注册确认、邀请、一次性验证码和密码重置都跨越“浏览器 → SMTP → 邮件 → 浏览器”边界。coding agent 可以改页面并操作浏览器，但本地开发仍常要求人打开 Mailpit，找到正确邮件，再复制链接回浏览器。目标用户是已经使用本地 SMTP 捕获工具、希望让 coding agent 或 CI 验收完整事务邮件流程的小型 Web 团队；不面向营销邮件团队，也不验证真实投递率。

## 两类独立需求证据

1. 商业能力：Mailtrap 提供 Email Sandbox 和官方 MCP，可让 AI IDE 发送、检索和查看沙箱邮件；Litmus 把跨客户端预览、链接、图片、可访问性和审批做成正式 Previews & QA 产品。它们证明测试邮件和预发送检查是持续工作，不证明本地开源实现一定有付费市场。
2. 现实开发流程：Supabase CLI 已用 Mailpit 捕获本地注册确认和密码重置邮件，但官方步骤仍是取得 Mailpit URL、在浏览器打开并手工查找邮件。Mailpit 自身提供集成 API，却明确说明 HTML 截图不能由 API 自动化。两处共同留下“自动取得真实邮件页面并形成浏览器证据”的窄缺口。

## 商业、开源与人工替代

| 方案 | 类型 | 已覆盖 | 本方向仍需验证的差异 |
|---|---|---|---|
| Mailtrap Email Sandbox + MCP | 商业产品 | 沙箱 SMTP、邮件检索/查看、AI IDE 工具 | 需要账户和 API token；本方向只主张本地回环、无外部投递 |
| Litmus Previews & QA | 商业产品 | 100+ 邮件客户端预览、链接/图片/可访问性检查、审批 | 远强于浏览器预览；本方向不与其竞争跨客户端兼容性 |
| MailSandbox | 开源/自托管 | Mailpit fork，增加 Postmark 模拟和邮件 list/get/search/analyze MCP | 已覆盖“让 Agent 读邮件”；没有替代浏览器落地页验收和统一证据包，且截至核实时仅约 7 Stars、最近 release 为 2025-09 |
| Mailpit + 手工浏览器 | 现实流程 | SMTP 捕获、HTML/link 检查、手工截图和复制链接 | 步骤可用但无法稳定归属并行测试，也不能自动形成一次运行的证据清单 |

## 产品定义

第一版是一个薄编排器，而不是新的 SMTP 服务或 MCP server。它给一次测试生成唯一收件地址，等待 Mailpit 捕获匹配邮件，再要求 Chrome DevTools MCP 打开该邮件的 HTML 页面，核对主题、关键文案和允许域名内的链接，继续访问落地页，最后输出 JSON 清单与 PNG 截图。默认只允许回环地址，不开启 Mailpit 的内部 HTTP 代理能力。

## 仓库组合

### axllent/mailpit

- 来源身份：7 月 31 日发现的本月核心。
- 许可证：MIT。
- 接口：SMTP、`/api/v1/messages`、`/view/<ID>.html`、标签/plus addressing。
- 职责：接收和保存测试邮件，提供真实 MIME/HTML 输出。
- 部署限制：单静态二进制或容器；公开暴露时需要认证、TLS 和更新安全版本；本轮只绑定回环地址。
- 验证：官方 v1.30.6 静态二进制接收合成邮件，API 返回预期元数据和摘要，L2。

### ChromeDevTools/chrome-devtools-mcp

- 来源身份：7 月 Top 1。
- 许可证：Apache-2.0。
- 接口：MCP `navigate`、`evaluate`、`screenshot`。
- 职责：读取渲染后的邮件页面、检查链接并生成浏览器截图。
- 部署限制：需要 Node 20.19+ 和 Chrome；必须使用隔离 profile、限制 URL 和关闭不需要的遥测。
- 验证：v1.6.0 官方 npm tarball在隔离无头 Chrome 中完成 MCP 初始化、导航、页面求值与截图，L2。

两仓库职责不重叠：Mailpit 不驱动浏览器，Chrome DevTools MCP 不接收 SMTP 或解析邮箱队列。

## L3 组合实验

链路：`Python 标准库 SMTP 合成邮件 → Mailpit 127.0.0.1:11025 → Mailpit REST/HTML → Chrome DevTools MCP → 页面事实 + 临时 PNG`。

固定结果：Mailpit API 返回一封收件人为 `qa+run-202607@reposignal.invalid`、主题为 `RepoSignal synthetic reset` 的消息；Chrome DevTools MCP 导航到 `/view/latest.html`，读取标题 `Reset password` 和带固定测试 token 的回环链接，并在系统临时目录生成截图。因此组合为 L3。实验未点击真实外部链接、未使用真实邮箱、用户数据或凭据。

## 自研缺口与 Ponytail 边界

只需要唯一 run id、轮询超时、精确消息匹配、允许域名、固定断言、证据 manifest 和清理。第一版不重做邮件 UI、MCP server、跨客户端渲染、垃圾邮件评分或视觉 AI 判断；这些已有成熟工具，增加只会扩大误报和安全面。

## MVP 与停止条件

- MVP：在一个合成密码重置应用中连续运行三次，均只取得本次邮件，核对主题/正文/链接，访问回环落地页并生成 JSON + PNG；任一失败都保留可读原因。
- 成功标准：零真实投递、零跨运行串信、关键链接实际可打开、工件可由人工复核。
- 停止条件：用户主要需要 Outlook/Gmail 真实渲染；MailSandbox 加现有浏览器测试用少量脚本即可稳定覆盖；并行收件匹配持续产生误判；或必须放宽到任意外部 URL 才能工作。

## 判断与证据边界

值得做新开源项目的技术实验，原因是组合已达到 L3、现实流程明确且实现面很薄。尚未验证真实团队是否愿意采用、是否减少测试时间、CI 稳定性、不同框架兼容、真实邮件客户端表现、客户、收入、价格和市场规模。

## 来源

- [Mailpit GitHub](https://github.com/axllent/mailpit)
- [Mailpit Releases](https://github.com/axllent/mailpit/releases)
- [Mailpit integration testing](https://mailpit.axllent.org/docs/integration/)
- [Mailpit HTML screenshots](https://mailpit.axllent.org/docs/usage/html-screenshots/)
- [Chrome DevTools MCP](https://github.com/ChromeDevTools/chrome-devtools-mcp)
- [Mailtrap MCP](https://github.com/mailtrap/mailtrap-mcp)
- [Mailtrap Sandbox for AI workflows](https://mailtrap.io/sandbox-for-ai-workflows/)
- [Litmus Previews & QA](https://help.litmus.com/article/119-litmus-presend-testing-guide)
- [Supabase password email local development](https://github.com/supabase/supabase/blob/master/apps/docs/content/guides/auth/passwords.mdx)
- [MailSandbox](https://github.com/btafoya/mailsandbox)
