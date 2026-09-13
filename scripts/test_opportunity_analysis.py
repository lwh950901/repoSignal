import unittest

from scripts import opportunity_analysis as analysis


class PlanIdentityTests(unittest.TestCase):
    def test_fixed_template_keeps_family_when_components_change(self):
        name = "本地优先个人 AI 工作台（组合 5 个项目，今日锚点 2 个）"

        self.assertEqual(analysis.plan_family(name), "local-first-personal-ai-workbench")
        self.assertEqual(
            analysis.plan_family(name),
            analysis.plan_family("本地优先个人 AI 工作台"),
        )
        self.assertNotEqual(
            analysis.plan_variant(["owner/one", "owner/two"]),
            analysis.plan_variant(["owner/one", "owner/three"]),
        )

    def test_variant_is_independent_of_component_order_and_case(self):
        expected = analysis.plan_variant(["Owner/One", "owner/two"])

        self.assertEqual(
            analysis.plan_variant(["OWNER/TWO", "owner/one", "owner/one"]),
            expected,
        )

    def test_legacy_markdown_derives_identity_from_heading_and_links(self):
        markdown = """# GitHub 项目组合可行性方案｜2026-08-29

## 可行性方案

### 1. 本地优先个人 AI 工作台（组合 2 个项目，今日锚点 1 个）

| 角色 | 项目 |
|---|---|
| 编排 | [`owner/one`](https://github.com/Owner/One) |
| 记忆 | [`owner/two`](https://github.com/owner/two) |

## 单点项目机会（供参考）
"""

        identities = analysis.parse_plan_identities(markdown)

        self.assertEqual(len(identities), 1)
        self.assertEqual(identities[0]["family"], "local-first-personal-ai-workbench")
        self.assertEqual(
            identities[0]["variant"],
            analysis.plan_variant(["owner/one", "owner/two"]),
        )
        self.assertEqual(identities[0]["repositories"], ["owner/one", "owner/two"])

    def test_explicit_identity_is_preserved_for_new_reports(self):
        markdown = """## 可行性方案

### 1. 自定义方案（组合 1 个项目）

**方案身份**：`plan_family=manual-family` · `variant=manual-variant`

| 角色 | 项目 |
|---|---|
| test | [`owner/one`](https://github.com/owner/one) |
"""

        identities = analysis.parse_plan_identities(markdown)

        self.assertEqual(identities[0]["family"], "manual-family")
        self.assertEqual(identities[0]["variant"], "manual-variant")


class ReuseAwareSelectionTests(unittest.TestCase):
    @staticmethod
    def project(repo, tag_score=5, stars=0):
        return {
            "id": repo,
            "repo": repo,
            "score": 85,
            "stars": stars,
            "tags": {"agent": tag_score},
            "fields": {"risks": "", "quality": "", "activity": ""},
        }

    def test_pick_best_penalizes_recent_component_reuse(self):
        frequent = self.project("owner/frequent", stars=1000)
        fresh = self.project("owner/fresh", stars=10)

        selected = analysis.pick_best(
            [frequent, fresh],
            "agent",
            set(),
            set(),
            reuse_counts={"owner/frequent": 3},
        )

        self.assertEqual(selected["id"], "owner/fresh")

    def test_portfolio_may_return_fewer_than_three_plans(self):
        a = self.project("owner/shared")
        b = self.project("owner/other")
        combos = [
            {"name": "first", "score": 80, "today_count": 2, "total": 1,
             "stars": 100, "picks": {"agent": a}},
            {"name": "overlapping", "score": 74, "today_count": 2, "total": 2,
             "stars": 90, "picks": {"agent": a, "memory": b}},
            {"name": "below-threshold", "score": 69, "today_count": 3, "total": 1,
             "stars": 200, "picks": {"agent": b}},
        ]

        selected = analysis.select_combo_portfolio(combos, max_count=3)

        self.assertEqual([combo["name"] for combo in selected], ["first"])

    def test_portfolio_does_not_restore_rejected_candidates(self):
        combo = {
            "name": "blocked-quality",
            "score": 69,
            "today_count": 3,
            "total": 1,
            "stars": 100,
            "picks": {"agent": self.project("owner/only")},
        }

        self.assertEqual(analysis.select_combo_portfolio([combo]), [])


class FeasibilityRenderingTests(unittest.TestCase):
    def test_combo_table_only_exposes_role_project_and_reason(self):
        project = {
            "id": "owner/tool",
            "repo": "owner/tool",
            "url": "https://github.com/owner/tool",
            "score": 85,
            "stars": 100,
            "tags": {"agent": 5},
            "source": "daily",
            "source_date": "2026-09-07",
            "fields": {
                "value": "完成最小任务闭环。",
                "risks": "需先在隔离环境验证。",
                "quality": "",
                "activity": "",
                "metrics": "MIT",
            },
        }
        combo = {
            "name": "test plan",
            "score": 80,
            "score_parts": [("组件可靠度", 30, 35)],
            "plan_family": "test-family",
            "variant": "test-variant",
            "pitch": "test pitch",
            "target": "test audience",
            "market": "test market",
            "rationale": "test rationale",
            "picks": {"Agent 编排": project},
            "slot_supply": {"agent": 1},
            "min_supply": 1,
            "total": 1,
            "today_count": 1,
            "stars": 100,
            "differentiation": "test differentiation",
            "mvp": "test mvp",
        }

        report = analysis.render(
            [project], [project], [combo], [], "2026-09-07", "2026-06-09",
            "2026-09-07", 1, 0, None,
        )

        self.assertIn("| 角色 | 项目 | 入选理由 |", report)
        self.assertNotIn("| 角色 | 项目 | 来源 | 许可证 | 入选理由 |", report)
        self.assertIn(
            "| Agent 编排 | [`owner/tool`](https://github.com/owner/tool) | 完成最小任务闭环。 |",
            report,
        )


