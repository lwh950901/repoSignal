#!/usr/bin/env python3
"""基于最近 90 天发现的 GitHub 项目，生成"可行性方案"（业务方向 × 多项目组合）。

用法：
  python3 scripts/opportunity_analysis.py [--date YYYY-MM-DD] [--data-root PATH]
          [--output PATH] [--no-llm] [--check]

行为：
  1. 项目池：解析 daily/ 与 weekly/ 中最近 90 天窗口内所有报告的项目条目，
     按 owner/repo 去重；每个项目保留来源（日期/周号）可追溯。
  2. 能力标签聚类（agent/memory/rag/sandbox/observability/gateway/codeintel/
     design/security/document/local/comm），组合模板从全池挑选真实项目，
     输出"可行性方案"（业务定位 / 目标客户 / 市场机会 / 组合分工 / 风险），
     并给出 0-100 确定性综合评分（组件可靠度 / 组件供给 / 风险敞口 /
     今日锚点 / 来源多样性 / 许可证 / 完整度）与高中低档位。
  3. 可选增强：设置 OPPORTUNITY_LLM_API_KEY（或 OPENAI_API_KEY）时调用
     OpenAI 兼容接口补充视角；失败不影响主流程。
  4. 输出 data/github-project-digest/feasibility/YYYY-MM-DD.md，
     并追加一行运行记录到同目录 runs.log。

退出码：0 成功；2 输入缺失；1 其他错误。
"""

