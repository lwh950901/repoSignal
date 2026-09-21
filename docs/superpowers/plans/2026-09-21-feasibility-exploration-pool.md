# Feasibility Exploration Pool Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 让单个今日可执行项目也能作为探索锚点，从最近 90 天项目池补齐可连接组件，同时修复 `可复用型` 日报解析。

**Architecture:** 保留现有双轨选择器、闭环门槛、双评分和冷却机制。探索生成器改为按今日项目逐个播种，枚举包含种子能力面的 3–5 能力组合，并优先从今日项目、其次从 90 天池选择低复用组件；业务身份由种子能力面决定。

**Tech Stack:** Python 3 标准库、`unittest`、Markdown 任务契约

---

### Task 1: 修复 `可复用型` 日报解析

**Files:**
- Modify: `scripts/opportunity_analysis.py:72-77`
- Test: `scripts/test_opportunity_analysis.py`

- [ ] **Step 1: Write the failing test**

新增一个临时日报测试，内容连续包含 `学习型` 和 `可复用型` 两个三级标题；断言
`parse_daily()` 返回两个独立项目，且各自字段不串写。

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest scripts.test_opportunity_analysis.DailyParsingTests.test_reusable_section_starts_a_new_project -v`

Expected: FAIL，当前解析器只得到一个项目或字段被后一个项目覆盖。

- [ ] **Step 3: Write minimal implementation**

把日报类型表达式改为：

```python
r"(?:(?P<kind>额外发现|爆发型|实用型|潜力型|学习型|可复用型)[：:]\s*)?"
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m unittest scripts.test_opportunity_analysis.DailyParsingTests.test_reusable_section_starts_a_new_project -v`

Expected: PASS。

### Task 2: 用 90 天池补齐探索组合

**Files:**
- Modify: `scripts/opportunity_analysis.py:1290-1315`
- Modify: `scripts/opportunity_analysis.py:1536-1642`
- Modify: `scripts/opportunity_analysis.py:2018-2030`
- Test: `scripts/test_opportunity_analysis.py:430-505`

- [ ] **Step 1: Write the failing tests**

覆盖以下行为：

```python
def test_one_today_anchor_can_use_pool_complements(self):
    today = self.project("owner/today-agent", {"agent": 6}, "Agent 编排框架。")
    history = [
        self.project("owner/history-document", {"document": 5}, "文档解析接口。"),
        self.project("owner/history-rag", {"rag": 5}, "知识检索接口。"),
    ]
    combos = analysis.build_exploratory_combos(
        [today] + history, [today], {today["id"]}, reuse_counts={})
    self.assertEqual(len(combos), 1)
    self.assertEqual(combos[0]["today_count"], 1)
    self.assertIn(today["id"], {p["id"] for p in combos[0]["picks"].values()})

def test_seed_face_defines_business_problem(self):
    # 今日 agent 锚点与历史 document/rag 组合后，problem_id 仍来自 agent。
    self.assertEqual(combo["business"]["problem_id"],
                     analysis.BUSINESS_PROBLEMS["agent"]["problem_id"])

def test_prefers_today_complement_then_low_reuse_history(self):
    # 同能力面有今日组件时先选今日；只有历史组件时，近期复用少者优先。
    self.assertIn("owner/today-rag", selected_ids)
    self.assertIn("owner/fresh-document", selected_ids)
    self.assertNotIn("owner/frequent-document", selected_ids)

