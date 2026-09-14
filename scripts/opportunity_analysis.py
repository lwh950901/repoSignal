#!/usr/bin/env python3
"""基于最近 90 天发现的 GitHub 项目，生成"可行性方案"（业务方向 × 多项目组合）。

用法：
  python3 scripts/opportunity_analysis.py [--date YYYY-MM-DD] [--data-root PATH]
          [--output PATH] [--no-llm] [--check]

行为：
  1. 前置条件：当天日报 daily/<运行日期>.md 必须存在；当天无日报即跳过——
     不分析、不写报告与 runs.log，以退出码 2 结束（不回退到更早的日报）。
  2. 项目池：解析 daily/ 与 weekly/ 中最近 90 天窗口内所有报告的项目条目，
     按 owner/repo 去重；每个项目保留来源（日期/周号）可追溯。
  3. 能力标签聚类（agent/memory/rag/sandbox/observability/gateway/codeintel/
     design/security/document/local/comm），组合模板从全池挑选真实项目，
     输出"可行性方案"（业务定位 / 目标客户 / 市场机会 / 组合分工 / 风险），
     并给出 0-100 确定性综合评分（组件可靠度 / 组件供给 / 风险敞口 /
     今日锚点 / 来源多样性 / 许可证 / 完整度）与高中低档位。
     方案名按能力面拼成（场景 · 差异化能力 · 业务主体），业务身份 plan_family 由
     customer + problem + expected_outcome 派生，与技术词、标题措辞、组件集合解耦。
  4. 双轨产出：每天 1-3 个方案 = 最多 1 个成熟方向（固定模板，evidence_status=
     supply-checked）+ 最多 2 个探索方向（今日锚点 + ≥2 个互补组件，to-validate）；
     没有合格探索方向时允许少于 3 个，0 个方案时报告明确写“本轮无合格方案”。
  5. 可选增强：设置 OPPORTUNITY_LLM_API_KEY（或 OPENAI_API_KEY）时调用
     OpenAI 兼容接口补充视角；失败不影响主流程。
  6. 输出 data/github-project-digest/feasibility/YYYY-MM-DD.md，
     并追加一行运行记录到同目录 runs.log。

退出码：0 成功；2 输入缺失；1 其他错误。
"""

import argparse
import hashlib
import json
import os
import re
import sys
import urllib.error
import urllib.request
from datetime import date, datetime, timedelta
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DATA_ROOT = REPO_ROOT / "data" / "github-project-digest"

WEEK_RE = re.compile(r"^(\d{4})-W(\d{2})$")
DAILY_FILE_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})\.md$")
DATE_RE = re.compile(r"^(\d{4})-(\d{2})-(\d{2})$")
GITHUB_URL_RE = re.compile(
    r"https?://github\.com/([^/\s)\]#]+)/([^/\s)\]#]+)", re.IGNORECASE
)
PLAN_IDENTITY_RE = re.compile(
    r"\*\*方案身份\*\*[：:]\s*`plan_family=([^`]+)`\s*·\s*`variant=([^`]+)`"
)
PLAN_BUSINESS_RE = re.compile(r"\*\*业务语义\*\*[：:]\s*(.+)$", re.MULTILINE)

REPO_LINE_RE = re.compile(
    r"^-\s*仓库[：:]\s*\[([^\]]+)\]\((https?://[^)\s]+)\)\s*$"
)
FIELD_LINE_RE = re.compile(r"^-\s*([^：:]{1,14})[：:]\s*(.*)$")
DAILY_SECTION_RE = re.compile(
    r"^###\s+(?:(?P<num>\d+)\.\s*)?"
    r"(?:(?P<kind>额外发现|爆发型|实用型|潜力型|学习型)[：:]\s*)?"
    r"(?P<repo>[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)"
    r"(?:\s*[—–-]\s*(?P<score>\d+)/100)?"
)
WEEKLY_SECTION_RE = re.compile(
    r"^##\s+(?P<num>\d+)\.\s+(?P<title>.+)$"
)

LABEL_MAP = {
    "一句话定位": "tagline", "项目简介": "tagline",
    "类型与适合用途": "fits",
    "核心亮点与场景": "highlights",
    "主要技术栈": "stack",
    "实时指标": "metrics",
    "近期有意义活动": "activity",
    "质量证据": "quality", "质量与维护": "quality",
    "风险": "risks", "真实风险": "risks",
    "推荐理由": "reason", "入选理由": "reason",
    "评分拆分": "scores",
    "上手建议": "howto",
    "本周精选价值": "value",
}

TAG_RULES = {
    "agent": ("agent", "harness", "swarm", "编排", "工作流", "workflow",
              "多代理", "多 agent", "sdk", "框架", "meta-harness"),
    "memory": ("记忆", "memory", "会话", "session", "长期"),
    "rag": ("rag", "检索", "知识库", "知识图谱", "向量", "vector",
            "embedding", "召回", "索引", "语义", "知识"),
    "sandbox": ("沙箱", "sandbox", "隔离", "microvm", "kvm", "容器",
                "docker", "虚拟机", "不可信", "执行环境"),
    "observability": ("可观测", "observability", "观测", "trace", "追踪",
                      "评测", "eval", "监控", "日志", "telemetry", "成本", "用量"),
    "gateway": ("网关", "gateway", "路由", "router", "provider",
                "模型", "多模型", "接入", "oauth"),
    "codeintel": ("代码", "审查", "review", "调用链", "ast", "tree-sitter",
                  "重构", "解析器"),
    "design": ("设计", "design", "原型", "视觉"),
    "security": ("安全", "security", "审计", "红队", "越狱", "漏洞",
                 "cve", "威胁"),
    "document": ("文档", "pdf", "markdown", "ocr", "转换", "文件",
                 "office", "docx", "epub"),
    "local": ("本地", "local-first", "本地优先", "离线", "自托管",
              "桌面", "隐私", "无云"),
    "comm": ("通信", "消息", "聊天", "chat", "协作", "邮件",
             "telegram", "discord", "whatsapp", "会议"),
}

# 单点项目的商业化角度：每个标签 3 个变体，报告内按出现顺序轮换，避免同一句式连排。
TAG_CN = {"agent": "Agent", "memory": "记忆", "rag": "检索", "sandbox": "沙箱",
          "observability": "观测", "gateway": "网关", "codeintel": "代码理解",
          "design": "设计", "security": "安全", "document": "文档",
          "local": "本地", "comm": "协作"}
COMBO_ROLES = {"agent": "Agent 编排", "memory": "长期记忆", "rag": "检索/知识库",
               "sandbox": "执行沙箱", "observability": "观测/评测", "gateway": "模型网关",
               "codeintel": "代码理解", "design": "设计/原型", "security": "安全审计",
               "document": "文档处理", "local": "本地形态", "comm": "协作入口"}
TAG_ANGLE = {
    "agent": ["可包装成垂直场景的 Agent 托管/订阅产品",
              "可拆出可复用的 Agent 编排能力做独立服务",
              "可做成面向特定岗位的 Agent 工具集"],
    "memory": ["可做成记忆/会话上下文的独立存储服务",
                "适合作为 Agent 产品的记忆层插件",
                "可接入 RAG 或 Agent 产品补足记忆短板"],
    "rag": ["可做成垂直领域知识库（法律/医疗/代码）",
            "可包装为检索质量与引用溯源见长的知识产品",
            "可作为 RAG 管线的检索内核对外服务"],
    "sandbox": ["可提供不可信代码的隔离执行环境",
                "适合作为 Agent 平台与 CI 的沙箱层",
                "可做成安全评估用的隔离运行服务"],
    "observability": ["可做 Agent/LLM 成本与质量观测",
                      "可嵌入现有观测栈补 Agent 可观测性",
                      "可做成评测与回归的独立服务"],
    "gateway": ["可做模型网关/统一接入层",
                "适合按用量与路由策略提供接入服务",
                "可做成多模型切换与成本控制的中转层"],
    "codeintel": ["可做代码理解/审查服务",
                  "适合作为仓库级代码分析的独立工具",
                  "可做成 PR 评审与调用链分析的组件"],
    "design": ["可做 AI 设计交付服务",
               "适合按生成量/导出量提供设计工具服务",
               "可嵌入设计工作流作为素材生成层"],
    "security": ["可做 Agent 安全审计与红队服务",
                 "适合作为发布前的安全检查环节",
                 "可做成 MCP/Skill 供应链审计工具"],
    "document": ["可做文档解析/转换服务",
                 "适合作为 RAG 上游的入库清洗组件",
                 "可做成格式转换 API 或批处理工具"],
    "local": ["可做隐私优先的本地工具商业版",
              "适合做自托管/离线场景的订阅产品",
              "可提供支持与定制服务变现"],
    "comm": ["可做团队协作/通知聚合产品",
             "适合接入 IM 做消息自动化",
             "可做垂直行业通信自动化组件"],
}

