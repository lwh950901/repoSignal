# Learnings

## [LRN-20260809-005] correction

**Logged**: 2026-08-09T16:12:13+08:00
**Priority**: critical
**Status**: pending
**Area**: backend

### Summary
月报候选范围应只来自已发布日报和周报；候选账本是扫描审计层，不是月报可直接选材的发布来源。

### Details
用户明确质疑月报筛选候选账本。2026-07-20 的设计为了让月报“不是四份周报的拼接”并扩大人工策展池，未经可验证的用户要求就把候选账本、日报和周报并列为月报来源；实现计划随后把这一选择固化进 `generate_monthly_digest.py`。这允许未进入任何日报或周报的扫描候选（如 Mailpit）直接进入月报，绕过推荐历史与既有发布层级。正确层级是：候选账本只服务每日发现的扫描、审计和筛选；日报发布发现；周报从日报精选；月报从已发布日报与周报汇总并重新核实，不应从候选账本补项目。

### Suggested Action
从月报生成器的 `collect_candidates` 删除 `candidate_evidence` 输入，更新测试确保仅存在于候选账本的仓库不会进入月度候选，并同步修正文档与月报自动化提示。保留候选账本本身供日报审计使用。

### Metadata
- Source: user_feedback
- Related Files: scripts/generate_monthly_digest.py, docs/superpowers/specs/2026-07-20-monthly-selection-design.md, docs/superpowers/specs/2026-07-20-monthly-business-research-redesign.md, README.md
- Tags: monthly-source-boundary, candidate-ledger, publication-pipeline, correction
- See Also: LRN-20260809-004, LRN-20260809-003

---

## [LRN-20260827-001] correction

**Logged**: 2026-08-27T20:20:00+08:00
**Priority**: medium
**Status**: resolved
**Area**: config

### Summary
“在开源雷达周刊新增可行性方案”指完整周刊中的完整方案同步，不是独立的精简方案卡预览。

### Details
先前把测试产物做成了只含三个摘要卡片的预览，并在标题中加入“测试预览”。用户明确要求保持正式周刊标题、交付完整开源雷达周刊数据，并让“本周可行性精选”与来源 feasibility 方案内容同步且无缺漏。

后续又把“至少展示 1 个”实现成没有合格方案就阻塞整个周刊。用户进一步明确：可行性方案是附加内容，任何缺失或质量不足都不能阻塞开源雷达周刊主任务。

### Suggested Action
自动任务应完整复制入选方案的评分、定位、目标客户、市场机会、可行性依据、组合表、差异化、MVP、全部风险和验证路径，仅转换小节标题以避开项目解析器；全文项目数量校验应按周报项目章节计算，而不是按全部 GitHub 链接计算。有本周可行性数据时展示 1–3 个；数据缺失或无法安全展示时应跳过该章节并照常完成主周刊。

