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


if __name__ == "__main__":
    unittest.main()