# 组合模板：槽位 (标签, 角色)。只有真实项目 ≥2 个且槽位 ≥2 才输出；
# 槽位按顺序挑选全池中标签分最高的未使用项目。
TEMPLATES = [
    {
        "name": "企业内部知识助手（私有化 RAG × Agent）",
        "slots": [
            ("agent", "Agent 编排/工作流底座"),
            ("rag", "知识库与检索"),
            ("memory", "长期记忆"),
            ("sandbox", "执行沙箱"),
            ("observability", "评测与观测"),
        ],
        "pitch": "把散落在各部门的文档接进私有化知识库，员工提问能拿到带出处的答案，需要动手的事由 Agent 在人工审批后执行。",
        "target": "数据敏感的中大型企业（法律/金融/制造/医疗），对数据出境和合规有硬性要求。",
        "market": "企业愿意为'数据不出境 + 答案可追溯'付费；近 90 天池里编排、检索、记忆、沙箱、评测组件都已齐备。",
        "differentiation": "相比单点 RAG 或 Agent 框架，它把'数据私有化 + 人工审批 + 效果评测'一起交付，不用客户自己拼。",
        "rationale": "池中编排、检索、记忆、沙箱、评测组件都能找到，'问答 + 审批执行'的最小闭环可以全部自托管。",
        "mvp": "先固定 agent + rag + 评测三件套：接入一个部门的文档集，配一条评测集，Agent 只能执行一个需要审批的动作；记忆和沙箱二期再加。",
    },
    {
        "name": "可审计的 Agent 开发/交付平台（CI 化 Agent 流水线）",
        "slots": [
            ("sandbox", "执行沙箱/隔离"),
            ("observability", "可观测与评测"),
            ("security", "安全审计"),
            ("agent", "Agent 编排"),
            ("gateway", "模型网关/成本"),
        ],
        "pitch": "让 Agent 任务像 CI 一样跑：进沙箱执行、全程留痕、出审计报告，人工批准后才允许写仓库。",
        "target": "已在使用 coding agent（Codex/Claude Code/Cursor）的研发团队与平台工程组。",
        "market": "Agent 开始真正干活后，'跑挂了怎么恢复、花了多少钱、有没有越权'成为刚需；近 90 天池里隔离执行和观测组件明显变多。",
        "differentiation": "相比单个 harness 或观测工具，它把隔离执行、trace 评测和审计报告串成一条流水线。",
        "rationale": "长任务 Agent 的失败恢复、可观测、安全执行是池里反复出现的主题，组件已成熟，适合拼成 CI 流水线。",
        "mvp": "受限流水线：沙箱内跑一次任务、记录 trace、输出审计报告，人工审批后才允许写仓库；成本与多 Agent 编排后置。",
    },
    {
        "name": "本地优先个人 AI 工作台",
        "slots": [
            ("local", "本地优先/桌面形态"),
            ("agent", "Agent 编排"),
            ("memory", "长期记忆"),
            ("gateway", "模型接入/网关"),
            ("rag", "本地知识检索"),
        ],
        "pitch": "数据全部留在本机、模型可自由切换、记忆可导出的个人 AI 工作台。",
        "target": "重视隐私的个人开发者、知识工作者与小型团队。",
        "market": "池里本地优先、自托管类项目反复出现（记忆/桌面/网关），个人为'数据不离开本机'付费的趋势在上升。",
        "differentiation": "对比云端工作台，卖点是无云依赖和数据所有权；对比单点记忆工具，卖点是一整套工作台。",
        "rationale": "本地记忆、模型网关、Agent 编排在池里都能找到，拼起来就是个人知识工作台。",
        "mvp": "先用两个组件跑通'本地记忆写入→Agent 读取→输出压缩'，再决定桌面端与多渠道接入。",
    },
    {
        "name": "多 Agent 协作控制面（团队级）",
        "slots": [
            ("agent", "多 Agent 编排"),
            ("comm", "通信/协作入口"),
            ("observability", "会话观测与审计"),
            ("gateway", "模型路由/成本"),
            ("memory", "共享记忆"),
        ],
        "pitch": "给团队一个统一面板：所有 Agent 的会话、审批、花费和审计记录都在一处，散落的 Agent 变成可管理的资产。",
        "target": "已在使用多个 coding agent 工具、或计划让 Agent 参与团队流程的团队。",
        "market": "团队里 Agent 工具越用越杂是真实痛点；池中编排、协作入口、成本观测组件刚好都成熟了。",
        "differentiation": "对比单 Agent 工具，它把多 Agent 的会话、审批、审计、成本收到一个控制面里。",
        "rationale": "编排、协作入口、成本观测组件在池中都齐，面向团队做控制面的条件具备了。",
        "mvp": "接一个 Agent 宿主 + 一个协作渠道 + 审计日志，验证审批、打断、失败恢复三个动作，再扩展多 Agent。",
    },
    {
        "name": "文档/知识处理管线（入库前处理）",
        "slots": [
            ("document", "文档解析/转换"),
            ("rag", "检索与知识库"),
            ("observability", "质量评测"),
            ("agent", "处理编排"),
        ],
        "pitch": "入库前解析→转换→质检的知识处理管道，解决 RAG 上游脏数据导致的召回与引用质量问题。",
        "target": "RAG/搜索/文档产品团队，以及自建知识库的企业。",
        "market": "RAG 效果差，问题大多出在入库前的解析和清洗；池里解析/转换与检索组件都已成熟。",
        "differentiation": "对比单点解析库或向量库，它把解析、转换、质检串成一条管道，不用工程师自己拼。",
        "rationale": "解析/转换、检索、评测组件都能拼成'入库前处理 + 质检'管道，正好打 RAG 上游脏数据这个常见瓶颈。",
        "mvp": "固定管道：文档→Markdown→索引→评测报告，用自有样本对比接入前后的召回与引用质量。",
    },
    {
        "name": "安全 Agent 平台（扫描-修复-验证）",
        "slots": [
            ("security", "安全审计/扫描"),
            ("sandbox", "隔离执行"),
            ("agent", "Agent 编排"),
            ("codeintel", "代码理解"),
            ("observability", "证据与报告"),
        ],
        "pitch": "让安全扫描由 Agent 自动跑：扫出问题、给出修复建议、独立验证是否修好，每一步留证据，由人审批放行。",
        "target": "企业安全团队、DevSecOps 平台组。",
        "market": "Agent 带来新的攻击面（Skill/MCP/供应链），池里安全类项目（红队/审计/沙箱）也在密集出现。",
        "differentiation": "对比传统 SAST 只报问题，它把'扫描 + 修复建议 + 独立验证'做成完整流程，且每一步有证据。",
        "rationale": "池里的安全审计、沙箱、代码理解组件正好能拼出'扫描→修复→验证'这条线。",
        "mvp": "在授权靶场跑'扫描→修复建议→独立验证'三步，保留证据与人工审批，再评估接入正式仓库。",
    },
    {
        "name": "代码审查与重构平台（仓库级）",
        "slots": [
            ("codeintel", "代码理解/调用链"),
            ("observability", "回归与评测"),
            ("agent", "修复编排"),
            ("gateway", "模型接入/成本"),
        ],
        "pitch": "把仓库级的审查、重构建议和回归验证串成一条线：Agent 提改动、测试给证据，人只审结论。",
        "target": "中型以上研发团队、平台工程组，以及需要长期维护老代码库的团队。",
        "market": "AI 写代码越来越快，但'改得对不对、有没有破坏别处'仍靠人盯；池里代码理解与回归评测组件都已可用。",
        "differentiation": "对比单点代码补全或 lint，它把'理解仓库→提改动→跑证据'做成可复核流程，而不只是给建议。",
        "rationale": "代码理解、评测、编排、模型接入在池中都能找到，仓库级审阅闭环可以自建。",
        "mvp": "选一个有测试的仓库：Agent 只提 PR 草稿，必须附回归对比结果，人工只做批准或打回。",
    },
    {
        "name": "开源依赖与许可证合规扫描（供应链）",
        "slots": [
            ("security", "漏洞与审计"),
            ("document", "清单与报告"),
            ("codeintel", "依赖/调用分析"),
            ("observability", "证据与复测"),
        ],
        "pitch": "每次依赖变动都产出可交付的清单与证据：哪些包、什么许可证、哪些漏洞真影响了调用路径。",
        "target": "要过审计的研发团队、企业安全与合规岗，以及对外交付产品的厂商。",
        "market": "供应链事件和许可证纠纷反复发生，'扫描结果要能给人看、能复测'是硬需求；池里审计与报告组件齐备。",
        "differentiation": "对比只报 CVE 的扫描器，它把依赖清单、许可证、调用路径影响和复测证据连成一份可审计产物。",
        "rationale": "安全审计、文档生成、依赖分析和评测组件在池中都有，适合拼成面向审计的供应链检查。",
        "mvp": "固定一条流水线：解析依赖→标注许可证与漏洞→给出受影响调用路径→输出报告，在一个仓库上跑通。",
    },
    {
        "name": "团队通知聚合与消息自动化（IM 接入）",
        "slots": [
            ("comm", "消息入口/通知"),
            ("agent", "处理编排"),
            ("memory", "会话上下文"),
            ("observability", "质量与成本"),
        ],
        "pitch": "把散在各处的告警、工单和机器人消息收进一个入口，按规则自动分流、摘要和回执。",
        "target": "值班与运维团队、客服与支持团队，以及靠 IM 协作的中小团队。",
        "market": "消息渠道越多，漏看和重复处理越常见；池里通信入口、会话记忆和编排组件都已成熟。",
        "differentiation": "对比单一机器人脚本，它把多渠道接入、上下文记忆和回执审计放在一处，规则可版本化。",
        "rationale": "通信入口、编排、会话记忆与成本观测组件池中都有，能拼出可维护的消息自动化。",
        "mvp": "先接一个渠道做告警分流：自动摘要 + 升级规则 + 处理回执，稳定后再扩渠道。",
    },
    {
        "name": "设计稿到组件代码交付管线（设计系统）",
        "slots": [
            ("design", "设计/原型"),
            ("codeintel", "组件与代码结构"),
            ("agent", "生成编排"),
            ("observability", "回归与验收"),
        ],
        "pitch": "把设计稿和既有组件库对齐：产出的不是一次性代码，而是能进设计系统的组件改动和验收记录。",
        "target": "有设计系统的产品团队、前端平台组，以及外包交付团队。",
        "market": "'设计还原靠人肉'仍是常态；设计、代码理解与回归组件在池里都能找到，生成质量有验收兜底。",
        "differentiation": "对比通用设计转代码工具，它绑定现有组件库和验收流程，产出可维护而不是一次性页面。",
        "rationale": "设计、代码理解、编排、评测组件齐备，能把'设计→组件→验收'做成一条可回归的管线。",
        "mvp": "挑 1 个组件库：从设计稿生成 3 个组件改动，附截图对比与回归结果，人工验收后再扩大范围。",
    },
    {
        "name": "垂直知识库检索服务（引用溯源）",
        "slots": [
            ("rag", "检索内核"),
            ("document", "文档解析"),
            ("memory", "会话记忆"),
            ("observability", "检索质量评测"),
        ],
        "pitch": "面向一个垂直领域的检索服务：答案必须带引用出处，检索质量和覆盖率可被评测和回归。",
        "target": "法律/医疗/金融等专业领域的产品团队，以及要对外交付检索能力的厂商。",
        "market": "通用模型答专业问题不可信，'带出处的检索'才是可交付形态；池里解析、检索与评测组件都已成熟。",
        "differentiation": "对比通用 RAG 框架，它把引用溯源和检索质量评测当一等功能，而不是事后补。",
        "rationale": "解析、检索、记忆与评测组件在池中都能找到，垂直检索服务的最小闭环可以全部自建。",
        "mvp": "选一个领域语料：解析→索引→带引用问答→评测集打分，先证明引用准确率再谈扩容。",
    },
]

