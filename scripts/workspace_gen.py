#!/usr/bin/env python3
"""组合开发工作区生成器（供 opportunity_analysis.py 调用）。

把每条业务组合落成一个可继续开发的骨架目录：

  opportunity/<日期>/<序号>-<slug>/
  ├── README.md       # 业务定位 / 可行性 / 组合分工 / MVP / 风险
  ├── TASKS.md        # P0/P1 开发任务清单（含验收标准）
  ├── COMPONENTS.md   # 各组件接入指南（安装、验证、风险）
  ├── .env.example    # 环境变量占位
  ├── verify.sh       # 结构自检
  └── apps/mvp/       # 最小闭环代码占位（按 entry 语言）

代码为占位 + 接线点，不假装能运行；每个接入点指向上游仓库文档。
"""

import re
from pathlib import Path

# 组合名称 → (slug, pitch, entry语言)
WORKSPACE_META = {
    "企业内部知识助手（私有化 RAG × Agent）": (
        "enterprise-knowledge-assistant",
        "面向数据敏感的中大型企业（法律/金融/制造）：用私有化 RAG+Agent 把分散文档"
        "变成可审批、可溯源、可评测的问答与执行助手。",
        "python"),
    "可审计的 Agent 开发/交付平台（CI 化 Agent 流水线）": (
        "auditable-agent-delivery-platform",
        "面向需要把 coding agent 放进 CI 的工程团队：隔离执行、trace 评测与安全审计"
        "一体的 Agent 交付流水线，让 Agent 产出可回放、可验收。",
        "python"),
    "本地优先个人 AI 工作台": (
        "local-first-ai-workbench",
        "面向重视隐私的个人开发者/知识工作者：数据留在本机、模型可换、记忆可导出，"
        "打造可拥有的个人 AI 工作台。",
        "typescript"),
    "多 Agent 协作控制面（团队级）": (
        "multi-agent-collaboration-console",
        "面向已在使用多个 coding agent 工具的团队：统一会话、审批、成本与审计，"
        "把零散 Agent 变成可管理的协作控制面。",
        "typescript"),
    "文档/知识处理管线（入库前处理）": (
        "document-knowledge-pipeline",
        "面向 RAG/搜索产品构建者：提供入库前解析→转换→质检的管道，"
        "解决脏数据导致的召回与引用质量问题。",
        "python"),
    "安全 Agent 平台（扫描-修复-验证）": (
        "agent-security-platform",
        "面向企业安全团队：把 Agent 扫描→修复→验证变成带证据链、"
        "可人工审批的发布门禁与红队预检服务。",
        "python"),
}

LICENSE_RE = re.compile(r"(MIT|Apache-2\.0|AGPL-3\.0|GPL-3\.0|MPL-2\.0|BSD-[0-9]-Clause)")


def workspace_rel_path(combo, index, date_str):
    meta = WORKSPACE_META.get(combo["name"])
    slug = meta[0] if meta else f"combo-{index}"
    return f"{date_str}/{index}-{slug}"


def extract_license(project):
    text = " ".join([
        project["fields"].get("metrics", ""),
        project["fields"].get("risks", ""),
        project["fields"].get("quality", ""),
    ])
    m = LICENSE_RE.search(text)
    return m.group(1) if m else "（见仓库 LICENSE）"


def _clip(text, n):
    text = re.sub(r"\s+", " ", (text or "")).strip()
    return text if len(text) <= n else text[: n - 1].rstrip() + "…"


def _picks(combo):
    return list(combo["picks"].items())


def _howto(p):
    """验证/接入路径：优先上手建议，日报项目回退到推荐理由或一句话定位。"""
    return (p["fields"].get("howto")
            or p["fields"].get("reason")
            or p["fields"].get("value")
            or p["fields"].get("tagline")
            or "见上游 README")