import argparse
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

    today_projects：锚点日报（当天存在则当天，否则取 <= run_date 的最近一份）解析的项目；
    pool_projects：最近 90 天窗口内全部唯一项目（含 today 项目），每项带 source_date。
    """
    cutoff = date.fromisoformat(run_date) - timedelta(days=90)
    run_d = date.fromisoformat(run_date)
    # 锚点日报：当天优先，否则取 <= run_date 的最近一份
    anchor_date = None
    for f in sorted((data_root / "daily").glob("*.md"), reverse=True):
        m = DAILY_FILE_RE.match(f.name)
        if m and m.group(1) <= run_date:
            anchor_date = m.group(1)
            break
    if anchor_date is None:
        return None, None, 0, 0, ""
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


def pick_best(projects, tag, exclude, today_ids):
    cands = [p for p in projects if p["id"] not in exclude and p["tags"].get(tag, 0) > 0]
    if not cands:
        return None
    # 维护滞后项目整体排在健康项目之后；今日锚点项目加权优先；同组按标签分、Stars
    cands.sort(key=lambda p: (
        _maintenance_flag(p),
        -(p["tags"][tag] + (TODAY_BONUS if p["id"] in today_ids else 0)),
        -p["stars"]))
    return cands[0]


def load_recent_combo_names(data_root, run_date, n=2):
    """读取 run_date 之前最近 n 份可行性报告，返回其中同时出现的方案名集合。

    用于'同一方案最多连续出现两天'的新鲜度限制：方案名同时出现在最近两份
    报告里说明已连续出现两天，第三天应跳过。
    """
    files = []
    for f in sorted((data_root / "feasibility").glob("20??-??-??.md"), reverse=True):
        m = DAILY_FILE_RE.match(f.name)
        if m and m.group(1) < run_date:
            files.append(f)
        if len(files) >= n:
            break
    if len(files) < n:
        return set()
    name_sets = []
    for f in files:
        names = set()
        for line in f.read_text(encoding="utf-8").splitlines():
            hm = re.match(r"^### \d+\.\s+(.+?)(（组合|$)", line)
            if hm:
                names.add(hm.group(1).strip())
        name_sets.append(names)
    return set.intersection(*name_sets)


def top_tag(p):
    """项目能力面最高分的标签；同分时取 TAG_RULES 中靠前的标签，保证确定性。"""
    order = {t: i for i, t in enumerate(TAG_RULES)}
    return max(p["tags"].items(), key=lambda kv: (kv[1], -order.get(kv[0], 99)))[0]


def build_anchor_combo(projects, today_projects, today_ids, blocked_names=None):
    """固定模板命中不足时，用今日锚点按能力互补直接拼一个全新组合。

    全部组件来自今日日报（新鲜度最高），能力面尽量分散（同一能力面最多两个）；
    方案名带"今日锚点组合"前缀，用于与固定模板方案区分。
    """
    blocked_names = blocked_names or set()
    anchors = [p for p in today_projects if p["tags"]]
    if len(anchors) < 2:
        return None
    anchors.sort(key=lambda p: p["stars"], reverse=True)
    picks = {}
    covered = set()
    # 第一轮：按 Stars 优先收不同能力面的锚点；第二轮：有空位再补其余锚点
    for p in anchors:
        t = top_tag(p)
        if t not in covered:
            picks[COMBO_ROLES[t]] = p
            covered.add(t)
            if len(picks) >= 5:
                break
    if len(picks) < 5:
        used_ids = {x["id"] for x in picks.values()}
        for p in anchors:
            if p["id"] in used_ids:
                continue
            t = top_tag(p)
            role = COMBO_ROLES[t]
            while role in picks:
                role += "（二）"
            picks[role] = p
            used_ids.add(p["id"])
            if len(picks) >= 5:
                break
    if len(picks) < 2 or len({top_tag(p) for p in picks.values()}) < 2:
        return None
    tags = [t for t in TAG_RULES if any(top_tag(p) == t for p in picks.values())]
    # 角色用项目真实定位（tagline 首句），避免能力面标签与项目错配；
    # 方案名用项目短名，保证可读性与唯一性（新鲜度规则按名匹配）。
    def role_of(p):
        tagline = (p["fields"].get("tagline") or "").strip()
        if tagline:
            role = first_sentence(tagline, 60)
            if role and role != p["repo"]:
                return role
        return COMBO_ROLES.get(top_tag(p), top_tag(p))

    roles = {}
    for r, p in picks.items():
        role = role_of(p)
        while role in roles.values():
            role += "（二）"
        roles[r] = role
    picks = {roles[r]: p for r, p in picks.items()}
    repo_short = picks[list(picks)[0]]["repo"].split("/")[-1]
    name = "今日锚点组合：{} 等 {} 个新发现项目".format(repo_short, len(picks))
    if name in blocked_names:
        return None
    slot_tags = [top_tag(p) for p in picks.values()]
    supply = {t: sum(1 for p in projects if t in p["tags"]) for t in set(slot_tags)}
    min_supply = min(supply.values())
    today_count = len(picks)
    score, score_parts = combo_score(
        {"slots": [(t, r) for r, t in zip(picks.keys(), slot_tags)]},
        picks, today_count, min_supply)
    roles_text = "、".join("{}（`{}`）".format(r, p["repo"]) for r, p in picks.items())
    return {
        "score": score,
        "score_parts": score_parts,
        "name": name,
        "pitch": "把今日新发现的 {} 个项目作为组合试用候选：{}。先各自试用、记录产出，再找可打通的组合路径。".format(
            len(picks), roles_text),
        "target": "想第一时间试用今日新发现项目的个人开发者与研究型小团队。",
        "market": "今日 {} 个锚点分属 {} 等能力面，池中对应候选 {} 个，组件供给充足；"
                   "先用小规模试用验证价值，再决定产品化方向。".format(
                       len(picks), "、".join(TAG_CN[t] for t in tags), min_supply),
        "differentiation": "完全由今日新发现驱动，组件全部来自今日日报，新鲜度最高，不依赖固定模板。",
        "rationale": "全部组件来自今日日报，能力面尽量互补（{} 个），无需等待固定模板命中即可拼出组合。".format(len(tags)),
        "mvp": "先分别试用各组件并记录可用产出，再打通 {} 之间的最小数据流或协作流；其余按试用反馈取舍。".format(
            "、".join("`{}`".format(p["repo"]) for p in list(picks.values())[:3])),
        "picks": picks,
        "slot_supply": supply,
        "min_supply": min_supply,
        "total": len(picks),
        "today_count": today_count,
        "stars": sum(p["stars"] for p in picks.values()),
    }


def build_combos(projects, today_ids=None, blocked_names=None):
    today_ids = today_ids or set()
    blocked_names = blocked_names or set()
    combos = []
    total = len(projects)
    for tpl in TEMPLATES:
        if tpl["name"] in blocked_names:
            continue  # 新鲜度规则：同一方案最多连续出现两天，第三天跳过
        picks = {}
        used = set()
        for tag, role in tpl["slots"]:
            p = pick_best(projects, tag, used, today_ids)
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
        # 综合评分：分项按确定性规则计算，总分 = 分项之和，保证明细可加总。
        score, score_parts = combo_score(tpl, picks, today_count, min_supply)
        combos.append({
            "score": score,
            "score_parts": score_parts,
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
        })
    # 保持历史可复现：组合排序维持原规则（今日锚点多者优先，其次组件数与 Stars）；
    # 评分不参与排序，仅作展示与行动建议的推荐依据。
    combos.sort(key=lambda c: (c["today_count"], c["total"], c["stars"]), reverse=True)
    return combos[:3]


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


def _source_label(p, anchor_date=None):
    base = f"{p['source_date']} {'日报' if p['source'] == 'daily' else '周报'}"
    if anchor_date and p["source_date"] == anchor_date and p["source"] == "daily":
        base += "（今日）"
    return base


def render(projects, today_projects, combos, singles, run_date, cutoff,
           anchor_date, n_daily_files, n_weekly_files, llm_text, blocked=None,
           fallback_name=None):
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
      "{} 个唯一项目（日报 {} 份 / 周报 {} 份）。方案 1-3 个，"
      "取决于当日锚点能命中几个组合模板。".format(
          anchor_date, len(today_projects), cutoff, run_date,
          n, n_daily_files, n_weekly_files))
    A("> 评分（0-100，确定性规则，用于方案横向比较，不代表商业结论）："
      "组件可靠度 35 · 组件供给 15 · 风险敞口 15 · 今日锚点 15 · "
      "来源多样性 10 · 许可证 5 · 完整度 5；档位：≥85 高，70-84 中，<70 低。")
    A("> 验证路径（固定）：每个组件按来源报告的'上手建议/真实风险'复核"
      "（固定版本、隔离环境、自有数据复测）。")
    if blocked:
        skipped = {n for n in blocked if n != fallback_name}
        if skipped:
            A("> 新鲜度规则：以下方案已连续出现两天，本轮跳过（同一方案最多连续两天）：{}。".format(
                "、".join(sorted(skipped))))
        if fallback_name:
            A("> 保底：{}已连续出现两天，但本轮无其他可用组合，保底保留。".format(fallback_name))
    if any(c["name"].startswith("今日锚点组合：") for c in combos):
        A("> 补充说明：固定模板未拼满 3 个方案，已用今日新发现直接拼接'今日锚点组合'（组件全部来自今日日报）。")
    A("")
    A("## 可行性方案")
    A("")
    if not combos:
        if blocked:
            A("（今日锚点未命中其余组合模板，本轮无组合方案；"
              "被新鲜度规则跳过：{}。）".format("、".join(sorted(blocked))))
        else:
            A("（项目池不足以形成 ≥2 个组件的组合，仅见单点机会。）")
    for i, c in enumerate(combos, 1):
        A("### {}. {}（组合 {} 个项目，今日锚点 {} 个）".format(
            i, c["name"], c["total"], c["today_count"]))
        A("")
        parts_str = " · ".join("{} {}/{}".format(k, v, w) for k, v, w in c["score_parts"])
        grade = "高" if c["score"] >= 85 else ("中" if c["score"] >= 70 else "低")
        A("**方案评分**：**{}/100（{}）**（{}）".format(c["score"], grade, parts_str))
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
        A("| 角色 | 项目 | 来源 | 许可证 | 入选理由 |")
        A("|---|---|---|---|---|")
        for role, p in c["picks"].items():
            basis = (p["fields"].get("value") or p["fields"].get("reason")
                     or p["fields"].get("tagline") or "")
            lic = p["fields"].get("metrics", "")
            m = re.search(r"(MIT|Apache-2\.0|AGPL-3\.0|GPL-3\.0|MPL-2\.0|BSD-[0-9]-Clause)",
                          lic)
            A("| {} | [`{}`]({}) | {} | {} | {} |".format(
                role, p["repo"], p["url"], _source_label(p, anchor_date),
                m.group(1) if m else "（见仓库）",
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
                    help="只解析项目池并打印摘要，不写报告")
    args = ap.parse_args(argv)

    if not DATE_RE.fullmatch(args.date):
        print(f"错误: 日期必须是 YYYY-MM-DD：{args.date!r}", file=sys.stderr)
        return 2

    today_projects, projects, n_daily, n_weekly, anchor_date = load_project_pool(
        args.data_root, args.date)
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
    blocked = load_recent_combo_names(args.data_root, args.date)
    combos = build_combos(projects, today_ids, blocked)
    # 固定模板命中不足 3 个时，用今日锚点直接拼接全新组合（不重复已有方案）
    if len(combos) < 3:
        anchor_combo = build_anchor_combo(projects, today_projects, today_ids, blocked)
        if anchor_combo and anchor_combo["name"] not in {c["name"] for c in combos}:
            combos.append(anchor_combo)
            combos.sort(key=lambda c: (c["today_count"], c["total"], c["stars"]),
                        reverse=True)
            combos = combos[:3]
    fallback_name = None
    if not combos and blocked:
        # 兜底：仍无任何可用组合时，放行一个被跳过的方案，避免空报告
        all_combos = build_combos(projects, today_ids)
        if all_combos:
            fallback_name = all_combos[0]["name"]
            combos = [all_combos[0]]
    singles = build_single_angles(projects)
    llm_text = llm_enhance(projects, combos, args.no_llm)
    report = render(projects, today_projects, combos, singles, args.date,
                    cutoff.isoformat(), anchor_date, n_daily, n_weekly, llm_text,
                    blocked, fallback_name)

    out_dir = args.data_root / "feasibility"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = args.output or (out_dir / f"{args.date}.md")
    out_path.write_text(report + "\n", encoding="utf-8")

    runs = out_dir / "runs.log"
    ts = datetime.now().isoformat(timespec="seconds")
    with runs.open("a", encoding="utf-8") as fh:
        blocked_note = f" blocked={'、'.join(sorted(blocked))}" if blocked else ""
        fallback_note = f" fallback={fallback_name}" if fallback_name else ""
        fh.write(f"{ts} OK anchor={anchor_date} window=90d cutoff={cutoff.isoformat()} "
                 f"daily={n_daily} weekly={n_weekly} projects={len(projects)} "
                 f"combos={len(combos)} output={out_path.name}{blocked_note}{fallback_note}\n")
    print(f"OK: {out_path}（项目池 {len(projects)}，组合 {len(combos)}）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