CLIP = 64


def clip(text, n=CLIP):
    text = re.sub(r"\s+", " ", (text or "")).strip()
    return text if len(text) <= n else text[: n - 1].rstrip() + "…"


def first_sentence(text, limit=96):
    """取第一句完整句子；超限时在最近的逗号/空格处截断，避免机器式省略号连篇。"""
    text = re.sub(r"\s+", " ", (text or "")).strip()
    if not text:
        return ""
    m = re.match(r"^(.+?[。！？!?])", text)
    sent = m.group(1) if m else text
    if len(sent) <= limit:
        return sent
    head = sent[:limit].rstrip()
    cut = max(head.rfind("，"), head.rfind(","), head.rfind("；"), head.rfind(" "))
    if cut >= limit // 2:
        head = head[:cut]
    return head.rstrip("，,；; ") + "…"


def esc(text):
    return (text or "").replace("|", "｜")


def normalize_repo(raw):
    repo = (raw or "").strip().strip("`")
    m = GITHUB_URL_RE.search(repo)
    if m:
        repo = f"{m.group(1)}/{m.group(2)}"
    repo = repo.strip("/ ").lower()
    return repo if re.fullmatch(r"[^/\s]+/[^/\s]+", repo) else None


PLAN_FAMILIES = {
    "企业内部知识助手（私有化 RAG × Agent）": "private-enterprise-rag-agent",
    "可审计的 Agent 开发/交付平台（CI 化 Agent 流水线）": "auditable-agent-delivery",
    "本地优先个人 AI 工作台": "local-first-personal-ai-workbench",
    "多 Agent 协作控制面（团队级）": "multi-agent-control-plane",
    "文档/知识处理管线（入库前处理）": "document-ingestion-pipeline",
    "安全 Agent 平台（扫描-修复-验证）": "secure-agent-platform",
    "代码审查与重构平台（仓库级）": "repo-code-review-platform",
    "开源依赖与许可证合规扫描（供应链）": "oss-supply-chain-compliance",
    "团队通知聚合与消息自动化（IM 接入）": "team-message-automation",
    "设计稿到组件代码交付管线（设计系统）": "design-to-code-delivery",
    "垂直知识库检索服务（引用溯源）": "vertical-knowledge-retrieval",
}


def normalize_plan_name(name):
    """Return the stable business-plan name without issue-local numbering/details."""
    value = re.sub(r"^可行性方案\s+\d+[：:]\s*", "", (name or "").strip())
    value = re.sub(r"^\d+\.\s*", "", value)
    return re.sub(r"（组合\s+\d+\s+个项目.*$", "", value).strip()


def _stable_digest(value):
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:12]


def plan_family(name):
    """Identify a business plan independently from its current components."""
    normalized = normalize_plan_name(name)
    return PLAN_FAMILIES.get(normalized, "custom-" + _stable_digest(normalized))


def plan_variant(repositories):
    """Identify one unordered, case-insensitive component set."""
    normalized = sorted({repo for raw in repositories if (repo := normalize_repo(raw))})
    return _stable_digest("\n".join(normalized))


def parse_plan_business(block):
    """解析 `**业务语义**` 行（`key=value` 以 · 分隔）；旧报告无此行时返回 None。"""
    match = PLAN_BUSINESS_RE.search(block or "")
    if not match:
        return None
    fields = {}
    for item in match.group(1).split("·"):
        item = item.strip().strip("`").strip()
        if "=" not in item:
            continue
        key, _, value = item.partition("=")
        fields[key.strip()] = value.strip()
    return fields or None


def parse_plan_identities(markdown):
    """Parse plan identities from current or legacy feasibility/radar Markdown."""
    source = markdown or ""
    for marker in ("## 本周可行性精选", "## 可行性方案"):
        start = source.find(marker)
        if start >= 0:
            start = source.find("\n", start)
            source = source[start + 1:] if start >= 0 else ""
            next_section = re.search(r"^##\s+", source, re.MULTILINE)
            if next_section:
                source = source[:next_section.start()]
            break
    heading_re = re.compile(
        r"^###\s+(?:可行性方案\s+\d+[：:]\s*|\d+\.\s+)(.+)$",
        re.MULTILINE,
    )
    matches = list(heading_re.finditer(source))
    identities = []
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(source)
        block = source[match.start():end]
        repositories = sorted({
            repo for owner, name in GITHUB_URL_RE.findall(block)
            if (repo := normalize_repo(f"{owner}/{name}"))
        })
        name = normalize_plan_name(match.group(1))
        explicit = PLAN_IDENTITY_RE.search(block)
        business = parse_plan_business(block)
        identities.append({
            "name": name,
            "family": explicit.group(1) if explicit else plan_family(name),
            "variant": explicit.group(2) if explicit else plan_variant(repositories),
            "repositories": repositories,
            "track": (business or {}).get("track"),
            "business": business,
        })
    return identities


def parse_section_entries(lines, section_re, source):
    entries = []
    current = None
    for raw in lines:
        line = raw.rstrip("\n")
        m = section_re.match(line)
        if m:
            if current and current["fields"]:
                entries.append(current)
            gd = m.groupdict()
            current = {
                "repo_raw": gd.get("repo") or gd.get("title") or "",
                "kind": gd.get("kind") or "",
                "score": int(gd["score"]) if gd.get("score") else None,
                "source": source,
                "fields": {},
            }
            continue
        if current is None:
            continue
        rm = REPO_LINE_RE.match(line)
        if rm:
            current["repo_raw"] = rm.group(1)
            current["url"] = rm.group(2)
            continue
        fm = FIELD_LINE_RE.match(line)
        if fm:
            key = LABEL_MAP.get(fm.group(1).strip(), fm.group(1).strip())
            current["fields"][key] = fm.group(2).strip()
            continue
        if line.startswith("- "):
            if current["fields"]:
                last = list(current["fields"].keys())[-1]
                current["fields"][last] += "\n" + line[2:].strip()
            continue
        if line and not line.startswith("#"):
            if current["fields"]:
                last = list(current["fields"].keys())[-1]
                current["fields"][last] += " " + line.strip()
    if current and current["fields"]:
        entries.append(current)
    return entries


def parse_weekly(path):
    return parse_section_entries(path.read_text(encoding="utf-8").splitlines(),
                                 WEEKLY_SECTION_RE, "weekly")


def parse_daily(path):
    return parse_section_entries(path.read_text(encoding="utf-8").splitlines(),
                                 DAILY_SECTION_RE, "daily")


def tag_project(project):
    text = " ".join([
        project["fields"].get("tagline", ""),
        project["fields"].get("fits", ""),
        project["fields"].get("highlights", ""),
        project["fields"].get("stack", ""),
        project["fields"].get("value", "") or project["fields"].get("reason", ""),
    ]).lower()
    tags = {}
    for tag, keywords in TAG_RULES.items():
        # 二进制计分：每个关键词最多贡献 1 分，避免冗长条目虚高
        hits = sum(1 for k in keywords if k in text)
        if hits:
            tags[tag] = hits
    return tags


def extract_stars(project):
    m = re.search(r"([\d,]+(?:\.\d+)?k?)\s*Stars?",
                  project["fields"].get("metrics", ""), re.IGNORECASE)
    if not m:
        return 0
    s = m.group(1).replace(",", "")
    if s.endswith("k"):
        return int(float(s[:-1]) * 1000)
    return int(float(s))


def load_project_pool(data_root, run_date):
    """加载项目池，返回 (today_projects, pool_projects, n_daily, n_weekly, anchor_date)。

    today_projects：当天日报 daily/<run_date>.md 解析的项目；
    pool_projects：最近 90 天窗口内全部唯一项目（含 today 项目），每项带 source_date。
    当天无日报时返回空结果（anchor_date 为空串），调用方按输入缺失处理。
    """
    cutoff = date.fromisoformat(run_date) - timedelta(days=90)
    run_d = date.fromisoformat(run_date)
    # 锚点只认当天日报：缺失即视为输入缺失，不回退到更早的日报（当天无日报不出方案）
    if not (data_root / "daily" / f"{run_date}.md").is_file():
        return None, None, 0, 0, ""
    anchor_date = run_date
    projects = []
    seen = set()
    today_ids = set()
    daily_files = 0
    weekly_files = 0
    for f in sorted((data_root / "daily").glob("*.md")):
        m = DAILY_FILE_RE.match(f.name)
        # 窗口下限 cutoff，上限 run_date：补跑历史日期时不得混入 run_date 之后的日报
        if not m or date.fromisoformat(m.group(1)) < cutoff \
                or date.fromisoformat(m.group(1)) > run_d:
            continue
        daily_files += 1
        for e in parse_daily(f):
            repo = normalize_repo(e.get("repo_raw") or "")
            if not repo or repo in seen:
                continue
            seen.add(repo)
            e.update(repo=repo, url=e.get("url") or f"https://github.com/{repo}",
                     source_date=m.group(1), id=repo,
                     tags=tag_project(e), stars=extract_stars(e))
            projects.append(e)
            if m.group(1) == anchor_date:
                today_ids.add(repo)
    for f in sorted((data_root / "weekly").glob("*.md")):
        m = WEEK_RE.match(f.stem)
        if not m:
            continue
        week_start = date.fromisocalendar(int(m.group(1)), int(m.group(2)), 1)
        if week_start < cutoff or week_start > run_d:
            continue
        weekly_files += 1
        for e in parse_weekly(f):
            repo = normalize_repo(e.get("repo_raw") or "")
            if not repo or repo in seen:
                continue
            seen.add(repo)
            e.update(repo=repo, url=e.get("url") or f"https://github.com/{repo}",
                     source_date=f"W{m.group(2)}", id=repo,
                     tags=tag_project(e), stars=extract_stars(e))
            projects.append(e)
    today_projects = [p for p in projects if p["id"] in today_ids]
    return today_projects, projects, daily_files, weekly_files, anchor_date