def test_no_connected_pool_components_returns_empty(self):
    # gateway + memory + sandbox 不能形成一条弱连通流，仍返回空。
    self.assertEqual(combos, [])
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 -m unittest scripts.test_opportunity_analysis.ExploratoryTrackTests -v`

Expected: 至少“单今日锚点补池”测试 FAIL。

- [ ] **Step 3: Make business semantics seed-driven**

给 `exploratory_business` 增加可选 `primary_tag`；传入时客户问题、预期结果和业务流
使用该能力面的 `BUSINESS_PROBLEMS`，而不是由补充组件的稀缺度决定。

- [ ] **Step 4: Implement bounded connected-combination search**

在 `build_exploratory_combos` 中：

- 过滤无接口依据和非执行项目；
- 每个今日项目按 `top_tag()` 作为独立种子；
- 枚举包含种子能力面的 3–5 能力面集合；
- 每个补充能力面优先选择今日候选，否则调用 `pick_best()` 从 90 天池选择；
- 把 `reuse_counts` 传入选择器；
- 只保留 `combo_flow()` 通过的候选，并按技术分、今日组件数、低复用量和稳定键排序；
- 每个探索候选的 `today_count` 按真实来源计算，文案明确区分今日锚点和历史补充组件。

- [ ] **Step 5: Thread reuse counts from main**

将主流程调用改为：

```python
exploratory_candidates = build_exploratory_combos(
    projects, today_projects, today_ids, None,
    reuse_counts=reuse_counts,
    feedback=feedback, run_date=args.date, rejected=rejected,
)
```

- [ ] **Step 6: Run exploratory tests**

Run: `python3 -m unittest scripts.test_opportunity_analysis.ExploratoryTrackTests -v`

Expected: PASS。

### Task 3: 同步报告说明和定时任务契约

**Files:**
- Modify: `scripts/opportunity_analysis.py:20-35, 1826-1836`
- Modify: `data/github-project-digest/feasibility/KUN-TASK.md:10-65`
- Test: `scripts/test_opportunity_analysis.py`

- [ ] **Step 1: Update report assertions**

断言探索报告说明包含“今日可执行锚点”和“最近 90 天项目池互补组件”，且不再包含
“组件全部来自今日日报”。

- [ ] **Step 2: Update generator copy**

脚本模块说明、报告简介、探索方案 `pitch`、`differentiation` 和 `rationale` 都改为
“今日锚点决定方向，90 天池只补齐数据流”。

- [ ] **Step 3: Update KUN-TASK contract**

把“今日锚点 ≥3 个项目”替换为：每个探索方向至少 1 个今日可执行锚点，另从今日或
最近 90 天池选择至少 2 个互补组件；今日锚点必须参与主数据流并决定客户问题。

- [ ] **Step 4: Run rendering tests**

Run: `python3 -m unittest scripts.test_opportunity_analysis.DualTrackRenderingTests -v`

Expected: PASS。

### Task 4: Verification handoff

**Files:**
- Inspect: `scripts/opportunity_analysis.py`
- Inspect: `scripts/test_opportunity_analysis.py`
- Inspect: `data/github-project-digest/feasibility/KUN-TASK.md`

- [ ] **Step 1: Static checks without executing the user-owned test run**

Run: `git diff --check`

Expected: 无输出、退出码 0。

- [ ] **Step 2: Give the user exact test commands**

```bash
python3 -m unittest scripts.test_opportunity_analysis -v
python3 scripts/opportunity_analysis.py --date 2026-09-21 --check
python3 scripts/opportunity_analysis.py --date 2026-09-21 --output /tmp/feasibility-2026-09-21.md --no-llm
```

不覆盖 `data/github-project-digest/feasibility/2026-09-21.md`，由用户自行检查临时报告。

> 本工作区的三个实现目标文件在计划开始前已有未提交修改，因此实现阶段不自动提交它们，
> 避免把既有改动混入新提交；最终以工作区 diff 交付。

## 执行状态

- 已实现 Task 1–3 的代码、回归用例与任务契约修改。
- 按用户要求未运行 `unittest`、`--check` 或报告生成命令，由用户自行测试。
- 已通过 `py_compile` 语法检查与目标文件 `git diff --check`。

## 后续处置（2026-09-21 晚，按用户指令「以今天之前为准」）

- 全量回归可见输出：移除探索池文案（简介/业务定位/市场机会/组合依据/差异化）；
  简介、元数据（正文显示）、组件表（“组件数据流 + 组合方案”两张表）恢复今晨形态；
  同时恢复 MVP 实验数值口径与多步下一步动作；`KUN-TASK.md` 正文契约同步恢复。
- 保留纯内部机制（不改变读者可见合同）：今日锚点 + 90 天池候选组装、`可复用型`
  解析修复、非执行组件过滤、历史复用降权。
- 唯一可见增量：探索组合在「组合依据」一处简短标注「另有 N 个互补组件来自最近
  90 天项目池」。
- 定时任务提示词（Kun「每日 GitHub 组合可行性方案」）已同步到回归后的合同。
- 追加（同日）：报告说明精简为一行（连同命名说明行 ≤150 字），KUN-TASK 与定时任务提示词已同步新规则。
- 追加 2（同日）：参考 09-19 对比去重——正文移除 客户问题、接入方式、组件数据流表与最大不确定性段落（转内部校验）；需求证据收紧为一行；业务定位回一句话。生成器、测试、KUN-TASK 与定时任务提示词已同步。
- 追加 3（同日）：下一步动作收敛为 1 条（判断驱动）；主要风险去掉截断括注，逐组件一句。生成器、测试、KUN-TASK 与定时任务提示词已同步。
- 验证：`python3 -m unittest scripts.test_opportunity_analysis` 78 项通过；
  `2026-09-21.md` 已用回归后的生成器重出（临时输出比对后落盘）。
