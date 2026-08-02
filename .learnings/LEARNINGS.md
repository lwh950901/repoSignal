# Learnings

## [LRN-20260802-001] correction

**Logged**: 2026-08-02T20:12:00+08:00
**Priority**: high
**Status**: promoted
**Area**: config

### Summary
仅少量文案修改应立即处理，不创建规格、计划或额外确认流程。

### Details
在调整顶部 Tab 的几个短标签时，原流程把一个可直接完成的文案替换扩展成了设计文档、用户复核和提交步骤，增加了不必要的等待。用户明确纠正：当改动仅涉及少量现有文案，目标和替换内容已经清楚时，应直接修改并进行与风险相称的轻量验证。

### Suggested Action
先判断是否属于局部、明确、低风险的纯文案替换；若是，跳过 brainstorming、规格和实施计划，直接编辑相关文件并运行定向检查。只有文案会改变信息架构、产品行为或存在关键歧义时，才进入设计流程。

### Metadata
- Source: user_feedback
- Related Files: src/components/PeriodSwitcher.astro, docs/superpowers/specs/2026-08-02-period-tab-labels-design.md
- Tags: workflow, copy-editing, planning, user-preference
- Promoted: AGENTS.md

---

## [LRN-20260629-001] correction

**Logged**: 2026-06-29T00:00:00+08:00
**Priority**: high
**Status**: resolved
**Area**: config

### Summary
GitHub 项目推荐中，用户反馈标注只能辅助微调，发现真正高质量项目始终是最高优先级。

### Details
最初的设计容易让“收藏 / 一般 / 不感兴趣”看起来像主要排序依据。用户明确指出标注优先度不是最高。正确原则是保持探索性与质量优先，反馈只在候选质量接近时影响排序，不能把推荐固化在既有兴趣中。

### Suggested Action
在自动任务提示和评分规则中明确：核心质量评分决定入围，反馈仅作次级排序信号，并保留跨领域惊喜项目的位置。

### Metadata
- Source: user_feedback
- Related Files: docs/superpowers/specs/2026-06-29-github-project-digest-design.md
- Tags: github-discovery, feedback, ranking, exploration

### Resolution
- **Resolved**: 2026-06-29T00:00:00+08:00
- **Notes**: 已将反馈机制降为次级信号，并明确项目质量和发现价值优先。

---

## [LRN-20260629-002] correction

**Logged**: 2026-06-29T12:45:00+08:00
**Priority**: high
**Status**: resolved
**Area**: config

### Summary
自动任务依赖特定 skill 时，任务提示必须显式要求调用该 skill，不能只在创建任务的当前对话中使用。

### Details
受控试运行读取并执行了 `find-github-projects` 的扫描器与评分规则，但最初的两个自动任务提示只复述了类似工作流，没有明确要求未来独立运行显式调用该 skill。因此后续任务可能绕过 skill，只模仿输出格式。

### Suggested Action
在每日发现与每周精选提示开头写明必须调用 `find-github-projects`、读取其评分规则，并在结果中报告 skill、扫描器和降级路径的实际使用情况。

### Metadata
- Source: user_feedback
- Related Files: /Users/elvis/.codex/automations/github/automation.toml, /Users/elvis/.codex/automations/github-2/automation.toml
- Tags: automation, skills, github-discovery, prompt-contract

### Resolution
- **Resolved**: 2026-06-29T12:45:00+08:00
- **Notes**: 两个自动任务均已加入强制 skill 调用与执行证据要求；周任务同时限制 live search 只能核验本周候选。

---
