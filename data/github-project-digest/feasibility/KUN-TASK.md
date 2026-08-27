# Kun 定时任务：每日 GitHub 项目组合可行性方案

> 触发方式：每天 06:30（Asia/Shanghai）。工作区：`/Users/elvis/Desktop/repo-signal`。
> 本文件是任务执行指令，Kun 定时触发后由 agent 按"执行步骤"完整执行，
> 并在结束时向用户汇报。

## 目标

以当天日报发现的 GitHub 项目为锚点，结合最近 90 天项目池，产出 **3 个"多 GitHub
项目组合"可行性方案**（业务定位 / 目标客户 / 市场机会 / 组合分工 / 差异化 /
MVP 范围 / 风险 / 0-100 综合评分），不写代码。验证路径为固定文案，统一放在报告简介。

## 输入

- 项目池：`data/github-project-digest/daily/*.md` 与 `weekly/*.md` 中最近 90 天的全部项目
- 今日锚点：`data/github-project-digest/daily/<今天日期>.md`；当天无日报（周末/未生成）时自动取最近一份

## 执行步骤

1. 校验输入：`python3 scripts/opportunity_analysis.py --check`
   - 期望输出形如 `POOL date=... anchor=... today=N unique=M ...`；
     若失败或 `daily/`、`weekly/` 无数据，检查目录后回报，不要猜测、
     不要联网核验 GitHub。
2. 生成报告：`python3 scripts/opportunity_analysis.py`
   - 默认按今天日期输出到 `data/github-project-digest/feasibility/<今天>.md`
   - 当天日报未生成时，脚本会自动取最近一份，报告头部会标注实际锚点日期；
   - 如需补跑历史日期：`--date YYYY-MM-DD`
3. 核对产出：读取报告，确认
   - 有 `### N.` 方案小节（当日数据不足时脚本允许 1-3 个，按实际数量核对）；
   - 每个方案组合表里至少 1 个项目来源标注为"（今日）"；
   - 每个方案含 `**方案评分**：N/100` 行（含分项明细，总分=分项之和）；
   - runs.log（`data/github-project-digest/feasibility/runs.log`）追加了本次记录；
   - 脚本退出码为 0。
4. 向用户汇报（简短）：
   - 方案的名称；
   - 每个方案的核心组合：今日锚点项目（角色）+ 关键补充组件；
   - 每个方案的评分（N/100 与档位，如 76/100（中））；
   - 报告完整路径 `data/github-project-digest/feasibility/<今天>.md`；
   - 如失败：说明失败原因与已检查的输入状态，最多重试一次，不要重复运行。

## 产出

- `data/github-project-digest/feasibility/YYYY-MM-DD.md`：可行性方案报告（3 个组合）
- `data/github-project-digest/feasibility/runs.log`：运行记录（锚点、池规模、组合数）

## 验证标准

- 脚本退出码 0；
- 报告含 3 个方案，每个方案含 ≥1 个今日锚点项目；
- 每个方案有 0-100 综合评分行（组件可靠度/组件供给/风险敞口/今日锚点/来源多样性/许可证/完整度，含高中低档位）；
- 组件全部来自项目池且来源可追溯（来源列带日期/周号）。

## 规则与边界

- 本任务只读取仓库内已有报告，不联网核验 GitHub；所有项目事实以日报/周报为准。
- 报告是可行性研究草稿，不包含代码，不构成商业结论。
- 只读 `daily/`、`weekly/` 下的源报告；只写 `feasibility/` 目录；不修改脚本。
- 可选增强：环境变量 `OPPORTUNITY_LLM_API_KEY`（或 `OPENAI_API_KEY`，
  可配 `OPPORTUNITY_LLM_BASE_URL` / `OPPORTUNITY_LLM_MODEL`）时，
  脚本自动在报告尾部附 LLM 增强视角；失败不影响主流程。

## 手动运行

```bash
python3 scripts/opportunity_analysis.py --check   # 只校验输入
python3 scripts/opportunity_analysis.py           # 生成今天报告
```
