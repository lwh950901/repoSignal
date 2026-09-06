import tempfile
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


if __name__ == "__main__":
    unittest.main()