def _maintenance_flag(p):
    """报告文本明确标注维护滞后的项目，选槽时降权（避免把停摆项目当底座）。"""
    text = " ".join([
        p["fields"].get("risks", ""),
        p["fields"].get("quality", ""),
        p["fields"].get("activity", ""),
    ])
    return "维护" in text and any(k in text for k in ("滞后", "停滞", "明显不足", "减缓"))


def _clean_evidence(s):
    """去除依据文本中的 Markdown 链接残留与多余空白。"""
    s = re.sub(r"\[([^\]]*)\]\(https?://[^)\s]+\)", r"\1", s or "")
    return re.sub(r"\s+", " ", s).strip()


TODAY_BONUS = 3  # 今日锚点项目在选槽时的加权
RECENT_COMPONENT_REUSE_PENALTY = 2
PORTFOLIO_OVERLAP_PENALTY = 8
MIN_COMBO_SCORE = 70
OVERLAP_TOLERANCE = 1        # 允许共享的组件数：少量重叠不淘汰真正不同的方向
MAX_MATURE_PLANS = 1         # 每天最多 1 个成熟方向（固定模板）
MAX_EXPLORATORY_PLANS = 2    # 每天最多 2 个探索方向（今日锚点拼接，待验证）
TRACK_MATURE = "mature"
TRACK_EXPLORATORY = "exploratory"
EVIDENCE_VERIFIED = "supply-checked"   # 成熟方向：池内组件供给已核对
EVIDENCE_TO_VALIDATE = "to-validate"   # 探索方向：方向与需求都待验证

# 方案综合评分：分项 (名称, 满分)，总分 100；全部为确定性规则，可复现。
# 语义：可行性 = 组件可靠度 + 供给 + 风险敞口 + 今日新颖度 + 来源多样性 + 许可证 + 完整度。
SCORE_PARTS = [
    ("组件可靠度", 35),  # 组件来源评分，短板(min)主导；维护滞后组件每个 -5
    ("组件供给", 15),    # 最稀缺槽位的池内候选数（分段计分，避免饱和）
    ("风险敞口", 15),    # 无高风险提示（越狱/凭据/合规/未验证/不可信/alpha/beta/快速迭代）组件占比
    ("今日锚点", 15),    # 组合中今日新发现项目：1 个 5 分 / 2 个 10 / ≥3 个 15
    ("来源多样性", 10),  # 组件来源日期去重数占比（来源分散 → 信号独立）
    ("许可证", 5),       # 宽松许可证（MIT/Apache/BSD/MPL）组件占比
    ("完整度", 5),       # 组合槽位填满比例
]
NEUTRAL_QUALITY = 70  # 来源报告无评分时的中性基线
PERMISSIVE_LICENSES = ("MIT", "Apache-2.0", "BSD-", "MPL-2.0")
HIGH_RISK_WORDS = ("越狱", "jailbreak", "凭据", "credential", "合规",
                   "未验证", "不可信", "alpha", "beta", "快速迭代")


def _license_is_permissive(p):
    m = re.search(r"(MIT|Apache-2\.0|AGPL-3\.0|GPL-3\.0|MPL-2\.0|BSD-[0-9]-Clause)",
                  p["fields"].get("metrics", ""))
    return bool(m and m.group(1).startswith(PERMISSIVE_LICENSES))


def _supply_points(min_supply):
    """最稀缺槽位候选数分段计分：>=100 满分；50-99 得 12-14；20-49 得 6-11；<20 线性 0-6。"""
    if min_supply >= 100:
        return 15
    if min_supply >= 50:
        return 12 + round(3 * (min_supply - 50) / 50)
    if min_supply >= 20:
        return 6 + round(6 * (min_supply - 20) / 30)
    return round(6 * min_supply / 20)


def combo_score(tpl, picks, today_count, min_supply):
    """按确定性规则计算方案综合评分，返回 (总分, 分项明细)。"""
    n = len(picks)
    scores = [p["score"] for p in picks.values() if p.get("score")]
    quality = (sum(scores) / len(scores)) if scores else NEUTRAL_QUALITY
    stalled = sum(1 for p in picks.values() if _maintenance_flag(p))
    # 可靠度短板主导：min 占 5/7、均值占 2/7；维护滞后组件每个再扣 5 分（下限 0）
    reliable = round(35 * (5 * min(scores) + 2 * quality) / (7 * 100)) if scores \
        else round(35 * quality / 100)
    reliable = max(0, reliable - 5 * stalled)
    high_risk = sum(1 for p in picks.values()
                    if any(w in (p["fields"].get("risks") or "").lower()
                           for w in HIGH_RISK_WORDS))
    src_days = len({p["source_date"] for p in picks.values()})
    permissive = sum(1 for p in picks.values() if _license_is_permissive(p))
    parts = [
        ("组件可靠度", reliable, 35),
        ("组件供给", _supply_points(min_supply), 15),
        ("风险敞口", round(15 * (1 - high_risk / n)), 15),
        ("今日锚点", min(15, 5 * today_count), 15),
        ("来源多样性", round(10 * src_days / n), 10),
        ("许可证", round(5 * permissive / n), 5),
        ("完整度", round(5 * n / len(tpl["slots"])), 5),
    ]
    return sum(v for _, v, _ in parts), parts


def pick_best(projects, tag, exclude, today_ids, reuse_counts=None):
    reuse_counts = reuse_counts or {}
    cands = [p for p in projects if p["id"] not in exclude and p["tags"].get(tag, 0) > 0]
    if not cands:
        return None
    # 维护滞后项目整体排在健康项目之后；近期反复入选的组件逐次扣分，
    # 但仍保留今日锚点加权与 Stars 作为稳定的同分决胜项。
    cands.sort(key=lambda p: (
        _maintenance_flag(p),
        -(p["tags"][tag]
          + (TODAY_BONUS if p["id"] in today_ids else 0)
          - RECENT_COMPONENT_REUSE_PENALTY * reuse_counts.get(p["id"], 0)),
        -p["stars"]))
    return cands[0]


def load_recent_component_counts(data_root, run_date, days=7):
    """Count component appearances in recent feasibility reports before run_date."""
    start = date.fromisoformat(run_date) - timedelta(days=days)
    counts = {}
    for path in sorted((data_root / "feasibility").glob("20??-??-??.md")):
        match = DAILY_FILE_RE.match(path.name)
        if not match:
            continue
        source_date = date.fromisoformat(match.group(1))
        if not start <= source_date < date.fromisoformat(run_date):
            continue
        for identity in parse_plan_identities(path.read_text(encoding="utf-8")):
            for repo in identity["repositories"]:
                counts[repo] = counts.get(repo, 0) + 1
    return counts


def select_combo_portfolio(combos, max_count=3, min_score=MIN_COMBO_SCORE,
                           used_repositories=None):
    """Greedily select a non-padded portfolio with component-overlap penalties.

    少量共享组件（≤ OVERLAP_TOLERANCE）不扣分：真正不同的业务方向不应该因为
    一两个公共组件被淘汰；超出容忍度的重叠才按次扣分。
    """
    remaining = list(combos)
    selected = []
    used_repositories = set(used_repositories or ())
    while remaining and len(selected) < max_count:
        ranked = []
        for combo in remaining:
            repositories = {p["id"] for p in combo["picks"].values()}
            overlap = len(repositories & used_repositories)
            penalty = PORTFOLIO_OVERLAP_PENALTY * max(0, overlap - OVERLAP_TOLERANCE)
            adjusted_score = combo["score"] - penalty
            ranked.append((adjusted_score, combo["today_count"], combo["total"],
                           combo["stars"], combo, repositories))
        adjusted_score, _, _, _, best, repositories = max(
            ranked, key=lambda row: row[:4])
        if adjusted_score < min_score:
            break
        chosen = dict(best)
        chosen["selection_score"] = adjusted_score
        selected.append(chosen)
        used_repositories.update(repositories)
        remaining.remove(best)
    return selected


def select_tracked_portfolio(combos, min_score=MIN_COMBO_SCORE,
                             max_mature=MAX_MATURE_PLANS,
                             max_exploratory=MAX_EXPLORATORY_PLANS):
    """双轨选择：最多 1 个成熟方向 + 最多 2 个探索方向，不足不补齐。

    成熟方向先选，探索方向在剩余组件上选；若探索方向与已选成熟方向属于同一
    业务身份（customer + problem + expected_outcome 相同），则跳过——同一业务
    方向换名称/换组件不得在同一份报告里出现两次。
    """
    mature_pool = [c for c in combos if c.get("track") == TRACK_MATURE]
    exploratory_pool = [c for c in combos if c.get("track") == TRACK_EXPLORATORY]
    selected = select_combo_portfolio(mature_pool, max_count=max_mature,
                                      min_score=min_score)
    used = {p["id"] for combo in selected for p in combo["picks"].values()}
    taken = {key for key in (business_key(c.get("business")) for c in selected) if key}
    exploratory_pool = [c for c in exploratory_pool
                        if business_key(c.get("business")) not in taken]
    selected += select_combo_portfolio(exploratory_pool, max_count=max_exploratory,
                                       min_score=min_score, used_repositories=used)
    return selected


def load_recent_families(data_root, run_date, n=2):
    """读取 run_date 之前最近 n 份可行性报告，返回同时出现的方案身份（family → 展示名）。

    用于'同一方案最多连续出现两天'的新鲜度限制：同一 family 同时出现在最近两份
    报告里说明已连续出现两天，第三天应跳过。身份优先取报告内的 `**方案身份**` 行，
    旧报告没有该行时按标题名回退（与 parse_plan_identities 一致）。
    """
    files = []
    for f in sorted((data_root / "feasibility").glob("20??-??-??.md"), reverse=True):
        m = DAILY_FILE_RE.match(f.name)
        if m and m.group(1) < run_date:
            files.append(f)
        if len(files) >= n:
            break
    if len(files) < n:
        return {}
    seen_by_file = []
    for f in files:
        seen = {}
        for identity in parse_plan_identities(f.read_text(encoding="utf-8")):
            seen.setdefault(identity["family"], identity["name"])
        seen_by_file.append(seen)
    blocked = set.intersection(*(set(seen) for seen in seen_by_file))
    # 展示名取较新一份的标题，报告简介里仍能以人话说明跳过了哪个方案
    return {family: seen_by_file[0][family] for family in blocked}


