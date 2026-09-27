import tempfile
import json
import unittest
from pathlib import Path

from scripts import weekly_feasibility_selector as selector


def plan(title, score, *repositories):
    rows = "\n".join(
        f"| role | [`{repo}`](https://github.com/{repo}) |"
        for repo in repositories
    )
    return f"""### 1. {title}

**方案评分**：**{score}/100（中）**

**业务定位**：test

| role | project |
|---|---|
{rows}
"""


class WeeklySelectorTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tempdir.name)
        (self.root / "feasibility").mkdir()
        (self.root / "radar").mkdir()

    def tearDown(self):
        self.tempdir.cleanup()

    def write_feasibility(self, day, body):
        (self.root / "feasibility" / f"{day}.md").write_text(
            f"# test\n\n## 可行性方案\n\n{body}\n\n## 单点项目机会（供参考）\n",
            encoding="utf-8",
        )

    def write_radar(self, week, body):
        (self.root / "radar" / f"{week}.md").write_text(
            f"# 开源雷达周刊\n\n## 本周可行性精选\n\n{body}\n\n## 本周优先试用\n",
            encoding="utf-8",
        )

    def test_prior_four_week_family_is_hard_blocked_even_when_variant_changes(self):
        self.write_feasibility(
            "2026-08-31",
            plan("本地优先个人 AI 工作台（组合 2 个项目）", 88,
                 "new/one", "new/two"),
        )
        self.write_radar(
            "2026-W35",
            plan("本地优先个人 AI 工作台（组合 2 个项目）", 80,
                 "old/one", "old/two").replace("### 1.", "### 可行性方案 1："),
        )

        result = selector.select_weekly_plans("2026-W36", self.root)

        self.assertEqual(result["selected"], [])
        self.assertEqual(
            result["blockedFamilies"],
            ["local-first-personal-ai-workbench"],
        )

    def test_current_week_deduplicates_family_and_keeps_best_variant(self):
        self.write_feasibility(
            "2026-08-31",
            plan("多 Agent 协作控制面（团队级）", 74, "a/one", "a/two"),
        )
        self.write_feasibility(
            "2026-09-01",
            plan("多 Agent 协作控制面（团队级）", 82, "b/one", "b/two"),
        )

        result = selector.select_weekly_plans("2026-W36", self.root)

        self.assertEqual(result["candidateCount"], 2)
        self.assertEqual(result["deduplicatedCount"], 1)
        self.assertEqual(len(result["selected"]), 1)
        self.assertEqual(result["selected"][0]["sourceDate"], "2026-09-01")

    def test_missing_days_are_non_blocking_and_selection_is_not_padded(self):
        self.write_feasibility(
            "2026-09-02",
            plan("企业内部知识助手（私有化 RAG × Agent）", 69,
                 "a/one", "a/two"),
        )

        result = selector.select_weekly_plans("2026-W36", self.root)

        self.assertEqual(result["datesRead"], ["2026-09-02"])
        self.assertEqual(result["selected"], [])
        self.assertEqual(len(result["missingDates"]), 5)

    def test_selects_plan_with_current_dual_score_format(self):
        self.write_feasibility(
            "2026-08-31",
            plan("可溯源的知识问答工作台", 92, "a/one", "b/two")
            .replace(
                "**方案评分**：**92/100（中）**",
                "**双评分**：技术组合成熟度 **92/100（高）** · "
                "需求证据强度 **59/100（低）**",
            ),
        )

        result = selector.select_weekly_plans("2026-W36", self.root)

        self.assertEqual(result["candidateCount"], 1)
        self.assertEqual(len(result["selected"]), 1)
        self.assertEqual(result["selected"][0]["score"], 92)

    def test_uses_history_identity_when_daily_display_name_changed(self):
        repositories = ["a/one", "b/two"]
        self.write_feasibility(
            "2026-08-31",
            plan("设计稿到组件代码交付管线", 92, *repositories),
        )
        history = {
            "date": "2026-08-31",
            "family": "design-to-code-delivery",
            "variant": selector.analysis.plan_variant(repositories),
            "repositories": repositories,
        }
        (self.root / "feasibility" / "plan-history.jsonl").write_text(
            json.dumps(history, ensure_ascii=False) + "\n", encoding="utf-8"
        )
        self.write_radar(
            "2026-W35",
            plan("设计稿到组件代码交付管线", 80, "old/one")
            .replace("### 1.", "### 可行性方案 1：")
            + "\n**方案身份**：`plan_family=design-to-code-delivery` "
            "· `variant=old-variant`\n",
        )

        result = selector.select_weekly_plans("2026-W36", self.root)

        self.assertEqual(result["candidateCount"], 1)
        self.assertEqual(result["blockedFamilies"], ["design-to-code-delivery"])
        self.assertEqual(result["selected"], [])

    def test_rejects_unrecognized_score_instead_of_silently_skipping_plan(self):
        self.write_feasibility(
            "2026-08-31",
            plan("新的方案", 92, "a/one", "b/two")
            .replace("**方案评分**", "**新评分格式**"),
        )

        with self.assertRaisesRegex(ValueError, "2026-08-31"):
            selector.select_weekly_plans("2026-W36", self.root)

    def test_prior_radar_without_visible_identity_uses_plan_history(self):
        prior_repositories = ["old/one", "old/two"]
        current_repositories = ["new/one", "new/two"]
        self.write_radar(
            "2026-W35",
            plan("更早的展示名称", 80, *prior_repositories)
            .replace("### 1.", "### 可行性方案 1："),
        )
        self.write_feasibility(
            "2026-08-31",
            plan("本周展示名称", 92, *current_repositories),
        )
        records = [
            {"date": "2026-08-25", "family": "same-business-family",
             "variant": selector.analysis.plan_variant(prior_repositories)},
            {"date": "2026-08-31", "family": "same-business-family",
             "variant": selector.analysis.plan_variant(current_repositories)},
        ]
        (self.root / "feasibility" / "plan-history.jsonl").write_text(
            "".join(json.dumps(record) + "\n" for record in records), encoding="utf-8"
        )

        result = selector.select_weekly_plans("2026-W36", self.root)

        self.assertEqual(result["blockedFamilies"], ["same-business-family"])
        self.assertEqual(result["selected"], [])


if __name__ == "__main__":
    unittest.main()
