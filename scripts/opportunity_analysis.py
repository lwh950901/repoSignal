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
     输出"可行性方案"（业务定位 / 目标客户 / 市场机会 / 组合分工 / 风险）。
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

TAG_ANGLE = {
    "agent": "可包装为垂直领域 Agent 托管服务（SaaS/私有化），按任务或席位收费",
    "memory": "可做'个人/团队长期记忆即服务'，或作为现有 Agent 产品的记忆层插件",
    "rag": "可做领域知识库产品（法律/医疗/代码），以检索质量与引用溯源为卖点",
    "sandbox": "可提供'不可信代码执行即服务'，面向 Agent 平台与 CI 的隔离执行层",
    "observability": "可做 Agent/LLM 成本与质量观测 SaaS，或嵌入现有 DevOps 观测栈",
    "gateway": "可做模型网关/统一接入层，按用量与路由策略收费",
    "codeintel": "可做代码理解/审查服务，按仓库或席位订阅",
    "design": "可做 AI 设计交付服务，按生成量/导出量计费",
    "security": "可做 Agent 安全审计与红队服务，面向企业内部发布门禁",
    "document": "可做文档解析/转换 API，按页或文档计费",
    "local": "可做隐私优先的本地工具商业版（支持/托管/定制）",
    "comm": "可做团队协作/通知聚合产品，或垂直行业通信自动化",
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
        "pitch": "用私有化 RAG+Agent 把企业分散文档变成可审批、可溯源、可评测的问答与执行助手。",
        "target": "数据敏感的中大型企业（法律/金融/制造/医疗），对数据出境和合规有硬性要求。",
        "market": "企业知识管理与 GenAI 预算持续增长，私有化部署的合规需求明确；90 天池内供给组件（编排/检索/记忆/沙箱/评测）齐全。",
        "differentiation": "相对单点 RAG 或 Agent 框架，交付'合规私有化 + 人工审批 + 评测门禁'的一体化闭环。",
        "rationale": "编排、检索/知识库、记忆、沙箱与评测组件在 90 天池中同时可用，"
                     "'知识问答 + Agent 执行'的最小闭环已能用自托管组件拼出。",
        "mvp": "固定 agent+rag+observability 三件套做部门级问答闭环：一个文档集、一条评测集、一个需审批的工具动作；记忆与沙箱作为二期。",
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
        "pitch": "把沙箱、观测、安全审计与模型网关拼成 CI 化的 Agent 交付流水线，让 Agent 产出可回放、可验收。",
        "target": "已在使用 coding agent（Codex/Claude Code/Cursor）的研发团队与平台工程组。",
        "market": "Agent 进入生产后，失败恢复、成本与合规缺口成为刚需；90 天池内隔离执行与观测组件密集出现。",
        "differentiation": "相对单个 harness 或观测工具，提供'隔离执行 + trace 评测 + 审计门禁'的端到端流水线。",
        "rationale": "长任务 Agent 的失败恢复、可观测与安全执行是 90 天池中反复出现的主题，"
                     "组件供给成熟，适合拼成 CI/交付流水线。",
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
        "market": "本地优先与自托管在 90 天池中多次出现（记忆/桌面/网关组件密集），个人知识管理付费意愿在上升。",
        "differentiation": "相对云端工作台，主打数据所有权与模型中立；相对单点记忆工具，提供完整工作台闭环。",
        "rationale": "本地优先、隐私与自托管是 90 天池中的稳定主题，"
                     "本地记忆+模型网关+Agent 编排可以拼成个人知识工作台产品。",
        "mvp": "两个组件先跑通'本地记忆写入→Agent 读取→输出压缩'闭环，再决定桌面端与多渠道接入。",
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
        "pitch": "统一会话、审批、成本与审计的多 Agent 协作控制面，把零散 Agent 变成可管理的团队资产。",
        "target": "已在使用多个 coding agent 工具、或计划让 Agent 参与团队流程的团队。",
        "market": "多 Agent 工具碎片化是真实痛点；90 天池中编排、协作入口与成本观测组件同时成熟。",
        "differentiation": "相对单 Agent 工具，提供'多 Agent 会话 + 审批 + 审计 + 成本'的统一控制面。",
        "rationale": "多 Agent 编排、协作入口与成本观测组件在 90 天池中齐全，"
                     "面向团队提供控制面产品的时机成熟。",
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
        "market": "RAG 效果瓶颈普遍在上游解析与清洗；90 天池中解析/转换与检索组件成熟且可组合。",
        "differentiation": "相对单点解析库或向量库，提供'解析 + 转换 + 质量门禁'的完整管道。",
        "rationale": "文档解析/转换与检索、评测组件可以拼成'入库前处理 + 质量门禁'的管道，"
                     "解决 RAG 上游脏数据这一常见瓶颈。",
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
        "pitch": "把 Agent 扫描→修复→验证变成带证据链、可人工审批的发布门禁与红队预检服务。",
        "target": "企业安全团队、DevSecOps 平台组。",
        "market": "Agent 相关攻击面快速扩大（Skill/MCP/供应链），安全供给在 90 天池中密集出现（红队/审计/沙箱）。",
        "differentiation": "相对传统 SAST，提供'Agent 驱动扫描 + 修复 + 独立验证'的证据链闭环。",
        "rationale": "安全审计、沙箱与代码理解组件在 90 天池中可拼成'扫描→修复→验证'的 "
                     "Agent 安全流水线，面向发布门禁与红队预检。",
        "mvp": "在授权靶场跑'扫描→修复建议→独立验证'三步，保留证据链与人工审批，再评估接入正式仓库。",
    },
]

