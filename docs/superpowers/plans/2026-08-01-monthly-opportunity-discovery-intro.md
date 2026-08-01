# 月报机会发现流程简介 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在月报“真实业务与项目机会”章节简介中说明发现流程，并直接解释 L2、L3。

**Architecture:** 复用 `MonthlyReportView.astro` 已有的章节简介节点，将其放到标题正下方，并为该章节使用单列标题布局。用现有布局合同测试锁定文案和层级，不增加 Markdown 字段、解析逻辑、组件或依赖。

**Tech Stack:** Astro、TypeScript、Vitest、CSS

---

### Task 1: 替换机会章节简介

**Files:**
- Modify: `src/components/layout-contract.test.ts`
- Modify: `src/components/MonthlyReportView.astro`

- [x] **Step 1: 写入失败测试**

在月报布局合同测试中加入：

```ts
expect(view).toContain("至少一个核心仓库需跑通单仓库核心流程（L2）");
expect(view).toContain("两个以上仓库用真实格式数据完成连接（L3）");
```

- [x] **Step 2: 运行测试并确认失败**

Run: `npm test -- src/components/layout-contract.test.ts`

Expected: FAIL，提示新简介片段不存在。

- [x] **Step 3: 完成最小实现**

把 `MonthlyReportView.astro` 中机会章节标题旁的简介替换为：

```astro
<p>先从本月仓库中寻找可组合的能力，再核对需求证据、商业产品、开源替代和现实人工流程。至少一个核心仓库需跑通单仓库核心流程（L2）；随后尝试让两个以上仓库用真实格式数据完成连接（L3），未跑通则明确降级。</p>
```

- [x] **Step 4: 运行聚焦测试并确认通过**

Run: `npm test -- src/components/layout-contract.test.ts`

Expected: 该测试文件全部通过。

- [x] **Step 5: 完成综合验证**

依次运行：

```text
npm test
npm run check
npm run build
```

Expected: 所有测试通过、Astro 诊断为零、生产构建完成。随后检查 1440px 与 360px 静态页面，确认简介换行正常且 `scrollWidth` 不超过视口宽度。

- [x] **Step 6: 保留未提交状态**

按本任务约束不执行 `git add`、`git commit` 或 `git push`；只报告相关修改和验证结果。

### Task 2: 增加四步发现流程

**Files:**
- Modify: `src/components/layout-contract.test.ts`
- Modify: `src/components/MonthlyReportView.astro`
- Modify: `src/styles/global.css`

- [x] **Step 1: 写入失败测试**

在月报布局合同测试中断言语义化流程、四个步骤和响应式网格存在：

```ts
expect(view).toContain('aria-labelledby="monthly-discovery-title"');
expect(view).toContain('<h3 id="monthly-discovery-title">发现流程</h3>');
expect(view).toContain("01｜仓库盘点");
expect(view).toContain("02｜需求核实");
expect(view).toContain("03｜组合设计");
expect(view).toContain("04｜验证发布");
expect(styles).toMatch(/\.monthly-discovery__steps\s*\{[^}]*grid-template-columns:\s*repeat\(4,/s);
expect(styles).toMatch(/@media \(max-width: 768px\)[\s\S]*\.monthly-discovery__steps\s*\{[^}]*grid-template-columns:\s*1fr/s);
```

- [x] **Step 2: 运行测试并确认失败**

Run: `npm test -- src/components/layout-contract.test.ts`

Expected: FAIL，提示发现流程标记不存在。

- [x] **Step 3: 完成最小实现**

在机会章节简介之后加入静态、语义化的 `section > h3 + ol`，包含已确认的四步文案。为 `.monthly-discovery__steps` 添加桌面四列网格，并在现有 `max-width: 768px` 媒体查询中切换为单列。流程不增加数据字段或 JavaScript。

- [x] **Step 4: 运行聚焦测试并确认通过**

Run: `npm test -- src/components/layout-contract.test.ts`

Expected: 该测试文件 10/10 通过。

- [x] **Step 5: 完成综合与视觉验证**

依次运行 `npm test`、`npm run check`、`npm run build`。在 1440px 和 360px 视口打开 `/monthly/2026-07/`，确认流程分别为四列和单列，标题、简介、流程、机会卡片顺序正确，且 `scrollWidth` 等于视口宽度。

- [x] **Step 6: 保留未提交状态**

不执行提交、合并或推送；保留当前分支和用户已有改动。
