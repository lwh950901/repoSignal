import re
import plistlib
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROMPT = ROOT / "docs" / "automation-prompts" / "github-daily.md"
OPPORTUNITY_PLIST = ROOT / "scripts" / "com.reposignal.opportunity-analysis.plist"


class DailyAutomationContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = PROMPT.read_text(encoding="utf-8")

    def test_prompt_is_short_and_preserves_quality_contract(self):
        self.assertLessEqual(len(self.text), 5500)
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
            "36–60 小时窗口",
            "+200 且 +30%",
            "+500 且 +20%",
            "+1,000 且 +10%",
            "实用型必须",
            "潜力型",
            "学习型",
        ):
            self.assertIn(required, self.text)

    def test_prompt_enforces_resource_limits(self):
        for required in (
            "daily_digest_runner.py discover",
            "daily_digest_runner.py shortlist",
            "最多 6 条",
            "每条最多 12 个",
            "只对最终 4–5 项",
            "每项最多 2 个",
            "4,000 tokens",
            "15 分钟",
            "30 分钟",
            "60 分钟",
            "85 分钟",
            "90 分钟",
            "不得循环重试",
        ):
            self.assertIn(required, self.text)
        self.assertNotIn("response_length=long", self.text)

    def test_prompt_requires_checkpoint_and_forbids_automatic_retry(self):
        self.assertIn("daily_digest_checkpoint.py start", self.text)
        self.assertIn("daily_digest_checkpoint.py resume", self.text)
        self.assertIn("daily_digest_checkpoint.py inspect", self.text)
        self.assertIn("daily_digest_checkpoint.py audit", self.text)
        self.assertIn("daily_digest_checkpoint.py finalize", self.text)
        self.assertRegex(self.text, r"不自动补跑|禁止自动补跑")
        self.assertIn("日报自动化的职责在 finalize 和验证完成后结束", self.text)
        self.assertRegex(self.text, r"resume[^\n]*(?:人工|手动)|(?:人工|手动)[^\n]*resume")

    def test_prompt_forbids_high_context_reads_and_keeps_model(self):
        self.assertIn("不得读取源码", self.text)
        self.assertIn("不得读取完整 memory、history、candidate、feedback 或 trial-status", self.text)
        self.assertIn("gpt-5.6-terra", self.text)
        self.assertIn("high", self.text)

    def test_daily_automation_never_handles_feasibility(self):
        self.assertNotIn("feasibility", self.text.lower())
        self.assertNotIn("run-opportunity-analysis", self.text)

    def test_feasibility_remains_an_independent_launchd_job(self):
        config = plistlib.loads(OPPORTUNITY_PLIST.read_bytes())
        self.assertEqual(
            [
                "/bin/bash",
                "/Users/elvis/Desktop/repo-signal/scripts/run-opportunity-analysis.sh",
            ],
            config["ProgramArguments"],
        )
        self.assertEqual({"Hour": 8, "Minute": 30}, config["StartCalendarInterval"])

    def test_schedule_contract_has_only_one_start_time(self):
        match = re.search(r"RRULE：`([^`]+)`", self.text)
        self.assertIsNotNone(match)
        self.assertEqual(
            "FREQ=WEEKLY;BYDAY=MO,TU,WE,TH,FR,SA;BYHOUR=5;BYMINUTE=0;BYSECOND=0",
            match.group(1),
        )
        self.assertEqual(1, self.text.count("BYHOUR="))


if __name__ == "__main__":
    unittest.main()