CLIP = 64


def clip(text, n=CLIP):
    text = re.sub(r"\s+", " ", (text or "")).strip()
    return text if len(text) <= n else text[: n - 1].rstrip() + "…"


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
        if not m or date.fromisoformat(m.group(1)) < cutoff:
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
        if week_start < cutoff:
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


def build_combos(projects, today_ids=None):
    today_ids = today_ids or set()
    combos = []
    total = len(projects)
    for tpl in TEMPLATES:
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
        combos.append({
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
    # 今日锚点多者优先，其次组件数与 Stars
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
           anchor_date, n_daily_files, n_weekly_files, llm_text):
    n = len(projects)
    today_ids = {p["id"] for p in today_projects}
    L = []
    A = L.append
    A(f"# GitHub 项目组合可行性方案｜{run_date}")
    A("")
    A("> 由定时任务自动生成（`scripts/opportunity_analysis.py`），属于可行性研究草稿，"
      "不包含代码，不是公开结论；落地前需逐个组件复核。")
    A("> 今日锚点：`daily/{}.md`（{} 个项目）；组合池：最近 90 天（{} ~ {}）"
      "{} 个唯一项目（日报 {} 份 / 周报 {} 份）。".format(
          anchor_date, len(today_projects), cutoff, run_date,
          n, n_daily_files, n_weekly_files))
    A("")
    A("## 可行性方案")
    A("")
    if not combos:
        A("（项目池不足以形成 ≥2 个组件的组合，仅见单点机会。）")
    for i, c in enumerate(combos, 1):
        A("### {}. {}（组合 {} 个项目，今日锚点 {} 个）".format(
            i, c["name"], c["total"], c["today_count"]))
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
        A("**为什么现在可行**：{} 本组合含今日发现项目 {} 个（{}）；"
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
                esc(clip(_clean_evidence(basis), 72))))
        A("")
        A("**差异化**：{}".format(c["differentiation"]))
        A("")
        A("**MVP 范围（做什么，不含代码）**：{}".format(c["mvp"]))
        A("")
        risks = []
        for role, p in c["picks"].items():
            r = (p["fields"].get("risks") or "").strip()
            if r:
                risks.append("- `{}`（{}）：{}".format(p["repo"], role, clip(r, 100)))
        if risks:
            A("**主要风险（来源报告）**：")
            A("")
            A("\n".join(risks))
        A("")
        A("**验证路径**：每个组件按来源报告的'上手建议/真实风险'复核（固定版本、"
          "隔离环境、自有数据复测）；本方案为可行性研究，不包含代码。")
        A("")
    A("## 单点项目机会（供参考）")
    A("")
    for p, top, evidence in singles:
        A("- `{}`（`#{}`）→ {}。依据：{}".format(
            p["repo"], top, TAG_ANGLE[top], clip(evidence, 100)))
    A("")
    A("## 行动建议")
    A("")
    if combos:
        top = combos[0]
        A("1. 优先推进今日锚点最多的组合：「{}」（{} 组件，今日锚点 {} 个）。".format(
            top["name"], top["total"], top["today_count"]))
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

    combos = build_combos(projects, today_ids)
    singles = build_single_angles(projects)
    llm_text = llm_enhance(projects, combos, args.no_llm)
    report = render(projects, today_projects, combos, singles, args.date,
                    cutoff.isoformat(), anchor_date, n_daily, n_weekly, llm_text)

    out_dir = args.data_root / "feasibility"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = args.output or (out_dir / f"{args.date}.md")
    out_path.write_text(report + "\n", encoding="utf-8")

    runs = out_dir / "runs.log"
    ts = datetime.now().isoformat(timespec="seconds")
    with runs.open("a", encoding="utf-8") as fh:
        fh.write(f"{ts} OK anchor={anchor_date} window=90d cutoff={cutoff.isoformat()} "
                 f"daily={n_daily} weekly={n_weekly} projects={len(projects)} "
                 f"combos={len(combos)} output={out_path.name}\n")
    print(f"OK: {out_path}（项目池 {len(projects)}，组合 {len(combos)}）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