def top_tag(p):
    """项目能力面最高分的标签；同分时取 TAG_RULES 中靠前的标签，保证确定性。"""
    order = {t: i for i, t in enumerate(TAG_RULES)}
    return max(p["tags"].items(), key=lambda kv: (kv[1], -order.get(kv[0], 99)))[0]


# 组合命名（展示层）：名称 = <场景限定> · <差异化能力> · <业务主体>，三段均来自能力面，
# 不嵌入项目名与日期；业务身份（plan_family）另由 customer + problem + expected_outcome 派生，
# 因此调整措辞不会打断跨天去重，换技术词也不会伪装成新业务方向。
ANCHOR_SCENE = {
    "local": "本地优先",
    "comm": "团队协作",
    "security": "安全合规",
    "document": "文档智能",
    "codeintel": "研发效能",
    "design": "设计辅助",
}
ANCHOR_CAPABILITY = {
    "rag": "知识增强",
    "gateway": "多模型",
    "memory": "长期记忆",
    "sandbox": "隔离执行",
    "observability": "可观测",
    "agent": "多 Agent",
}
ANCHOR_CORE_NOUN = {
    "agent": "Agent 工作台",
    "security": "安全 Agent 平台",
    "document": "文档处理管线",
    "codeintel": "代码智能平台",
    "rag": "知识助手",
    "comm": "协作控制面",
    "local": "本地 AI 工作台",
    "observability": "评测观测平台",
    "gateway": "模型接入平台",
    "memory": "记忆服务",
    "sandbox": "执行沙箱服务",
    "design": "设计协作工具",
}
# 业务主体优先取更偏业务的能力面；场景限定优先取更偏形态的能力面；
# 差异化能力取池内覆盖率最低（最能区分本次组合）的能力面。
ANCHOR_CORE_PRIORITY = ("agent", "security", "document", "codeintel", "rag",
                        "comm", "local", "observability", "gateway", "memory",
                        "sandbox", "design")
ANCHOR_SCENE_PRIORITY = ("local", "comm", "security", "document", "codeintel",
                         "design")
# 能力面与固定模板完全一致时，业务身份仍由模板 slug 表示（历史周报/雷达按 slug 去重）。


def anchor_face_segments(faces, supply=None):
    """把能力面拆成三段：业务主体 / 场景限定 / 差异化能力。

    业务主体取最偏业务的能力面；场景限定取最偏形态的能力面；差异化能力取池内
    覆盖率最低（最能区分本次组合）的能力面。名称与业务语义共用这一拆分，保证
    “标题里写的”和“业务语义里记的”是同一个方向。
    """
    ranked = [tag for tag in ANCHOR_CORE_PRIORITY if tag in faces]
    if not ranked:
        return None, None, None
    core_tag = ranked[0]
    scene_tag = next((tag for tag in ANCHOR_SCENE_PRIORITY
                      if tag in faces and tag != core_tag), None)
    cap_tags = [tag for tag in ranked[1:]
                if tag != scene_tag and tag in ANCHOR_CAPABILITY]
    if not cap_tags:
        cap_tag = None
    elif supply:
        cap_tag = min(cap_tags, key=lambda tag: (supply.get(tag, 0),
                                                 ANCHOR_CORE_PRIORITY.index(tag)))
    else:
        cap_tag = cap_tags[0]
    return core_tag, scene_tag, cap_tag


def anchor_plan_name(faces, supply=None):
    """按能力面拼三段式业务名：<场景限定> · <差异化能力> · <业务主体>。

    名称只是展示层：业务身份（plan_family）由 customer + problem + expected_outcome
    派生，改措辞、换技术词或换组件都不会产生新的业务方向。
    """
    core_tag, scene_tag, cap_tag = anchor_face_segments(faces, supply)
    if core_tag is None:
        return "多能力面组合方案"
    segments = []
    if scene_tag:
        segments.append(ANCHOR_SCENE[scene_tag])
    if cap_tag:
        segments.append(ANCHOR_CAPABILITY[cap_tag])
    segments.append(ANCHOR_CORE_NOUN[core_tag])
    return " · ".join(segments)


# 业务语义层：track / customer / problem / workflow / delivery / expected_outcome。
# 业务身份由 customer + problem + expected_outcome 三元组派生，与技术能力面、
# 标题措辞、组件集合都无关；成熟方向继续沿用模板 slug（周报/雷达按 slug 去重，
# 保持历史兼容），探索方向用业务三元组哈希。
def _mature_business(customer_id, customer, problem_id, problem, outcome_id,
                     expected_outcome, workflow, delivery):
    """成熟方向的业务语义：模板方向已核对池内组件供给，证据状态固定。"""
    return {
        "customer_id": customer_id, "customer": customer,
        "problem_id": problem_id, "problem": problem,
        "outcome_id": outcome_id, "expected_outcome": expected_outcome,
        "workflow": workflow, "delivery": delivery,
        "evidence_status": EVIDENCE_VERIFIED,
    }


TEMPLATE_BUSINESS = {
    "企业内部知识助手（私有化 RAG × Agent）": _mature_business(
        "privacy-bound-enterprises", "数据敏感的中大型企业（法律/金融/制造/医疗）",
        "untraceable-internal-answers", "文档散落在各部门，问答没有出处，动手的事还要人盯",
        "traceable-answers-and-approval", "带出处的问答与可审批的执行闭环",
        "私有化知识库入库 → 带出处问答 → 人工审批后执行", "企业内网自托管交付"),
    "可审计的 Agent 开发/交付平台（CI 化 Agent 流水线）": _mature_business(
        "agent-shipping-teams", "已在使用 coding agent 的研发团队与平台工程组",
        "unaccountable-agent-runs", "Agent 跑挂了无法恢复，花了多少钱、有没有越权也说不清",
        "auditable-agent-pipeline", "像 CI 一样可恢复、可审计的 Agent 交付流水线",
        "沙箱内执行 → 留痕与审计报告 → 人工批准后写仓库", "团队内自建流水线，接入现有 CI"),
    "本地优先个人 AI 工作台": _mature_business(
        "privacy-first-individuals", "重视隐私的个人开发者、知识工作者与小型团队",
        "cloud-bound-personal-tools", "个人数据留在云端、模型换不了、记忆导不出来",
        "on-device-ai-workspace", "数据不出本机、模型可切换的个人 AI 工作台",
        "本地记忆写入 → Agent 读取 → 输出压缩与导出", "桌面端本地安装，无云依赖"),
    "多 Agent 协作控制面（团队级）": _mature_business(
        "multi-agent-teams", "已同时使用多个 coding agent 的团队",
        "scattered-agent-sessions", "会话、审批、花费散在各工具里，没人说得清谁在跑什么",
        "unified-agent-control-plane", "会话、审批、审计、成本收在一处的控制面",
        "接一个 Agent 宿主 + 一个协作渠道 → 审批与打断 → 审计日志", "团队内部署，接入现有 IM"),
    "文档/知识处理管线（入库前处理）": _mature_business(
        "rag-product-teams", "RAG/搜索/文档产品团队与自建知识库的企业",
        "dirty-ingestion-input", "入库文档格式乱、质量差，召回与引用质量不可控",
        "clean-ingestion-pipeline", "解析-转换-质检一条管道，入库前把脏数据挡掉",
        "文档 → Markdown → 索引 → 评测报告", "按管线组件交付，接进现有入库流程"),
    "安全 Agent 平台（扫描-修复-验证）": _mature_business(
        "security-teams", "企业安全团队与 DevSecOps 平台组",
        "unverified-security-fixes", "扫描只报问题，修复是否真的修好没人独立验证",
        "evidence-backed-remediation", "扫描-修复建议-独立验证三步都留证据",
        "授权靶场扫描 → 修复建议 → 独立验证与证据归档", "私有部署，接进现有安全流程"),
    "代码审查与重构平台（仓库级）": _mature_business(
        "legacy-code-teams", "中型以上研发团队与需要长期维护老代码库的团队",
        "unreviewable-large-changes", "AI 写的改动越来越大，改得对不对、有没有破坏别处靠人盯",
        "evidence-backed-refactor", "仓库级理解 + 回归证据支撑的重构交付",
        "理解仓库 → 提改动（PR 草稿）→ 跑回归对比 → 人工批准", "贴着仓库交付，进入现有研发流程"),
    "开源依赖与许可证合规扫描（供应链）": _mature_business(
        "audited-delivery-teams", "要过审计的研发团队与企业安全/合规岗",
        "unverified-supply-chain", "依赖变动后许可证与漏洞影响说不清",
        "auditable-dependency-report", "可给人看、可复测的依赖与许可证审计报告",
        "解析依赖 → 标注许可证与漏洞 → 受影响调用路径 → 报告", "私有部署，按审计周期出报告"),
    "团队通知聚合与消息自动化（IM 接入）": _mature_business(
        "im-collaborating-teams", "值班运维、客服支持团队与靠 IM 协作的中小团队",
        "noisy-message-channels", "消息渠道多，漏看和重复处理反复发生",
        "routed-messages-with-receipts", "按规则分流、摘要并留下处理回执的消息自动化",
        "接一个渠道 → 自动摘要与分流 → 升级规则与回执", "接入现有 IM，不新增工作台"),
    "设计稿到组件代码交付管线（设计系统）": _mature_business(
        "design-system-teams", "有设计系统的产品团队与前端平台组",
        "design-implementation-drift", "设计稿与组件库对不上，还原全靠人肉",
        "design-system-aligned-components", "能进设计系统、带验收记录的组件改动",
        "设计稿 → 组件改动 → 截图对比与回归验收", "接进现有设计系统与验收流程"),
    "垂直知识库检索服务（引用溯源）": _mature_business(
        "domain-experts", "法律/医疗/金融等专业领域的产品团队",
        "untrusted-domain-answers", "通用模型答专业问题不可信，答案没有出处",
        "citation-backed-domain-search", "带引用出处、可评测的垂直检索服务",
        "领域语料解析 → 索引 → 带引用问答 → 评测集打分", "按检索服务交付，可私有化"),
}

