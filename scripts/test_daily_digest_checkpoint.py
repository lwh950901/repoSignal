import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

import daily_digest_checkpoint as checkpoint


DATE = "2026-09-14"
SLOTS = ["爆发型", "实用型", "潜力型", "学习型"]
REPOS = ["acme/burst", "acme/useful", "acme/potential", "acme/learning"]
FIELDS = [
    "仓库",
    "一句话定位",
    "类型与适合用途",
    "核心亮点与场景",
    "主要技术栈",
    "实时指标",
    "近期有意义活动",
    "质量证据",
    "风险",
    "推荐理由",
]


def report_text(date=DATE, slots=None, omit_field=None):
    slots = slots or SLOTS
    blocks = []
    for index, (slot, repo) in enumerate(zip(slots, REPOS), 1):
        rows = []
        for field in FIELDS:
            if field == omit_field:
                continue
            value = f"{repo} 的 {field}"
            if field == "仓库":
                value = f"[{repo}](https://github.com/{repo})"
            rows.append(f"- {field}：{value}")
        blocks.append(f"### {index}. {slot}：{repo} — {80 + index}/100\n\n" + "\n".join(rows))
    return (
        f"# GitHub 优质项目每日发现｜{date}\n\n"
        "> 今日重点：测试。\n\n"
        "## 今日结论\n\n测试。\n\n"
        "## 主推荐\n\n"
        + "\n\n".join(blocks)
        + "\n\n## 今天最值得亲自试用\n\nacme/burst。\n"
    )


def candidate(repo):
    return {
        "date": DATE,
        "repo": repo,
        "url": f"https://github.com/{repo}",
        "lanes": ["test"],
        "sources": ["github-search"],
        "stars": 6000,
        "forks": 100,
        "license": "MIT",
        "archived": False,
        "pushed": "2026-09-13T00:00:00Z",
        "status": "discovered",
        "verified": False,
        "reason": None,
    }


def selection(repo, slot, index):
    return {
        "repo": repo,
        "slot": slot,
        "score": 80 + index,
        "reason": f"{slot} 推荐理由",
        "activity": "2026-09-13 有意义提交",
        "sources": ["github-repository", "github-readme"],
        "verified": True,
        "repeat_exception": False,
    }


class DailyDigestCheckpointTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        for name in ("candidates", "daily", "daily-runs"):
            (self.root / name).mkdir()
        (self.root / "history.jsonl").write_text("", encoding="utf-8")
        (self.root / "feedback.jsonl").write_text(
            json.dumps({"repo": "user/requested", "status": "pending"}) + "\n",
            encoding="utf-8",
        )
        (self.root / "trial-status.json").write_text("{}\n", encoding="utf-8")

    def tearDown(self):
        self.temp.cleanup()

    def write_candidates(self, records=None):
        records = records or [candidate(repo) for repo in REPOS]
        text = "".join(json.dumps(item, ensure_ascii=False) + "\n" for item in records)
        (self.root / "candidates" / f"{DATE}.jsonl").write_text(text, encoding="utf-8")

    def write_inputs(self, report=None, selections=None):
        draft = self.root / "draft.md"
        picks = self.root / "selections.json"
        draft.write_text(report or report_text(), encoding="utf-8")
        picks.write_text(
            json.dumps(
                selections
                or [selection(repo, slot, i) for i, (repo, slot) in enumerate(zip(REPOS, SLOTS), 1)],
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        return draft, picks

    def test_inspect_without_candidates_needs_discovery(self):
        result = checkpoint.inspect_run(DATE, self.root)
        self.assertEqual("needs_discovery", result["stage"])
        self.assertIn("candidate_ledger", result["missing"])

    def test_inspect_candidates_ready_is_compact(self):
        self.write_candidates()
        prior = [
            {"date": "2026-09-01", "repo": REPOS[0], "role": "primary"},
            {"date": "2026-09-01", "repo": "unrelated/old", "role": "primary"},
        ]
        (self.root / "history.jsonl").write_text(
            "".join(json.dumps(item) + "\n" for item in prior), encoding="utf-8"
        )
        result = checkpoint.inspect_run(DATE, self.root)
        rendered = json.dumps(result, ensure_ascii=False)
        self.assertEqual("candidates_ready", result["stage"])
        self.assertEqual(4, result["candidateCount"])
        self.assertIn("user/requested", result["userCandidates"])
        self.assertEqual([REPOS[0]], result["recentDuplicateRepos"])
        self.assertLess(len(rendered), 2000)
        self.assertNotIn("近期有意义活动", rendered)

    def test_finalize_rejects_bad_report_without_overwriting_final(self):
        self.write_candidates()
        final = self.root / "daily" / f"{DATE}.md"
        final.write_text("keep me\n", encoding="utf-8")
        draft, picks = self.write_inputs(report=report_text(omit_field="风险"))
        with self.assertRaisesRegex(checkpoint.ValidationError, "风险"):
            checkpoint.finalize_run(DATE, self.root, draft, picks)
        self.assertEqual("keep me\n", final.read_text(encoding="utf-8"))

    def test_finalize_rejects_wrong_slot_and_unknown_candidate(self):
        self.write_candidates()
        wrong = [selection(repo, slot, i) for i, (repo, slot) in enumerate(zip(REPOS, SLOTS), 1)]
        wrong[0]["repo"] = "outside/not-found"
        draft, picks = self.write_inputs(selections=wrong)
        with self.assertRaisesRegex(checkpoint.ValidationError, "候选"):
            checkpoint.finalize_run(DATE, self.root, draft, picks)

        draft.write_text(report_text(slots=["实用型", "爆发型", "潜力型", "学习型"]), encoding="utf-8")
        good = [selection(repo, slot, i) for i, (repo, slot) in enumerate(zip(REPOS, SLOTS), 1)]
        picks.write_text(json.dumps(good, ensure_ascii=False), encoding="utf-8")
        with self.assertRaisesRegex(checkpoint.ValidationError, "顺序"):
            checkpoint.finalize_run(DATE, self.root, draft, picks)

    def test_finalize_rejects_unapproved_recent_duplicate(self):
        self.write_candidates()
        prior = {
            "date": "2026-09-01",
            "repo": REPOS[0],
            "slot": "潜力型",
            "role": "primary",
        }
        (self.root / "history.jsonl").write_text(json.dumps(prior) + "\n", encoding="utf-8")
        draft, picks = self.write_inputs()
        with self.assertRaisesRegex(checkpoint.ValidationError, "90 天"):
            checkpoint.finalize_run(DATE, self.root, draft, picks)

    def test_finalize_rejects_conflicting_same_day_history(self):
        self.write_candidates()
        stale = {
            "date": DATE,
            "repo": "stale/selection",
            "slot": "潜力型",
            "score": 80,
            "role": "primary",
        }
        (self.root / "history.jsonl").write_text(json.dumps(stale) + "\n", encoding="utf-8")
        draft, picks = self.write_inputs()
        with self.assertRaisesRegex(checkpoint.ValidationError, "同日 history"):
            checkpoint.finalize_run(DATE, self.root, draft, picks)

    def test_finalize_is_atomic_enough_and_idempotent(self):
        self.write_candidates()
        draft, picks = self.write_inputs()
        first = checkpoint.finalize_run(DATE, self.root, draft, picks)
        second = checkpoint.finalize_run(DATE, self.root, draft, picks)

        self.assertEqual("complete", first["stage"])
        self.assertEqual("complete", second["stage"])
        history = [json.loads(line) for line in (self.root / "history.jsonl").read_text().splitlines()]
        self.assertEqual(4, len(history))
        candidates = [
            json.loads(line)
            for line in (self.root / "candidates" / f"{DATE}.jsonl").read_text().splitlines()
        ]
        self.assertTrue(all(item["status"] == "primary" and item["verified"] for item in candidates))
        status = json.loads((self.root / "trial-status.json").read_text())
        self.assertEqual(DATE, status["latest_daily_run"]["date"])
        saved = json.loads((self.root / "daily-runs" / f"{DATE}.json").read_text())
        self.assertEqual("complete", saved["stage"])
        self.assertEqual("complete", checkpoint.inspect_run(DATE, self.root)["stage"])

    def test_corrupt_candidate_does_not_overwrite_report(self):
        path = self.root / "candidates" / f"{DATE}.jsonl"
        path.write_text("{broken\n", encoding="utf-8")
        final = self.root / "daily" / f"{DATE}.md"
        final.write_text("keep me\n", encoding="utf-8")
        draft, picks = self.write_inputs()
        with self.assertRaises(checkpoint.ValidationError):
            checkpoint.finalize_run(DATE, self.root, draft, picks)
        self.assertEqual("keep me\n", final.read_text(encoding="utf-8"))

    def test_cli_inspect_prints_one_compact_json_object(self):
        self.write_candidates()
        output = io.StringIO()
        with redirect_stdout(output):
            exit_code = checkpoint.main(["inspect", DATE, "--data-root", str(self.root)])
        self.assertEqual(0, exit_code)
        self.assertEqual("candidates_ready", json.loads(output.getvalue())["stage"])


if __name__ == "__main__":
    unittest.main()