def _readme(combo, projects, date_str, weekly_name, daily_name):
    meta = WORKSPACE_META.get(combo["name"], ("", combo.get("pitch", ""), ""))
    n = len(projects)
    L = [
        f"# {combo['name']}",
        "",
        f"> 自动生成于 {date_str}（来源：`weekly/{weekly_name}` ＋ `daily/{daily_name}`）。",
        "> 组合开发工作区：结构与接入指南已就绪，`apps/mvp/` 为占位骨架，"
        "需按各上游仓库文档继续开发（见 TASKS.md）。",
        "",
        "## 业务定位",
        "",
        meta[1],
        "",
        "## 为什么现在可行",
        "",
        f"{combo['rationale']}（本周 {n} 个候选中 {combo['signal']} 个命中该能力面。）",
        "",
        "## 组合与分工",
        "",
        "| 角色 | 仓库 | 许可证 | 技术栈 | 验证路径（来源报告） |",
        "|---|---|---|---|---|",
    ]
    for role, p in _picks(combo):
        L.append(
            f"| {role} | [`{p['repo']}`]({p['url']}) | {extract_license(p)} | "
            f"{_clip(p['fields'].get('stack', ''), 44)} | "
            f"{_clip(_howto(p), 56)} |")
    L += [
        "",
        "## 集成拓扑（草图）",
        "",
        " → ".join(role for role, _ in _picks(combo)),
        "",
        "## MVP 范围（P0）",
        "",
        combo["mvp"],
        "",
        "## 主要风险（来源报告）",
        "",
    ]
    for role, p in _picks(combo):
        L.append(f"- `{p['repo']}`（{role}）："
                 f"{_clip(p['fields'].get('risks') or '见上游报告', 110)}")
    L += [
        "",
        "## 下一步",
        "",
        "1. 按 COMPONENTS.md 安装各组件并锁定版本；",
        "2. 按 TASKS.md 的 P0 顺序逐项开发（每项有验收标准）；",
        "3. 每个组件接入前先跑通上游最小示例，不直接照搬 README 基准；",
        "4. 完成 P0 后运行 `./verify.sh` 自检，再进入 P1 加固。",
        "",
    ]
    return "\n".join(L)


def _tasks(combo):
    L = [
        f"# 开发任务清单（{combo['name']}）",
        "",
        "## P0：MVP 闭环",
        "",
        "- [ ] 0.1 初始化：按 COMPONENTS.md 安装全部组件，锁定版本",
    ]
    for i, (role, p) in enumerate(_picks(combo), 1):
        L.append(f"- [ ] 0.{i + 1} 组件冒烟：`{p['repo']}`（{role}）——跑通上游最小示例；"
                 f"验收：{_clip(_howto(p), 90)}")
    L += [
        f"- [ ] 0.{len(_picks(combo)) + 2} 端到端：按 MVP 描述完成最小闭环；"
        f"验收：{combo['mvp']}",
        "",
        "## P1：加固",
        "",
        "- [ ] 权限与数据边界：逐组件核对上游风险字段，最小权限接入",
        "- [ ] 评测与观测：接入评测集与 trace，记录基线并对比",
        "- [ ] 许可证复核：逐仓库核对 LICENSE 与商用/二次分发边界",
        "- [ ] 部署与回滚：固定版本、备份与升级演练",
        "",
        "## 验收总则",
        "",
        "固定版本、隔离环境、先只读后写、用自己的数据复测；"
        "上游 README 的基准数字不能当作保证。",
        "",
    ]
    return "\n".join(L)


def _components(combo):
    L = [f"# 组件接入指南（{combo['name']}）", "",
         "每个组件先跑通上游最小示例，再在本工作区接线。", ""]
    for role, p in _picks(combo):
        L += [
            f"## {p['repo']}（{role}）",
            "",
            f"- 仓库：{p['url']}",
            f"- 许可证：{extract_license(p)}",
            f"- 技术栈：{_clip(p['fields'].get('stack', ''), 120)}",
            f"- 安装/上手（来源日报/周报）："
            f"{_clip(_howto(p), 220)}",
            f"- 风险（来源报告）：{_clip(p['fields'].get('risks') or '见上游报告', 180)}",
            "- 接入 TODO：跑通上游最小示例后，在 `apps/mvp/` 中完成本角色接线"
            "（对应 TASKS.md 冒烟任务）。",
            "",
        ]
    return "\n".join(L)