# 探索方向的业务语义表：每个能力面一套“客户问题 + 预期结果 + 业务流”，
# 全部是待验证假设，不得写成市场需求已成立。
BUSINESS_CUSTOMERS = {
    "agent": {"id": "agent-adopting-teams", "text": "想把多步骤任务交给 Agent 的团队"},
    "memory": {"id": "context-heavy-users", "text": "需要长期上下文的知识工作者"},
    "rag": {"id": "knowledge-seekers", "text": "要反复查资料并核对出处的知识工作者"},
    "sandbox": {"id": "untrusted-runner-teams", "text": "需要隔离执行不可信任务的团队"},
    "observability": {"id": "agent-ops-teams", "text": "要对 Agent 质量与花费负责的团队"},
    "gateway": {"id": "multi-model-teams", "text": "同时接多个模型供应商的团队"},
    "codeintel": {"id": "legacy-code-teams", "text": "需要长期维护老代码库的研发团队"},
    "design": {"id": "design-system-teams", "text": "有设计系统的产品团队"},
    "security": {"id": "audited-teams", "text": "有合规与审计要求的团队"},
    "document": {"id": "document-heavy-teams", "text": "文档密集的业务团队"},
    "local": {"id": "privacy-first-users", "text": "重视数据留在本机的个人与小型团队"},
    "comm": {"id": "im-collaborating-teams", "text": "靠 IM 协作的中小团队"},
}
BUSINESS_PROBLEMS = {
    "agent": {"problem_id": "unrepeatable-workflows",
              "problem": "多步骤任务串不起来、也复现不了",
              "outcome_id": "repeatable-workflows",
              "expected_outcome": "长任务变成可复用、可审批的流程",
              "workflow": "把流程拆成可审批的步骤 → 跑通一条 → 记录产出"},
    "memory": {"problem_id": "forgotten-context",
               "problem": "会话与偏好留不住，每次都要重讲一遍",
               "outcome_id": "persistent-context",
               "expected_outcome": "上下文能长期复用",
               "workflow": "接入上下文存储 → 记录与召回 → 人工核对准确性"},
    "rag": {"problem_id": "untraceable-answers",
            "problem": "资料散落各处，答案没有出处可查",
            "outcome_id": "traceable-answers",
            "expected_outcome": "每条结论都能指回来源",
            "workflow": "自有语料入库 → 带引用检索 → 引用核对"},
    "sandbox": {"problem_id": "unsafe-execution",
                "problem": "不可信任务没有隔离执行环境",
                "outcome_id": "isolated-execution",
                "expected_outcome": "不可信任务在隔离环境里跑",
                "workflow": "隔离环境跑任务 → 记录资源与网络边界 → 复测"},
    "observability": {"problem_id": "unmeasured-quality",
                      "problem": "跑起来的质量与花费无法评测",
                      "outcome_id": "measured-quality",
                      "expected_outcome": "质量与花费可评测、可回归",
                      "workflow": "记录一次真实任务 → 建评测集 → 回归对比"},
    "gateway": {"problem_id": "uncontrolled-model-access",
                "problem": "模型与供应商多，接入方式和花费不可控",
                "outcome_id": "governed-model-access",
                "expected_outcome": "接入与花费可统一管理",
                "workflow": "统一接入层 → 路由与限额 → 记录用量"},
    "codeintel": {"problem_id": "unknown-codebase",
                  "problem": "老代码库没人敢动",
                  "outcome_id": "understood-codebase",
                  "expected_outcome": "仓库级理解与回归证据",
                  "workflow": "解析仓库与调用链 → 标注风险点 → 小步替换并回归"},
    "design": {"problem_id": "design-implementation-drift",
               "problem": "设计稿与组件库对不上",
               "outcome_id": "aligned-components",
               "expected_outcome": "设计与组件库对齐",
               "workflow": "设计稿对齐组件库 → 生成组件改动 → 截图验收"},
    "security": {"problem_id": "unverified-changes",
                 "problem": "改动与依赖无法验证来源",
                 "outcome_id": "verified-changes",
                 "expected_outcome": "改动有证据可复核",
                 "workflow": "列出改动与依赖 → 标注影响面 → 留证复核"},
    "document": {"problem_id": "dirty-input",
                 "problem": "入库文档格式乱、质量差",
                 "outcome_id": "clean-input",
                 "expected_outcome": "入库前清洗与质检",
                 "workflow": "文档入库前解析 → 质检 → 输出清洗结果"},
    "local": {"problem_id": "cloud-bound-data",
              "problem": "数据不想上云，但工具都在云上",
              "outcome_id": "on-device-data",
              "expected_outcome": "数据留在本机也能用",
              "workflow": "本地跑通一条链路 → 记录完全离线的能力边界"},
    "comm": {"problem_id": "noisy-channels",
             "problem": "消息渠道多，漏看与重复处理",
             "outcome_id": "routed-messages",
             "expected_outcome": "消息按规则分流与回执",
             "workflow": "接一个渠道 → 自动分流与摘要 → 记录回执"},
}
BUSINESS_DELIVERY = {
    "local": {"id": "self-hosted", "text": "本地/自托管交付，数据不出本机"},
    "comm": {"id": "inside-im", "text": "接入现有 IM，不新增工作台"},
    "security": {"id": "private-with-evidence", "text": "私有部署 + 审计证据交付"},
    "document": {"id": "pipeline-service", "text": "按管线交付，不改变现有文档入口"},
    "codeintel": {"id": "repo-side", "text": "贴着仓库交付，进入现有研发流程"},
    "design": {"id": "design-system-side", "text": "接进现有设计系统与验收流程"},
}
BUSINESS_CUSTOMER_FALLBACK = {"id": "trial-users",
                              "text": "想第一时间试用今日新发现项目的个人开发者与研究型小团队"}
BUSINESS_DELIVERY_FALLBACK = {"id": "trial-first", "text": "先小范围试用，再决定交付形态"}


def business_key(business):
    """业务方向键：客户 + 客户问题 + 预期结果；缺字段时返回 None（不参与去重）。"""
    business = business or {}
    ids = (business.get("customer_id"), business.get("problem_id"),
           business.get("outcome_id"))
    return ids if all(ids) else None


def business_family(customer_id, problem_id, outcome_id):
    """业务身份：由业务三元组派生，确定性且与措辞、技术词、组件无关。"""
    return "biz-" + _stable_digest("\n".join((customer_id, problem_id, outcome_id)))


def exploratory_business(faces, supply=None):
    """探索方向的业务语义：客户取场景面，客户问题与预期结果取差异化能力面。

    返回的语义是待验证假设（evidence_status=to-validate），不代表需求已成立。
    """
    core_tag, scene_tag, cap_tag = anchor_face_segments(faces, supply)
    primary = cap_tag or core_tag or "agent"
    problem = BUSINESS_PROBLEMS[primary]
    customer = BUSINESS_CUSTOMERS.get(scene_tag) or BUSINESS_CUSTOMERS.get(core_tag, {})
    delivery = BUSINESS_DELIVERY.get(scene_tag) or BUSINESS_DELIVERY.get(core_tag, {})
    return {
        "customer_id": customer.get("id", BUSINESS_CUSTOMER_FALLBACK["id"]),
        "customer": customer.get("text", BUSINESS_CUSTOMER_FALLBACK["text"]),
        "problem_id": problem["problem_id"],
        "problem": problem["problem"],
        "outcome_id": problem["outcome_id"],
        "expected_outcome": problem["expected_outcome"],
        "workflow": problem["workflow"],
        "delivery_id": delivery.get("id", BUSINESS_DELIVERY_FALLBACK["id"]),
        "delivery": delivery.get("text", BUSINESS_DELIVERY_FALLBACK["text"]),
        "evidence_status": EVIDENCE_TO_VALIDATE,
    }


def _combo_role(p):
    """角色名用项目真实定位（tagline 首句），避免能力面标签与项目错配。"""
    tagline = (p["fields"].get("tagline") or "").strip()
    if tagline:
        role = first_sentence(tagline, 60)
        if role and role != p["repo"]:
            return role
    return COMBO_ROLES.get(top_tag(p), top_tag(p))


def build_exploratory_combos(projects, today_projects, today_ids, blocked_families=None,
                            limit=MAX_EXPLORATORY_PLANS):
    """生成探索方向（最多 limit 个）：1 个今日锚点 + ≥2 个互补组件，全部来自今日日报。

    方向以"最能区分的能力面"为种子（池内覆盖率最低优先），每个种子给出一个业务
    语义（客户问题 + 预期结果）；同一业务语义只保留评分最高的一个，避免同一方向
    换标题重复出现。探索方向一律标注待验证。
    """
    blocked_families = blocked_families or {}
    anchors = [p for p in today_projects if p["tags"]]
    if len(anchors) < 3:
        return []              # 需要 1 个锚点 + ≥2 个互补组件
    anchors.sort(key=lambda p: (p["stars"], p["id"]), reverse=True)
    supply = {t: sum(1 for p in projects if t in p["tags"]) for t in TAG_RULES}
    seed_faces = sorted({top_tag(p) for p in anchors},
                        key=lambda t: (supply.get(t, 0), ANCHOR_CORE_PRIORITY.index(t)))
    candidates = []
    seen_keys = set()
    for seed_face in seed_faces[:6]:
        combo = _exploratory_combo(projects, anchors, seed_face, today_ids, supply)
        if combo is None or combo["plan_family"] in blocked_families:
            continue
        key = business_key(combo["business"])
        if key and key in seen_keys:
            continue
        if key:
            seen_keys.add(key)
        candidates.append(combo)
    # 稳定排序：评分 → 今日锚点数 → 组件数 → Stars → 名称，全部为确定性字段
    candidates.sort(key=lambda c: (c["score"], c["today_count"], c["total"], c["stars"],
                                c["name"]), reverse=True)
    return candidates[:limit]


