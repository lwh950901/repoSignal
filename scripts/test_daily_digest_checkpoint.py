import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from datetime import datetime, timedelta, timezone
from pathlib import Path

try:
    from scripts import daily_digest_checkpoint as checkpoint
except ModuleNotFoundError:  # Allow direct execution from scripts/.
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


def report_text(date=DATE, slots=None, omit_field=None, repos=None):
    slots = slots or SLOTS
    blocks = []
    for index, (slot, repo) in enumerate(zip(slots, repos or REPOS), 1):
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

    def test_start_is_idempotent_and_preserves_original_deadline(self):
        started = datetime(2026, 9, 14, 21, 30, tzinfo=timezone.utc)
        first = checkpoint.start_run(DATE, self.root, now=started)
        second = checkpoint.start_run(DATE, self.root, now=started + timedelta(minutes=20))

        self.assertEqual(started.isoformat(timespec="seconds"), first["startedAt"])
        self.assertEqual(first["startedAt"], second["startedAt"])
        self.assertEqual(first["deadlineAt"], second["deadlineAt"])
        self.assertEqual("needs_discovery", second["stage"])

    def test_progress_updates_counts_and_caps_recent_errors(self):
        started = datetime(2026, 9, 14, 21, 30, tzinfo=timezone.utc)
        checkpoint.start_run(DATE, self.root, now=started)
        for index in range(7):
            result = checkpoint.record_progress(
                DATE,
                self.root,
                "discovery",
                now=started + timedelta(minutes=index + 1),
                candidate_count=index,
                verified_count=max(index - 2, 0),
                error=f"error-{index}",
            )

        self.assertEqual("discovery", result["stage"])
        self.assertEqual(6, result["candidateCount"])
        self.assertEqual(4, result["verifiedCount"])
        self.assertEqual([f"error-{index}" for index in range(2, 7)], result["errors"])
        self.assertEqual(
            (started + timedelta(minutes=7)).isoformat(timespec="seconds"),
            result["lastProgressAt"],
        )

    def test_audit_actions_follow_runtime_boundaries(self):
        started = datetime(2026, 9, 14, 21, 30, tzinfo=timezone.utc)
        checkpoint.start_run(DATE, self.root, now=started)
        cases = [
            (29, "continue_discovery"),
            (30, "stop_discovery"),
            (60, "start_report"),
            (75, "start_report"),
            (85, "finalize_now"),
            (90, "stop"),
        ]
        for minutes, action in cases:
            with self.subTest(minutes=minutes):
                result = checkpoint.audit_run(
                    DATE, self.root, now=started + timedelta(minutes=minutes)
                )
                self.assertEqual(action, result["action"])
                self.assertEqual(minutes, result["elapsedMinutes"])

    def test_audit_marks_fifteen_minutes_without_progress_as_stalled(self):
        started = datetime(2026, 9, 14, 21, 30, tzinfo=timezone.utc)
        checkpoint.start_run(DATE, self.root, now=started)
        checkpoint.record_progress(
            DATE, self.root, "discovery", now=started + timedelta(minutes=5)
        )

        fresh = checkpoint.audit_run(
            DATE, self.root, now=started + timedelta(minutes=19, seconds=59)
        )
        stalled = checkpoint.audit_run(
            DATE, self.root, now=started + timedelta(minutes=20)
        )
        self.assertFalse(fresh["stalled"])
        self.assertTrue(stalled["stalled"])

    def test_finalize_preserves_runtime_metadata(self):
        started = datetime.now(timezone.utc).replace(microsecond=0)
        checkpoint.start_run(DATE, self.root, now=started)
        self.write_candidates()
        draft, picks = self.write_inputs()

        checkpoint.finalize_run(DATE, self.root, draft, picks)

        saved = json.loads((self.root / "daily-runs" / f"{DATE}.json").read_text())
        self.assertEqual(started.isoformat(timespec="seconds"), saved["startedAt"])
        self.assertEqual((started + timedelta(minutes=90)).isoformat(timespec="seconds"), saved["deadlineAt"])

    def test_manual_resume_resets_budget_but_preserves_progress(self):
        started = datetime(2026, 9, 14, 21, 30, tzinfo=timezone.utc)
        checkpoint.start_run(DATE, self.root, now=started)
        checkpoint.record_progress(
            DATE,
            self.root,
            "discovery",
            now=started + timedelta(minutes=20),
            candidate_count=7,
            verified_count=2,
            error="rate limited",
        )
        resumed_at = started + timedelta(hours=3)

        resumed = checkpoint.resume_run(DATE, self.root, now=resumed_at)

        self.assertEqual(2, resumed["attempt"])
        self.assertEqual(resumed_at.isoformat(timespec="seconds"), resumed["startedAt"])
        self.assertEqual(
            (resumed_at + timedelta(minutes=90)).isoformat(timespec="seconds"),
            resumed["deadlineAt"],
        )
        self.assertEqual("discovery", resumed["stage"])
        self.assertEqual(7, resumed["candidateCount"])
        self.assertEqual(2, resumed["verifiedCount"])
        self.assertEqual(["rate limited"], resumed["errors"])

    def test_finalize_refuses_an_expired_non_complete_budget(self):
        started = datetime(2026, 9, 14, 21, 30, tzinfo=timezone.utc)
        checkpoint.start_run(DATE, self.root, now=started)
        self.write_candidates()
        draft, picks = self.write_inputs()

        with self.assertRaisesRegex(checkpoint.ValidationError, "90 分钟"):
            checkpoint.finalize_run(
                DATE,
                self.root,
                draft,
                picks,
                now=started + timedelta(minutes=91),
            )
        self.assertFalse((self.root / "daily" / f"{DATE}.md").exists())

    def test_cli_resume_and_audit_use_injected_time(self):
        started = "2026-09-14T21:30:00+00:00"
        resumed = "2026-09-15T01:00:00+00:00"
        output = io.StringIO()
        with redirect_stdout(output):
            self.assertEqual(
                0,
                checkpoint.main(
                    ["start", DATE, "--data-root", str(self.root), "--now", started]
                ),
            )
        output = io.StringIO()
        with redirect_stdout(output):
            self.assertEqual(
                0,
                checkpoint.main(
                    ["resume", DATE, "--data-root", str(self.root), "--now", resumed]
                ),
            )
        self.assertEqual(resumed, json.loads(output.getvalue())["startedAt"])
        output = io.StringIO()
        with redirect_stdout(output):
            self.assertEqual(
                0,
                checkpoint.main(
                    ["audit", DATE, "--data-root", str(self.root), "--now", resumed]
                ),
            )
        self.assertEqual("continue_discovery", json.loads(output.getvalue())["action"])

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

    def test_finalize_allows_blocked_burst_slot_with_reusable_pick(self):
        self.write_candidates()
        slots = ["实用型", "潜力型", "学习型", "可复用型"]
        report = report_text(slots=slots).replace(
            "## 今日结论\n\n测试。",
            "## 今日结论\n\n爆发型位置阻塞：本轮无合格加速证据。",
        )
        selections = [
            selection(repo, slot, index)
            for index, (repo, slot) in enumerate(zip(REPOS, slots), 1)
        ]
        draft, picks = self.write_inputs(report=report, selections=selections)

        result = checkpoint.finalize_run(DATE, self.root, draft, picks)

        self.assertEqual("complete", result["stage"])

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
        self.assertNotIn("feasibility", saved)
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

    def test_preflight_checks_real_inputs_without_writing_artifacts(self):
        self.write_candidates()
        draft, picks = self.write_inputs()
        before = {str(p): p.read_bytes() for p in self.root.rglob("*") if p.is_file()}
        output = io.StringIO()
        with redirect_stdout(output):
            code = checkpoint.main([
                "preflight", DATE, "--data-root", str(self.root),
                "--draft", str(draft), "--selections", str(picks),
            ])
        self.assertEqual(0, code)
        self.assertEqual("valid", json.loads(output.getvalue())["status"])
        after = {str(p): p.read_bytes() for p in self.root.rglob("*") if p.is_file()}
        self.assertEqual(before, after)

    def test_preflight_rejects_a_user_request_missing_from_ledger(self):
        self.write_candidates()
        draft, picks = self.write_inputs()
        values = json.loads(picks.read_text())
        values[0]["repo"] = "user/requested"
        picks.write_text(json.dumps(values))
        with self.assertRaisesRegex(checkpoint.ValidationError, "选择不在当日候选中"):
            checkpoint.preflight_run(DATE, self.root, draft, picks)

    def test_report_names_malformed_heading_instead_of_miscounting(self):
        text = report_text().replace("爆发型：acme/burst", "爆发型:acme/burst")
        with self.assertRaisesRegex(checkpoint.ValidationError, "标题格式.*acme/burst"):
            checkpoint.validate_report(text, DATE)

    def test_next_day_preflight_finalize_and_repeat_for_all_supported_layouts(self):
        run_date = "2026-09-18"
        now = datetime(2026, 9, 17, 21, 0, tzinfo=timezone.utc)
        layouts = [SLOTS, SLOTS + ["可复用型"], ["实用型", "潜力型", "学习型", "可复用型"]]
        for index, slots in enumerate(layouts):
            with self.subTest(slots=slots):
                root = self.root / str(index)
                (root / "candidates").mkdir(parents=True)
                repos = (REPOS + ["acme/reusable"])[:len(slots)]
                records = [dict(candidate(repo), date=run_date) for repo in repos]
                (root / "candidates" / f"{run_date}.jsonl").write_text(
                    "".join(json.dumps(record) + "\n" for record in records)
                )
                text = report_text(date=run_date, slots=slots, repos=repos)
                if "爆发型" not in slots:
                    text = text.replace("## 今日结论\n\n测试。", "## 今日结论\n\n爆发型位置阻塞：缺乏加速证据。")
                draft, picks = root / "draft.md", root / "picks.json"
                draft.write_text(text)
                picks.write_text(json.dumps([
                    selection(repo, slot, i) for i, (repo, slot) in enumerate(zip(repos, slots), 1)
                ]))
                checkpoint.start_run(run_date, root, now=now)
                self.assertEqual("valid", checkpoint.preflight_run(run_date, root, draft, picks)["status"])
                for _ in range(2):
                    result = checkpoint.finalize_run(run_date, root, draft, picks, now=now + timedelta(minutes=10))
                    self.assertEqual("complete", result["stage"])
                    self.assertEqual([], result["missing"])
                    self.assertEqual(len(slots), result["selectedCount"])
                self.assertEqual(len(slots), len((root / "history.jsonl").read_text().splitlines()))


if __name__ == "__main__":
    unittest.main()
