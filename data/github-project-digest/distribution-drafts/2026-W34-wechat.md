# 开源雷达周刊

![开源雷达周刊｜每周开源项目精选](/covers/repository-radar-weekly-subtitle.png)

这一周的十个项目集中在一件事上：让 AI 从演示走向可观察、可验证、可约束的工程系统。既有把 trace、评测和提示词管理放在一起的 Opik，也有把工作流、隔离运行和验收证据拆开的 ADK、Symphony 与 Agent Substrate；TurboVec 则把本地检索的性能与取舍放回可复测的工程语境。

另一条线索是把边界写进工具本身。LangExtract 让抽取结果回到原文位置，Career-ops 把求职自动化停在人工确认之前，AI-Infra-Guard 把 Agent、Skill 和 MCP 的安全检查拆成模块，MarkItDown 与 Apex Inference Chip 则提供了很适合顺藤摸瓜阅读源码的工程样本。

## 一、把 AI 应用做成可观察的系统
### 1. Opik：LLM 与 Agent 的观测、评测工作台
**介绍：** [Opik](https://github.com/comet-ml/opik) 是面向 LLM、RAG 和 Agent 的开源平台，覆盖调用 trace、实验数据、Prompt 管理、评测与生产监控，并支持自托管。

**推荐依据：** 它同时具备 Python 上手路径、RAG 指标、Agent trace、部署材料以及持续维护信号，适合补齐 AI 应用从调试到上线观察之间的缺口。

**适合：** 已经在做 RAG 或 Agent，希望把调用链、数据集评测和成本观察接入同一工作流的团队。

**注意：** 平台会接触 Prompt、输入输出和用户数据；启用自托管前仍要单独审计权限、脱敏、存储与保留策略，LLM-as-a-judge 也不能代替领域验收。

### 2. Google ADK Python：代码优先的复杂 Agent 框架
**介绍：** [Google ADK Python](https://github.com/google/adk-python) 是面向复杂 AI Agent 的 Python 框架，提供多 Agent 编排、工具调用、工作流、人工确认与部署接口。

**推荐依据：** 2.0 工作流、示例、测试与部署材料能够连成一条路径，适合观察带状态、重试和人工确认的 Agent 如何落到应用工程。

**适合：** 需要构建多 Agent、MCP 或 OpenAPI 工具接入，并计划验证部署路径的应用团队。

**注意：** 2.0 对 Agent API、事件模型和会话结构带来迁移影响；与 Google 云服务的结合也需要自行评估供应商依赖、成本和数据治理。

### 3. TurboVec：面向本地检索的 Rust 向量索引
**介绍：** [TurboVec](https://github.com/RyanCodrai/turbovec) 是基于 TurboQuant 的 Rust 向量索引库，通过 Python 绑定提供本地向量检索、增量更新、过滤与持久化能力。

**推荐依据：** Trending 增长、可运行示例和 benchmark 入口共同构成了清楚的试用路径；它把低内存检索、量化与本地部署集中在一个可做对照实验的仓库里。

**适合：** 想用自己的 embedding 验证小型 RAG，或研究 SIMD、量化和持久化索引取舍的开发者。

**注意：** 作者给出的性能结论有固定硬件和数据集前提，量化也可能影响召回；不要直接替换现有向量库，应在自己的维度、过滤比例和 CPU 上复测。

### 4. LangExtract：让结构化抽取回到原文证据
**介绍：** [LangExtract](https://github.com/google/langextract) 用 LLM 从非结构化文本提取结构化信息，并将结果映射回原文字符跨度，提供 Python 库和可视化审阅工具。

**推荐依据：** source grounding、长文档分块、provider 扩展和 HTML 审阅形成了清楚的使用入口，使它比单纯的抽取封装更适合搭建可回溯的数据处理管线。

**适合：** 做文档抽取、检索前处理，或需要检查抽取结果与原文对应关系的二次开发者。

**注意：** 字符跨度可追溯不代表结论正确；模型、提示、示例和分块策略仍会影响输出，医疗、法律等高风险文本还需独立校验并隔离 provider 凭证。

## 二、给 Agent 加上运行与安全边界
### 5. Career-ops：带人工确认的本地求职工作台
**介绍：** [Career-ops](https://github.com/santifer/career-ops) 将 AI coding CLI 组织为本地求职工作台，覆盖岗位扫描、结构化评估、简历生成和申请跟踪，并保留人工确认环节。

**推荐依据：** 它把岗位合法性信号、草稿生成、浏览器自动化和“只起草、不提交”的边界放在同一业务流程中，是观察 Agent Skills 如何服务具体工作流的好样本。

**适合：** 想研究 Agent 驱动的业务流程，或希望在本地整理求职管线、先人工审阅再行动的个人开发者。

**注意：** 岗位评估和简历内容可能出现错误或泄露个人资料；站点抓取也受页面变化和服务条款影响，浏览器自动化与 PDF 生成应使用隔离凭证并保留人工审核。

### 6. AI-Infra-Guard：Agent 与 MCP 的安全扫描平台
**介绍：** [AI-Infra-Guard](https://github.com/Tencent/AI-Infra-Guard) 是面向 Agent、Skills、MCP、AI 基础设施和越狱评测的安全测试平台，提供扫描器、规则库以及 Web 与 CLI 入口。

**推荐依据：** 它把 Skill、MCP、Agent 与漏洞规则拆成可组合的扫描面，适合作为内部 Agent 发布前安全检查的研究和二次开发入口。

**适合：** 需要在明确授权范围内审计 AI 工作流，或准备研究内部 Skill、MCP 安全门禁的安全团队与平台工程师。

**注意：** 扫描报告不是完整安全证明，规则覆盖、误报漏报、漏洞库更新和部署数据权限都需自行验证；越狱和攻击性样例只能用于授权的测试目标。

### 7. Agent Substrate：高密度有状态 Agent runtime
**介绍：** [Agent Substrate](https://github.com/agent-substrate/substrate) 是基于 Kubernetes 的 Agent runtime，通过 actor/worker 映射、挂起恢复和状态快照承载有状态 Agent。

**推荐依据：** 它把控制面调度、空闲复用和状态恢复做成可阅读的实现与 Demo，提供了研究长任务 Agent 基础设施的一组具体对象。

**适合：** 想拆解 Kubernetes 调度、隔离、状态持久化和多租户资源复用的基础设施工程师。

**注意：** 项目仍处于早期，依赖 Kubernetes、gVisor 等复杂组件；Demo 的复用比例与恢复表现不应外推到生产，权限边界、快照策略和延迟需要在隔离集群中自行压测。

### 8. OpenAI Symphony：把交付证据纳入自治编码流程
**介绍：** [OpenAI Symphony](https://github.com/openai/symphony) 将项目工作转成隔离的实现运行，参考实现把工作项、独立 workspace、编码 Agent 和验收证据串联起来。

**推荐依据：** SPEC 与 Elixir 参考实现并置，适合逐模块理解自治编码系统如何处理调度、隔离，以及 CI 和 Review 证据回传。

**适合：** 希望研究 Agent 生命周期、隔离工作区和人类验收闭环的工程团队与架构学习者。

**注意：** 项目明确属于 engineering preview／实验性参考实现；Linear webhook、worktree、密钥处理和自动合并策略不能直接照搬，必须先补足沙箱、审计、超时和人工审批。

## 三、从文档管线到硬件验证的源码样本
### 9. MarkItDown：多格式内容转 Markdown 的转换器
**介绍：** [MarkItDown](https://github.com/microsoft/markitdown) 将 PDF、Office、图片、音频、HTML、CSV、JSON、XML、ZIP、YouTube 和 EPUB 等输入转换为 Markdown，提供 Python API、CLI、Docker 和插件框架。

**推荐依据：** 它的价值不止于单一转换功能；格式适配器、可选依赖、测试、插件边界和安全契约，适合沿文档处理管线阅读与改造。

**适合：** 想研究文档转换、OCR、插件机制，或在受控环境内做多格式内容预处理的开发者。

**注意：** 转换过程可能接触进程可访问的文件或网络资源，不能把宽权限调用直接暴露给不可信用户；第三方云与 OCR 插件还会带来额外依赖和数据外传风险。

### 10. Apex Inference Chip：验证优先的 FPGA 推理设计
**介绍：** [Apex Inference Chip](https://github.com/SigmanticAI/apex-inference-chip) 是在真实 FPGA 上运行 Qwen2.5-0.5B 的推理芯片设计，用 RTL、NumPy golden model、测试与硬件实测连接模型算法和芯片实现。

**推荐依据：** 本周最有价值的部分是它把 `spec → golden model → frozen vectors → RTL → testbench/SVA/coverage → FPGA silicon` 组织成可追踪的学习路径，并区分实测与推算指标。

**适合：** 希望理解 Transformer 推理硬件化、KV-cache 量化、数值一致性和 RTL 验证链路的工程学习者。

**注意：** 项目只覆盖一层 Transformer 与特定 FPGA、工具链；仓库中的性能数字不能外推为通用推理能力，时序、精度和资源占用需要在目标硬件上重新验证。

## 本周优先试用
如果只选三个入口：想建立 AI 应用观测闭环可先试 Opik；想把复杂 Agent 工作流跑起来可从 Google ADK Python 开始；想研究自治编码系统的隔离与验收证据，可先只读 Symphony 的规格和参考实现。

完整的筛选依据、维护信号和上手建议见 [2026-W34 完整周报](/weekly/2026-W34/)。

这十个项目中，哪一个最值得我们下一周做一次真实试用？欢迎留言告诉我你关心的场景。

---

**关于仓库雷达**

仓库雷达持续整理值得使用、学习和二次开发的开源项目。日报负责发现，周报负责筛选，也会尽量把风险和低成本试法说清楚。