def _exploratory_combo(projects, anchors, seed_face, today_ids, supply):
    """按一个能力面种子拼一个探索方向：种子锚点 + 尽可能互补的今日组件。"""
    seed = next(p for p in anchors if top_tag(p) == seed_face)
    picks = {COMBO_ROLES[seed_face]: seed}
    covered = {seed_face}
    used_ids = {seed["id"]}
    for p in anchors:          # anchors 已按 Stars + id 排序，结果确定
        tag = top_tag(p)
        if tag in covered or p["id"] in used_ids:
            continue
        role = COMBO_ROLES[tag]
        while role in picks:
            role += "（二）"
        picks[role] = p
        covered.add(tag)
        used_ids.add(p["id"])
        if len(picks) >= 5:
            break
    if len(picks) < 3:
        return None            # 必须有 ≥2 个互补组件
    roles = {}
    for role, p in picks.items():
        candidate = _combo_role(p)
        while candidate in roles.values():
            candidate += "（二）"
        roles[role] = candidate
    picks = {roles[role]: p for role, p in picks.items()}
    slot_tags = [top_tag(p) for p in picks.values()]
    faces = frozenset(slot_tags)
    supply_by_face = {t: sum(1 for p in projects if t in p["tags"]) for t in set(slot_tags)}
    min_supply = min(supply_by_face.values())
    today_count = len(picks)
    business = exploratory_business(faces, supply)
    name = anchor_plan_name(faces, supply)
    score, score_parts = combo_score(
        {"slots": [(t, r) for r, t in zip(picks.keys(), slot_tags)]},
        picks, today_count, min_supply)
    roles_text = "、".join("{}（`{}`）".format(r, p["repo"]) for r, p in picks.items())
    combo = {
        "score": score,
        "score_parts": score_parts,
        "name": name,
        "origin": "anchor",
        "track": TRACK_EXPLORATORY,
        "business": business,
        "pitch": "按'{}'方向，把今日新发现的 {} 个项目先拼成可试用组合：{}。"
                  "方向与需求都待验证，先各自试用、记录产出，再判断能否打通。".format(
                      name, len(picks), roles_text),
        "target": business["customer"],
        "market": "（待验证假设）客户问题：{}；预期结果：{}。今日 {} 个锚点分属 {} 等能力面，"
                   "池中对应候选 {} 个——这只说明组件可拼装，不代表市场需求成立；"
                   "先小范围试用再判断。".format(
                       business["problem"], business["expected_outcome"], len(picks),
                       "、".join(TAG_CN[t] for t in slot_tags if t in TAG_CN), min_supply),
        "differentiation": "完全由今日新发现驱动，组件全部来自今日日报；与固定模板方向不同，"
                           "属于待验证的探索方向。",
        "rationale": "全部组件来自今日日报，能力面尽量互补（{} 个）；该方向未经过市场验证，"
                      "先按业务语义里的客户问题做小范围试用。".format(len(faces)),
        "mvp": "先分别试用各组件并记录可用产出，再打通 {} 之间的最小数据流或协作流；"
               "其余按试用反馈取舍。".format(
                   "、".join("`{}`".format(p["repo"]) for p in list(picks.values())[:3])),
        "picks": picks,
        "slot_supply": supply_by_face,
        "min_supply": min_supply,
        "total": len(picks),
        "today_count": today_count,
        "stars": sum(p["stars"] for p in picks.values()),
    }
    repositories = [p["id"] for p in picks.values()]
    combo["plan_family"] = business_family(business["customer_id"], business["problem_id"],
                                           business["outcome_id"])
    combo["variant"] = plan_variant(repositories)
    return combo


def build_combos(projects, today_ids=None, blocked_families=None, reuse_counts=None):
    """成熟方向：先按固定模板确定业务方向，再为各方向分配组件。

    与旧版“各模板先抢同一个全局最优组件、再在组合阶段互相扣分”不同：组件按方向
    顺序分配，优先避开已被前面方向占用的仓库，只有没有替代品时才允许复用，
    因此不同方向不会都落在同一个底座项目上。
    """
    today_ids = today_ids or set()
    blocked_families = blocked_families or {}
    reuse_counts = reuse_counts or {}
    combos = []
    allocated = set()
    for tpl in TEMPLATES:
        family = plan_family(tpl["name"])
        if family in blocked_families:
            continue  # 新鲜度规则：同一方案最多连续出现两天，第三天跳过
        picks = {}
        used = set()
        for tag, role in tpl["slots"]:
            p = pick_best(projects, tag, allocated | used, today_ids, reuse_counts)
            if p is None:      # 允许复用：方向不应该因为组件被占用而消失
                p = pick_best(projects, tag, used, today_ids, reuse_counts)
            if p is None:
                continue
            picks[role] = p
            used.add(p["id"])
        if len(picks) < 2 or len(used) < 2:
            continue
        slot_tags = {s[0] for s in tpl["slots"]}
        # 每个槽位的候选项目数：直接回答"每个位置有多少现成组件可选"
        slot_supply = {tag: sum(1 for p in projects if tag in p["tags"])
                       for tag, _ in tpl["slots"]}
        min_supply = min(slot_supply.values())
        today_count = sum(1 for p in picks.values() if p["id"] in today_ids)
        if today_count == 0:
            continue  # 以今日发现为主：组合必须包含至少一个今日锚点项目
        allocated.update(used)   # 已被本方向占用的仓库，后续方向优先避开
        # 综合评分：分项按确定性规则计算，总分 = 分项之和，保证明细可加总。
        score, score_parts = combo_score(tpl, picks, today_count, min_supply)
        combo = {
            "score": score,
            "score_parts": score_parts,
            "origin": "template",
            "track": TRACK_MATURE,
            "business": dict(TEMPLATE_BUSINESS[tpl["name"]]),
            "name": tpl["name"],
            "pitch": tpl["pitch"],
            "target": tpl["target"],
            "market": tpl["market"],
            "differentiation": tpl["differentiation"],
            "rationale": tpl["rationale"],
            "mvp": tpl["mvp"],
            "picks": picks,
            "slot_supply": slot_supply,
            "min_supply": min_supply,
            "total": len(picks),
            "today_count": today_count,
            "stars": sum(p["stars"] for p in picks.values()),
        }
        repositories = [p["id"] for p in picks.values()]
        combo["plan_family"] = family
        combo["variant"] = plan_variant(repositories)
        combos.append(combo)
    # 保持历史可复现：组合排序维持原规则（今日锚点多者优先，其次组件数与 Stars）；
    # 评分不参与排序，仅作展示与行动建议的推荐依据。
    combos.sort(key=lambda c: (c["today_count"], c["total"], c["stars"]), reverse=True)
    return combos


def build_single_angles(projects):
    rows = []
    for p in sorted(projects, key=lambda p: p["stars"], reverse=True):
        if not p["tags"]:
            continue
        top = max(p["tags"].items(), key=lambda kv: kv[1])[0]
        evidence = (p["fields"].get("value") or p["fields"].get("reason")
                    or p["fields"].get("tagline") or "")
        rows.append((p, top, _clean_evidence(evidence)))
    return rows[:8]


