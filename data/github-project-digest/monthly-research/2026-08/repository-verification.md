# 2026-08 仓库与组合验证

> 内部核实摘要；日期：2026-09-01。

## 验证等级

- L0：官方仓库、许可证、维护状态和文档入口已核对。
- L1：安装/启动入口已复核。
- L2：官方最小流程或发布检查有可复核的预期输出；本月部分为原始日报已经记录的仓库侧证据，未把它们误称为本机重跑。
- L3：两个以上仓库完成真实格式数据连接。
- L4：授权真实任务完成。

## Top 5 事实核对

| 仓库 | 冻结事实 | 许可证 | 等级 | 官方来源 |
|---|---|---|---|---|
| openai/codex | 8 月 Rust release、跨平台安装、测试和持续推送；8 月 29 日快照 119.2k Stars/18.2k Forks | Apache-2.0 | L1 | GitHub、Releases |
| microsoft/playwright-mcp | npx、MCP、accessibility tree、测试/CI、Docker/devcontainer；8 月 28 日快照 36,548/3,069 | Apache-2.0 | L0 | GitHub、npm |
| google/adk-python | v2.7.1、workflow/runtime、Samples、CI 与 8 月修复；8 月 31 日快照 21,334/3,916 | Apache-2.0 | L0 | GitHub、Release、ADK docs |
| comet-ml/opik | Python/TS SDK、自托管、PyTest、v2.2.30；8 月 18 日快照 21,431/1,711 | Apache-2.0 | L0 | GitHub、Opik docs |
| fission-ai/openspec | v1.8.0、CLI、tests、schemas、artifact workflow；8 月 12 日快照 64,573/4,450 | MIT | L1 | GitHub、Releases |

## 组合数据流核对

| 组合 | 核心输入 | 核心输出 | 可复核 L2 | L3 结果 |
|---|---|---|---|---|
| 本地工作台 | 授权 Markdown、固定任务 | 检索上下文、摘要、导出文件 | ADK Go 样例/发布检查（source-side） | 未确认：本机没有 Go，且未配置模型凭据。 |
| 安全 Agent 平台 | 授权靶场源码/回环服务 | 扫描 JSON、影响范围、审批证据 | AI-Infra-Guard CLI、code-review-graph build/test（source-side） | 未确认：Docker socket 权限拒绝；Python CLI 下载 TLS 失败。 |
| 私有知识助手 | 脱敏 Markdown、固定问题 | 带引用答案、模拟审批、trace | ADK Go 样例/发布检查（source-side） | 未确认：CubeSandbox 的 Linux/KVM 前置不满足；没有真实数据。 |

## 安全 L3 尝试日志

1. 读取 AI-Infra-Guard、ADK Go、Cognee、Opik、code-review-graph 的官方 README，确认输入/输出、Docker/Go/LLM 前置与许可证。
2. `docker info --format '{{.ServerVersion}}'` 返回 Docker API socket permission denied，未启动或修改 Docker。
3. 在 `/private/tmp/reposignal-crg-env` 创建隔离 venv；普通 pip DNS 失败。经批准的一次外部网络重试在镜像 TLS certificate verify failed 后结束。
4. 没有使用 insecure/trusted-host，不读取凭据或真实业务数据；因此所有组合只标“文档层面可行”。