_ENV = ("# 组合开发工作区环境变量（按 COMPONENTS.md 补齐；不要提交真实密钥）\n"
        "# 模型/LLM（按组合所用组件选择，本地模型可留空）\n"
        "LLM_API_KEY=\nLLM_BASE_URL=\n"
        "# 各组件专属配置见各自上游文档（示例，按需重命名）\n"
        "# <组件>_TOKEN=\n# <组件>_BASE_URL=\nLOG_LEVEL=info\n")

_VERIFY = """#!/usr/bin/env bash
# {name} 工作区自检：检查结构完整性。
set -euo pipefail
cd "$(dirname "$0")"
for f in README.md TASKS.md COMPONENTS.md .env.example apps/mvp; do
  [ -e "$f" ] || {{ echo "MISSING: $f"; exit 1; }}
done
echo "OK: {name} 工作区结构完整"
echo "下一步：按 COMPONENTS.md 安装组件 → 按 TASKS.md 开发 → 完成后再跑本脚本"
"""


def _mvp_python(combo):
    L = [f"\"\"\"{combo['name']} — MVP 骨架（自动生成占位，尚未接线）。", "",
         "接线顺序（对应 TASKS.md / COMPONENTS.md）："]
    for i, (role, p) in enumerate(_picks(combo), 1):
        L.append(f"{i}. {p['repo']}（{role}）—— TODO: 按上游 README 接入并跑通最小示例")
    L += ["\"\"\"", "", "", "def main():",
          "    print(\"MVP 骨架就绪：请按 TASKS.md 逐项接入组件（详见 COMPONENTS.md）\")",
          "", "", "if __name__ == \"__main__\":", "    main()", ""]
    return "\n".join(L)


def _mvp_ts(combo):
    L = [f"// {combo['name']} — MVP 骨架（自动生成占位，尚未接线）。",
         "// 接线顺序（对应 TASKS.md / COMPONENTS.md）："]
    for i, (role, p) in enumerate(_picks(combo), 1):
        L.append(f"// {i}. {p['repo']}（{role}）—— TODO: 按上游 README 接入并跑通最小示例")
    L += ["", "function main() {",
          "  console.log('MVP 骨架就绪：请按 TASKS.md 逐项接入组件（详见 COMPONENTS.md）');",
          "}", "", "main();", ""]
    return "\n".join(L)


_PKG = """{{
  "name": "mvp",
  "private": true,
  "scripts": {{ "start": "tsx index.ts" }},
  "devDependencies": {{ "tsx": "^4.0.0", "typescript": "^5.0.0" }}
}}
"""


def generate_workspaces(combos, projects, date_str, out_dir, weekly_name, daily_name):
    """为每条组合生成工作区；返回生成的工作区目录列表。"""
    made = []
    for i, combo in enumerate(combos, 1):
        ws = out_dir / workspace_rel_path(combo, i, date_str)
        ws.mkdir(parents=True, exist_ok=True)
        (ws / "README.md").write_text(
            _readme(combo, projects, date_str, weekly_name, daily_name) + "\n",
            encoding="utf-8")
        (ws / "TASKS.md").write_text(_tasks(combo) + "\n", encoding="utf-8")
        (ws / "COMPONENTS.md").write_text(_components(combo) + "\n", encoding="utf-8")
        (ws / ".env.example").write_text(_ENV, encoding="utf-8")
        (ws / "verify.sh").write_text(_VERIFY.format(name=combo["name"]), encoding="utf-8")
        mvp = ws / "apps" / "mvp"
        mvp.mkdir(parents=True, exist_ok=True)
        (mvp / "README.md").write_text(
            f"# MVP（{combo['name']}）\n\n占位骨架：按 TASKS.md / COMPONENTS.md 接线。\n",
            encoding="utf-8")
        entry = WORKSPACE_META.get(combo["name"], ("", "", "python"))[2]
        if entry == "typescript":
            (mvp / "index.ts").write_text(_mvp_ts(combo), encoding="utf-8")
            (mvp / "package.json").write_text(_PKG, encoding="utf-8")
        else:
            (mvp / "main.py").write_text(_mvp_python(combo), encoding="utf-8")
            (mvp / "requirements.txt").write_text(
                "# TODO: 按 COMPONENTS.md 添加组件依赖并锁定版本\n", encoding="utf-8")
        made.append(ws)
    return made