def llm_enhance(projects, combos, no_llm):
    if no_llm:
        return None
    key = os.environ.get("OPPORTUNITY_LLM_API_KEY") or os.environ.get("OPENAI_API_KEY")
    if not key:
        return None
    base = os.environ.get("OPPORTUNITY_LLM_BASE_URL", "https://api.openai.com/v1").rstrip("/")
    model = os.environ.get("OPPORTUNITY_LLM_MODEL", "gpt-4o-mini")
    compact = [{
        "repo": p["repo"],
        "source": p["source_date"],
        "kind": p["kind"] or "",
        "tagline": clip(p["fields"].get("tagline", ""), 120),
        "stack": clip(p["fields"].get("stack", ""), 160),
        "value": clip(p["fields"].get("value") or p["fields"].get("reason") or "", 140),
        "risks": clip(p["fields"].get("risks") or "", 120),
    } for p in projects]
    combo_text = "\n".join(
        f"- {c['name']}: " + " + ".join(f"`{p['repo']}`（{role}）"
                                        for role, p in c["picks"].items())
        for c in combos
    )
    prompt = (
        f"你是开源项目商业化分析师。以下是最近 90 天发现的 {len(projects)} 个真实开源项目"
        "（JSON：repo/来源/定位/技术栈/价值/风险）：\n"
        + json.dumps(compact, ensure_ascii=False, indent=1)
        + "\n我已用确定性规则给出组合草案：\n" + combo_text
        + "\n请输出两部分：\n"
        "1) ## 可行业务方向：3-5 个（目标客户、最小可行范围、为什么现在可行），只使用上面给出的项目；\n"
        "2) ## 多项目组合开发方案：3-5 个（组合清单、各项目分工、MVP 边界、主要风险）。\n"
        "要求：不得虚构不存在的项目；不要重复我已列出的组合（除非补充新理由）；"
        "用中文，输出 Markdown。"
    )
    body = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.4,
    }
    req = urllib.request.Request(
        f"{base}/chat/completions",
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {key}"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=150) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return data["choices"][0]["message"]["content"]
    except (urllib.error.URLError, OSError, KeyError, IndexError, json.JSONDecodeError) as exc:
        print(f"警告: LLM 增强失败，跳过（{exc}）", file=sys.stderr)
        return None


def track_label(combo):
    """业务轨道标签：成熟方向（组件供给已核对）/ 探索方向（待验证）。"""
    if combo.get("track") == TRACK_MATURE:
        return "成熟方向（组件供给已核对）"
    if combo.get("track") == TRACK_EXPLORATORY:
        return "探索方向（待验证）"
    return "未标注轨道"


def business_semantics_line(combo):
    """机器可读的业务语义行（`key=value` 以 · 分隔），供解析、去重与审计使用。"""
    business = combo.get("business") or {}
    fields = (
        ("track", combo.get("track")),
        ("customer", business.get("customer")),
        ("problem", business.get("problem")),
        ("workflow", business.get("workflow")),
        ("delivery", business.get("delivery")),
        ("expected_outcome", business.get("expected_outcome")),
        ("evidence_status", business.get("evidence_status")),
    )
    return " · ".join("`{}={}`".format(key, value) for key, value in fields if value)


def render(projects, today_projects, combos, singles, run_date, cutoff,
           anchor_date, n_daily_files, n_weekly_files, llm_text, blocked=None,
           no_plan_reason=None):
    n = len(projects)
    today_ids = {p["id"] for p in today_projects}
    L = []
    A = L.append
    A(f"# GitHub 项目组合可行性方案｜{run_date}")
    A("")
    A("> 由定时任务自动生成（`scripts/opportunity_analysis.py`）：以今日日报项目为锚点、"
      "结合最近 90 天项目池拼出的多项目组合可行性研究草稿；不包含代码，不是公开结论，"
      "落地前需逐个组件复核。")
    A("> 输入：今日锚点 `daily/{}.md`（{} 个项目）；组合池：最近 90 天（{} ~ {}）"
      "{} 个唯一项目（日报 {} 份 / 周报 {} 份）。方案 1-3 个：最多 1 个成熟方向"
      "（固定模板命中）+ 最多 2 个探索方向（今日锚点拼接，待验证）；"
      "没有合格探索方向时少于 3 个。".format(
          anchor_date, len(today_projects), cutoff, run_date,
          n, n_daily_files, n_weekly_files))
    A("> 评分（0-100，确定性规则，用于方案横向比较，不代表商业结论）："
      "组件可靠度 35 · 组件供给 15 · 风险敞口 15 · 今日锚点 15 · "
      "来源多样性 10 · 许可证 5 · 完整度 5；档位：≥85 高，70-84 中，<70 低。")
    A("> 验证路径（固定）：每个组件按来源报告的'上手建议/真实风险'复核"
      "（固定版本、隔离环境、自有数据复测）。")
    if blocked:
        A("> 新鲜度规则：以下方案已连续出现两天，本轮跳过（同一方案最多连续两天）：{}。".format(
            "、".join(sorted(blocked.values()))))
    if any(c.get("track") == TRACK_EXPLORATORY for c in combos):
        A("> 探索方向：由今日锚点直接拼接，组件全部来自今日日报；已标注为待验证，"
          "只说明组件可拼装，不代表市场需求成立。")
    A("")
    A("## 可行性方案")
    A("")
    if not combos:
        A("（本轮无合格方案：{}。）".format(
            no_plan_reason or "成熟方向与探索方向都未达到合格线，不构成组合产出"))
        if blocked:
            A("")
            A("（被新鲜度规则跳过：{}。）".format("、".join(sorted(blocked.values()))))
    for i, c in enumerate(combos, 1):
        A("### {}. {}（组合 {} 个项目，今日锚点 {} 个）".format(
            i, c["name"], c["total"], c["today_count"]))
        A("")
        parts_str = " · ".join("{} {}/{}".format(k, v, w) for k, v, w in c["score_parts"])
        grade = "高" if c["score"] >= 85 else ("中" if c["score"] >= 70 else "低")
        A("**方案评分**：**{}/100（{}）**（{}）".format(c["score"], grade, parts_str))
        A("")
        A("**方案身份**：`plan_family={}` · `variant={}`".format(
            c["plan_family"], c["variant"]))
        A("")
        A("**业务轨道**：{}".format(track_label(c)))
        A("")
        semantics = business_semantics_line(c)
        if semantics:
            A("**业务语义**：{}".format(semantics))
            A("")
        if c.get("track") == TRACK_EXPLORATORY:
            A("**待验证说明**：组件可拼装 ≠ 需求成立；本方向需先小范围试用并记录产出，"
              "再判断是否值得投入。")
            A("")
        A("**业务定位**：{}".format(c["pitch"]))
        A("")
        A("**目标客户**：{}".format(c["target"]))
        A("")
        A("**市场机会**：{}".format(c["market"]))
        A("")
        today_picks = ["`{}`".format(p["repo"]) for p in c["picks"].values()
                       if p["id"] in today_ids]
        supply_str = " · ".join("{} {}".format(t, c2)
                                 for t, c2 in c["slot_supply"].items())
        A("**可行性依据**：{} 本组合含今日发现项目 {} 个（{}）；"
          "池中各能力面候选充足（{}），最稀缺槽位也有 {} 个候选。".format(
              c["rationale"], c["today_count"], "、".join(today_picks),
              supply_str, c["min_supply"]))
        A("")
        A("**组合方案**：")
        A("")
        A("| 角色 | 项目 | 入选理由 |")
        A("|---|---|---|")
        for role, p in c["picks"].items():
            basis = (p["fields"].get("value") or p["fields"].get("reason")
                     or p["fields"].get("tagline") or "")
            A("| {} | [`{}`]({}) | {} |".format(
                role, p["repo"], p["url"],
                esc(first_sentence(_clean_evidence(basis), 72))))
        A("")
        A("**差异化**：{}".format(c["differentiation"]))
        A("")
        A("**MVP 范围（做什么，不含代码）**：{}".format(c["mvp"]))
        A("")
        risks = []
        for role, p in c["picks"].items():
            r = (p["fields"].get("risks") or "").strip()
            if r:
                risks.append("- `{}`（{}）：{}".format(p["repo"], role, first_sentence(r, 100)))
        if risks:
            A("**主要风险（来源报告）**：")
            A("")
            A("\n".join(risks))
        A("")
    A("## 单点项目机会（供参考）")
    A("")
    angle_count: dict[str, int] = {}
    for p, top, evidence in singles:
        idx = angle_count.get(top, 0)
        angle_count[top] = idx + 1
        variants = TAG_ANGLE[top]
        angle = variants[idx % len(variants)] if isinstance(variants, list) else variants
        A("- `{}`（`#{}`）→ {}。依据：{}".format(
            p["repo"], top, angle, first_sentence(evidence, 100)))
    A("")
    A("## 行动建议")
    A("")
    if combos:
        top = max(combos, key=lambda c: c["score"])
        A("1. 优先推进评分最高的组合：「{}」（{} / 100，{} 组件，今日锚点 {} 个）。".format(
            top["name"], top["score"], top["total"], top["today_count"]))
    A("2. 每个组合先核验 2-3 个核心组件：许可证、维护状态、来源报告中的真实风险。")
    A("3. 投入开发前，先用目标客户访谈或小范围试用验证需求假设，再决定组合取舍。")
    A("4. 本方案由定时任务自动生成并保留历史；每周新增周报与日报后重跑，信号会自动更新。")
    A("")
    if llm_text:
        A("## LLM 增强视角（可选配置）")
        A("")
        A("> 以下内容由配置的模型生成，未逐项核验，仅供扩展思路。")
        A("")
        A(llm_text.strip())
        A("")
    return "\n".join(L)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--date", default=date.today().isoformat(),
                    help="运行日期 YYYY-MM-DD（默认今天）")
    ap.add_argument("--data-root", type=Path, default=DEFAULT_DATA_ROOT)
    ap.add_argument("--output", type=Path, default=None,
                    help="报告输出路径（默认 feasibility/日期.md）")
    ap.add_argument("--no-llm", action="store_true", help="跳过 LLM 增强")
    ap.add_argument("--check", action="store_true",
                    help="只校验输入并打印项目池摘要，不写报告（当天日报缺失时退出码 2）")
    args = ap.parse_args(argv)

    if not DATE_RE.fullmatch(args.date):
        print(f"错误: 日期必须是 YYYY-MM-DD：{args.date!r}", file=sys.stderr)
        return 2

    today_projects, projects, n_daily, n_weekly, anchor_date = load_project_pool(
        args.data_root, args.date)
    if not anchor_date:
        print(f"错误: 当天日报缺失（daily/{args.date}.md），本次可行性方案跳过执行",
              file=sys.stderr)
        return 2
    if not projects or not today_projects:
        print("错误: 最近 90 天窗口内未解析到项目，或锚点日报为空", file=sys.stderr)
        return 2
    cutoff = date.fromisoformat(args.date) - timedelta(days=90)
    today_ids = {p["id"] for p in today_projects}

    if args.check:
        print(f"POOL date={args.date} anchor={anchor_date} "
              f"today={len(today_projects)} unique={len(projects)} "
              f"daily_files={n_daily} weekly_files={n_weekly}")
        return 0

    # 新鲜度规则对所有运行生效（含补跑历史日期）：连续出现两天的方案第三天跳过。
    # 依据是 run_date 之前已存在的报告文件，同一文件集下结果可复现。
    blocked = load_recent_families(args.data_root, args.date)
    reuse_counts = load_recent_component_counts(args.data_root, args.date)
    # 双轨产出：成熟方向（固定模板，先定方向再分配组件）+ 探索方向（今日锚点拼接，待验证）
    mature_candidates = build_combos(projects, today_ids, blocked, reuse_counts)
    exploratory_candidates = build_exploratory_combos(projects, today_projects,
                                                     today_ids, blocked)
    combos = select_tracked_portfolio(mature_candidates + exploratory_candidates)
    no_plan_reason = ""
    if not combos:
        no_plan_reason = ("成熟方向候选 {} 个、探索方向候选 {} 个，均未达到合格线（≥{} 分）"
                          "或缺少今日锚点".format(len(mature_candidates),
                                                len(exploratory_candidates),
                                                MIN_COMBO_SCORE))
        print(f"警告: 本轮无合格方案（{no_plan_reason}）", file=sys.stderr)
    singles = build_single_angles(projects)
    llm_text = llm_enhance(projects, combos, args.no_llm)
    report = render(projects, today_projects, combos, singles, args.date,
                    cutoff.isoformat(), anchor_date, n_daily, n_weekly, llm_text,
                    blocked, no_plan_reason)

    out_dir = args.data_root / "feasibility"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = args.output or (out_dir / f"{args.date}.md")
    out_path.write_text(report + "\n", encoding="utf-8")

    runs = out_dir / "runs.log"
    ts = datetime.now().isoformat(timespec="seconds")
    mature_n = sum(1 for c in combos if c.get("track") == TRACK_MATURE)
    exploratory_n = sum(1 for c in combos if c.get("track") == TRACK_EXPLORATORY)
    with runs.open("a", encoding="utf-8") as fh:
        blocked_note = f" blocked={'、'.join(sorted(blocked))}" if blocked else ""
        plan_note = "" if combos else " no-qualified-plan"
        fh.write(f"{ts} OK anchor={anchor_date} window=90d cutoff={cutoff.isoformat()} "
                 f"daily={n_daily} weekly={n_weekly} projects={len(projects)} "
                 f"candidates={len(mature_candidates) + len(exploratory_candidates)} "
                 f"combos={len(combos)} mature={mature_n} exploratory={exploratory_n} "
                 f"output={out_path.name}{blocked_note}{plan_note}\n")
    if combos:
        print(f"OK: {out_path}（项目池 {len(projects)}，方案 {len(combos)}："
              f"成熟 {mature_n} + 探索 {exploratory_n}）")
    else:
        print(f"OK: {out_path}（项目池 {len(projects)}，方案 0：本轮无合格方案）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
