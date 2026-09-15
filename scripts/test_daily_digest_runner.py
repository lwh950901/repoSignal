import json
import os
import tempfile
import time
import unittest
from contextlib import redirect_stdout
from io import StringIO
from unittest.mock import patch
from pathlib import Path

try:
    from scripts import candidate_ledger
    from scripts import daily_digest_runner as runner
except ModuleNotFoundError:  # Allow direct execution from scripts/.
    import candidate_ledger
    import daily_digest_runner as runner


DATE = "2026-09-15"


def candidate(repo, lane, *, stars=6000, license_id="MIT", archived=False, pushed="2026-09-14T12:00:00Z"):
    return {
        "date": DATE,
        "repo": repo,
        "url": f"https://github.com/{repo}",
        "description": f"Compact description for {repo}",
        "language": "Python",
        "topics": ["agents", "automation"],
        "created": "2026-07-01T00:00:00Z",
        "updated": pushed,
        "lanes": [lane],
        "sources": ["github-search"],
        "stars": stars,
        "forks": 120,
        "license": license_id,
        "archived": archived,
        "pushed": pushed,
        "status": "discovered",
        "verified": False,
        "reason": None,
    }


class DailyDigestShortlistTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root / "candidates").mkdir()
        (self.root / "daily-runs").mkdir()
        (self.root / "history.jsonl").write_text("", encoding="utf-8")
        (self.root / "feedback.jsonl").write_text(
            json.dumps({"repo": "user/requested", "status": "pending"}) + "\n",
            encoding="utf-8",
        )

    def tearDown(self):
        self.temp.cleanup()

    def write_candidates(self, records):
        path = self.root / "candidates" / f"{DATE}.jsonl"
        path.write_text(
            "".join(json.dumps(record, ensure_ascii=False) + "\n" for record in records),
            encoding="utf-8",
        )

    def test_shortlist_applies_hard_filters_and_three_per_slot_cap(self):
        lanes = ["growth", "mature", "emerging", "learning_rag"]
        records = []
        for lane in lanes:
            records.extend(
                candidate(f"acme/{lane}-{index}", lane, stars=9000 - index)
                for index in range(5)
            )
        records.extend(
            [
                candidate("bad/archived", "mature", archived=True),
                candidate("bad/no-license", "emerging", license_id="NOASSERTION"),
                candidate("old/recent-repeat", "learning_rag"),
            ]
        )
        self.write_candidates(records)
        (self.root / "history.jsonl").write_text(
            json.dumps({"date": "2026-09-01", "repo": "old/recent-repeat", "role": "primary"})
            + "\n",
            encoding="utf-8",
        )

        result = runner.build_shortlist(DATE, self.root)

        self.assertEqual(
            {"爆发型", "实用型", "潜力型", "学习型"}, set(result["slots"])
        )
        self.assertTrue(all(len(items) <= 3 for items in result["slots"].values()))
        rendered = json.dumps(result, ensure_ascii=False, separators=(",", ":"))
        self.assertNotIn("bad/archived", rendered)
        self.assertNotIn("bad/no-license", rendered)
        self.assertNotIn("old/recent-repeat", rendered)
        self.assertEqual(1, result["rejected"]["archived"])
        self.assertEqual(1, result["rejected"]["unclearLicense"])
        self.assertEqual(1, result["rejected"]["recentDuplicate"])
        self.assertLess(len(rendered), 7000)

    def test_pending_user_candidates_remain_visible_and_repeat_is_flagged(self):
        requested = candidate("user/requested", "user_candidate", stars=7000)
        self.write_candidates([requested])
        (self.root / "history.jsonl").write_text(
            json.dumps({"date": "2026-09-10", "repo": "user/requested", "role": "primary"})
            + "\n",
            encoding="utf-8",
        )

        result = runner.build_shortlist(DATE, self.root)

        self.assertEqual(["user/requested"], result["userCandidates"])
        item = result["slots"]["爆发型"][0]
        self.assertEqual("user/requested", item["repo"])
        self.assertTrue(item["repeatRequiresEvidence"])

    def test_shortlist_is_deterministic_and_keeps_quality_metadata(self):
        records = [
            candidate("acme/older", "mature", stars=9000, pushed="2026-09-10T00:00:00Z"),
            candidate("acme/newer", "mature", stars=5000, pushed="2026-09-14T00:00:00Z"),
        ]
        self.write_candidates(records)

        first = runner.build_shortlist(DATE, self.root)
        second = runner.build_shortlist(DATE, self.root)

        self.assertEqual(first, second)
        items = first["slots"]["实用型"]
        self.assertEqual(["acme/older", "acme/newer"], [item["repo"] for item in items])
        for field in ("description", "language", "topics", "created", "updated", "license"):
            self.assertIn(field, items[0])

    def test_verified_primary_candidates_survive_compaction_in_compatible_slots(self):
        records = [
            candidate(f"popular/cross-{index}", "cross_domain", stars=100000 - index)
            for index in range(5)
        ]
        questdb = candidate("questdb/questdb", "cross_domain", stars=17321)
        questdb.update({"status": "primary", "verified": True})
        text_to_cad = candidate("earthtojake/text-to-cad", "cross_domain", stars=15762)
        text_to_cad.update({"status": "primary", "verified": True})
        paddle = candidate(
            "paddlepaddle/paddleocr",
            "learning_rag",
            stars=89521,
            pushed="2026-07-22T11:59:34Z",
        )
        paddle.update({"status": "primary", "verified": True})
        records.extend([questdb, text_to_cad, paddle])
        records.extend(
            candidate(f"popular/learning-{index}", "learning_rag", stars=120000 - index)
            for index in range(4)
        )
        self.write_candidates(records)

        result = runner.build_shortlist(DATE, self.root)

        useful = {item["repo"] for item in result["slots"]["实用型"]}
        potential = {item["repo"] for item in result["slots"]["潜力型"]}
        learning = {item["repo"] for item in result["slots"]["学习型"]}
        self.assertIn("questdb/questdb", useful)
        self.assertIn("earthtojake/text-to-cad", potential)
        self.assertIn("paddlepaddle/paddleocr", learning)

    def test_candidate_ledger_retains_compact_metadata(self):
        raw = {
            "full_name": "Acme/Metadata",
            "description": "Useful automation toolkit",
            "language": "Python",
            "topics": ["agents", "workflow"],
            "created_at": "2026-01-01T00:00:00Z",
            "updated_at": "2026-09-14T00:00:00Z",
            "objective_score_hint": 88,
            "risk_flags": ["pre-release"],
            "open_issues": 12,
        }
        record = candidate_ledger.build_record(raw, DATE, "mature", "github-search")
        self.assertEqual("Useful automation toolkit", record["description"])
        self.assertEqual("Python", record["language"])
        self.assertEqual(["agents", "workflow"], record["topics"])
        self.assertEqual("2026-01-01T00:00:00Z", record["created"])
        self.assertEqual("2026-09-14T00:00:00Z", record["updated"])
        self.assertEqual(88, record["scoreHint"])
        self.assertEqual(["pre-release"], record["riskFlags"])
        self.assertEqual(12, record["openIssues"])

    def test_shortlist_output_mode_prints_only_a_count_summary(self):
        self.write_candidates([candidate("acme/compact", "mature")])
        output_path = Path(self.temp.name) / "shortlist.json"
        stdout = StringIO()

        with redirect_stdout(stdout):
            exit_code = runner.main(
                [
                    "shortlist",
                    DATE,
                    "--data-root",
                    str(self.root),
                    "--output",
                    str(output_path),
                ]
            )

        self.assertEqual(0, exit_code)
        summary = json.loads(stdout.getvalue())
        self.assertNotIn("slots", summary)
        self.assertEqual(1, summary["candidateCount"])
        self.assertIn("slots", json.loads(output_path.read_text(encoding="utf-8")))

    def test_shortlist_cli_refuses_an_expired_budget(self):
        self.write_candidates([candidate("acme/late", "mature")])
        started = runner.datetime.now(runner.timezone.utc) - runner.timedelta(minutes=91)
        runner.checkpoint.start_run(DATE, self.root, now=started)
        stdout = StringIO()

        with redirect_stdout(stdout):
            exit_code = runner.main(
                ["shortlist", DATE, "--data-root", str(self.root)]
            )

        self.assertEqual(2, exit_code)
        self.assertIn("90 分钟", json.loads(stdout.getvalue())["error"])


class DailyDigestDiscoveryTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name) / "data"
        (self.root / "candidates").mkdir(parents=True)
        (self.root / "daily-runs").mkdir()
        (self.root / "history.jsonl").write_text("", encoding="utf-8")
        (self.root / "feedback.jsonl").write_text("", encoding="utf-8")
        self.log = Path(self.temp.name) / "scanner.log"
        self.scanner = Path(self.temp.name) / "fake_scanner.py"
        self.scanner.write_text(
            """#!/usr/bin/env python3
import hashlib
import json
import os
import sys

args = sys.argv[1:]
query = args[args.index('--query') + 1]
with open(os.environ['FAKE_SCANNER_LOG'], 'a', encoding='utf-8') as handle:
    handle.write(json.dumps({'query': query, 'insecure': '--insecure' in args}) + '\\n')
mode = os.environ.get('FAKE_SCANNER_MODE', 'ok')
if mode == 'tls_once' and '--insecure' not in args:
    print('certificate verify failed', file=sys.stderr)
    raise SystemExit(1)
if mode == 'all_fail' or (mode == 'partial' and 'robotics' in query):
    print('GitHub API error 403: rate limit', file=sys.stderr)
    raise SystemExit(1)
slug = hashlib.sha1(query.encode()).hexdigest()[:10]
print(json.dumps([{
    'full_name': 'scan/' + slug,
    'html_url': 'https://github.com/scan/' + slug,
    'description': 'scanner result',
    'language': 'Python',
    'topics': ['agent'],
    'created_at': '2026-08-01T00:00:00Z',
    'updated_at': '2026-09-14T00:00:00Z',
    'pushed_at': '2026-09-14T00:00:00Z',
    'stargazers_count': 6000,
    'forks_count': 100,
    'license': 'MIT',
    'archived': False,
}]))
""",
            encoding="utf-8",
        )

    def tearDown(self):
        self.temp.cleanup()

    def env(self, mode):
        value = dict(os.environ)
        value["FAKE_SCANNER_LOG"] = str(self.log)
        value["FAKE_SCANNER_MODE"] = mode
        return value

    def calls(self):
        if not self.log.exists():
            return []
        return [json.loads(line) for line in self.log.read_text().splitlines()]

    def ledger(self):
        path = self.root / "candidates" / f"{DATE}.jsonl"
        return [json.loads(line) for line in path.read_text().splitlines()]

    def test_discover_runs_six_lanes_and_retains_provenance(self):
        result = runner.discover(
            DATE, self.root, self.scanner, env=self.env("ok"), timeout_seconds=5
        )

        self.assertEqual("complete", result["status"])
        self.assertEqual(6, result["successfulLanes"])
        self.assertEqual(6, len(self.calls()))
        observed_lanes = {lane for item in self.ledger() for lane in item["lanes"]}
        self.assertEqual(set(runner.DISCOVERY_QUERIES), observed_lanes)

    def test_tls_error_retries_once_with_insecure(self):
        result = runner.discover(
            DATE, self.root, self.scanner, env=self.env("tls_once"), timeout_seconds=5
        )

        calls = self.calls()
        self.assertEqual("complete", result["status"])
        self.assertEqual(12, len(calls))
        self.assertEqual(6, sum(1 for call in calls if call["insecure"]))

    def test_non_tls_failure_is_not_retried_and_partial_results_are_written(self):
        result = runner.discover(
            DATE, self.root, self.scanner, env=self.env("partial"), timeout_seconds=5
        )

        self.assertEqual("partial", result["status"])
        self.assertEqual(5, result["successfulLanes"])
        self.assertEqual(1, len(result["errors"]))
        self.assertEqual(6, len(self.calls()))
        self.assertEqual(5, len(self.ledger()))

    def test_all_non_tls_failures_are_not_retried(self):
        with self.assertRaisesRegex(RuntimeError, "全部失败"):
            runner.discover(
                DATE, self.root, self.scanner, env=self.env("all_fail"), timeout_seconds=5
            )
        self.assertEqual(6, len(self.calls()))
        self.assertFalse((self.root / "candidates" / f"{DATE}.jsonl").exists())

    def test_existing_candidate_ledger_is_never_overwritten(self):
        path = self.root / "candidates" / f"{DATE}.jsonl"
        path.write_text('{"keep":true}\n', encoding="utf-8")

        with self.assertRaisesRegex(FileExistsError, "已存在"):
            runner.discover(
                DATE, self.root, self.scanner, env=self.env("ok"), timeout_seconds=5
            )

        self.assertEqual('{"keep":true}\n', path.read_text(encoding="utf-8"))
        self.assertEqual([], self.calls())

    def test_tls_retry_is_skipped_when_the_deadline_expires(self):
        failure = runner.subprocess.CompletedProcess(
            args=[], returncode=1, stdout="", stderr="certificate verify failed"
        )

        def slow_first_attempt(*args, **kwargs):
            time.sleep(0.02)
            return failure

        deadline = runner.datetime.now(runner.timezone.utc) + runner.timedelta(seconds=0.005)
        with patch.object(runner, "_run_scanner", side_effect=slow_first_attempt) as scanner:
            result = runner._discover_lane(
                "growth", "query", self.scanner, 5, None, deadline
            )

        self.assertEqual(1, scanner.call_count)
        self.assertIn("deadline", result["error"])


if __name__ == "__main__":
    unittest.main()