### Metadata
- Source: user_feedback
- Related Files: /Users/elvis/.codex/automations/automation/automation.toml, data/github-project-digest/feasibility/*.md, src/lib/radar.ts
- Tags: radar, feasibility, automation, output-contract
- Pattern-Key: radar.optional_feasibility.must_not_block
- Recurrence-Count: 2

### Resolution
- **Resolved**: 2026-08-27T20:20:00+08:00
- **Notes**: 后续任务契约按完整方案同步修正，并明确可行性附加内容不得阻塞周刊主任务。

---

## [LRN-20260827-002] correction

**Logged**: 2026-08-27T20:30:00+08:00
**Priority**: high
**Status**: resolved
**Area**: config

### Summary
月报中的“真实业务与项目机会”就是可行性方案的月度公开形态，不应另建“本月可行性精选”章节。

### Details
先前把月度业务机会研究与 feasibility 方案错误地定义为两个独立输出，导致重复信息、重复计数和不必要的数据模型扩展。正确关系是：月度任务从当月 feasibility 数据中去重筛选方案，再补充月度需求证据、竞品调查和组合验证，最终写入现有“真实业务与项目机会”章节。

### Suggested Action
月度自动任务继续复用现有 MonthlyOpportunity 合同与页面，不新增独立 feasibility 集合或导航；当月有至少三个唯一方案时，公开恰好三个经过月度核实的机会，数据不足时展示全部且不阻塞。

### Metadata
- Source: user_feedback
- Related Files: /Users/elvis/.codex/automations/top-5/automation.toml, src/lib/monthly.ts, src/components/MonthlyReportView.astro
- Tags: monthly, feasibility, opportunity, domain-model

### Resolution
- **Resolved**: 2026-08-27T20:30:00+08:00
- **Notes**: 月度任务恢复单一“真实业务与项目机会”章节，feasibility 作为其候选来源和研究底稿。

---

## [LRN-20260809-004] correction

**Logged**: 2026-08-09T16:08:15+08:00
**Priority**: high
**Status**: pending
**Area**: docs

### Summary
仓库设计文档中的规则不能直接归因于用户明确说过；应区分可验证的书面记录与会话来源。

### Details
用户追问“什么时候说过月报需要筛选候选账本”。Git 证据只能确认该规则最早写入 2026-07-20 的月度设计文档，由 Elvis 提交，并在同日的业务研究重构和 README 中继续保留。当前上下文没有用户原话或审批记录，提交作者也不能证明规则由用户主动提出。此前把现行规格自然地当成用户意图，归因过度。

### Suggested Action
回答历史决策来源时分别说明：当前会话明确要求、仓库现行规格、Git 最早记录、以及无法确认的原始讨论；没有会话证据时不要说“用户要求过”。

### Metadata
- Source: user_feedback
- Related Files: docs/superpowers/specs/2026-07-20-monthly-selection-design.md, docs/superpowers/specs/2026-07-20-monthly-business-research-redesign.md, README.md
- Tags: provenance, git-history, user-intent, correction
- See Also: LRN-20260809-002, LRN-20260809-003

---

## [LRN-20260809-003] correction

**Logged**: 2026-08-09T15:55:14+08:00
**Priority**: high
**Status**: pending
**Area**: docs

### Summary
雷达周刊只以本周周报和日报为事实来源是正确契约；读取月度内容只能是可选的分发去重参考，不能称为缺失输入。

### Details
用户指出雷达周刊本来就应根据本周周精选和日发现撰写。此前将“没有读取月度全文”描述为自动化缺陷，混淆了事实来源与跨栏目编辑协调。当前 W32 草稿忠实包含周报最终 10 项，因此包含 Mailpit 是符合既有任务要求的；与月度发现重合是两个栏目共享上游项目产生的自然结果。只有用户额外要求避免跨栏目重复时，才应增加月度内容作为负向编辑参考，而且不得用它改变本周事实或项目名单。

### Suggested Action
后续解释和实现时明确两层：日报/周报决定雷达项目与事实；月度内容若启用，只用于标记延续观察、调整角度或提示重复，不作为事实来源和选项过滤器。

### Metadata
- Source: user_feedback
- Related Files: data/github-project-digest/distribution-drafts/2026-W32-wechat.md, data/github-project-digest/weekly/2026-W32.md, data/github-project-digest/monthly/2026-07.md
- Tags: source-contract, editorial-deduplication, radar-weekly, monthly, correction
- See Also: LRN-20260809-001, LRN-20260809-002

---

## [LRN-20260809-002] correction

**Logged**: 2026-08-09T15:49:00+08:00
**Priority**: critical
**Status**: pending
**Area**: docs

### Summary
用户说“这周雷达周刊”时应先确认其指向已公开最新一期，而不能默认指向尚未发布的当前周审核稿。

### Details
用户询问雷达周刊与月度发现重合，实际指的是已公开 `radar/2026-W31.md` 与 `monthly/2026-07.md`。此前错误地比较了新生成但未发布的 `distribution-drafts/2026-W32-wechat.md`，因此只发现 Mailpit 这一无关重合。正确对比显示 W31 雷达 10 项中有 3 项与 7 月月度发现重合：`cvat-ai/cvat`、`heygen-com/hyperframes`、`alibaba/open-code-review`。

### Suggested Action
处理“本周、最新、当前”内容问题时，先根据发布目录和草稿目录区分公开最新一期与待审核下一期；报告比较对象和发布状态后再分析重合。

### Metadata
- Source: user_feedback
- Related Files: data/github-project-digest/radar/2026-W31.md, data/github-project-digest/monthly/2026-07.md, data/github-project-digest/distribution-drafts/2026-W32-wechat.md
- Tags: publication-state, period-resolution, radar-weekly, monthly, correction
- See Also: LRN-20260809-001

---

## [LRN-20260809-001] correction

**Logged**: 2026-08-09T15:45:30+08:00
**Priority**: high
**Status**: pending
**Area**: docs

### Summary
月报与雷达周刊内容重合是分发层的编辑问题，不应擅自扩大为周报选项或推荐历史问题。

### Details
用户指出 W32 周报本身没有问题；问题只在公众号雷达周刊与已发布月度发现出现重合。此前建议重做周报名单、替换 Mailpit 并修改跨周期去重，错误地改变了上游事实来源和周报职责。正确边界是保持周报最终 10 项不变，在雷达周刊写作前读取最近月度内容；遇到重合项目时，将其标为延续观察，换用本周新增证据和不同编辑角度，避免把月度内容重新包装成首次发现。

### Suggested Action
修改雷达周刊自动化写作规则：月报只作为分发文案去重参考，不影响周报项目选择；重合项目仍完整出现，但必须说明与月度内容的关系、避免复述原角度，并聚焦本周更新与单仓库试用边界。

### Metadata
- Source: user_feedback
- Related Files: data/github-project-digest/distribution-drafts/2026-W32-wechat.md, data/github-project-digest/monthly/2026-07.md, data/github-project-digest/weekly/2026-W32.md
- Tags: editorial-scope, radar-weekly, monthly, overlap, correction

---

## [LRN-20260809-002] correction

**Logged**: 2026-08-09T18:25:00+08:00
**Priority**: critical
**Status**: pending
**Area**: config

### Summary
周精选必须覆盖当周周一至周六全部已要求的日报；缺少任何一天时应阻塞，不能提前锁定不完整候选范围。

### Details
W32 周报在 8 月 8 日日报尚未生成时，仍使用周一至周五 32 个候选完成了 10 项精选。8 月 8 日日报后来补录了 7 个候选，但此前只修改周报说明为“范围已锁定”，没有重新筛选，违背了“本周日报和周报”的输入边界。正确处理是把六份日报视为完整输入集合；任何一份缺失都不生成周报，输入补齐后必须基于全部候选重新统一复核。

### Suggested Action
在周报自动化中增加六份日报存在性硬检查，缺一即阻塞且不写周报；雷达自动化也应在读取周报前确认六份日报齐全，并确认周报的候选范围确实包含周一至周六。修正 W32 周报后再据其重写雷达 10 项。

### Metadata
- Source: user_feedback
- Related Files: /Users/elvis/.codex/automations/github-2/automation.toml, /Users/elvis/.codex/automations/automation/automation.toml, data/github-project-digest/weekly/2026-W32.md, data/github-project-digest/daily/2026-08-08.md
- Tags: weekly-digest, input-completeness, automation, blocking, correction

---

## [LRN-20260809-003] correction

**Logged**: 2026-08-09T19:30:00+08:00
**Priority**: high
**Status**: resolved
**Area**: docs

### Summary
雷达项目段落应沿用历史结构，把推荐依据放在“适合”之前，并让“适合”与“注意”直接相邻。

### Details
为减少 AI 模板腔，W32 删除了重复的“为什么推荐”标签，但没有移动其正文，导致每项形成“适合 → 无标签推荐段落 → 注意”的新结构。W31 及此前文章的稳定阅读顺序是先完成项目介绍和推荐判断，再给出“适合”和“注意”。只删标签、不调整段落位置破坏了栏目一致性。

### Suggested Action
雷达自动化固定项目内部顺序为“项目介绍与推荐依据 → 适合 → 注意”，禁止在“适合”和“注意”之间插入段落，也不恢复模板化“为什么推荐”标签。

### Metadata
- Source: user_feedback
- Related Files: data/github-project-digest/radar/2026-W32.md, data/github-project-digest/distribution-drafts/2026-W32-wechat.md, /Users/elvis/.codex/automations/automation/automation.toml
- Tags: radar-weekly, editorial-structure, consistency, correction

### Resolution
- **Resolved**: 2026-08-09T19:30:00+08:00
- **Notes**: 已重排 W32 两份雷达稿的 10 个项目段落，将固定顺序写入雷达自动化，并在公开雷达解析器中加入“适合”与“注意”相邻的构建期回归检查。

---

## [LRN-20260809-004] correction

**Logged**: 2026-08-09T19:30:00+08:00
**Priority**: high
**Status**: resolved
**Area**: docs

### Summary
从 W32 起，雷达项目正文固定使用“补充介绍、推荐依据、适合、注意”四个同级加粗标签。

### Details
仅把推荐依据移动到“适合”之前仍没有完全满足格式一致性：前两段保持无标签，而后两段有“适合、注意”标签，视觉层级不统一。用户进一步明确，补充介绍和推荐依据也应与适合、注意采用相同格式。

### Suggested Action
每个项目严格按 `**补充介绍：**`、`**推荐依据：**`、`**适合：**`、`**注意：**` 的顺序书写，四项各占一个自然段，不插入无标签段落。历史冻结文章不迁移，新格式从 W32 起由解析器、测试、自动化和 Luna 清单共同强制。

### Metadata
- Source: user_feedback
- Related Files: data/github-project-digest/radar/2026-W32.md, data/github-project-digest/distribution-drafts/2026-W32-wechat.md, src/lib/radar.ts, src/lib/radar.test.ts, /Users/elvis/.codex/automations/automation/automation.toml
- Tags: radar-weekly, labeled-sections, format-contract, correction

### Resolution
- **Resolved**: 2026-08-09T19:30:00+08:00
- **Notes**: W32 两份雷达稿已统一四标签格式；构建期校验、测试、自动化和 Luna 复核清单均已同步。

---

## [LRN-20260809-005] correction

**Logged**: 2026-08-09T19:34:00+08:00
**Priority**: high
**Status**: resolved
**Area**: docs

### Summary
雷达四标签的第一个标签必须精确写为“介绍”，不能扩写成“补充介绍”。

### Details
用户要求前两段与“适合、注意”使用同级标签时，错误地把第一个标签命名为“补充介绍”。用户随后明确正确名称是“介绍”。这说明格式契约不仅要约束顺序和层级，还要约束标签的精确文字，不能自行扩写。

### Suggested Action
从 W32 起只接受 `**介绍：**`、`**推荐依据：**`、`**适合：**`、`**注意：**` 四个精确标签。自动化、Luna 清单、解析器错误信息和测试均使用同一组常量文字。

### Metadata
- Source: user_feedback
- Related Files: data/github-project-digest/radar/2026-W32.md, data/github-project-digest/distribution-drafts/2026-W32-wechat.md, src/lib/radar.ts, src/lib/radar.test.ts, /Users/elvis/.codex/automations/automation/automation.toml
- Tags: radar-weekly, exact-labels, format-contract, correction

### Resolution
- **Resolved**: 2026-08-09T19:34:00+08:00
- **Notes**: W32 稿件、构建校验、测试、自动化和 Luna 清单已全部改为精确标签“介绍”。

---

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

## [LRN-20260814-001] correction

**Logged**: 2026-08-14T18:41:18+08:00
**Priority**: medium
**Status**: pending
**Area**: config

### Summary
用户询问“每一类的优化方案”时，应围绕各类型分别优化，不扩展成整个发现流程的基础设施方案。

### Details
在 GitHub 日报规则讨论中，用户要求为爆发型、实用型、潜力型、学习型分别增加细节优化。先前回答把重点放到了指标快照、证据账本和整体判定流程，偏离了用户想比较四类自身筛选条件的范围。

### Suggested Action
遇到同类请求时，按类型逐项给出目标、加分项、否决项和建议阈值；只有用户明确询问整体流程时，再讨论扫描、快照、账本和验证基础设施。

### Metadata
- Source: user_feedback
- Related Files: docs/superpowers/specs/2026-06-29-github-project-digest-design.md
- Tags: github-discovery, classification, scope-control, automation
- Pattern-Key: github_digest.answer_scope.per_type
- Recurrence-Count: 2
- First-Seen: 2026-08-14T18:41:18+08:00
- Last-Seen: 2026-08-14T18:44:11+08:00

---