class AnchorBusinessNamingTests(unittest.TestCase):
    @staticmethod
    def project(repo, tags, tagline, stars=0):
        return {
            "id": repo,
            "repo": repo,
            "url": f"https://github.com/{repo}",
            "score": 85,
            "stars": stars,
            "tags": tags,
            "source_date": "2026-09-07",
            "fields": {
                "tagline": tagline,
                "risks": "",
                "quality": "",
                "activity": "",
                "metrics": "MIT",
            },
        }

    def test_business_name_composes_qualifier_and_core(self):
        self.assertEqual(
            analysis.anchor_business_name({"agent", "local", "rag", "observability"}),
            "本地优先 Agent 工作台",
        )
        self.assertEqual(
            analysis.anchor_business_name({"agent", "comm", "rag"}),
            "团队协作 Agent 工作台",
        )

    def test_every_capability_face_has_business_naming(self):
        for tag in analysis.TAG_RULES:
            self.assertIn(tag, analysis.ANCHOR_CORE_NOUN)
            self.assertIn(tag, analysis.ANCHOR_QUALIFIER)

    def test_anchor_combo_reuses_template_name_when_faces_match(self):
        projects = [
            self.project("owner/local", {"local": 5}, "本地优先笔记应用。", stars=500),
            self.project("owner/agent", {"agent": 5}, "Agent 编排框架。", stars=400),
            self.project("owner/memory", {"memory": 4}, "长期记忆存储。", stars=300),
            self.project("owner/gateway", {"gateway": 4}, "多模型接入网关。", stars=200),
            self.project("owner/rag", {"rag": 4}, "本地知识检索。", stars=100),
        ]

        combo = analysis.build_anchor_combo(
            projects, projects, {p["id"] for p in projects})

        self.assertEqual(combo["name"], "本地优先个人 AI 工作台")
        self.assertEqual(combo["plan_family"], "local-first-personal-ai-workbench")
        self.assertEqual(combo["origin"], "anchor")

    def test_anchor_combo_without_template_match_gets_composed_name(self):
        projects = [
            self.project("owner/agent", {"agent": 6}, "Agent 编排框架。", stars=500),
            self.project("owner/rag", {"rag": 5}, "知识库检索。", stars=300),
            self.project("owner/local", {"local": 4}, "本地优先桌面助手。", stars=100),
        ]

        combo = analysis.build_anchor_combo(
            projects, projects, {p["id"] for p in projects})

        self.assertEqual(combo["name"], "本地优先 Agent 工作台")
        self.assertNotIn("今日锚点组合", combo["name"])
        self.assertTrue(combo["plan_family"].startswith("custom-"))

    def test_anchor_combo_is_suppressed_when_business_name_is_blocked(self):
        projects = [
            self.project("owner/agent", {"agent": 6}, "Agent 编排框架。", stars=500),
            self.project("owner/rag", {"rag": 5}, "知识库检索。", stars=300),
            self.project("owner/local", {"local": 4}, "本地优先桌面助手。", stars=100),
        ]

        combo = analysis.build_anchor_combo(
            projects, projects, {p["id"] for p in projects},
            blocked_names={"本地优先 Agent 工作台"},
        )

        self.assertIsNone(combo)

    def test_render_notes_anchor_origin_plans_only(self):
        project = self.project("owner/tool", {"agent": 5}, "任务闭环工具。")
        combo = {
            "name": "本地优先 Agent 工作台",
            "origin": "anchor",
            "score": 80,
            "score_parts": [("组件可靠度", 30, 35)],
            "plan_family": "custom-e3f7d5a9c2b1",
            "variant": "test-variant",
            "pitch": "按'本地优先 Agent 工作台'方向组合今日项目。",
            "target": "test audience",
            "market": "test market",
            "rationale": "test rationale",
            "picks": {"Agent 编排": project},
            "slot_supply": {"agent": 1},
            "min_supply": 1,
            "total": 1,
            "today_count": 1,
            "stars": 100,
            "differentiation": "test differentiation",
            "mvp": "test mvp",
        }

        def build(origin):
            combo["origin"] = origin
            return analysis.render(
                [project], [project], [combo], [], "2026-09-07", "2026-06-09",
                "2026-09-07", 1, 0, None,
            )

        report = build("anchor")

        self.assertIn("补充说明：固定模板未拼满 3 个方案", report)
        self.assertIn("### 1. 本地优先 Agent 工作台（组合 1 个项目，今日锚点 1 个）", report)
        self.assertNotIn("补充说明", build("template"))


if __name__ == "__main__":
    unittest.main()
