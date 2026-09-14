import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROMPT = ROOT / "docs" / "automation-prompts" / "github-daily.md"


class DailyAutomationContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = PROMPT.read_text(encoding="utf-8")

    def test_prompt_is_short_and_preserves_quality_contract(self):
        self.assertLessEqual(len(self.text), 6500)
        for required in (
            "find-github-projects",
            "社区信号 25%",
            "维护状态 25%",
            "项目质量 20%",
            "用户适合度 20%",
            "风险 10%",
            "爆发型、实用型、潜力型、学习型",
            "十个字段",
            "90 天",
            "feasibility",
        ):
            self.assertIn(required, self.text)

    def test_prompt_enforces_resource_limits(self):
        for required in (
            "最多 6 条",
            "每条最多 12 个",
            "只对最终 4–5 项",
            "每项最多 2 个",
            "4,000 tokens",
            "35 分钟",
            "40 分钟",
            "不得循环重试",
        ):
            self.assertIn(required, self.text)
        self.assertNotIn("response_length=long", self.text)

    def test_prompt_requires_checkpoint_and_forbids_automatic_retry(self):
        self.assertIn("daily_digest_checkpoint.py inspect", self.text)
        self.assertIn("daily_digest_checkpoint.py finalize", self.text)
        self.assertRegex(self.text, r"不自动补跑|禁止自动补跑")
        self.assertIn("日报是主产物", self.text)

    def test_schedule_contract_has_only_one_start_time(self):
        match = re.search(r"RRULE：`([^`]+)`", self.text)
        self.assertIsNotNone(match)
        self.assertEqual(
            "FREQ=WEEKLY;BYDAY=MO,TU,WE,TH,FR,SA;BYHOUR=5;BYMINUTE=30;BYSECOND=0",
            match.group(1),
        )
        self.assertEqual(1, self.text.count("BYHOUR="))


if __name__ == "__main__":
    unittest.main()
